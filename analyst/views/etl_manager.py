# analyst/views/etl_manager.py
"""
ETL Manager views — con seguridad reforzada.

Capas de seguridad implementadas:
  1. ALLOWED_ETL_APPS  — whitelist de apps cuyos modelos son extractables.
                         Se configura en settings.ANALYST_ETL_ALLOWED_APPS.
  2. sql_override      — solo superusuarios pueden definir o ejecutar SQL raw.
  3. Validacion SQL    — solo SELECT. Se rechazan DDL/DML.
  4. model_path        — validado en guardado Y en ejecucion.
  5. Filtros ORM       — lookup restringido a lista segura; campos validados
                         contra el modelo real para evitar traversal.
  6. Limite de filas   — max_rows con techo configurable para no-superusers.
  7. AnalystBase       — el usuario solo puede extraer sus propias bases.
"""

import re
import json
import time
import logging
import pickle
import base64
import uuid as _uuid

import pandas as pd
from django.apps    import apps as django_apps
from django.conf    import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db      import connection
from django.db.models import (
    Count, Sum, Avg, Min, Max,
    IntegerField, FloatField, DecimalField,
    DateField, DateTimeField, BooleanField,
)
from django.http    import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils   import timezone
from django.views.decorators.http import require_GET, require_POST

# ← CAMBIO: se agrega AnalystBase al import
from analyst.models import ETLSource, ETLJob, StoredDataset, AnalystBase

logger = logging.getLogger(__name__)

# ============================================================================
# Security configuration
# ============================================================================

_HARDCODED_EXCLUDED = frozenset({
    'admin', 'auth', 'contenttypes', 'sessions',
    'messages', 'staticfiles', 'channels',
    'django_extensions', 'axes',
})

def _get_allowed_apps() -> frozenset:
    configured = getattr(settings, 'ANALYST_ETL_ALLOWED_APPS', None)
    if configured is not None and len(configured) > 0:
        return frozenset(configured) - _HARDCODED_EXCLUDED
    all_apps = {m._meta.app_label for m in django_apps.get_models()}
    return all_apps - _HARDCODED_EXCLUDED


def _is_model_allowed(model_path: str) -> bool:
    if not model_path or '.' not in model_path:
        return False
    return model_path.split('.')[0].lower() in _get_allowed_apps()


_SAFE_LOOKUPS = frozenset({
    'exact', 'iexact', 'contains', 'icontains',
    'startswith', 'istartswith', 'endswith', 'iendswith',
    'gt', 'gte', 'lt', 'lte',
    'in', 'isnull', 'range',
    'date', 'year', 'month', 'day',
})

_SQL_FORBIDDEN = re.compile(
    r'\b(DROP|DELETE|INSERT|UPDATE|ALTER|TRUNCATE|EXEC|EXECUTE|CALL|CREATE|REPLACE|MERGE|GRANT|REVOKE)\b',
    re.IGNORECASE,
)
_SQL_MUST_SELECT = re.compile(r'^\s*(--[^\n]*\n\s*)*SELECT\b', re.IGNORECASE)

MAX_ROWS_NON_SUPERUSER = getattr(settings, 'ANALYST_ETL_MAX_ROWS', 100_000)


def _validate_sql(sql: str):
    sql = sql.strip()
    if not sql:
        return "El SQL no puede estar vacio."
    if not _SQL_MUST_SELECT.match(sql):
        return "Solo se permiten consultas SELECT."
    if _SQL_FORBIDDEN.search(sql):
        return "El SQL contiene palabras clave no permitidas (DDL/DML)."
    return None


def _validate_field_name(name: str) -> bool:
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(name)))


def _model_field_names(model_path: str) -> set:
    """
    Retorna el conjunto de nombres de campo consultables via ORM.
    Usa f.attname para FK reales (ej: user_id) en lugar de f.name+'_id',
    y omite relaciones no-concretas (GenericForeignKey, M2M, reverse FK).
    """
    try:
        app_label, model_name = model_path.rsplit('.', 1)
        Model = django_apps.get_model(app_label, model_name)
        names = set()
        for f in Model._meta.get_fields():
            if f.many_to_many or f.one_to_many:
                continue
            if f.is_relation:
                attname = getattr(f, 'attname', None)
                if attname:
                    names.add(attname)
            else:
                names.add(f.name)
        return names
    except Exception:
        return set()

# ============================================================================
# Helpers
# ============================================================================

AGG_FUNCS = {'count': Count, 'sum': Sum, 'avg': Avg, 'min': Min, 'max': Max}


def _serialize(df: pd.DataFrame) -> str:
    return base64.b64encode(pickle.dumps(df)).decode()


def _save_as_stored_dataset(df, name, description, source_label, user):
    from django.core.cache import cache as _cache
    ds_id    = _uuid.uuid4()
    perm_key = StoredDataset.make_cache_key(str(ds_id))
    dtype_map = {str(c): str(df.dtypes.iloc[i]) for i, c in enumerate(df.columns)}
    blob = _serialize(df)
    _cache.set(perm_key, {"data": blob,
        "meta": {"stored_dataset_id": str(ds_id), "filename": source_label}}, timeout=None)
    return StoredDataset.objects.create(
        id=ds_id, name=name, description=description,
        cache_key=perm_key, rows=len(df), col_count=len(df.columns),
        columns=[str(c) for c in df.columns], dtype_map=dtype_map,
        source_file=source_label, data_blob=blob, created_by=user,
    )


def _dtype_for_field(field) -> str:
    if isinstance(field, IntegerField):               return "int64"
    if isinstance(field, (FloatField, DecimalField)): return "float64"
    if isinstance(field, DateTimeField):              return "datetime64[ns]"
    if isinstance(field, DateField):                  return "object"
    if isinstance(field, BooleanField):               return "bool"
    return "object"


def _discoverable_models() -> list:
    allowed = _get_allowed_apps()
    result  = []
    for model in django_apps.get_models():
        app = model._meta.app_label
        if app in _HARDCODED_EXCLUDED or app not in allowed:
            continue
        result.append({
            "path":           f"{app}.{model.__name__}",
            "app":            app,
            "model":          model.__name__,
            "verbose":        str(model._meta.verbose_name),
            "verbose_plural": str(model._meta.verbose_name_plural),
        })
    return sorted(result, key=lambda x: (x["app"], x["model"]))


def _model_fields(model_path: str) -> list:
    if not _is_model_allowed(model_path):
        raise PermissionError(f"Modelo no permitido: {model_path}")
    app_label, model_name = model_path.rsplit('.', 1)
    Model  = django_apps.get_model(app_label, model_name)
    fields = []
    for f in Model._meta.get_fields():
        if f.many_to_many or f.one_to_many:
            continue
        if f.is_relation:
            attname = getattr(f, 'attname', None)
            if not attname:
                continue
            fields.append({
                "name": attname,
                "verbose": f"{getattr(f,'verbose_name',f.name)} (ID)",
                "dtype": "int64", "is_fk": True,
                "rel_model": f"{f.related_model._meta.app_label}.{f.related_model.__name__}"
                              if getattr(f, 'related_model', None) else None,
            })
        else:
            fields.append({
                "name": f.name,
                "verbose": str(getattr(f, 'verbose_name', f.name)),
                "dtype": _dtype_for_field(f), "is_fk": False,
            })
    return fields


def _source_row(src) -> dict:
    last = src.jobs.first()
    return {
        "id": str(src.id), "name": src.name, "description": src.description,
        "model_path": src.model_path, "sql_mode": bool(src.sql_override.strip()),
        "fields": src.fields, "filters": src.filters, "date_field": src.date_field,
        "aggregations": src.aggregations, "chunk_size": src.chunk_size,
        "max_rows": src.max_rows, "frequency": src.frequency,
        # ← CAMBIO: se expone analyst_base_id si existe
        "analyst_base_id": str(src.analyst_base_id) if src.analyst_base_id else None,
        # SIM-4
        "sim_account_id":  str(src.sim_account_id)  if src.sim_account_id  else None,
        "created_at": src.created_at.isoformat(),
        "last_run": last.created_at.isoformat() if last else None,
        "last_status": last.status if last else None,
        "job_count": src.jobs.count(),
    }


def _job_row(job) -> dict:
    return {
        "id": str(job.id), "source_id": str(job.source_id),
        "source_name": job.source.name, "status": job.status,
        "error_msg": job.error_msg, "rows_extracted": job.rows_extracted,
        "duration_s": job.duration_s,
        "dataset_id": str(job.result_dataset_id) if job.result_dataset_id else None,
        "dataset_name": job.result_dataset.name if job.result_dataset else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "created_at": job.created_at.isoformat(),
    }

# ============================================================================
# ETL Execution engine
# ============================================================================

# ← NUEVO: función de extracción desde AnalystBase
def _extract_analyst_base(source, runtime_params, user):
    """
    Extrae datos de un AnalystBase propiedad del usuario y aplica
    los mismos filtros de campo/fecha/límite configurados en el ETLSource.
    """
    from analyst.services.base_validator import BaseValidator

    try:
        base = AnalystBase.objects.get(id=source.analyst_base_id, created_by=user)
    except AnalystBase.DoesNotExist:
        return None, "AnalystBase no encontrada o sin permiso de acceso."

    df = BaseValidator.load_dataframe(base)

    if df is None or df.empty:
        return pd.DataFrame(columns=[c['name'] for c in base.schema]), None

    real_cols = set(df.columns)

    # ── Filtros de columnas (misma lógica que ORM, sobre el DataFrame) ───────
    for f in (source.filters or []):
        field  = str(f.get("field", "")).strip()
        lookup = str(f.get("lookup", "exact")).strip()
        value  = f.get("value", "")
        negate = bool(f.get("negate", False))

        if field not in real_cols or lookup not in _SAFE_LOOKUPS:
            continue

        try:
            col = df[field].astype(str)
            if   lookup == "exact":        mask = col == str(value)
            elif lookup == "iexact":       mask = col.str.lower() == str(value).lower()
            elif lookup == "contains":     mask = col.str.contains(str(value), na=False)
            elif lookup == "icontains":    mask = col.str.contains(str(value), case=False, na=False)
            elif lookup == "startswith":   mask = col.str.startswith(str(value))
            elif lookup == "istartswith":  mask = col.str.lower().str.startswith(str(value).lower())
            elif lookup == "endswith":     mask = col.str.endswith(str(value))
            elif lookup == "iendswith":    mask = col.str.lower().str.endswith(str(value).lower())
            elif lookup == "isnull":       mask = df[field].isna()
            elif lookup == "gt":           mask = pd.to_numeric(df[field], errors='coerce') > float(value)
            elif lookup == "gte":          mask = pd.to_numeric(df[field], errors='coerce') >= float(value)
            elif lookup == "lt":           mask = pd.to_numeric(df[field], errors='coerce') < float(value)
            elif lookup == "lte":          mask = pd.to_numeric(df[field], errors='coerce') <= float(value)
            else:
                continue

            df = df[~mask] if negate else df[mask]
        except Exception as e:
            logger.warning("Filtro AnalystBase ignorado (%s %s): %s", field, lookup, e)
            continue

    # ── Filtro de fecha ───────────────────────────────────────────────────────
    df_field = (runtime_params.get("date_field") or source.date_field or "").strip()
    if df_field and df_field in real_cols:
        try:
            date_col = pd.to_datetime(df[df_field], errors='coerce')
            if runtime_params.get("date_from"):
                df = df[date_col >= pd.to_datetime(runtime_params["date_from"])]
            if runtime_params.get("date_to"):
                df = df[date_col <= pd.to_datetime(runtime_params["date_to"])]
        except Exception as e:
            logger.warning("Filtro de fecha en AnalystBase ignorado: %s", e)

    # ── Selección de columnas ─────────────────────────────────────────────────
    selected = [f for f in (source.fields or []) if f in real_cols]
    if selected:
        df = df[selected]

    # ── Límite de filas ───────────────────────────────────────────────────────
    max_rows = source.max_rows or 0
    if not user.is_superuser and (not max_rows or max_rows > MAX_ROWS_NON_SUPERUSER):
        max_rows = MAX_ROWS_NON_SUPERUSER
    if max_rows:
        df = df.head(max_rows)

    return df.reset_index(drop=True), None


def _sim_interaction_fields() -> list:
    """
    SIM-4: Introspección de sim.Interaction sin pasar por el whitelist de modelos permitidos.
    """
    try:
        from django.apps import apps as _dapps
        Model = _dapps.get_model('sim', 'Interaction')
        fields = []
        for f in Model._meta.get_fields():
            if f.many_to_many or f.one_to_many:
                continue
            if f.is_relation:
                attname = getattr(f, 'attname', None)
                if not attname:
                    continue
                fields.append({
                    "name":    attname,
                    "verbose": f"{getattr(f, 'verbose_name', f.name)} (ID)",
                    "dtype":   "object",
                    "is_fk":   True,
                })
            else:
                fields.append({
                    "name":    f.name,
                    "verbose": str(getattr(f, 'verbose_name', f.name)),
                    "dtype":   _dtype_for_field(f),
                    "is_fk":   False,
                })
        return fields
    except Exception:
        return []


def _extract_sim_account(source, runtime_params, user):
    """
    SIM-4: Extrae Interactions de una SimAccount del usuario.
    Campos reales del modelo: fecha (DateField), hora_inicio / hora_fin (TimeField).
    Filtro de fecha aplica sobre `fecha`.
    """
    try:
        from sim.models import SimAccount, Interaction
    except ImportError:
        return None, "App 'sim' no disponible en este entorno."

    try:
        account = SimAccount.objects.get(id=source.sim_account_id, created_by=user)
    except SimAccount.DoesNotExist:
        return None, "SimAccount no encontrada o sin permiso de acceso."

    qs = Interaction.objects.filter(account=account)

    # ── Filtro de fecha (campo real: fecha) ───────────────────────────────────
    date_from = (runtime_params.get("date_from") or "").strip()
    date_to   = (runtime_params.get("date_to")   or "").strip()
    if date_from:
        qs = qs.filter(fecha__gte=date_from)
    if date_to:
        qs = qs.filter(fecha__lte=date_to)

    # ── Filtro por SimRun (opcional) ──────────────────────────────────────────
    run_id = (runtime_params.get("run_id") or "").strip()
    if run_id:
        qs = qs.filter(run_id=run_id)

    # ── Límite de filas ───────────────────────────────────────────────────────
    limit = source.max_rows or 0
    if not user.is_superuser and (not limit or limit > MAX_ROWS_NON_SUPERUSER):
        limit = MAX_ROWS_NON_SUPERUSER

    qs = qs.order_by('fecha', 'hora_inicio')
    if limit:
        qs = qs[:limit]

    records = list(qs.values())
    if not records:
        return pd.DataFrame(), None

    df = pd.DataFrame(records)

    # ── Selección de campos específicos ───────────────────────────────────────
    if source.fields:
        selected = [f for f in source.fields if f in df.columns]
        if selected:
            df = df[selected]

    return df.reset_index(drop=True), None


def _run_extraction(source, runtime_params, user):
    # ── Sim path (SIM-4) ──────────────────────────────────────────────────────
    if getattr(source, 'sim_account_id', None):
        return _extract_sim_account(source, runtime_params, user)

    # ── AnalystBase path ──────────────────────────────────────────────────────
    # ← NUEVO: se evalúa primero antes que SQL y ORM
    if getattr(source, 'analyst_base_id', None):
        return _extract_analyst_base(source, runtime_params, user)

    # ── SQL path (superusers only) ────────────────────────────────────────────
    if source.sql_override.strip():
        if not user.is_superuser:
            return None, "SQL personalizado solo disponible para superusuarios."
        err = _validate_sql(source.sql_override)
        if err:
            return None, err
        try:
            with connection.cursor() as cur:
                cur.execute(source.sql_override.strip(),
                            runtime_params.get("sql_params", []))
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
            df = pd.DataFrame(rows, columns=cols)
            if source.max_rows:
                df = df.head(source.max_rows)
            return df, None
        except Exception as exc:
            return None, f"SQL error: {exc}"

    # ── ORM path ─────────────────────────────────────────────────────────────
    if not _is_model_allowed(source.model_path):
        return None, f"Modelo no permitido: {source.model_path}"

    try:
        app_label, model_name = source.model_path.rsplit('.', 1)
        Model = django_apps.get_model(app_label, model_name)
    except Exception as exc:
        return None, f"Modelo no encontrado: {source.model_path} — {exc}"

    try:
        real_fields = _model_field_names(source.model_path)
        qs = Model.objects.all()

        # Filtros validados
        fk = {}
        ek = {}
        for f in (source.filters or []):
            field  = str(f.get("field", "")).strip()
            lookup = str(f.get("lookup", "exact")).strip()
            if (not _validate_field_name(field) or field not in real_fields
                    or lookup not in _SAFE_LOOKUPS):
                continue
            key = f"{field}__{lookup}" if lookup != "exact" else field
            (ek if f.get("negate") else fk)[key] = f.get("value", "")
        if fk: qs = qs.filter(**fk)
        if ek: qs = qs.exclude(**ek)

        # Filtro de fecha por rango
        df_field = (runtime_params.get("date_field") or source.date_field or "").strip()
        if df_field and _validate_field_name(df_field) and df_field in real_fields:
            if runtime_params.get("date_from"):
                qs = qs.filter(**{f"{df_field}__date__gte": runtime_params["date_from"]})
            if runtime_params.get("date_to"):
                qs = qs.filter(**{f"{df_field}__date__lte": runtime_params["date_to"]})

        # Agregaciones
        agg_cfg  = source.aggregations or {}
        group_by = [g for g in (agg_cfg.get("group_by") or [])
                    if _validate_field_name(g) and g in real_fields]

        if group_by:
            qs = qs.values(*group_by)
            agg_kw = {}
            for agg in (agg_cfg.get("aggregations") or []):
                fn    = str(agg.get("func", "count")).lower()
                field = str(agg.get("field", "id")).strip()
                alias = re.sub(r'[^a-zA-Z0-9_]', '_', str(agg.get("alias") or f"{fn}_{field}"))
                if fn in AGG_FUNCS and _validate_field_name(field):
                    agg_kw[alias] = AGG_FUNCS[fn](field)
            if agg_kw:
                qs = qs.annotate(**agg_kw)
            cols = group_by + list(agg_kw.keys())
            df   = pd.DataFrame(list(qs.values(*cols)), columns=cols)
        else:
            selected = [f for f in (source.fields or [])
                        if _validate_field_name(f) and f in real_fields]
            qs = qs.values(*selected) if selected else qs.values()

            limit = source.max_rows or None
            if not user.is_superuser and (not limit or limit > MAX_ROWS_NON_SUPERUSER):
                limit = MAX_ROWS_NON_SUPERUSER

            records, count = [], 0
            for obj in qs.iterator(chunk_size=max(100, source.chunk_size or 5000)):
                records.append(obj)
                count += 1
                if limit and count >= limit:
                    break
            df = pd.DataFrame(records) if records else pd.DataFrame()

        # Override de columnas en runtime
        rt = [f for f in (runtime_params.get("fields") or []) if _validate_field_name(f)]
        if rt and not df.empty:
            df = df[[c for c in rt if c in df.columns]] or df

        return df, None

    except Exception as exc:
        logger.error("ETL extraction error %s: %s", source.id, exc, exc_info=True)
        return None, str(exc)

# ============================================================================
# Views
# ============================================================================

def _get_sim_accounts(user) -> list:
    """SIM-4: cuentas activas del simulador accesibles por el usuario."""
    try:
        from sim.models import SimAccount as _SA
        return [
            {
                "id":           str(s.id),
                "name":         s.name,
                "canal":        s.canal,
                "account_type": s.account_type,
            }
            for s in _SA.objects.filter(created_by=user, is_active=True).order_by('name')
        ]
    except Exception:
        return []


@login_required
def etl_list(request):
    sources = ETLSource.objects.filter(created_by=request.user).prefetch_related("jobs")
    jobs    = ETLJob.objects.filter(triggered_by=request.user).select_related(
                  "source", "result_dataset")[:50]
    return render(request, "analyst/etl_manager.html", {
        "sources":      sources,
        "jobs":         jobs,
        "is_superuser": request.user.is_superuser,
        "max_rows_cap": MAX_ROWS_NON_SUPERUSER,
    })


@login_required
@require_GET
def etl_models_api(request):
    # ← CAMBIO: ahora también devuelve las bases del usuario
    try:
        analyst_bases = AnalystBase.objects.filter(
            created_by=request.user
        ).values('id', 'name', 'category', 'schema', 'row_count')

        bases_list = [
            {
                "id":        str(b["id"]),
                "name":      b["name"],
                "category":  b["category"],
                "row_count": b["row_count"],
                "col_count": len(b["schema"]),
                "columns":   [c["name"] for c in b["schema"]],
            }
            for b in analyst_bases
        ]

        return JsonResponse({
            "success":       True,
            "models":        _discoverable_models(),
            "analyst_bases": bases_list,
            "sql_allowed":   request.user.is_superuser,
            # SIM-4
            "sim_accounts":           _get_sim_accounts(request.user),
            "sim_interaction_fields": _sim_interaction_fields(),
        })
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_GET
def etl_model_fields_api(request):
    model_path = request.GET.get("model_path", "").strip()
    if not model_path:
        return JsonResponse({"success": False, "error": "model_path requerido."}, status=400)
    try:
        return JsonResponse({"success": True, "fields": _model_fields(model_path)})
    except PermissionError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=403)
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)


@login_required
@require_POST
def etl_source_save(request):
    try:
        body         = json.loads(request.body)
        source_id    = body.get("id")
        name         = (body.get("name") or "").strip()
        model_path   = body.get("model_path", "").strip()
        sql_override = body.get("sql_override", "").strip()
        # ← NUEVO: leer analyst_base_id del cuerpo
        analyst_base_id = body.get("analyst_base_id") or None
        # SIM-4
        sim_account_id  = body.get("sim_account_id")  or None

        if not name:
            return JsonResponse({"success": False, "error": "El nombre es requerido."}, status=400)

        # Debe haber al menos una fuente
        if not model_path and not sql_override and not analyst_base_id and not sim_account_id:
            return JsonResponse(
                {"success": False,
                 "error": "Se requiere modelo, SQL, base analista o cuenta simulador."},
                status=400)

        # Security checks
        if sql_override and not request.user.is_superuser:
            return JsonResponse(
                {"success": False, "error": "SQL personalizado reservado para administradores."},
                status=403)
        if sql_override:
            err = _validate_sql(sql_override)
            if err:
                return JsonResponse({"success": False, "error": err}, status=400)
        if model_path and not _is_model_allowed(model_path):
            return JsonResponse(
                {"success": False,
                 "error": f"Modelo no permitido: '{model_path}'. "
                           "Verifica ANALYST_ETL_ALLOWED_APPS en settings."},
                status=403)

        # ← NUEVO: validar que la AnalystBase pertenece al usuario
        if analyst_base_id:
            if not AnalystBase.objects.filter(
                id=analyst_base_id, created_by=request.user
            ).exists():
                return JsonResponse(
                    {"success": False, "error": "AnalystBase no encontrada o sin permiso."},
                    status=403)

        # SIM-4: validar que la SimAccount pertenece al usuario
        if sim_account_id:
            try:
                from sim.models import SimAccount as _SA
                if not _SA.objects.filter(id=sim_account_id, created_by=request.user).exists():
                    return JsonResponse(
                        {"success": False, "error": "SimAccount no encontrada o sin permiso."},
                        status=403)
            except ImportError:
                return JsonResponse(
                    {"success": False, "error": "App 'sim' no disponible."}, status=400)

        # Validate field names and filters against the real model
        # (para AnalystBase se validan contra su schema, no contra ORM)
        if model_path:
            real_fields = _model_field_names(model_path)
            safe_fields = [f for f in (body.get("fields") or [])
                           if _validate_field_name(f) and f in real_fields]
            safe_filters = []
            for f in (body.get("filters") or []):
                field  = str(f.get("field", "")).strip()
                lookup = str(f.get("lookup", "exact")).strip()
                if _validate_field_name(field) and field in real_fields and lookup in _SAFE_LOOKUPS:
                    safe_filters.append({
                        "field": field, "lookup": lookup,
                        "value": f.get("value", ""),
                        "negate": bool(f.get("negate", False)),
                    })
        elif analyst_base_id:
            # Para AnalystBase: validar columnas contra su schema
            try:
                base = AnalystBase.objects.get(id=analyst_base_id, created_by=request.user)
                base_cols = {c['name'] for c in base.schema}
            except AnalystBase.DoesNotExist:
                base_cols = set()

            safe_fields = [f for f in (body.get("fields") or [])
                           if _validate_field_name(f) and f in base_cols]
            safe_filters = []
            for f in (body.get("filters") or []):
                field  = str(f.get("field", "")).strip()
                lookup = str(f.get("lookup", "exact")).strip()
                if _validate_field_name(field) and field in base_cols and lookup in _SAFE_LOOKUPS:
                    safe_filters.append({
                        "field": field, "lookup": lookup,
                        "value": f.get("value", ""),
                        "negate": bool(f.get("negate", False)),
                    })
        else:
            safe_fields  = []
            safe_filters = []

        max_rows = int(body.get("max_rows") or 0)
        if not request.user.is_superuser and (max_rows == 0 or max_rows > MAX_ROWS_NON_SUPERUSER):
            max_rows = MAX_ROWS_NON_SUPERUSER

        defaults = {
            "name":             name,
            "description":      body.get("description", ""),
            "model_path":       model_path,
            "fields":           safe_fields,
            "filters":          safe_filters,
            "date_field":       body.get("date_field", ""),
            "aggregations":     body.get("aggregations", {}),
            "sql_override":     sql_override,
            "chunk_size":       max(100, int(body.get("chunk_size") or 5000)),
            "max_rows":         max_rows,
            "frequency":        body.get("frequency", "manual"),
            "created_by":       request.user,
            # ← NUEVO: guardar referencia a la AnalystBase
            "analyst_base_id":  analyst_base_id,
            # SIM-4
            "sim_account_id":   sim_account_id,
        }

        if source_id:
            src = get_object_or_404(ETLSource, id=source_id, created_by=request.user)
            for k, v in defaults.items():
                if k != "created_by":
                    setattr(src, k, v)
            src.save()
            created = False
        else:
            src = ETLSource.objects.create(**defaults)
            created = True

        logger.info("ETLSource %s by %s: %s", "created" if created else "updated",
                    request.user, src.name)
        return JsonResponse({"success": True, "created": created, "source": _source_row(src)})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON invalido."}, status=400)
    except Exception as exc:
        logger.error("etl_source_save: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_POST
def etl_source_delete(request, source_id):
    src = get_object_or_404(ETLSource, id=source_id, created_by=request.user)
    src.delete()
    logger.info("ETLSource deleted by %s: %s", request.user, source_id)
    return JsonResponse({"success": True})


@login_required
@require_POST
def etl_source_run(request, source_id):
    src = get_object_or_404(ETLSource, id=source_id, created_by=request.user)

    # Re-validate at run time
    if src.sql_override.strip() and not request.user.is_superuser:
        return JsonResponse({"success": False, "error": "Sin permiso para ejecutar fuentes SQL."}, status=403)
    if src.model_path and not _is_model_allowed(src.model_path):
        return JsonResponse(
            {"success": False, "error": f"Modelo '{src.model_path}' ya no esta en la lista permitida."},
            status=403)
    # ← NUEVO: verificar que la AnalystBase aún existe y pertenece al usuario
    if src.analyst_base_id:
        if not AnalystBase.objects.filter(
            id=src.analyst_base_id, created_by=request.user
        ).exists():
            return JsonResponse(
                {"success": False,
                 "error": "La base de datos analista asociada ya no existe o no tienes acceso."},
                status=403)

    # SIM-4: verificar que la SimAccount aún existe y pertenece al usuario
    if src.sim_account_id:
        try:
            from sim.models import SimAccount as _SA
            if not _SA.objects.filter(id=src.sim_account_id, created_by=request.user).exists():
                return JsonResponse(
                    {"success": False,
                     "error": "La cuenta sim asociada ya no existe o no tienes acceso."},
                    status=403)
        except ImportError:
            return JsonResponse(
                {"success": False, "error": "App 'sim' no disponible."}, status=400)

    try:
        body = json.loads(request.body)
        dataset_name   = (body.get("dataset_name") or src.name).strip()
        description    = body.get("description", src.description)
        runtime_params = {
            "date_from":  body.get("date_from", ""),
            "date_to":    body.get("date_to", ""),
            "date_field": body.get("date_field", ""),
            "fields":     body.get("fields", []),
        }
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON invalido."}, status=400)

    job = ETLJob.objects.create(
        source=src, runtime_params=runtime_params,
        status="running", triggered_by=request.user, started_at=timezone.now(),
    )

    # source_label refleja el tipo de fuente
    if src.sim_account_id:
        source_label = f"Sim:{src.sim_account_id}"
    elif src.analyst_base_id:
        source_label = f"AnalystBase:{src.analyst_base_id}"
    else:
        source_label = f"ETL:{src.model_path or 'SQL'}"

    t0 = time.perf_counter()
    try:
        df, err = _run_extraction(src, runtime_params, request.user)
        if err or df is None:
            job.status = "error"
            job.error_msg = err or "Sin datos."
            job.duration_s = round(time.perf_counter() - t0, 2)
            job.finished_at = timezone.now()
            job.save()
            return JsonResponse({"success": False, "error": job.error_msg}, status=500)

        ds = _save_as_stored_dataset(df, dataset_name, description, source_label, request.user)
        duration = round(time.perf_counter() - t0, 2)
        job.status = "done"
        job.rows_extracted = len(df)
        job.duration_s = duration
        job.result_dataset = ds
        job.finished_at = timezone.now()
        job.save()

        logger.info("ETL job %s: %d rows %.1fs → %s by %s",
                    job.id, len(df), duration, ds.id, request.user)
        return JsonResponse({
            "success": True,
            "job": _job_row(job),
            "dataset": {"id": str(ds.id), "name": ds.name,
                        "rows": ds.rows, "col_count": ds.col_count, "columns": ds.columns},
        })
    except Exception as exc:
        job.status = "error"
        job.error_msg = str(exc)
        job.duration_s = round(time.perf_counter() - t0, 2)
        job.finished_at = timezone.now()
        job.save()
        logger.error("ETL job %s failed: %s", job.id, exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_GET
def etl_job_status(request, job_id):
    job = get_object_or_404(ETLJob, id=job_id, triggered_by=request.user)
    return JsonResponse({"success": True, "job": _job_row(job)})
