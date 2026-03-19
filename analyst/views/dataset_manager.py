# analyst/views/dataset_manager.py
"""
CRUD views for StoredDataset.

GET  /analyst/datasets/              → list all datasets for current user
POST /analyst/datasets/save/         → save a preview cache_key as a StoredDataset
POST /analyst/datasets/<id>/delete/  → delete dataset (DB row + Redis key)
GET  /analyst/datasets/<id>/preview/ → load into a preview key (same as load_clip_as_preview)
GET  /analyst/datasets/<id>/export/  → download as CSV
GET  /analyst/datasets/api/columns/  → return columns for one or more datasets (used by builder)
"""

import json
import logging
import pickle
import base64
import csv

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone

from analyst.models import StoredDataset
from analyst.utils.clipboard import DataFrameClipboard

logger = logging.getLogger(__name__)

DATASET_TTL = None  # stored datasets don't expire automatically


# ─── Serialization helpers ────────────────────────────────────────────────────

def _serialize(df: pd.DataFrame) -> str:
    return base64.b64encode(pickle.dumps(df)).decode()


def _deserialize(s: str) -> pd.DataFrame:
    return pickle.loads(base64.b64decode(s.encode()))


def _load_df(cache_key: str):
    """Returns (df, meta) from cache only. Does NOT check DB blob."""
    raw = cache.get(cache_key)
    if not raw:
        return None, None
    try:
        return _deserialize(raw["data"]), raw.get("meta", {})
    except Exception as exc:
        logger.error("Dataset deserialize error %s: %s", cache_key, exc)
        return None, None


def _store_df(cache_key: str, df: pd.DataFrame, meta: dict) -> None:
    cache.set(cache_key, {"data": _serialize(df), "meta": meta}, timeout=DATASET_TTL)


def _load_df_persistent(ds: StoredDataset):
    """
    Load DataFrame for a StoredDataset with two-tier fallback:
      1. Cache (Redis / LocMemCache) — fast path
      2. data_blob DB field  — survives Django restarts and Redis outages

    Also re-warms the cache from DB if it was cold.
    Returns (df, meta) or (None, None).
    """
    cache_key = ds.cache_key

    # ── Tier 1: cache hit ──────────────────────────────────────────────────
    raw = cache.get(cache_key)
    if raw:
        try:
            return _deserialize(raw["data"]), raw.get("meta", {})
        except Exception as exc:
            logger.warning("Cache deserialize failed for %s: %s — trying DB blob", cache_key, exc)

    # ── Tier 2: DB blob fallback ───────────────────────────────────────────
    if not ds.data_blob:
        logger.warning("Dataset %s: cache miss and no data_blob in DB.", ds.id)
        return None, None

    try:
        df   = _deserialize(ds.data_blob)
        meta = {"stored_dataset_id": str(ds.id), "filename": ds.source_file}
        # Re-warm cache so subsequent requests are fast
        _store_df(cache_key, df, meta)
        logger.info("Dataset %s re-warmed cache from DB blob (%d rows).", ds.id, len(df))
        return df, meta
    except Exception as exc:
        logger.error("DB blob deserialize failed for %s: %s", ds.id, exc)
        return None, None


def _persist_blob(ds: StoredDataset, df: pd.DataFrame) -> None:
    """Write serialized DataFrame to data_blob and save only that field."""
    try:
        StoredDataset.objects.filter(pk=ds.pk).update(data_blob=_serialize(df))
        logger.debug("data_blob written for dataset %s (%d rows)", ds.id, len(df))
    except Exception as exc:
        # Non-fatal — cache is the primary store
        logger.warning("Could not write data_blob for %s: %s", ds.id, exc)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _dataset_row(ds: StoredDataset) -> dict:
    return {
        "id":          str(ds.id),
        "name":        ds.name,
        "description": ds.description,
        "rows":        ds.rows,
        "col_count":   ds.col_count,
        "columns":     ds.columns,
        "dtype_map":   ds.dtype_map,
        "source_file": ds.source_file,
        "created_at":  ds.created_at.isoformat(),
        "updated_at":  ds.updated_at.isoformat(),
        "created_by":  ds.created_by.get_full_name() or ds.created_by.username,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Views
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def dataset_list(request):
    """Main dataset manager page."""
    datasets = StoredDataset.objects.filter(created_by=request.user).order_by("-created_at")
    return render(request, "analyst/dataset_manager.html", {"datasets": datasets})


@login_required
@require_POST
def dataset_save(request):
    """
    Promote a preview/clip cache key into a permanent StoredDataset.

    POST JSON: {
        "cache_key": "df_preview_...",   # or clip key
        "source":    "preview"|"clip",
        "clip_name": "...",              # only when source == "clip"
        "name":      "My Dataset",
        "description": "..."
    }
    """
    try:
        body       = json.loads(request.body)
        source     = body.get("source", "preview")
        name       = (body.get("name") or "").strip()
        description = body.get("description", "")

        if not name:
            return JsonResponse({"success": False, "error": "El nombre es requerido."}, status=400)

        # ── Load the DataFrame from wherever it lives right now ───────────────
        if source == "clip":
            clip_name = body.get("clip_name", "").strip()
            if not clip_name:
                return JsonResponse({"success": False, "error": "clip_name requerido."}, status=400)
            df, meta = DataFrameClipboard.retrieve_df(request, clip_name)
            if df is None:
                return JsonResponse({"success": False, "error": f"Clip '{clip_name}' no encontrado."}, status=404)
        else:
            cache_key = body.get("cache_key", "").strip()
            if not cache_key:
                return JsonResponse({"success": False, "error": "cache_key requerido."}, status=400)
            df, meta = _load_df(cache_key)
            if df is None:
                return JsonResponse({"success": False, "error": "Preview no encontrado o expirado."}, status=404)

        # ── Build a permanent cache key and store ─────────────────────────────
        import uuid
        ds_id     = uuid.uuid4()
        perm_key  = StoredDataset.make_cache_key(str(ds_id))
        source_file = (meta or {}).get("filename", "")

        _store_df(perm_key, df, {**(meta or {}), "stored_dataset_id": str(ds_id)})

        col_dtypes = df.dtypes
        dtype_map  = {str(col): str(col_dtypes.iloc[i]) for i, col in enumerate(df.columns)}

        ds = StoredDataset.objects.create(
            id          = ds_id,
            name        = name,
            description = description,
            cache_key   = perm_key,
            rows        = len(df),
            col_count   = len(df.columns),
            columns     = [str(c) for c in df.columns],
            dtype_map   = dtype_map,
            source_file = source_file,
            data_blob   = _serialize(df),   # persist to DB for restart survival
            created_by  = request.user,
        )

        logger.info("StoredDataset created: %s (%dx%d) by %s", ds.name, ds.rows, ds.col_count, request.user)

        return JsonResponse({"success": True, "dataset": _dataset_row(ds)})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("dataset_save error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_POST
def dataset_delete(request, dataset_id):
    """Delete a StoredDataset and its Redis key."""
    try:
        ds = get_object_or_404(StoredDataset, id=dataset_id, created_by=request.user)
        cache.delete(ds.cache_key)
        ds.delete()
        return JsonResponse({"success": True})
    except Exception as exc:
        logger.error("dataset_delete error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_GET
def dataset_preview(request, dataset_id):
    """
    Load a StoredDataset into a fresh preview key so the upload panel
    edit tools can operate on it.
    Returns the same JSON shape as preview_async.
    """
    try:
        import uuid as _uuid
        from analyst.views.data_upload_async import (
            _preview_json, _cache_store, _resolve_model,
            _rows_page, _DEFAULT_PAGE_SIZE,
        )

        ds = get_object_or_404(StoredDataset, id=dataset_id, created_by=request.user)
        df, meta = _load_df_persistent(ds)   # cache → DB blob fallback

        if df is None:
            return JsonResponse(
                {"success": False,
                 "error": "Datos no disponibles. El dataset fue guardado antes de la versión 3 "
                          "(sin data_blob). Por favor elimínalo y vuelve a guardarlo."},
                status=404,
            )

        model_path = (meta or {}).get("model", "")
        model_class = None
        if model_path:
            model_class, _ = _resolve_model(model_path)

        preview_key = f"df_preview_{_uuid.uuid4().hex}"
        _cache_store(preview_key, df, {**(meta or {}), "stored_dataset_id": str(ds.id)})

        if model_class:
            return JsonResponse(_preview_json(df, preview_key, model_class, None, ds.source_file or ds.name))
        else:
            # No model – return a simple preview without mapping, but with full pagination
            col_dtypes = df.dtypes
            headers = []
            total = max(len(df), 1)
            for i, col in enumerate(df.columns):
                dtype_str = str(col_dtypes.iloc[i])
                nc = int(df.iloc[:, i].isna().sum())
                headers.append({
                    "name": str(col), "dtype": dtype_str, "type": dtype_str,
                    "missing_count": nc, "missing_percent": round(nc / total * 100, 1),
                })

            rows, pagination = _rows_page(df, page=1, page_size=_DEFAULT_PAGE_SIZE)

            return JsonResponse({
                "success": True, "cache_key": preview_key, "filename": ds.source_file or ds.name,
                "model": None, "model_verbose": "",
                "stats": {"rows": len(df), "columns": len(df.columns), "mapped_count": 0, "required_count": 0},
                "column_mapping": [{"column": h["name"], "dtype": h["dtype"], "matched": False, "mapped_to": None} for h in headers],
                "table": {"headers": headers, "rows": rows},
                "pagination": pagination,
                "excel_info": None, "required_fields": [], "missing_required": [],
                "unmapped_columns": [h["name"] for h in headers],
            })

    except Exception as exc:
        logger.error("dataset_preview error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_GET
def dataset_export(request, dataset_id):
    """Download a StoredDataset as CSV."""
    ds = get_object_or_404(StoredDataset, id=dataset_id, created_by=request.user)
    df, _ = _load_df_persistent(ds)

    if df is None:
        return HttpResponse("Datos no disponibles. Elimina y vuelve a guardar el dataset.", status=404, content_type="text/plain")

    filename = f"{ds.name.replace(' ', '_')}.csv"
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")  # BOM for Excel
    df.to_csv(response, index=False)
    return response


@login_required
@require_GET
def dataset_columns_api(request):
    """
    Return column info for one or more datasets/models.
    Used by the Report Builder to populate param selectors.

    GET ?ids[]=<uuid>&ids[]=<uuid>&models[]=app.Model
    """
    try:
        ids    = request.GET.getlist("ids[]")
        models = request.GET.getlist("models[]")
        result = {}

        for ds_id in ids:
            try:
                ds = StoredDataset.objects.get(id=ds_id, created_by=request.user)
                result[f"dataset:{ds_id}"] = {
                    "label":   ds.name,
                    "columns": [{"name": c, "dtype": ds.dtype_map.get(c, "object")} for c in ds.columns],
                }
            except StoredDataset.DoesNotExist:
                pass

        from django.apps import apps as django_apps
        from django.db.models import Field as DField
        for model_path in models:
            try:
                app_label, model_name = model_path.rsplit(".", 1)
                model_class = django_apps.get_model(app_label, model_name)
                cols = []
                for field in model_class._meta.get_fields():
                    if isinstance(field, DField) and not field.many_to_many:
                        cols.append({"name": field.name, "dtype": field.get_internal_type()})
                result[f"model:{model_path}"] = {
                    "label":   model_class._meta.verbose_name,
                    "columns": cols,
                }
            except Exception:
                pass

        return JsonResponse({"success": True, "sources": result})

    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=500)
