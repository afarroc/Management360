# analyst/views/data_upload_async/clipboard.py
"""
Clipboard operations:
  save_clipboard_async  — copies the current preview DF into DataFrameClipboard
  load_clip_as_preview  — loads a clipboard DF into a fresh preview cache key
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ._core import _cache_load, _cache_store, _new_preview_key, _preview_json, _resolve_model

logger = logging.getLogger(__name__)


@login_required
@require_POST
def save_clipboard_async(request):
    """
    Saves the current preview DataFrame to the clipboard (Redis-backed).
    """
    try:
        body             = json.loads(request.body)
        preview_key      = body.get("cache_key", "")
        clip_name        = body.get("clip_name", "").strip()
        clip_description = body.get("clip_description", "").strip()

        if not preview_key:
            return JsonResponse({"success": False, "error": "cache_key requerido."}, status=400)
        if not clip_name:
            return JsonResponse({"success": False, "error": "clip_name requerido."}, status=400)

        df, meta = _cache_load(preview_key)
        if df is None:
            return JsonResponse(
                {"success": False, "error": "Sesión expirada. Sube el archivo nuevamente."},
                status=404,
            )

        from analyst.utils.clipboard import DataFrameClipboard

        saved_key = DataFrameClipboard.store_df(
            request, df, key=clip_name,
            metadata={**meta, "description": clip_description},
        )
        clips = DataFrameClipboard.list_clips(request)
        return JsonResponse({
            "success": True,
            "message": f'Clip "{saved_key}" guardado exitosamente.',
            "clips":   clips,
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("save_clipboard_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_POST
def load_clip_as_preview(request):
    """
    Loads a clipboard DataFrame into a fresh preview cache key so the user
    can inspect / edit it in the SPA panel before confirming upload.

    POST body: { "clip_name": "...", "model": "app_label.ModelName" }
    Returns the same JSON shape as preview_async so renderPreview() works unchanged.
    """
    try:
        body       = json.loads(request.body)
        clip_name  = body.get("clip_name", "").strip()
        model_path = body.get("model", "").strip()

        if not clip_name:
            return JsonResponse({"success": False, "error": "clip_name requerido."}, status=400)
        if not model_path:
            return JsonResponse({"success": False, "error": "Selecciona un modelo destino."}, status=400)

        model_class, err = _resolve_model(model_path)
        if err:
            return err

        from analyst.utils.clipboard import DataFrameClipboard
        df, meta = DataFrameClipboard.retrieve_df(request, clip_name)

        if df is None:
            return JsonResponse(
                {"success": False, "error": f"Clip «{clip_name}» no encontrado o expirado."},
                status=404,
            )

        cache_key   = _new_preview_key()
        merged_meta = {
            **(meta or {}),
            "model":    model_path,
            "filename": (meta or {}).get("filename") or clip_name,
        }
        _cache_store(cache_key, df, merged_meta)
        logger.info("load_clip_as_preview – clip: %s, shape: %s, key: %s", clip_name, df.shape, cache_key)
        return JsonResponse(
            _preview_json(df, cache_key, model_class, None, merged_meta.get("filename", clip_name))
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("load_clip_as_preview error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)
