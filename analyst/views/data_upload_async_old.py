# analyst/views/data_upload_async.py
"""
Async (SPA-like) endpoints for the data upload panel.
All operations return JSON – no full-page reloads.
DataFrames live in Redis cache (not Django session).

Cache key lifecycle:
  1. preview_async  → creates  df_preview_<uuid>
  2. edit_*         → reads / updates the same key
  3. confirm_upload → reads the key, bulk_creates, deletes key
  4. save_clipboard → copies key's DF into DataFrameClipboard (also Redis)
"""

import uuid
import json
import logging
import pickle
import base64

import pandas as pd
from io import StringIO

from django.apps import apps
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Field

from analyst.services.excel_processor import ExcelProcessor
from analyst.services.file_processor_service import FileProcessorService

logger = logging.getLogger(__name__)

PREVIEW_TTL = 1800  # 30 min – enough time to work with the data


# ════════════════════════════════════════════════════════════════════════════════
# Redis helpers
# ════════════════════════════════════════════════════════════════════════════════

def _serialize(df: pd.DataFrame) -> str:
    return base64.b64encode(pickle.dumps(df)).decode()


def _deserialize(s: str) -> pd.DataFrame:
    return pickle.loads(base64.b64decode(s.encode()))


def _cache_store(key: str, df: pd.DataFrame, meta: dict) -> None:
    cache.set(key, {"data": _serialize(df), "meta": meta}, timeout=PREVIEW_TTL)


def _cache_load(key: str):
    """Returns (df, meta) or (None, None)."""
    raw = cache.get(key)
    if not raw:
        return None, None
    try:
        return _deserialize(raw["data"]), raw.get("meta", {})
    except Exception as exc:
        logger.error("Cache deserialize error for %s: %s", key, exc)
        cache.delete(key)
        return None, None


def _new_preview_key() -> str:
    return f"df_preview_{uuid.uuid4().hex}"


# ════════════════════════════════════════════════════════════════════════════════
# Column / model analysis
# ════════════════════════════════════════════════════════════════════════════════

def _field_meta(field) -> dict:
    """Extracts metadata about a model field useful for UI default-value suggestions."""
    ft = field.get_internal_type()
    unique = getattr(field, "unique", False)
    max_len = getattr(field, "max_length", None)

    # Build list of suggested generator strategies for this field
    generators = []
    name_lower = field.name.lower()

    if ft in ("CharField", "TextField"):
        if unique:
            generators.append({"id": "auto_slug",    "label": "Auto slug  (nombre + apellido → juan.garcia.3)"})
            generators.append({"id": "auto_initials","label": "Iniciales  (JG001, JG002…)"})
            generators.append({"id": "seq_prefix",   "label": "Prefijo + secuencia  (USER001, USER002…)"})
            generators.append({"id": "uuid_short",   "label": "UUID corto  (a1b2c3d4)"})
        generators.append({"id": "fixed",  "label": "Valor fijo para todos"})

    elif ft in ("IntegerField", "BigIntegerField", "SmallIntegerField", "PositiveIntegerField"):
        generators.append({"id": "seq",   "label": "Secuencia  (1, 2, 3…)"})
        generators.append({"id": "fixed", "label": "Valor fijo para todos"})
        generators.append({"id": "zero",  "label": "Cero (0)"})

    elif ft in ("FloatField", "DecimalField"):
        generators.append({"id": "fixed", "label": "Valor fijo para todos"})
        generators.append({"id": "zero",  "label": "Cero (0.0)"})

    elif ft == "BooleanField":
        generators.append({"id": "true",  "label": "True para todos"})
        generators.append({"id": "false", "label": "False para todos"})

    elif ft == "EmailField":
        if unique:
            generators.append({"id": "auto_email", "label": "Auto email  (nombre.apellido@empresa.com)"})
        generators.append({"id": "fixed", "label": "Email fijo para todos"})

    elif ft in ("DateField", "DateTimeField"):
        generators.append({"id": "today",  "label": "Fecha de hoy"})
        generators.append({"id": "fixed",  "label": "Fecha fija para todos"})

    # Password-specific hint
    if "password" in name_lower:
        generators = [
            {"id": "auto_unusable", "label": "Contraseña inutilizable  (set_unusable_password)"},
            {"id": "fixed_hash",    "label": "Contraseña fija (hasheada)"},
        ]

    return {
        "name":        field.name,
        "verbose":     str(getattr(field, "verbose_name", field.name)),
        "field_type":  ft,
        "max_length":  max_len,
        "unique":      unique,
        "has_default": field.has_default(),
        "default":     (field.default if field.has_default() and not callable(field.default) else None),
        "generators":  generators,
        # Hints about which existing DF columns could feed this field
        "source_hints": _source_hints(field),
    }


def _source_hints(field) -> list[str]:
    """Returns keywords that might appear in DF column names and are
    semantically useful for generating this field's value."""
    n = field.name.lower()
    mapping = {
        "username": ["nombre", "name", "first", "apellido", "last", "user"],
        "email":    ["email", "correo", "mail"],
        "first_name": ["nombre", "first", "name", "primer"],
        "last_name":  ["apellido", "last", "surname"],
        "password":   [],
        "phone":      ["telefono", "phone", "celular", "movil"],
    }
    for key, hints in mapping.items():
        if key in n:
            return hints
    return []


def _analyze(df: pd.DataFrame, model_class):
    """
    Returns (column_mapping_info, unmapped_columns, required_fields,
             mapped_count, missing_required).

    missing_required: list of field-meta dicts for required fields that are
                      NOT covered by the current DataFrame columns.
    """
    norm_to_field = {}
    all_model_fields = {}
    required_fields  = []

    for field in model_class._meta.get_fields():
        if not isinstance(field, Field) or field.auto_created:
            continue
        norm = FileProcessorService.normalize_name(field.name)
        norm_to_field[norm] = field.name
        all_model_fields[field.name] = field
        # Required: no null, no blank, no auto-increment pk, no callable default
        if (not field.null
                and not getattr(field, "blank", True)
                and not field.has_default()
                and field.get_internal_type() not in ("AutoField", "BigAutoField")):
            required_fields.append(_field_meta(field))

    column_mapping_info = []
    unmapped = []
    col_dtypes = df.dtypes

    # Set of model field names currently covered by DF columns
    covered_fields = set()
    for i, col in enumerate(df.columns):
        norm_col = FileProcessorService.normalize_name(str(col))
        mapped_to = norm_to_field.get(norm_col)
        matched = mapped_to is not None
        if matched:
            covered_fields.add(mapped_to)
        dtype_str = str(col_dtypes.iloc[i])
        column_mapping_info.append({
            "column":    str(col),
            "dtype":     dtype_str,
            "matched":   matched,
            "mapped_to": mapped_to,
        })
        if not matched:
            unmapped.append(str(col))

    # Missing required = required fields not covered by any DF column
    missing_required = [f for f in required_fields if f["name"] not in covered_fields]

    mapped_count = sum(1 for c in column_mapping_info if c["matched"])
    return column_mapping_info, unmapped, required_fields, mapped_count, missing_required


# ════════════════════════════════════════════════════════════════════════════════
# JSON response builder
# ════════════════════════════════════════════════════════════════════════════════

def _preview_json(df: pd.DataFrame, cache_key: str, model_class,
                   excel_info: dict = None, filename: str = "") -> dict:
    col_mapping, unmapped, req_fields, mapped_count, missing_req = _analyze(df, model_class)

    # Table headers with null stats
    headers = []
    total = max(len(df), 1)
    col_dtypes = df.dtypes  # Series indexed positionally – safe for duplicate cols
    for i, col in enumerate(df.columns):
        dtype_str = str(col_dtypes.iloc[i])
        # Count nulls positionally to handle duplicate column names
        nc = int(df.iloc[:, i].isna().sum())
        headers.append({
            "name": str(col),
            "dtype": dtype_str,
            "type": dtype_str,
            "missing_count": nc,
            "missing_percent": round(nc / total * 100, 1),
        })

    # First 10 rows – JSON-safe values
    rows = []
    for _, row in df.head(10).iterrows():
        cells = []
        for v in row:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                cells.append(None)
            elif v is True:
                cells.append(True)
            elif v is False:
                cells.append(False)
            else:
                cells.append(str(v))
        rows.append(cells)

    return {
        "success": True,
        "cache_key": cache_key,
        "model": f"{model_class._meta.app_label}.{model_class.__name__}" if model_class else None,
        "model_verbose": str(model_class._meta.verbose_name_plural) if model_class else "",
        "stats": {
            "rows": len(df),
            "columns": len(df.columns),
            "mapped_count": mapped_count,
            "required_count": len(req_fields),
        },
        "column_mapping": col_mapping,
        "table": {"headers": headers, "rows": rows},
        "excel_info": excel_info,
        "required_fields": req_fields,
        "missing_required": missing_req,
        "unmapped_columns": unmapped,
        "filename": filename,
    }


# ════════════════════════════════════════════════════════════════════════════════
# Helper: resolve model from "app_label.ModelName" string
# ════════════════════════════════════════════════════════════════════════════════

def _resolve_model(model_path: str):
    """Returns (model_class, error_response)."""
    try:
        app_label, model_name = model_path.rsplit(".", 1)
        return apps.get_model(app_label, model_name), None
    except (ValueError, LookupError) as exc:
        return None, JsonResponse({"success": False, "error": f"Modelo inválido: {exc}"}, status=400)


# ════════════════════════════════════════════════════════════════════════════════
# View: preview_async
# ════════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def preview_async(request):
    """
    Processes an uploaded file and returns a full JSON preview.
    Stores the DataFrame in Redis under a fresh UUID key.
    Replaces the old full-page-reload POST → document.write() approach.
    """
    try:
        file = request.FILES.get("file")
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
        no_header = request.POST.get("no_header", "") in ("on", "true", "1", "True")

        ext = file.name.rsplit(".", 1)[-1].lower()
        excel_info = None

        if ext in ("xls", "xlsx"):
            df, excel_info = ExcelProcessor.process_excel(
                file,
                sheet_name=sheet_name,
                cell_range=cell_range,
                no_header=no_header,
            )
        else:
            encoding = FileProcessorService.detect_encoding(file)
            content = file.read().decode(encoding, errors="replace")
            file.seek(0)
            first_line = content.split("\n")[0]
            delimiter = "," if "," in first_line else ";"
            df = pd.read_csv(StringIO(content), delimiter=delimiter)
            df.columns = [FileProcessorService.normalize_name(str(c)) for c in df.columns]

        if df is None or df.empty:
            return JsonResponse(
                {"success": False, "error": "El archivo no contiene datos en el rango especificado."},
                status=400,
            )

        cache_key = _new_preview_key()
        _cache_store(cache_key, df, {
            "filename": file.name,
            "model": model_path,
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


# ════════════════════════════════════════════════════════════════════════════════
# Generic edit helper
# ════════════════════════════════════════════════════════════════════════════════

def _edit(request, operation):
    """
    Shared logic for all in-place DataFrame edit operations.
    operation(df, body) → (df, error_string | None)
    """
    try:
        body = json.loads(request.body)
        cache_key = body.get("cache_key", "")
        model_path = body.get("model", "")

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse(
                {"success": False, "error": "Sesión expirada o inválida. Sube el archivo nuevamente."},
                status=404,
            )

        model_path = model_path or meta.get("model", "")
        model_class, err = _resolve_model(model_path)
        if err:
            return err

        df, error = operation(df, body)
        if error:
            return JsonResponse({"success": False, "error": error}, status=400)

        _cache_store(cache_key, df, meta)
        return JsonResponse(
            _preview_json(df, cache_key, model_class, meta.get("excel_info"), meta.get("filename", ""))
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido en el body."}, status=400)
    except Exception as exc:
        logger.error("Edit operation error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


# ════════════════════════════════════════════════════════════════════════════════
# Views: edit operations
# ════════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def delete_columns_async(request):
    """Drops selected columns from the working DataFrame."""
    def op(df, body):
        cols = body.get("columns", [])
        if not cols:
            return df, "No se especificaron columnas."
        missing = [c for c in cols if c not in df.columns]
        if missing:
            return df, f"Columnas no encontradas: {missing}"
        return df.drop(columns=cols), None

    return _edit(request, op)


@login_required
@require_POST
def replace_values_async(request):
    """Replaces a value in a specific column."""
    def op(df, body):
        col = body.get("column", "")
        old_val = body.get("old_value", "")
        new_val = body.get("new_value", "")
        if col not in df.columns:
            return df, f"Columna no encontrada: {col}"
        df = df.copy()
        df[col] = df[col].replace(old_val, new_val)
        return df, None

    return _edit(request, op)


@login_required
@require_POST
def fill_na_async(request):
    """Fills null values in a specific column."""
    def op(df, body):
        col = body.get("column", "")
        val = body.get("fill_value", "")
        if col not in df.columns:
            return df, f"Columna no encontrada: {col}"
        df = df.copy()
        df[col] = df[col].fillna(val)
        return df, None

    return _edit(request, op)


@login_required
@require_POST
def convert_date_async(request):
    """Converts a text column to datetime."""
    def op(df, body):
        col = body.get("column", "")
        fmt = body.get("date_format", "infer")
        if col not in df.columns:
            return df, f"Columna no encontrada: {col}"
        df = df.copy()
        try:
            if fmt == "infer":
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True)
            else:
                df[col] = pd.to_datetime(df[col], format=fmt)
        except Exception as exc:
            return df, f"Error convirtiendo fechas: {exc}"
        return df, None

    return _edit(request, op)



# ════════════════════════════════════════════════════════════════════════════════
# View: reanalyze_async  – re-map cached DataFrame against a different model
# ════════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def reanalyze_async(request):
    """
    Re-runs column mapping analysis against a different model WITHOUT touching
    the DataFrame.  Updates meta["model"] in the cache so subsequent edits and
    confirm_upload use the new model.

    POST JSON: { "cache_key": "...", "model": "app_label.ModelName" }
    Returns:   same shape as _preview_json so renderPreview() works unchanged.
    """
    try:
        body       = json.loads(request.body)
        cache_key  = body.get("cache_key", "").strip()
        model_path = body.get("model", "").strip()

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

        # Update the stored model in meta so future _edit / confirm calls use it
        meta = {**(meta or {}), "model": model_path}
        _cache_store(cache_key, df, meta)

        logger.info("reanalyze_async – key=%s new_model=%s shape=%s", cache_key, model_path, df.shape)
        return JsonResponse(
            _preview_json(df, cache_key, model_class, meta.get("excel_info"), meta.get("filename", ""))
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("reanalyze_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)

# ════════════════════════════════════════════════════════════════════════════════
# View: save_clipboard_async
# ════════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def save_clipboard_async(request):
    """
    Saves the current preview DataFrame to the clipboard (Redis-backed).
    Reads from preview cache_key and copies into DataFrameClipboard.
    """
    try:
        body = json.loads(request.body)
        preview_key = body.get("cache_key", "")
        clip_name = body.get("clip_name", "").strip()
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
            request,
            df,
            key=clip_name,
            metadata={**meta, "description": clip_description},
        )

        clips = DataFrameClipboard.list_clips(request)
        return JsonResponse({
            "success": True,
            "message": f'Clip "{saved_key}" guardado exitosamente.',
            "clips": clips,
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("save_clipboard_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


# ════════════════════════════════════════════════════════════════════════════════
# View: confirm_upload_async
# ════════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def confirm_upload_async(request):
    """
    Reads the working DataFrame from Redis, bulk-creates model instances.
    Optionally clears existing records first.
    Deletes the preview cache key on success.
    """
    try:
        body = json.loads(request.body)
        cache_key = body.get("cache_key", "")
        model_path = body.get("model", "")
        clear_existing = body.get("clear_existing", False)

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse(
                {"success": False, "error": "Sesión expirada. Sube el archivo nuevamente."},
                status=404,
            )

        model_path = model_path or meta.get("model", "")
        model_class, err = _resolve_model(model_path)
        if err:
            return err

        if clear_existing:
            deleted_count = model_class.objects.all().delete()[0]
            logger.info("Cleared %d existing records from %s", deleted_count, model_class.__name__)

        field_defaults = body.get("field_defaults", {})  # {field_name: {strategy, value, prefix, col_first, col_last, domain}}

        # Apply field generators to DataFrame before creating instances
        if field_defaults:
            df = _apply_field_defaults(df, model_class, field_defaults)

        records = FileProcessorService._create_instances_auto(df, model_class)
        if not records:
            return JsonResponse(
                {"success": False, "error": "No se generaron registros válidos. Verifica el mapeo de columnas."},
                status=400,
            )

        # Handle password field specially (must call set_unusable_password / set_password)
        records = _apply_password_fields(records, model_class, field_defaults)

        created = model_class.objects.bulk_create(records, ignore_conflicts=True)
        cache.delete(cache_key)  # Clean up – no longer needed

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


# ════════════════════════════════════════════════════════════════════════════════
# View: load_clip_as_preview
# ════════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def load_clip_as_preview(request):
    """
    Loads a clipboard DataFrame into a fresh preview cache key so the user
    can inspect / edit it in the SPA panel before confirming the upload.

    POST body: { "clip_name": "...", "model": "app_label.ModelName" }
    Returns the same JSON shape as preview_async so renderPreview() works unchanged.
    """
    try:
        body = json.loads(request.body)
        clip_name  = body.get("clip_name", "").strip()
        model_path = body.get("model",     "").strip()

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

        cache_key = _new_preview_key()
        merged_meta = {
            **(meta or {}),
            "model":    model_path,
            "filename": (meta or {}).get("filename") or clip_name,
        }
        _cache_store(cache_key, df, merged_meta)

        logger.info(
            "load_clip_as_preview – clip: %s, shape: %s, key: %s",
            clip_name, df.shape, cache_key,
        )
        return JsonResponse(
            _preview_json(df, cache_key, model_class, None, merged_meta.get("filename", clip_name))
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("load_clip_as_preview error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


# ════════════════════════════════════════════════════════════════════════════════
# View: save_as_dataset  (promote preview → StoredDataset)
# ════════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def save_as_dataset(request):
    """
    Persist the current preview DataFrame as a StoredDataset (permanent Redis key
    + DB row).  Called from the upload panel's "Guardar como Dataset" button.

    POST JSON: { "cache_key": "df_preview_...", "name": "...", "description": "..." }
    Returns:   { "success": true, "dataset": { id, name, rows, col_count, ... } }
    """
    try:
        import uuid as _uuid
        from analyst.models import StoredDataset

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
                {"success": False, "error": "Preview no encontrado o expirado. Vuelve a subir el archivo."},
                status=404,
            )

        ds_id    = _uuid.uuid4()
        perm_key = StoredDataset.make_cache_key(str(ds_id))

        # Write to Redis with no TTL (permanent until dataset is deleted)
        from django.core.cache import cache as _cache
        _cache.set(perm_key, {"data": _serialize(df), "meta": {**(meta or {}), "stored_dataset_id": str(ds_id)}}, timeout=None)

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
            data_blob   = _serialize(df),   # persist to DB for restart survival
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


# ════════════════════════════════════════════════════════════════════════════════
# Views: extended edit operations
# ════════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def rename_column_async(request):
    """Renames a single column."""
    def op(df, body):
        old_name = body.get("old_name", "").strip()
        new_name = body.get("new_name", "").strip()
        if not old_name:
            return df, "Nombre original requerido."
        if not new_name:
            return df, "Nuevo nombre requerido."
        if old_name not in df.columns:
            return df, f"Columna no encontrada: {old_name}"
        if new_name in df.columns and new_name != old_name:
            return df, f"Ya existe una columna con el nombre: {new_name}"
        return df.rename(columns={old_name: new_name}), None

    return _edit(request, op)


@login_required
@require_POST
def drop_duplicates_async(request):
    """Removes duplicate rows from the DataFrame."""
    def op(df, body):
        subset = body.get("subset") or None        # list of columns, or None → all
        keep   = body.get("keep", "first")         # 'first' | 'last' | False
        if subset:
            missing = [c for c in subset if c not in df.columns]
            if missing:
                return df, f"Columnas no encontradas: {missing}"
        before = len(df)
        keep_val = False if keep == "none" else keep
        df = df.drop_duplicates(subset=subset, keep=keep_val).reset_index(drop=True)
        removed = before - len(df)
        if removed == 0:
            return df, "No se encontraron filas duplicadas."
        return df, None

    return _edit(request, op)


@login_required
@require_POST
def sort_data_async(request):
    """Sorts the DataFrame by one or more columns."""
    def op(df, body):
        columns   = body.get("columns", [])
        ascending = body.get("ascending", True)     # bool or list of bools
        if not columns:
            return df, "Selecciona al menos una columna para ordenar."
        missing = [c for c in columns if c not in df.columns]
        if missing:
            return df, f"Columnas no encontradas: {missing}"
        if isinstance(ascending, bool):
            asc_list = [ascending] * len(columns)
        else:
            asc_list = ascending[:len(columns)]
        df = df.sort_values(by=columns, ascending=asc_list).reset_index(drop=True)
        return df, None

    return _edit(request, op)


@login_required
@require_POST
def convert_dtype_async(request):
    """Converts a column's data type (int, float, str, bool)."""
    def op(df, body):
        col      = body.get("column", "")
        dtype    = body.get("dtype", "")
        errors   = body.get("errors", "coerce")   # 'coerce' | 'raise'
        ALLOWED  = {"int": "Int64", "float": "float64", "str": "object", "bool": "bool",
                    "int64": "Int64", "float64": "float64", "object": "object"}
        if col not in df.columns:
            return df, f"Columna no encontrada: {col}"
        target = ALLOWED.get(dtype.lower())
        if not target:
            return df, f"Tipo no válido: {dtype}. Usa: int, float, str, bool."
        df = df.copy()
        try:
            if target == "Int64":
                df[col] = pd.to_numeric(df[col], errors=errors).astype("Int64")
            elif target == "float64":
                df[col] = pd.to_numeric(df[col], errors=errors).astype("float64")
            elif target == "object":
                df[col] = df[col].astype(str).replace("nan", "").replace("<NA>", "")
            elif target == "bool":
                df[col] = df[col].astype(bool)
        except Exception as exc:
            return df, f"Error convirtiendo tipo: {exc}"
        return df, None

    return _edit(request, op)


@login_required
@require_POST
def normalize_text_async(request):
    """Applies text normalization to a string column (strip, upper/lower/title, remove accents)."""
    import unicodedata

    def op(df, body):
        col       = body.get("column", "")
        ops_list  = body.get("ops", [])   # list of: strip, upper, lower, title, remove_accents
        if col not in df.columns:
            return df, f"Columna no encontrada: {col}"
        if not ops_list:
            return df, "Selecciona al menos una operación."
        df = df.copy()
        s = df[col].astype(str)
        for op_name in ops_list:
            if op_name == "strip":
                s = s.str.strip()
            elif op_name == "upper":
                s = s.str.upper()
            elif op_name == "lower":
                s = s.str.lower()
            elif op_name == "title":
                s = s.str.title()
            elif op_name == "remove_accents":
                s = s.apply(lambda x: unicodedata.normalize("NFD", x)
                            .encode("ascii", "ignore").decode("utf-8"))
        df[col] = s
        return df, None

    return _edit(request, op)

# ════════════════════════════════════════════════════════════════════════════════
# View: apply_defaults  – fills missing required fields before confirm_upload
# ════════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def apply_defaults_async(request):
    """
    Applies user-supplied default strategies to fill missing required fields
    in the working DataFrame, then returns a fresh preview.

    POST JSON:
    {
      "cache_key": "df_preview_...",
      "model":     "app.Model",
      "defaults": {
        "username":  {"strategy": "from_column",  "source": "nombre"},
        "password":  {"strategy": "fixed",        "value":  "Cambiar123!"},
        "email":     {"strategy": "template",     "template": "{nombre}.{apellido}@empresa.com"},
        "code":      {"strategy": "sequence",     "prefix": "USR", "start": 1, "pad": 4},
        "slug":      {"strategy": "slugify",      "source": "nombre"},
        "uuid_col":  {"strategy": "uuid"},
        "date_col":  {"strategy": "today"},
        "num_col":   {"strategy": "fixed",        "value": "0"},
      }
    }

    Strategies:
      fixed        → same literal value for every row
      from_column  → copy value from another column (with optional suffix for uniqueness)
      template     → f-string style: {col_name} placeholders filled per row
      sequence     → PREFIX0001, PREFIX0002, …  (guarantees uniqueness)
      slugify      → URL-safe slug from another column (unique via sequence suffix)
      uuid         → uuid4 per row
      today        → current date/datetime
    """
    import uuid as _uuid
    import re as _re
    from datetime import date as _date, datetime as _datetime

    def _slugify(s: str) -> str:
        """Simple ASCII slug: lowercase, spaces→-, strip non-alphanum."""
        import unicodedata
        s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
        s = s.lower().strip()
        s = _re.sub(r"[^\w\s-]", "", s)
        s = _re.sub(r"[\s_]+", "-", s)
        return s.strip("-")

    try:
        body      = json.loads(request.body)
        cache_key = body.get("cache_key", "")
        model_path = body.get("model", "")
        defaults  = body.get("defaults", {})   # {field_name: {strategy, ...}}

        if not defaults:
            return JsonResponse({"success": False, "error": "No se enviaron defaults."}, status=400)

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse(
                {"success": False, "error": "Sesión expirada. Sube el archivo nuevamente."},
                status=404,
            )

        model_path = model_path or meta.get("model", "")
        model_class, err = _resolve_model(model_path)
        if err:
            return err

        df = df.copy()

        for field_name, cfg in defaults.items():
            strategy = cfg.get("strategy", "fixed")
            n        = len(df)

            if strategy == "fixed":
                df[field_name] = str(cfg.get("value", ""))

            elif strategy == "from_column":
                src = cfg.get("source", "")
                if src not in df.columns:
                    return JsonResponse(
                        {"success": False, "error": f"Columna fuente '{src}' no existe."},
                        status=400,
                    )
                unique_field = getattr(model_class._meta.get_field(field_name), "unique", False) if field_name in [f.name for f in model_class._meta.get_fields()] else False
                if unique_field:
                    # Guarantee uniqueness: append row index if duplicated
                    base = df[src].astype(str).str.strip()
                    seen: dict = {}
                    result = []
                    for i, v in enumerate(base):
                        if v in seen:
                            seen[v] += 1
                            result.append(f"{v}_{seen[v]}")
                        else:
                            seen[v] = 0
                            result.append(v)
                    df[field_name] = result
                else:
                    df[field_name] = df[src].astype(str).str.strip()

            elif strategy == "template":
                tpl = cfg.get("template", "")
                # Extract {col} placeholders
                placeholders = _re.findall(r"\{(\w+)\}", tpl)
                missing_cols = [p for p in placeholders if p not in df.columns]
                if missing_cols:
                    return JsonResponse(
                        {"success": False,
                         "error": f"Columnas no encontradas en template: {missing_cols}"},
                        status=400,
                    )
                result = []
                for _, row in df.iterrows():
                    val = tpl
                    for p in placeholders:
                        val = val.replace(f"{{{p}}}", str(row[p]).strip())
                    result.append(val)
                # Make unique if field requires it
                unique_field = getattr(model_class._meta.get_field(field_name), "unique", False) if field_name in [f.name for f in model_class._meta.get_fields()] else False
                if unique_field:
                    seen: dict = {}
                    final = []
                    for v in result:
                        if v in seen:
                            seen[v] += 1
                            final.append(f"{v}{seen[v]}")
                        else:
                            seen[v] = 0
                            final.append(v)
                    result = final
                df[field_name] = result

            elif strategy == "sequence":
                prefix  = str(cfg.get("prefix", ""))
                start   = int(cfg.get("start", 1))
                pad     = int(cfg.get("pad", 0))
                df[field_name] = [
                    f"{prefix}{str(start + i).zfill(pad) if pad else start + i}"
                    for i in range(n)
                ]

            elif strategy == "slugify":
                src = cfg.get("source", "")
                if src not in df.columns:
                    return JsonResponse(
                        {"success": False, "error": f"Columna fuente '{src}' no existe."},
                        status=400,
                    )
                base = df[src].astype(str).apply(_slugify)
                seen: dict = {}
                result = []
                for v in base:
                    if v in seen:
                        seen[v] += 1
                        result.append(f"{v}-{seen[v]}")
                    else:
                        seen[v] = 0
                        result.append(v)
                df[field_name] = result

            elif strategy == "uuid":
                df[field_name] = [str(_uuid.uuid4()) for _ in range(n)]

            elif strategy == "today":
                try:
                    ft = model_class._meta.get_field(field_name).get_internal_type()
                except Exception:
                    ft = "DateField"
                if "DateTime" in ft:
                    df[field_name] = _datetime.now().isoformat()
                else:
                    df[field_name] = str(_date.today())

            else:
                return JsonResponse(
                    {"success": False, "error": f"Estrategia desconocida: '{strategy}'"},
                    status=400,
                )

        _cache_store(cache_key, df, meta)
        return JsonResponse(
            _preview_json(df, cache_key, model_class, meta.get("excel_info"), meta.get("filename", ""))
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("apply_defaults_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)

# ════════════════════════════════════════════════════════════════════════════════
# View: apply_field_defaults_async
# ════════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def apply_field_defaults_async(request):
    """
    Injects default/computed values for required fields missing from the DataFrame.
    
    Each entry in `defaults` can be:
      { "field": "username", "strategy": "auto_username", "source_cols": ["first_name","last_name"] }
      { "field": "password",  "strategy": "fixed",         "value": "changeme123" }
      { "field": "email",     "strategy": "derived_email",  "source_cols": ["first_name","last_name"], "domain": "empresa.com" }
      { "field": "is_active", "strategy": "fixed",          "value": "true" }
      { "field": "date_joined","strategy": "now" }
      { "field": "slug",      "strategy": "slugify",        "source_col": "name" }
      { "field": "order",     "strategy": "sequence",       "start": 1 }
      { "field": "custom",    "strategy": "fixed",          "value": "anything" }
    
    POST JSON: { "cache_key": "...", "model": "...", "defaults": [...] }
    Returns the same shape as _preview_json so renderPreview() works unchanged.
    """
    import unicodedata
    import re
    from django.utils.text import slugify as _slugify
    from django.utils import timezone

    def _slugify_str(s):
        s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

    def _make_unique(base_series, existing_set):
        """Add numeric suffix to make values unique within the series and against existing_set."""
        result = []
        seen = set(existing_set)
        counts = {}
        for val in base_series:
            if val not in seen:
                seen.add(val)
                result.append(val)
            else:
                counts[val] = counts.get(val, 0) + 1
                candidate = f"{val}{counts[val]}"
                while candidate in seen:
                    counts[val] += 1
                    candidate = f"{val}{counts[val]}"
                seen.add(candidate)
                result.append(candidate)
        return result

    try:
        body      = json.loads(request.body)
        cache_key = body.get("cache_key", "")
        model_path = body.get("model", "")
        defaults  = body.get("defaults", [])   # list of strategy dicts

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse(
                {"success": False, "error": "Sesión expirada. Sube el archivo nuevamente."},
                status=404,
            )

        model_path = model_path or meta.get("model", "")
        model_class, err = _resolve_model(model_path)
        if err:
            return err

        df = df.copy()
        errors = []

        for spec in defaults:
            field    = spec.get("field", "")
            strategy = spec.get("strategy", "fixed")

            if not field:
                continue

            try:
                if strategy == "fixed":
                    raw = spec.get("value", "")
                    # Try to cast to sensible type based on field
                    try:
                        f = model_class._meta.get_field(field)
                        ft = f.get_internal_type()
                        if ft in ("BooleanField", "NullBooleanField"):
                            val = str(raw).lower() in ("1", "true", "yes", "si", "sí")
                        elif ft in ("IntegerField", "BigIntegerField", "SmallIntegerField", "PositiveIntegerField"):
                            val = int(raw)
                        elif ft in ("FloatField", "DecimalField"):
                            val = float(raw)
                        else:
                            val = str(raw)
                    except Exception:
                        val = str(raw)
                    df[field] = val

                elif strategy == "now":
                    df[field] = timezone.now().isoformat()

                elif strategy == "sequence":
                    start = int(spec.get("start", 1))
                    df[field] = range(start, start + len(df))

                elif strategy == "slugify":
                    src = spec.get("source_col", "")
                    if src and src in df.columns:
                        df[field] = df[src].astype(str).apply(_slugify_str)
                    else:
                        errors.append(f"slugify: columna fuente '{src}' no encontrada.")

                elif strategy == "auto_username":
                    src_cols = spec.get("source_cols", [])
                    # Build base: first 3 chars of col[0] + col[1] (or single col)
                    if len(src_cols) >= 2 and src_cols[0] in df.columns and src_cols[1] in df.columns:
                        base = (
                            df[src_cols[0]].astype(str).str.strip()
                              .str.lower().str.replace(r"[^a-z0-9]", "", regex=True).str[:3]
                            + df[src_cols[1]].astype(str).str.strip()
                              .str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
                        )
                    elif len(src_cols) >= 1 and src_cols[0] in df.columns:
                        base = (
                            df[src_cols[0]].astype(str).str.strip()
                              .str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
                        )
                    else:
                        base = pd.Series([f"user{i}" for i in range(len(df))])

                    # Fetch existing usernames from DB if field is unique
                    try:
                        existing = set(model_class.objects.values_list(field, flat=True))
                    except Exception:
                        existing = set()

                    df[field] = _make_unique(base.tolist(), existing)

                elif strategy == "derived_email":
                    src_cols = spec.get("source_cols", [])
                    domain   = spec.get("domain", "example.com").lstrip("@")
                    if len(src_cols) >= 2 and src_cols[0] in df.columns and src_cols[1] in df.columns:
                        local = (
                            df[src_cols[0]].astype(str).str.strip()
                              .str.lower().str.replace(r"[^a-z0-9]", "", regex=True).str[:3]
                            + "."
                            + df[src_cols[1]].astype(str).str.strip()
                              .str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
                        )
                    elif len(src_cols) >= 1 and src_cols[0] in df.columns:
                        local = (
                            df[src_cols[0]].astype(str).str.strip()
                              .str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
                        )
                    else:
                        local = pd.Series([f"user{i}" for i in range(len(df))])

                    existing_emails = set()
                    try:
                        existing_emails = set(model_class.objects.values_list(field, flat=True))
                    except Exception:
                        pass

                    emails = [f"{l}@{domain}" for l in local.tolist()]
                    df[field] = _make_unique(emails, existing_emails)

                elif strategy == "hashed_password":
                    # Use Django's make_password so the hash is correct
                    from django.contrib.auth.hashers import make_password
                    raw_pwd = spec.get("value", "changeme123")
                    df[field] = make_password(raw_pwd)

                elif strategy == "concat":
                    src_cols  = spec.get("source_cols", [])
                    separator = spec.get("separator", " ")
                    available = [c for c in src_cols if c in df.columns]
                    if available:
                        df[field] = df[available].astype(str).agg(separator.join, axis=1)
                    else:
                        errors.append(f"concat: ninguna columna fuente encontrada para '{field}'.")

                elif strategy == "copy_col":
                    src = spec.get("source_col", "")
                    if src in df.columns:
                        df[field] = df[src]
                    else:
                        errors.append(f"copy_col: columna '{src}' no encontrada.")

            except Exception as exc:
                errors.append(f"Error en campo '{field}': {exc}")

        if errors:
            return JsonResponse({"success": False, "error": " | ".join(errors)}, status=400)

        _cache_store(cache_key, df, meta)
        return JsonResponse(
            _preview_json(df, cache_key, model_class, meta.get("excel_info"), meta.get("filename", ""))
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("apply_field_defaults_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)

# ════════════════════════════════════════════════════════════════════════════════
# Field-default generators  (used by confirm_upload_async)
# ════════════════════════════════════════════════════════════════════════════════

def _apply_field_defaults(df: pd.DataFrame, model_class, field_defaults: dict) -> pd.DataFrame:
    """
    Generates synthetic column values for required fields that are missing from df.

    field_defaults format:
      {
        "username": {
          "strategy": "auto_slug",         # or seq_prefix / uuid_short / fixed / auto_email / today / seq / zero / true / false / auto_initials
          "value":    "USER",               # used by fixed / seq_prefix (prefix)
          "col_first":"Nombre",             # DF column for first name
          "col_last": "Apellidos",          # DF column for last name
          "domain":   "empresa.com",        # used by auto_email
        },
        "password": { "strategy": "auto_unusable" },
        "is_active": { "strategy": "true" },
      }
    """
    import uuid as _uuid
    import re as _re

    df = df.copy()
    n = len(df)

    def _slug(s: str) -> str:
        s = str(s).lower().strip()
        s = _re.sub(r"[^a-z0-9\s]", "", s)
        return _re.sub(r"\s+", ".", s).strip(".")

    def _initials(first: str, last: str) -> str:
        f = str(first)[:1].upper() if first else "U"
        l = str(last)[:1].upper()  if last  else "X"
        return f + l

    for field_name, cfg in field_defaults.items():
        if field_name in df.columns:
            continue  # already exists – skip

        strategy  = cfg.get("strategy", "fixed")
        fix_val   = cfg.get("value", "")
        col_first = cfg.get("col_first", "")
        col_last  = cfg.get("col_last",  "")
        domain    = cfg.get("domain", "empresa.com")
        prefix    = cfg.get("prefix") or fix_val or "USER"

        # Helpers to resolve DF column values safely
        def _col(name):
            return df[name] if name and name in df.columns else pd.Series([""] * n)

        if strategy == "auto_slug":
            first = _col(col_first)
            last  = _col(col_last)
            bases = [_slug(f"{r[0]} {r[1]}") or "user" for r in zip(first, last)]
            seen  = {}
            result = []
            for b in bases:
                if b not in seen:
                    seen[b] = 0
                    result.append(b)
                else:
                    seen[b] += 1
                    result.append(f"{b}.{seen[b]}")
            df[field_name] = result

        elif strategy == "seq_prefix":
            df[field_name] = [f"{prefix}{i+1:04d}" for i in range(n)]

        elif strategy == "uuid_short":
            df[field_name] = [str(_uuid.uuid4())[:8] for _ in range(n)]

        elif strategy == "auto_initials":
            first = _col(col_first)
            last  = _col(col_last)
            counts = {}
            result = []
            for f, l in zip(first, last):
                base = _initials(f, l)
                counts[base] = counts.get(base, 0) + 1
                result.append(f"{base}{counts[base]:03d}")
            df[field_name] = result

        elif strategy == "auto_email":
            first = _col(col_first)
            last  = _col(col_last)
            bases = [f"{_slug(f)}.{_slug(l)}@{domain}" if _slug(f) or _slug(l)
                     else f"user{i}@{domain}" for i, (f, l) in enumerate(zip(first, last))]
            # Ensure uniqueness
            seen = {}
            result = []
            for b in bases:
                local, dom = b.rsplit("@", 1)
                if local not in seen:
                    seen[local] = 0
                    result.append(b)
                else:
                    seen[local] += 1
                    result.append(f"{local}.{seen[local]}@{dom}")
            df[field_name] = result

        elif strategy == "seq":
            df[field_name] = list(range(1, n + 1))

        elif strategy == "zero":
            df[field_name] = [0] * n

        elif strategy == "true":
            df[field_name] = [True] * n

        elif strategy == "false":
            df[field_name] = [False] * n

        elif strategy == "today":
            from django.utils.timezone import now as _now
            df[field_name] = [_now().date().isoformat()] * n

        elif strategy in ("fixed", "fixed_hash"):
            df[field_name] = [fix_val] * n

        elif strategy == "auto_unusable":
            # Sentinel – handled later in _apply_password_fields
            df[field_name] = ["__UNUSABLE__"] * n

    return df


def _apply_password_fields(records: list, model_class, field_defaults: dict) -> list:
    """Post-processes records to apply proper Django password hashing."""
    from django.contrib.auth.hashers import make_password

    for field_name, cfg in field_defaults.items():
        strategy = cfg.get("strategy", "")
        if strategy == "auto_unusable":
            for obj in records:
                if hasattr(obj, "set_unusable_password"):
                    obj.set_unusable_password()
                else:
                    setattr(obj, field_name, make_password(None))
        elif strategy == "fixed_hash":
            pw = make_password(cfg.get("value", "changeme"))
            for obj in records:
                setattr(obj, field_name, pw)

    return records

# ════════════════════════════════════════════════════════════════════════════════
# Views: filter rows by column value
# ════════════════════════════════════════════════════════════════════════════════

def _build_mask(df: pd.DataFrame, column: str, operator: str, value: str, case_sensitive: bool = False):
    """
    Returns a boolean Series mask for rows that match the filter.
    Supports:  eq, neq, contains, not_contains, starts_with, ends_with,
               gt, gte, lt, lte, is_null, is_not_null, regex
    """
    if column not in df.columns:
        raise ValueError(f"Columna no encontrada: {column}")

    s = df[column]

    # ── Null checks (no value needed) ──────────────────────────────────────
    if operator == "is_null":
        return s.isna()
    if operator == "is_not_null":
        return s.notna()

    # ── Numeric operators ───────────────────────────────────────────────────
    numeric_ops = {"gt", "gte", "lt", "lte"}
    if operator in numeric_ops:
        try:
            num_val = float(value)
            s_num   = pd.to_numeric(s, errors="coerce")
            if operator == "gt":  return s_num >  num_val
            if operator == "gte": return s_num >= num_val
            if operator == "lt":  return s_num <  num_val
            if operator == "lte": return s_num <= num_val
        except (ValueError, TypeError) as exc:
            raise ValueError(f"El valor '{value}' no es numérico.") from exc

    # ── Text / equality operators ───────────────────────────────────────────
    str_s = s.astype(str)
    if not case_sensitive:
        str_s  = str_s.str.lower()
        cmp    = value.lower()
    else:
        cmp = value

    if operator == "eq":
        return str_s == cmp
    if operator == "neq":
        return str_s != cmp
    if operator == "contains":
        return str_s.str.contains(cmp, regex=False, na=False)
    if operator == "not_contains":
        return ~str_s.str.contains(cmp, regex=False, na=False)
    if operator == "starts_with":
        return str_s.str.startswith(cmp, na=False)
    if operator == "ends_with":
        return str_s.str.endswith(cmp, na=False)
    if operator == "regex":
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            return str_s.str.contains(value, regex=True, flags=flags, na=False)
        except re.error as exc:
            raise ValueError(f"Expresión regular inválida: {exc}") from exc

    raise ValueError(f"Operador desconocido: {operator}")


@login_required
@require_POST
def filter_rows_count_async(request):
    """
    Counts rows matching the filter without modifying the DataFrame.
    Returns count, percentage, and up to 10 sample rows.

    POST JSON: { cache_key, column, operator, value, case_sensitive }
    """
    try:
        body           = json.loads(request.body)
        cache_key      = body.get("cache_key", "")
        column         = body.get("column", "")
        operator       = body.get("operator", "eq")
        value          = body.get("value", "")
        case_sensitive = bool(body.get("case_sensitive", False))

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse({"success": False, "error": "Sesión expirada."}, status=404)

        try:
            mask = _build_mask(df, column, operator, value, case_sensitive)
        except ValueError as exc:
            return JsonResponse({"success": False, "error": str(exc)}, status=400)

        matched_df  = df[mask]
        count       = int(mask.sum())
        total       = len(df)
        percent     = round(count / total * 100, 2) if total else 0

        # Sample rows (up to 10) – JSON-safe
        sample_rows = []
        for _, row in matched_df.head(10).iterrows():
            cells = []
            for v in row:
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    cells.append(None)
                else:
                    cells.append(str(v))
            sample_rows.append(cells)

        return JsonResponse({
            "success":   True,
            "count":     count,
            "total":     total,
            "percent":   percent,
            "columns":   [str(c) for c in df.columns],
            "sample":    sample_rows,
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("filter_rows_count_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_POST
def filter_rows_delete_async(request):
    """
    Deletes rows matching the filter and returns updated preview.

    POST JSON: { cache_key, model, column, operator, value, case_sensitive }
    """
    def op(df, body):
        column         = body.get("column", "")
        operator       = body.get("operator", "eq")
        value          = body.get("value", "")
        case_sensitive = bool(body.get("case_sensitive", False))
        try:
            mask = _build_mask(df, column, operator, value, case_sensitive)
        except ValueError as exc:
            return df, str(exc)

        removed = int(mask.sum())
        if removed == 0:
            return df, "No se encontraron filas que coincidan con el filtro."

        df = df[~mask].reset_index(drop=True)
        logger.info("filter_rows_delete: removed %d rows via %s %s '%s'",
                    removed, column, operator, value)
        return df, None

    return _edit(request, op)


@login_required
@require_POST
def filter_rows_replace_async(request):
    """
    Replaces a substring (or full value) in a target column,
    optionally scoped to rows matching a filter.

    POST JSON: {
        cache_key, model,
        filter_column, filter_operator, filter_value, filter_case,
        target_column,
        find_value,        # substring / regex pattern to find
        replace_with,      # replacement string (empty = delete the match)
        case_sensitive,    # bool
        use_regex,         # bool – treat find_value as regex
        apply_to_all_rows  # bool – ignore filter, act on entire column
    }
    """
    def op(df, body):
        filter_column  = body.get("filter_column", "")
        filter_op      = body.get("filter_operator", "eq")
        filter_value   = body.get("filter_value", "")
        filter_case    = bool(body.get("filter_case", False))
        target_column  = body.get("target_column", "")
        find_value     = body.get("find_value", "")
        replace_with   = body.get("replace_with", "")
        case_sensitive = bool(body.get("case_sensitive", False))
        use_regex      = bool(body.get("use_regex", False))
        apply_to_all   = bool(body.get("apply_to_all_rows", False))

        if target_column not in df.columns:
            return df, f"Columna destino no encontrada: '{target_column}'"

        df = df.copy()

        # ── Build row mask ────────────────────────────────────────────────────
        if apply_to_all or not filter_column or filter_column not in df.columns:
            mask = pd.Series([True] * len(df), index=df.index)
        else:
            try:
                mask = _build_mask(df, filter_column, filter_op, filter_value, filter_case)
            except ValueError as exc:
                return df, str(exc)

        matched_count = int(mask.sum())
        if matched_count == 0:
            return df, "No hay filas que coincidan con el filtro."

        # ── Perform substring / regex replacement ────────────────────────────
        col_series = df.loc[mask, target_column].astype(str)

        import re as _re
        flags = 0 if case_sensitive else _re.IGNORECASE

        if use_regex:
            # Validate pattern first
            try:
                _re.compile(find_value, flags)
            except _re.error as exc:
                return df, f"Expresión regular inválida: {exc}"
            replaced = col_series.str.replace(find_value, replace_with,
                                              regex=True, flags=flags)
        else:
            # Literal substring replace
            if not case_sensitive:
                # pandas str.replace with case-insensitive literal needs regex=True
                # but we escape the pattern to keep it literal
                pattern = _re.escape(find_value)
                replaced = col_series.str.replace(pattern, replace_with,
                                                  regex=True, flags=flags)
            else:
                replaced = col_series.str.replace(find_value, replace_with,
                                                  regex=False)

        df.loc[mask, target_column] = replaced

        changed = int((df.loc[mask, target_column] != col_series).sum())
        logger.info(
            "filter_rows_replace: '%s'→'%s' in col '%s', %d/%d rows affected",
            find_value, replace_with, target_column, changed, matched_count
        )
        if changed == 0:
            return df, f"No se encontró '{find_value}' en las {matched_count:,} filas filtradas."

        return df, None

    return _edit(request, op)


@login_required
@require_POST
def filter_unique_values_async(request):
    """
    Returns unique values for a column with counts and percentages.
    Caps at 500 values (sorted by frequency desc) to keep the response fast.

    POST JSON: { cache_key, column, max_values? }
    Returns:   { success, column, values:[{value,count,pct,is_null}],
                 total_unique, total_rows, capped }
    """
    MAX = 500

    try:
        body      = json.loads(request.body)
        cache_key = body.get("cache_key", "")
        column    = body.get("column", "")
        max_vals  = min(int(body.get("max_values", MAX)), MAX)

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse({"success": False, "error": "Sesión expirada."}, status=404)

        if column not in df.columns:
            return JsonResponse({"success": False, "error": f"Columna no encontrada: '{column}'"}, status=400)

        s = df[column]
        total_rows   = len(s)
        total_unique = int(s.nunique(dropna=False))

        # Value counts including NaN
        vc = s.value_counts(dropna=False).reset_index()
        vc.columns = ["value", "count"]
        vc = vc.sort_values("count", ascending=False)

        capped = len(vc) > max_vals
        vc     = vc.head(max_vals)

        values = []
        for _, row in vc.iterrows():
            v       = row["value"]
            cnt     = int(row["count"])
            is_null = v is None or (isinstance(v, float) and pd.isna(v))
            values.append({
                "value":   None if is_null else (str(v) if not isinstance(v, (int, float, bool)) else v),
                "count":   cnt,
                "pct":     round(cnt / total_rows * 100, 2) if total_rows else 0,
                "is_null": is_null,
            })

        return JsonResponse({
            "success":      True,
            "column":       column,
            "values":       values,
            "total_unique": total_unique,
            "total_rows":   total_rows,
            "capped":       capped,
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("filter_unique_values_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)
