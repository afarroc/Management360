# analyst/views/data_upload_async/_core.py
"""
Shared helpers used by all upload sub-modules.

  - Serialization / cache wrappers
  - Column / model analysis  (_field_meta, _source_hints, _analyze)
  - JSON response builder    (_preview_json)
  - Model resolver           (_resolve_model)
"""

import uuid
import logging
import pickle
import base64

import pandas as pd

from django.apps import apps
from django.core.cache import cache
from django.db.models import Field
from django.http import JsonResponse

from analyst.services.file_processor_service import FileProcessorService

logger = logging.getLogger(__name__)

PREVIEW_TTL = 1800  # 30 min


# ── Serialization ─────────────────────────────────────────────────────────────

def _serialize(df: pd.DataFrame) -> str:
    return base64.b64encode(pickle.dumps(df)).decode()


def _deserialize(s: str) -> pd.DataFrame:
    return pickle.loads(base64.b64decode(s.encode()))


# ── Cache helpers ─────────────────────────────────────────────────────────────

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


# ── Column / model analysis ───────────────────────────────────────────────────

def _source_hints(field) -> list:
    n = field.name.lower()
    mapping = {
        "username":   ["nombre", "name", "first", "apellido", "last", "user"],
        "email":      ["email", "correo", "mail"],
        "first_name": ["nombre", "first", "name", "primer"],
        "last_name":  ["apellido", "last", "surname"],
        "password":   [],
        "phone":      ["telefono", "phone", "celular", "movil"],
    }
    for key, hints in mapping.items():
        if key in n:
            return hints
    return []


def _field_meta(field) -> dict:
    """Extracts metadata about a model field useful for UI default-value suggestions."""
    ft      = field.get_internal_type()
    unique  = getattr(field, "unique", False)
    max_len = getattr(field, "max_length", None)

    generators = []
    name_lower = field.name.lower()

    if ft in ("CharField", "TextField"):
        if unique:
            generators += [
                {"id": "auto_slug",     "label": "Auto slug  (nombre + apellido → juan.garcia.3)"},
                {"id": "auto_initials", "label": "Iniciales  (JG001, JG002…)"},
                {"id": "seq_prefix",    "label": "Prefijo + secuencia  (USER001, USER002…)"},
                {"id": "uuid_short",    "label": "UUID corto  (a1b2c3d4)"},
            ]
        generators.append({"id": "fixed", "label": "Valor fijo para todos"})

    elif ft in ("IntegerField", "BigIntegerField", "SmallIntegerField", "PositiveIntegerField"):
        generators += [
            {"id": "seq",   "label": "Secuencia  (1, 2, 3…)"},
            {"id": "fixed", "label": "Valor fijo para todos"},
            {"id": "zero",  "label": "Cero (0)"},
        ]

    elif ft in ("FloatField", "DecimalField"):
        generators += [
            {"id": "fixed", "label": "Valor fijo para todos"},
            {"id": "zero",  "label": "Cero (0.0)"},
        ]

    elif ft == "BooleanField":
        generators += [
            {"id": "true",  "label": "True para todos"},
            {"id": "false", "label": "False para todos"},
        ]

    elif ft == "EmailField":
        if unique:
            generators.append({"id": "auto_email", "label": "Auto email  (nombre.apellido@empresa.com)"})
        generators.append({"id": "fixed", "label": "Email fijo para todos"})

    elif ft in ("DateField", "DateTimeField"):
        generators += [
            {"id": "today", "label": "Fecha de hoy"},
            {"id": "fixed", "label": "Fecha fija para todos"},
        ]

    if "password" in name_lower:
        generators = [
            {"id": "auto_unusable", "label": "Contraseña inutilizable  (set_unusable_password)"},
            {"id": "fixed_hash",    "label": "Contraseña fija (hasheada)"},
        ]

    return {
        "name":         field.name,
        "verbose":      str(getattr(field, "verbose_name", field.name)),
        "field_type":   ft,
        "max_length":   max_len,
        "unique":       unique,
        "has_default":  field.has_default(),
        "default":      (field.default if field.has_default() and not callable(field.default) else None),
        "generators":   generators,
        "source_hints": _source_hints(field),
    }


def _analyze(df: pd.DataFrame, model_class):
    """
    Returns (column_mapping_info, unmapped_columns, required_fields,
             mapped_count, missing_required).
    """
    norm_to_field    = {}
    all_model_fields = {}
    required_fields  = []

    for field in model_class._meta.get_fields():
        if not isinstance(field, Field) or field.auto_created:
            continue
        norm = FileProcessorService.normalize_name(field.name)
        norm_to_field[norm]       = field.name
        all_model_fields[field.name] = field
        if (not field.null
                and not getattr(field, "blank", True)
                and not field.has_default()
                and field.get_internal_type() not in ("AutoField", "BigAutoField")):
            required_fields.append(_field_meta(field))

    column_mapping_info = []
    unmapped            = []
    col_dtypes          = df.dtypes
    covered_fields      = set()

    for i, col in enumerate(df.columns):
        norm_col  = FileProcessorService.normalize_name(str(col))
        mapped_to = norm_to_field.get(norm_col)
        matched   = mapped_to is not None
        if matched:
            covered_fields.add(mapped_to)
        column_mapping_info.append({
            "column":    str(col),
            "dtype":     str(col_dtypes.iloc[i]),
            "matched":   matched,
            "mapped_to": mapped_to,
        })
        if not matched:
            unmapped.append(str(col))

    missing_required = [f for f in required_fields if f["name"] not in covered_fields]
    mapped_count     = sum(1 for c in column_mapping_info if c["matched"])
    return column_mapping_info, unmapped, required_fields, mapped_count, missing_required


_DEFAULT_PAGE_SIZE = 50
_MAX_PAGE_SIZE     = 500


def _rows_page(df: pd.DataFrame, page: int, page_size: int) -> tuple:
    """
    Returns (rows_list, pagination_dict).
    rows_list  : list of lists — JSON-safe cell values for the requested page.
    pagination : dict with total_rows, page, page_size, total_pages, start, end.
    """
    page_size   = max(1, min(page_size, _MAX_PAGE_SIZE))
    total_rows  = len(df)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    page        = max(1, min(page, total_pages))
    start       = (page - 1) * page_size          # 0-indexed
    end         = min(start + page_size, total_rows)

    rows = []
    for _, row in df.iloc[start:end].iterrows():
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

    pagination = {
        "total_rows":  total_rows,
        "page":        page,
        "page_size":   page_size,
        "total_pages": total_pages,
        "start":       start + 1,    # 1-indexed for display
        "end":         end,
    }
    return rows, pagination


def _preview_json(df: pd.DataFrame, cache_key: str, model_class,
                  excel_info: dict = None, filename: str = "",
                  page: int = 1, page_size: int = _DEFAULT_PAGE_SIZE) -> dict:
    col_mapping, unmapped, req_fields, mapped_count, missing_req = _analyze(df, model_class)

    # ── Column headers with null stats ────────────────────────────────────────
    headers    = []
    total      = max(len(df), 1)
    col_dtypes = df.dtypes
    for i, col in enumerate(df.columns):
        dtype_str = str(col_dtypes.iloc[i])
        nc = int(df.iloc[:, i].isna().sum())
        headers.append({
            "name":            str(col),
            "dtype":           dtype_str,
            "type":            dtype_str,
            "missing_count":   nc,
            "missing_percent": round(nc / total * 100, 1),
        })

    # ── Paginated rows ────────────────────────────────────────────────────────
    rows, pagination = _rows_page(df, page, page_size)

    return {
        "success":          True,
        "cache_key":        cache_key,
        "model":            f"{model_class._meta.app_label}.{model_class.__name__}" if model_class else None,
        "model_verbose":    str(model_class._meta.verbose_name_plural) if model_class else "",
        "stats": {
            "rows":           len(df),
            "columns":        len(df.columns),
            "mapped_count":   mapped_count,
            "required_count": len(req_fields),
        },
        "column_mapping":   col_mapping,
        "table":            {"headers": headers, "rows": rows},
        "pagination":       pagination,
        "excel_info":       excel_info,
        "required_fields":  req_fields,
        "missing_required": missing_req,
        "unmapped_columns": unmapped,
        "filename":         filename,
    }


# ── Model resolver ────────────────────────────────────────────────────────────

def _resolve_model(model_path: str):
    """Returns (model_class, error_response)."""
    try:
        app_label, model_name = model_path.rsplit(".", 1)
        return apps.get_model(app_label, model_name), None
    except (ValueError, LookupError) as exc:
        return None, JsonResponse({"success": False, "error": f"Modelo inválido: {exc}"}, status=400)
