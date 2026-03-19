# analyst/views/report_builder.py
"""
Report Builder – async JSON views.

GET  /analyst/reports/              → list reports
GET  /analyst/reports/builder/      → builder SPA page
POST /analyst/reports/build/        → run function, save Report, return result
GET  /analyst/reports/<id>/         → single report detail
POST /analyst/reports/<id>/delete/  → delete
GET  /analyst/reports/<id>/export/  → CSV download
GET  /analyst/reports/api/functions/ → registry (for builder UI)
"""

import json
import logging
import math
import pickle
import base64
import uuid as _uuid_mod
from io import StringIO

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.apps import apps as django_apps
from django.db.models import Field as DField

from analyst.models import StoredDataset, Report, AnalystBase, CrossSource
from analyst.report_functions import get_registry, get_function, get_meta
from analyst.utils.clipboard import DataFrameClipboard
from analyst.services.base_validator import BaseValidator

logger = logging.getLogger(__name__)
# ─── JSON serialization ───────────────────────────────────────────────────────

def _json_safe(obj):
    """Recursively convert to JSON-safe Python primitives."""
    if obj is None: return None
    if isinstance(obj, bool): return obj
    if isinstance(obj, int): return obj
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, str): return obj
    if isinstance(obj, _uuid_mod.UUID): return str(obj)
    if hasattr(obj, 'isoformat'): return obj.isoformat()
    if isinstance(obj, dict): return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [_json_safe(i) for i in obj]
    try:
        f = float(obj)
        if math.isnan(f) or math.isinf(f): return None
        return int(f) if float(int(f)) == f else f
    except (TypeError, ValueError): pass
    return str(obj)


def _safe_json_str(obj) -> str:
    """Serialize to strictly valid JSON string safe for inline <script>."""
    import re as _re
    result = json.dumps(_json_safe(obj), ensure_ascii=True, allow_nan=True)
    result = _re.sub(r'\bNaN\b',       'null', result)
    result = _re.sub(r'\bInfinity\b',  'null', result)
    result = _re.sub(r'\b-Infinity\b', 'null', result)
    return result.replace('</', r'<\/')





# ─── Helpers ──────────────────────────────────────────────────────────────────

def _deserialize(s: str) -> pd.DataFrame:
    return pickle.loads(base64.b64decode(s.encode()))


def _load_cache(key: str):
    raw = cache.get(key)
    if not raw:
        return None, None
    try:
        return _deserialize(raw["data"]), raw.get("meta", {})
    except Exception as exc:
        logger.error("Report builder deserialize error %s: %s", key, exc)
        return None, None


def _load_source(src: dict, request) -> pd.DataFrame:
    """
    Load a DataFrame from a source descriptor.

    src = {"type": "model"|"dataset"|"clip"|"analyst_base", "ref": "...", "name": "..."}
    """
    src_type = src.get("type")
    ref      = src.get("ref", "")

    if src_type == "dataset":
        ds = StoredDataset.objects.get(id=ref, created_by=request.user)
        df, _ = _load_cache(ds.cache_key)
        if df is None and ds.data_blob:
            try:
                df = _deserialize(ds.data_blob)
            except Exception:
                df = None
        if df is None:
            raise ValueError(f"Dataset '{ds.name}' no disponible.")
        return df

    if src_type == "cross_source":
        from analyst.models import CrossSource
        cs = CrossSource.objects.get(id=ref, created_by=request.user)
        if not cs.last_result:
            raise ValueError(f"El cruce '{cs.name}' no tiene resultado. Ejecútalo primero.")
        ds = cs.last_result
        df, _ = _load_cache(ds.cache_key)
        if df is None and ds.data_blob:
            try:
                df = _deserialize(ds.data_blob)
            except Exception:
                df = None
        if df is None:
            raise ValueError(f"Resultado del cruce '{cs.name}' no disponible.")
        return df

    elif src_type == "clip":
        df, _ = DataFrameClipboard.retrieve_df(request, ref)
        if df is None:
            raise ValueError(f"Clip '{ref}' no encontrado o expirado.")
        return df

    elif src_type == "analyst_base":
        try:
            base = AnalystBase.objects.get(id=ref, created_by=request.user)
        except AnalystBase.DoesNotExist:
            raise ValueError(f"AnalystBase '{ref}' no encontrada o sin acceso.")
        df = BaseValidator.load_dataframe(base)
        if df is None or df.empty:
            raise ValueError(f"La base '{base.name}' no tiene datos.")
        return df

    elif src_type == "model":
        app_label, model_name = ref.rsplit(".", 1)
        model_class = django_apps.get_model(app_label, model_name)
        qs = model_class.objects.all().values()
        df = pd.DataFrame.from_records(list(qs))
        if df.empty:
            raise ValueError(f"El modelo '{model_name}' no tiene registros.")
        return df

    raise ValueError(f"Tipo de fuente desconocido: '{src_type}'.")


def _report_row(r: Report) -> dict:
    return {
        "id":           str(r.id),
        "name":         r.name,
        "description":  r.description,
        "function_key": r.function_key,
        "function_label": get_meta(r.function_key)["label"] if get_meta(r.function_key) else r.function_key,
        "status":       r.status,
        "status_label": r.get_status_display(),
        "error_msg":    r.error_msg,
        "sources":      r.sources,
        "params":       r.params,
        "result_meta":  r.result_meta,
        "rows":         r.row_count,
        "created_at":   r.created_at.isoformat(),
        "updated_at":   r.updated_at.isoformat(),
        "created_by":   r.created_by.get_full_name() or r.created_by.username,
    }


def _df_to_json_safe(df: pd.DataFrame) -> list:
    """Convert DataFrame to list-of-dicts with JSON-safe values."""
    records = []
    for _, row in df.iterrows():
        rec = {}
        for col, val in row.items():
            if val is None or (isinstance(val, float) and pd.isna(val)):
                rec[str(col)] = None
            elif hasattr(val, "item"):          # numpy scalar
                rec[str(col)] = val.item()
            else:
                rec[str(col)] = val
        records.append(rec)
    return records


# ═══════════════════════════════════════════════════════════════════════════════
# Views
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def report_list(request):
    """Report list + builder SPA page."""
    reports  = Report.objects.filter(created_by=request.user).order_by("-created_at")
    datasets = StoredDataset.objects.filter(created_by=request.user).order_by("name")
    analyst_bases = AnalystBase.objects.filter(created_by=request.user).order_by("name")
    clips    = DataFrameClipboard.list_clips(request)

    # Available models (reuse logic from forms.py FORBIDDEN_MODELS pattern)
    try:
        from analyst.constants import FORBIDDEN_MODELS
        forbidden = set(FORBIDDEN_MODELS.values())
    except ImportError:
        forbidden = set()

    model_choices = []
    for app_config in django_apps.get_app_configs():
        if any(app_config.name.startswith(f) for f in ["auth", "admin", "contenttypes", "sessions"]):
            continue
        for model in app_config.get_models():
            path = f"{app_config.name}.{model.__name__}"
            if path not in forbidden:
                model_choices.append({
                    "value": path,
                    "label": f"{getattr(app_config, 'verbose_name', app_config.name)} – {model._meta.verbose_name}",
                })

    cross_sources = CrossSource.objects.filter(created_by=request.user).select_related('last_result').order_by('name')

    return render(request, "analyst/report_builder.html", {
        "reports":            reports,
        "registry":           get_registry(),
        # JSON-safe pre-serialized data for JS
        "registry_json":      _safe_json_str(get_registry()),
        "datasets_json":      _safe_json_str([
            {"id": str(ds.id), "name": ds.name, "columns": list(ds.columns)}
            for ds in datasets
        ]),
        "analyst_bases_json": _safe_json_str([
            {"id": str(b.id), "name": b.name, "columns": [col["name"] for col in b.schema]}
            for b in analyst_bases
        ]),
        "cross_sources_json": _safe_json_str([
            {"id": str(cs.id), "name": cs.name,
             "columns": list(cs.last_result.columns) if cs.last_result else []}
            for cs in cross_sources
        ]),
        "clips_json":         _safe_json_str([
            {"key": cl.get("key",""), "name": cl.get("filename") or cl.get("key",""),
             "columns": cl.get("columns", [])}
            for cl in clips
        ]),
        "model_choices_json": _safe_json_str(sorted(model_choices, key=lambda x: x["label"])),
        "reports_count":      reports.count(),
        "datasets_count":     datasets.count(),
        "clips_count":        len(clips),
    })


@login_required
@require_GET
def functions_api(request):
    """Return the function registry as JSON (for JS builder)."""
    return JsonResponse({"success": True, "functions": get_registry()})


@login_required
@require_POST
def report_build(request):
    """
    Build and persist a Report.

    POST JSON:
    {
        "name":         "Notas Mayo 2025",
        "description":  "...",
        "function_key": "quality_avg",
        "sources": {
            "base":  {"type": "model",   "ref": "accounts.Agent", "name": "Agentes"},
            "notes": {"type": "dataset", "ref": "<uuid>",         "name": "Notas Mayo"}
        },
        "params": {
            "join_col_base":  "id",
            "join_col_notes": "agente_id",
            "note_cols":      ["nota_llamada", "nota_chat"],
            "group_by":       "equipo",
            "min_score":      75
        }
    }
    """
    try:
        body         = json.loads(request.body)
        name         = (body.get("name") or "").strip()
        description  = body.get("description", "")
        function_key = body.get("function_key", "").strip()
        sources_desc = body.get("sources", {})   # {source_id: {type, ref, name}}
        params       = body.get("params", {})

        if not name:
            return JsonResponse({"success": False, "error": "Nombre requerido."}, status=400)
        if not function_key:
            return JsonResponse({"success": False, "error": "Función requerida."}, status=400)

        fn = get_function(function_key)
        if fn is None:
            return JsonResponse({"success": False, "error": f"Función '{function_key}' no registrada."}, status=400)

        # Create the DB row immediately so we can return its id to the client
        report = Report.objects.create(
            name=name, description=description,
            function_key=function_key,
            sources=list(sources_desc.values()),
            params=params,
            status="running",
            created_by=request.user,
        )

        try:
            # Load all source DataFrames
            dfs = {}
            for src_id, src_desc in sources_desc.items():
                dfs[src_id] = _load_source(src_desc, request)

            # Run the registered function
            result_df = fn(dfs, params)

            if not isinstance(result_df, pd.DataFrame):
                raise TypeError("La función debe devolver un DataFrame.")

            col_dtypes = result_df.dtypes
            columns    = [str(c) for c in result_df.columns]
            dtype_map  = {str(col): str(col_dtypes[col]) for col in result_df.columns}

            report.result_data = _df_to_json_safe(result_df)
            report.result_meta = {
                "rows":         len(result_df),
                "columns":      columns,
                "dtype_map":    dtype_map,
                "generated_at": report.updated_at.isoformat() if report.updated_at else None,
            }
            report.status    = "done"
            report.error_msg = ""
            report.save()

            logger.info("Report built: %s (%d rows) fn=%s by %s",
                        report.name, len(result_df), function_key, request.user)

            # Return first 100 rows for immediate preview
            preview_rows = _df_to_json_safe(result_df.head(100))
            return JsonResponse({
                "success": True,
                "report":  _report_row(report),
                "preview": {
                    "columns": columns,
                    "rows":    preview_rows,
                    "total":   len(result_df),
                },
            })

        except Exception as fn_exc:
            report.status    = "error"
            report.error_msg = str(fn_exc)
            report.save()
            logger.error("Report build fn error: %s", fn_exc, exc_info=True)
            return JsonResponse({"success": False, "error": str(fn_exc), "report_id": str(report.id)}, status=422)

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("report_build error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_GET
def report_detail(request, report_id):
    """Return full report data (paginated rows)."""
    try:
        report = get_object_or_404(Report, id=report_id, created_by=request.user)
        page   = int(request.GET.get("page", 1))
        size   = int(request.GET.get("size", 100))
        data   = report.result_data
        start  = (page - 1) * size
        return JsonResponse({
            "success": True,
            "report":  _report_row(report),
            "rows":    data[start:start + size],
            "total":   len(data),
            "page":    page,
            "pages":   max(1, (len(data) + size - 1) // size),
        })
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_POST
def report_delete(request, report_id):
    """Delete a report."""
    try:
        report = get_object_or_404(Report, id=report_id, created_by=request.user)
        report.delete()
        return JsonResponse({"success": True})
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_GET
def report_export(request, report_id):
    """Download report as CSV."""
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    if not report.result_data:
        return HttpResponse("Sin datos.", status=404, content_type="text/plain")

    df       = pd.DataFrame(report.result_data)
    filename = f"{report.name.replace(' ', '_')}.csv"
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    df.to_csv(response, index=False)
    return response


@login_required
@require_POST
def report_rerun(request, report_id):
    """
    Re-run an existing report with the same config.
    Updates result_data, result_meta and status in-place.
    """
    try:
        report = get_object_or_404(Report, id=report_id, created_by=request.user)

        fn = get_function(report.function_key)
        if fn is None:
            return JsonResponse({"success": False, "error": f"Función '{report.function_key}' ya no está registrada."}, status=400)

        report.status = "running"
        report.save(update_fields=["status"])

        # Rebuild sources_desc from stored sources
        sources_desc = {s.get("id", str(i)): s for i, s in enumerate(report.sources)}
        # report.sources was stored as list of source dicts — rebuild keyed by position
        # Try to reconstruct {src_id: {type, ref, name}} from sources list
        # Since we store list(sources_desc.values()), we need to rebuild keys from function meta
        meta = get_meta(report.function_key)
        if meta and meta.get("sources"):
            src_keys = [s["id"] for s in meta["sources"]]
            src_list = report.sources
            sources_desc = {
                src_keys[i]: src_list[i]
                for i in range(min(len(src_keys), len(src_list)))
            }
        else:
            sources_desc = {str(i): s for i, s in enumerate(report.sources)}

        dfs = {}
        for src_id, src_desc in sources_desc.items():
            dfs[src_id] = _load_source(src_desc, request)

        result_df = fn(dfs, report.params)
        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("La función debe devolver un DataFrame.")

        columns   = [str(c) for c in result_df.columns]
        dtype_map = {str(col): str(result_df.dtypes[col]) for col in result_df.columns}

        report.result_data = _df_to_json_safe(result_df)
        report.result_meta = {
            "rows": len(result_df), "columns": columns, "dtype_map": dtype_map,
            "generated_at": None,
        }
        report.status    = "done"
        report.error_msg = ""
        report.save()

        logger.info("Report re-run: %s (%d rows) by %s", report.name, len(result_df), request.user)

        preview_rows = _df_to_json_safe(result_df.head(100))
        return JsonResponse({
            "success": True,
            "report":  _report_row(report),
            "preview": {"columns": columns, "rows": preview_rows, "total": len(result_df)},
        })

    except Exception as exc:
        if 'report' in dir():
            report.status    = "error"
            report.error_msg = str(exc)
            report.save(update_fields=["status", "error_msg"])
        logger.error("report_rerun %s: %s", report_id, exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=422)
