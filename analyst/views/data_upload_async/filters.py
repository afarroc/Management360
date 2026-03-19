# analyst/views/data_upload_async/filters.py
"""
Filter-based read/write operations on the working DataFrame.

  _build_mask             — shared boolean mask builder
  filter_rows_count_async — count without modifying
  filter_rows_delete_async— delete matched rows
  filter_rows_replace_async — replace values in matched rows
  filter_unique_values_async — value-counts for a column
"""

import re
import json
import logging

import pandas as pd

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ._core import _cache_load
from .edit import _edit

logger = logging.getLogger(__name__)


# ── Mask builder ──────────────────────────────────────────────────────────────

def _build_mask(df: pd.DataFrame, column: str, operator: str,
                value: str, case_sensitive: bool = False):
    """
    Returns a boolean Series mask for rows matching the filter.
    Operators: eq, neq, contains, not_contains, starts_with, ends_with,
               gt, gte, lt, lte, is_null, is_not_null, regex
    """
    if column not in df.columns:
        raise ValueError(f"Columna no encontrada: {column}")

    s = df[column]

    if operator == "is_null":
        return s.isna()
    if operator == "is_not_null":
        return s.notna()

    if operator in {"gt", "gte", "lt", "lte"}:
        try:
            num_val = float(value)
            s_num   = pd.to_numeric(s, errors="coerce")
            if operator == "gt":  return s_num >  num_val
            if operator == "gte": return s_num >= num_val
            if operator == "lt":  return s_num <  num_val
            if operator == "lte": return s_num <= num_val
        except (ValueError, TypeError) as exc:
            raise ValueError(f"El valor '{value}' no es numérico.") from exc

    str_s = s.astype(str)
    if not case_sensitive:
        str_s = str_s.str.lower()
        cmp   = value.lower()
    else:
        cmp = value

    if operator == "eq":           return str_s == cmp
    if operator == "neq":          return str_s != cmp
    if operator == "contains":     return str_s.str.contains(cmp, regex=False, na=False)
    if operator == "not_contains": return ~str_s.str.contains(cmp, regex=False, na=False)
    if operator == "starts_with":  return str_s.str.startswith(cmp, na=False)
    if operator == "ends_with":    return str_s.str.endswith(cmp, na=False)
    if operator == "regex":
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            return str_s.str.contains(value, regex=True, flags=flags, na=False)
        except re.error as exc:
            raise ValueError(f"Expresión regular inválida: {exc}") from exc

    raise ValueError(f"Operador desconocido: {operator}")


# ── Views ─────────────────────────────────────────────────────────────────────

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

        df, _ = _cache_load(cache_key)
        if df is None:
            return JsonResponse({"success": False, "error": "Sesión expirada."}, status=404)

        try:
            mask = _build_mask(df, column, operator, value, case_sensitive)
        except ValueError as exc:
            return JsonResponse({"success": False, "error": str(exc)}, status=400)

        matched_df = df[mask]
        count      = int(mask.sum())
        total      = len(df)
        percent    = round(count / total * 100, 2) if total else 0

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
            "success": True,
            "count":   count,
            "total":   total,
            "percent": percent,
            "columns": [str(c) for c in df.columns],
            "sample":  sample_rows,
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("filter_rows_count_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_POST
def filter_rows_delete_async(request):
    """Deletes rows matching the filter and returns updated preview."""
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
        logger.info("filter_rows_delete: removed %d rows via %s %s '%s'",
                    removed, column, operator, value)
        return df[~mask].reset_index(drop=True), None
    return _edit(request, op)


@login_required
@require_POST
def filter_rows_replace_async(request):
    """
    Replaces a substring (or full value) in a target column,
    optionally scoped to rows matching a filter.
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

        col_series = df.loc[mask, target_column].astype(str)
        import re as _re
        flags = 0 if case_sensitive else _re.IGNORECASE

        if use_regex:
            try:
                _re.compile(find_value, flags)
            except _re.error as exc:
                return df, f"Expresión regular inválida: {exc}"
            replaced = col_series.str.replace(find_value, replace_with, regex=True, flags=flags)
        else:
            if not case_sensitive:
                pattern  = _re.escape(find_value)
                replaced = col_series.str.replace(pattern, replace_with, regex=True, flags=flags)
            else:
                replaced = col_series.str.replace(find_value, replace_with, regex=False)

        df.loc[mask, target_column] = replaced
        changed = int((df.loc[mask, target_column] != col_series).sum())
        logger.info("filter_rows_replace: '%s'→'%s' in '%s', %d/%d rows affected",
                    find_value, replace_with, target_column, changed, matched_count)
        if changed == 0:
            return df, f"No se encontró '{find_value}' en las {matched_count:,} filas filtradas."
        return df, None
    return _edit(request, op)


@login_required
@require_POST
def filter_unique_values_async(request):
    """
    Returns unique values for a column with counts and percentages.
    Caps at 500 values (sorted by frequency desc).

    POST JSON: { cache_key, column, max_values? }
    """
    MAX = 500

    try:
        body      = json.loads(request.body)
        cache_key = body.get("cache_key", "")
        column    = body.get("column", "")
        max_vals  = min(int(body.get("max_values", MAX)), MAX)

        df, _ = _cache_load(cache_key)
        if df is None:
            return JsonResponse({"success": False, "error": "Sesión expirada."}, status=404)
        if column not in df.columns:
            return JsonResponse({"success": False, "error": f"Columna no encontrada: '{column}'"}, status=400)

        s            = df[column]
        total_rows   = len(s)
        total_unique = int(s.nunique(dropna=False))

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
