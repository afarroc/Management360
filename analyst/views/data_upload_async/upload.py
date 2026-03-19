# analyst/views/data_upload_async/upload.py
"""
Core upload views:
  preview_async        — file → DataFrame → cache → JSON preview
  confirm_upload_async — DataFrame → bulk_create model instances
  reanalyze_async      — re-map cached DF against a different model
"""

import json
import logging

import pandas as pd
from io import StringIO

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from analyst.services.excel_processor import ExcelProcessor
from analyst.services.file_processor_service import FileProcessorService

from ._core import (
    _cache_load, _cache_store, _new_preview_key,
    _preview_json, _resolve_model, _rows_page,
    _DEFAULT_PAGE_SIZE, _MAX_PAGE_SIZE,
)
from .defaults import _apply_field_defaults, _apply_password_fields

logger = logging.getLogger(__name__)


@login_required
@require_POST
def preview_async(request):
    """
    Processes an uploaded file and returns a full JSON preview.
    Stores the DataFrame in Redis under a fresh UUID key.
    """
    try:
        file       = request.FILES.get("file")
        model_path = request.POST.get("model", "").strip()

        if not file:
            return JsonResponse({"success": False, "error": "No se recibió ningún archivo."}, status=400)
        if not model_path:
            return JsonResponse({"success": False, "error": "Selecciona un modelo destino."}, status=400)

        model_class, err = _resolve_model(model_path)
        if err:
            return err

        sheet_name = request.POST.get("sheet_name", "").strip() or None
        cell_range = request.POST.get("cell_range", "").strip() or None
        no_header  = request.POST.get("no_header", "") in ("on", "true", "1", "True")

        ext        = file.name.rsplit(".", 1)[-1].lower()
        excel_info = None

        if ext in ("xls", "xlsx"):
            df, excel_info = ExcelProcessor.process_excel(
                file, sheet_name=sheet_name, cell_range=cell_range, no_header=no_header,
            )
        else:
            encoding   = FileProcessorService.detect_encoding(file)
            content    = file.read().decode(encoding, errors="replace")
            file.seek(0)
            first_line = content.split("\n")[0]
            delimiter  = "," if "," in first_line else ";"
            df         = pd.read_csv(StringIO(content), delimiter=delimiter)
            df.columns = [FileProcessorService.normalize_name(str(c)) for c in df.columns]

        if df is None or df.empty:
            return JsonResponse(
                {"success": False, "error": "El archivo no contiene datos en el rango especificado."},
                status=400,
            )

        cache_key = _new_preview_key()
        _cache_store(cache_key, df, {
            "filename":   file.name,
            "model":      model_path,
            "excel_info": excel_info,
        })

        logger.info("preview_async – file: %s, shape: %s, key: %s", file.name, df.shape, cache_key)
        return JsonResponse(_preview_json(df, cache_key, model_class, excel_info, file.name))

    except ValueError as exc:
        logger.warning("preview_async ValueError: %s", exc)
        return JsonResponse({"success": False, "error": str(exc)}, status=400)
    except Exception as exc:
        logger.error("preview_async unexpected error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": f"Error inesperado: {exc}"}, status=500)


@login_required
@require_POST
def preview_page_async(request):
    """
    Returns a single page of rows from the cached DataFrame.
    Lightweight — does NOT re-run column analysis; headers come from the first
    preview_async call and are stored in the client.

    POST JSON:
      { "cache_key": "df_preview_...",
        "page":      1,           // 1-based, default 1
        "page_size": 50 }         // max 500, default 50

    Returns:
      { "success": true,
        "rows": [[...], ...],
        "pagination": { total_rows, page, page_size, total_pages, start, end } }
    """
    try:
        body      = json.loads(request.body)
        cache_key = body.get("cache_key", "")
        page      = int(body.get("page",      1))
        page_size = int(body.get("page_size", _DEFAULT_PAGE_SIZE))

        if not cache_key:
            return JsonResponse({"success": False, "error": "cache_key requerido."}, status=400)

        df, _ = _cache_load(cache_key)
        if df is None:
            return JsonResponse(
                {"success": False, "error": "Sesión expirada o inválida. Sube el archivo nuevamente."},
                status=404,
            )

        page_size = max(1, min(page_size, _MAX_PAGE_SIZE))
        rows, pagination = _rows_page(df, page, page_size)

        return JsonResponse({"success": True, "rows": rows, "pagination": pagination})

    except (ValueError, TypeError):
        return JsonResponse({"success": False, "error": "Parámetros inválidos."}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("preview_page_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_POST
def confirm_upload_async(request):
    """
    Reads the working DataFrame from Redis, bulk-creates model instances.
    Optionally clears existing records first. Deletes the preview key on success.
    """
    try:
        body           = json.loads(request.body)
        cache_key      = body.get("cache_key", "")
        model_path     = body.get("model", "")
        clear_existing = body.get("clear_existing", False)

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse(
                {"success": False, "error": "Sesión expirada. Sube el archivo nuevamente."},
                status=404,
            )

        model_path        = model_path or meta.get("model", "")
        model_class, err  = _resolve_model(model_path)
        if err:
            return err

        if clear_existing:
            deleted_count = model_class.objects.all().delete()[0]
            logger.info("Cleared %d existing records from %s", deleted_count, model_class.__name__)

        field_defaults = body.get("field_defaults", {})
        if field_defaults:
            df = _apply_field_defaults(df, model_class, field_defaults)

        records = FileProcessorService._create_instances_auto(df, model_class)
        if not records:
            return JsonResponse(
                {"success": False,
                 "error": "No se generaron registros válidos. Verifica el mapeo de columnas."},
                status=400,
            )

        records = _apply_password_fields(records, model_class, field_defaults)
        created = model_class.objects.bulk_create(records, ignore_conflicts=True)
        cache.delete(cache_key)

        logger.info("confirm_upload_async – %d records created in %s", len(created), model_class.__name__)
        return JsonResponse({
            "success": True,
            "message": (
                f"{len(created)} registros cargados exitosamente "
                f"en «{model_class._meta.verbose_name_plural}»."
            ),
            "count": len(created),
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("confirm_upload_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_POST
def reanalyze_async(request):
    """
    Re-runs column mapping analysis against a different model WITHOUT touching
    the DataFrame. Updates meta["model"] so subsequent edits/confirm use the new model.

    POST JSON: { "cache_key": "...", "model": "app_label.ModelName" }
    Returns:   same shape as _preview_json so renderPreview() works unchanged.
    """
    try:
        body       = json.loads(request.body)
        cache_key  = body.get("cache_key", "").strip()
        model_path = body.get("model", "").strip()
        page       = int(body.get("page", 1))
        page_size  = max(1, min(int(body.get("page_size", _DEFAULT_PAGE_SIZE)), _MAX_PAGE_SIZE))

        if not cache_key:
            return JsonResponse({"success": False, "error": "cache_key requerido."}, status=400)
        if not model_path:
            return JsonResponse({"success": False, "error": "Selecciona un modelo destino."}, status=400)

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse(
                {"success": False, "error": "Sesión expirada. Vuelve a subir el archivo."},
                status=404,
            )

        model_class, err = _resolve_model(model_path)
        if err:
            return err

        meta = {**(meta or {}), "model": model_path}
        _cache_store(cache_key, df, meta)

        logger.info("reanalyze_async – key=%s new_model=%s shape=%s", cache_key, model_path, df.shape)
        return JsonResponse(
            _preview_json(df, cache_key, model_class, meta.get("excel_info"), meta.get("filename", ""),
                          page=page, page_size=page_size)
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("reanalyze_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)
