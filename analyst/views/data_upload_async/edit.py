# analyst/views/data_upload_async/edit.py
"""
In-place DataFrame edit operations.

All views delegate to _edit(request, operation) which:
  1. Reads the DF from cache
  2. Calls operation(df, body) → (df, error | None)
  3. Writes the modified DF back to cache
  4. Returns _preview_json(...)
"""

import json
import logging

import pandas as pd

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ._core import (
    _cache_load, _cache_store, _preview_json, _resolve_model,
    _DEFAULT_PAGE_SIZE, _MAX_PAGE_SIZE,
)

logger = logging.getLogger(__name__)


# ── Generic edit wrapper ──────────────────────────────────────────────────────

def _edit(request, operation):
    """
    Shared logic for all in-place DataFrame edit operations.
    operation(df, body) → (df, error_string | None)
    """
    try:
        body       = json.loads(request.body)
        cache_key  = body.get("cache_key", "")
        model_path = body.get("model", "")
        page       = int(body.get("page", 1))
        page_size  = max(1, min(int(body.get("page_size", _DEFAULT_PAGE_SIZE)), _MAX_PAGE_SIZE))

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse(
                {"success": False, "error": "Sesión expirada o inválida. Sube el archivo nuevamente."},
                status=404,
            )

        model_path        = model_path or meta.get("model", "")
        model_class, err  = _resolve_model(model_path)
        if err:
            return err

        df, error = operation(df, body)
        if error:
            return JsonResponse({"success": False, "error": error}, status=400)

        _cache_store(cache_key, df, meta)
        return JsonResponse(
            _preview_json(df, cache_key, model_class, meta.get("excel_info"), meta.get("filename", ""),
                          page=page, page_size=page_size)
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido en el body."}, status=400)
    except Exception as exc:
        logger.error("Edit operation error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


# ── Edit views ────────────────────────────────────────────────────────────────

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
        col     = body.get("column", "")
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
        subset = body.get("subset") or None
        keep   = body.get("keep", "first")
        if subset:
            missing = [c for c in subset if c not in df.columns]
            if missing:
                return df, f"Columnas no encontradas: {missing}"
        before   = len(df)
        keep_val = False if keep == "none" else keep
        df = df.drop_duplicates(subset=subset, keep=keep_val).reset_index(drop=True)
        if before - len(df) == 0:
            return df, "No se encontraron filas duplicadas."
        return df, None
    return _edit(request, op)


@login_required
@require_POST
def sort_data_async(request):
    """Sorts the DataFrame by one or more columns."""
    def op(df, body):
        columns   = body.get("columns", [])
        ascending = body.get("ascending", True)
        if not columns:
            return df, "Selecciona al menos una columna para ordenar."
        missing = [c for c in columns if c not in df.columns]
        if missing:
            return df, f"Columnas no encontradas: {missing}"
        asc_list = [ascending] * len(columns) if isinstance(ascending, bool) else ascending[:len(columns)]
        return df.sort_values(by=columns, ascending=asc_list).reset_index(drop=True), None
    return _edit(request, op)


@login_required
@require_POST
def convert_dtype_async(request):
    """Converts a column's data type (int, float, str, bool)."""
    ALLOWED = {
        "int": "Int64", "float": "float64", "str": "object", "bool": "bool",
        "int64": "Int64", "float64": "float64", "object": "object",
    }

    def op(df, body):
        col    = body.get("column", "")
        dtype  = body.get("dtype", "")
        errors = body.get("errors", "coerce")
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
    """Applies text normalization to a string column."""
    import unicodedata

    def op(df, body):
        col      = body.get("column", "")
        ops_list = body.get("ops", [])
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
