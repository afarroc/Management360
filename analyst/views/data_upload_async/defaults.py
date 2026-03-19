# analyst/views/data_upload_async/defaults.py
"""
Default-value generators for required model fields.

Public views:
  apply_defaults_async       — applies strategy dicts (fixed/from_column/template/sequence/…)
  apply_field_defaults_async — newer strategy set (auto_username/derived_email/hashed_password/…)

Internal helpers (called by upload.confirm_upload_async):
  _apply_field_defaults      — fills missing columns before bulk_create
  _apply_password_fields     — post-processes records for proper Django password hashing
"""

import json
import logging
import uuid as _uuid
import re as _re
from datetime import date as _date, datetime as _datetime

import pandas as pd

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ._core import _cache_load, _cache_store, _preview_json, _resolve_model

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# View: apply_defaults_async
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def apply_defaults_async(request):
    """
    Applies user-supplied default strategies to fill missing required fields
    in the working DataFrame, then returns a fresh preview.

    Strategies: fixed, from_column, template, sequence, slugify, uuid, today
    """

    def _slugify(s: str) -> str:
        import unicodedata
        s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
        s = s.lower().strip()
        s = _re.sub(r"[^\w\s-]", "", s)
        s = _re.sub(r"[\s_]+", "-", s)
        return s.strip("-")

    try:
        body       = json.loads(request.body)
        cache_key  = body.get("cache_key", "")
        model_path = body.get("model", "")
        defaults   = body.get("defaults", {})

        if not defaults:
            return JsonResponse({"success": False, "error": "No se enviaron defaults."}, status=400)

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse({"success": False, "error": "Sesión expirada. Sube el archivo nuevamente."}, status=404)

        model_path        = model_path or meta.get("model", "")
        model_class, err  = _resolve_model(model_path)
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
                    return JsonResponse({"success": False, "error": f"Columna fuente '{src}' no existe."}, status=400)
                field_names = [f.name for f in model_class._meta.get_fields()]
                is_unique = getattr(model_class._meta.get_field(field_name), "unique", False) \
                            if field_name in field_names else False
                if is_unique:
                    base = df[src].astype(str).str.strip()
                    seen: dict = {}
                    result = []
                    for v in base:
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
                tpl          = cfg.get("template", "")
                placeholders = _re.findall(r"\{(\w+)\}", tpl)
                missing_cols = [p for p in placeholders if p not in df.columns]
                if missing_cols:
                    return JsonResponse({"success": False, "error": f"Columnas no encontradas en template: {missing_cols}"}, status=400)
                result = []
                for _, row in df.iterrows():
                    val = tpl
                    for p in placeholders:
                        val = val.replace(f"{{{p}}}", str(row[p]).strip())
                    result.append(val)
                field_names = [f.name for f in model_class._meta.get_fields()]
                is_unique = getattr(model_class._meta.get_field(field_name), "unique", False) \
                            if field_name in field_names else False
                if is_unique:
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
                prefix = str(cfg.get("prefix", ""))
                start  = int(cfg.get("start", 1))
                pad    = int(cfg.get("pad", 0))
                df[field_name] = [
                    f"{prefix}{str(start + i).zfill(pad) if pad else start + i}"
                    for i in range(n)
                ]

            elif strategy == "slugify":
                src = cfg.get("source", "")
                if src not in df.columns:
                    return JsonResponse({"success": False, "error": f"Columna fuente '{src}' no existe."}, status=400)
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
                df[field_name] = _datetime.now().isoformat() if "DateTime" in ft else str(_date.today())

            else:
                return JsonResponse({"success": False, "error": f"Estrategia desconocida: '{strategy}'"}, status=400)

        _cache_store(cache_key, df, meta)
        return JsonResponse(
            _preview_json(df, cache_key, model_class, meta.get("excel_info"), meta.get("filename", ""))
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("apply_defaults_async error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# View: apply_field_defaults_async
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def apply_field_defaults_async(request):
    """
    Injects default/computed values for required fields missing from the DataFrame.

    Strategies: fixed, now, sequence, slugify, auto_username, derived_email,
                hashed_password, concat, copy_col
    """
    import unicodedata
    from django.utils import timezone

    def _slugify_str(s):
        s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
        return _re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

    def _make_unique(base_series, existing_set):
        result = []
        seen   = set(existing_set)
        counts = {}
        for val in base_series:
            if val not in seen:
                seen.add(val)
                result.append(val)
            else:
                counts[val] = counts.get(val, 0) + 1
                candidate   = f"{val}{counts[val]}"
                while candidate in seen:
                    counts[val] += 1
                    candidate   = f"{val}{counts[val]}"
                seen.add(candidate)
                result.append(candidate)
        return result

    try:
        body       = json.loads(request.body)
        cache_key  = body.get("cache_key", "")
        model_path = body.get("model", "")
        defaults   = body.get("defaults", [])

        df, meta = _cache_load(cache_key)
        if df is None:
            return JsonResponse({"success": False, "error": "Sesión expirada. Sube el archivo nuevamente."}, status=404)

        model_path        = model_path or meta.get("model", "")
        model_class, err  = _resolve_model(model_path)
        if err:
            return err

        df     = df.copy()
        errors = []

        for spec in defaults:
            field    = spec.get("field", "")
            strategy = spec.get("strategy", "fixed")
            if not field:
                continue

            try:
                if strategy == "fixed":
                    raw = spec.get("value", "")
                    try:
                        f  = model_class._meta.get_field(field)
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
                    start    = int(spec.get("start", 1))
                    df[field] = range(start, start + len(df))

                elif strategy == "slugify":
                    src = spec.get("source_col", "")
                    if src and src in df.columns:
                        df[field] = df[src].astype(str).apply(_slugify_str)
                    else:
                        errors.append(f"slugify: columna fuente '{src}' no encontrada.")

                elif strategy == "auto_username":
                    src_cols = spec.get("source_cols", [])
                    if len(src_cols) >= 2 and src_cols[0] in df.columns and src_cols[1] in df.columns:
                        base = (
                            df[src_cols[0]].astype(str).str.strip().str.lower()
                              .str.replace(r"[^a-z0-9]", "", regex=True).str[:3]
                            + df[src_cols[1]].astype(str).str.strip().str.lower()
                              .str.replace(r"[^a-z0-9]", "", regex=True)
                        )
                    elif len(src_cols) >= 1 and src_cols[0] in df.columns:
                        base = (df[src_cols[0]].astype(str).str.strip().str.lower()
                                .str.replace(r"[^a-z0-9]", "", regex=True))
                    else:
                        base = pd.Series([f"user{i}" for i in range(len(df))])
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
                            df[src_cols[0]].astype(str).str.strip().str.lower()
                              .str.replace(r"[^a-z0-9]", "", regex=True).str[:3]
                            + "."
                            + df[src_cols[1]].astype(str).str.strip().str.lower()
                              .str.replace(r"[^a-z0-9]", "", regex=True)
                        )
                    elif len(src_cols) >= 1 and src_cols[0] in df.columns:
                        local = (df[src_cols[0]].astype(str).str.strip().str.lower()
                                 .str.replace(r"[^a-z0-9]", "", regex=True))
                    else:
                        local = pd.Series([f"user{i}" for i in range(len(df))])
                    try:
                        existing_emails = set(model_class.objects.values_list(field, flat=True))
                    except Exception:
                        existing_emails = set()
                    emails   = [f"{l}@{domain}" for l in local.tolist()]
                    df[field] = _make_unique(emails, existing_emails)

                elif strategy == "hashed_password":
                    from django.contrib.auth.hashers import make_password
                    df[field] = make_password(spec.get("value", "changeme123"))

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


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers  (called by confirm_upload_async)
# ═══════════════════════════════════════════════════════════════════════════════

def _apply_field_defaults(df: pd.DataFrame, model_class, field_defaults: dict) -> pd.DataFrame:
    """
    Generates synthetic column values for required fields missing from df.
    Called from confirm_upload_async before bulk_create.
    """
    df = df.copy()
    n  = len(df)

    def _slug(s: str) -> str:
        s = str(s).lower().strip()
        s = _re.sub(r"[^a-z0-9\s]", "", s)
        return _re.sub(r"\s+", ".", s).strip(".")

    def _initials(first: str, last: str) -> str:
        return (str(first)[:1].upper() if first else "U") + (str(last)[:1].upper() if last else "X")

    for field_name, cfg in field_defaults.items():
        if field_name in df.columns:
            continue

        strategy  = cfg.get("strategy", "fixed")
        fix_val   = cfg.get("value", "")
        col_first = cfg.get("col_first", "")
        col_last  = cfg.get("col_last", "")
        domain    = cfg.get("domain", "empresa.com")
        prefix    = cfg.get("prefix") or fix_val or "USER"

        def _col(name):
            return df[name] if name and name in df.columns else pd.Series([""] * n)

        if strategy == "auto_slug":
            first  = _col(col_first)
            last   = _col(col_last)
            bases  = [_slug(f"{r[0]} {r[1]}") or "user" for r in zip(first, last)]
            seen   = {}
            result = []
            for b in bases:
                if b not in seen:
                    seen[b] = 0; result.append(b)
                else:
                    seen[b] += 1; result.append(f"{b}.{seen[b]}")
            df[field_name] = result

        elif strategy == "seq_prefix":
            df[field_name] = [f"{prefix}{i+1:04d}" for i in range(n)]

        elif strategy == "uuid_short":
            df[field_name] = [str(_uuid.uuid4())[:8] for _ in range(n)]

        elif strategy == "auto_initials":
            first  = _col(col_first)
            last   = _col(col_last)
            counts = {}
            result = []
            for f, l in zip(first, last):
                base = _initials(f, l)
                counts[base] = counts.get(base, 0) + 1
                result.append(f"{base}{counts[base]:03d}")
            df[field_name] = result

        elif strategy == "auto_email":
            first  = _col(col_first)
            last   = _col(col_last)
            bases  = [f"{_slug(f)}.{_slug(l)}@{domain}" if _slug(f) or _slug(l)
                      else f"user{i}@{domain}" for i, (f, l) in enumerate(zip(first, last))]
            seen   = {}
            result = []
            for b in bases:
                local, dom = b.rsplit("@", 1)
                if local not in seen:
                    seen[local] = 0; result.append(b)
                else:
                    seen[local] += 1; result.append(f"{local}.{seen[local]}@{dom}")
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
