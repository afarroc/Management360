# analyst/views/data_upload_async/dataset.py
"""
Promotes a preview DataFrame to a permanent StoredDataset.
"""

import json
import logging
import uuid as _uuid

from django.contrib.auth.decorators import login_required
from django.core.cache import cache as _cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from analyst.models import StoredDataset
from ._core import _cache_load, _serialize

logger = logging.getLogger(__name__)


@login_required
@require_POST
def save_as_dataset(request):
    """
    Persist the current preview DataFrame as a StoredDataset (permanent Redis key
    + DB row). Called from the upload panel's "Guardar como Dataset" button.

    POST JSON: { "cache_key": "df_preview_...", "name": "...", "description": "..." }
    Returns:   { "success": true, "dataset": { id, name, rows, col_count, ... } }
    """
    try:
        body        = json.loads(request.body)
        cache_key   = body.get("cache_key", "").strip()
        name        = (body.get("name") or "").strip()
        description = body.get("description", "")

        if not cache_key:
            return JsonResponse({"success": False, "error": "cache_key requerido."}, status=400)
        if not name:
            return JsonResponse({"success": False, "error": "El nombre es requerido."}, status=400)

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse(
                {"success": False,
                 "error": "Preview no encontrado o expirado. Vuelve a subir el archivo."},
                status=404,
            )

        ds_id    = _uuid.uuid4()
        perm_key = StoredDataset.make_cache_key(str(ds_id))
        blob     = _serialize(df)

        # Write to cache with no TTL (permanent until dataset is deleted)
        _cache.set(perm_key, {
            "data": blob,
            "meta": {**(meta or {}), "stored_dataset_id": str(ds_id)},
        }, timeout=None)

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
            source_file = (meta or {}).get("filename", ""),
            data_blob   = blob,
            created_by  = request.user,
        )

        logger.info("StoredDataset created from preview: %s (%dx%d) by %s",
                    ds.name, ds.rows, ds.col_count, request.user)

        return JsonResponse({
            "success": True,
            "dataset": {
                "id":          str(ds.id),
                "name":        ds.name,
                "description": ds.description,
                "rows":        ds.rows,
                "col_count":   ds.col_count,
                "columns":     ds.columns,
                "created_at":  ds.created_at.isoformat(),
            },
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("save_as_dataset error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)
