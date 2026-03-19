# analyst/views/data_upload_async/__init__.py
"""
Package: analyst.views.data_upload_async

Converts the former single-file module into a structured package.
All public names are re-exported here so urls.py needs zero changes:

    from analyst.views import data_upload_async
    data_upload_async.preview_async        # still works

Sub-modules:
  _core      — cache helpers, field analysis, preview builder, model resolver
  upload     — preview_async, confirm_upload_async, reanalyze_async
  edit       — _edit + 9 in-place DataFrame edit views
  filters    — _build_mask + filter_rows_* + filter_unique_values_async
  clipboard  — save_clipboard_async, load_clip_as_preview
  dataset    — save_as_dataset
  defaults   — apply_defaults_async, apply_field_defaults_async
               + _apply_field_defaults, _apply_password_fields (internal)
"""

# ── Core helpers (available for import by other parts of the app) ─────────────
from ._core import (
    PREVIEW_TTL,
    _DEFAULT_PAGE_SIZE,
    _MAX_PAGE_SIZE,
    _serialize,
    _deserialize,
    _cache_store,
    _cache_load,
    _new_preview_key,
    _field_meta,
    _source_hints,
    _analyze,
    _rows_page,
    _preview_json,
    _resolve_model,
)

# ── Upload ────────────────────────────────────────────────────────────────────
from .upload import (
    preview_async,
    preview_page_async,
    confirm_upload_async,
    reanalyze_async,
)

# ── Edit ──────────────────────────────────────────────────────────────────────
from .edit import (
    _edit,
    delete_columns_async,
    replace_values_async,
    fill_na_async,
    convert_date_async,
    rename_column_async,
    drop_duplicates_async,
    sort_data_async,
    convert_dtype_async,
    normalize_text_async,
)

# ── Filters ───────────────────────────────────────────────────────────────────
from .filters import (
    _build_mask,
    filter_rows_count_async,
    filter_rows_delete_async,
    filter_rows_replace_async,
    filter_unique_values_async,
)

# ── Clipboard ─────────────────────────────────────────────────────────────────
from .clipboard import (
    save_clipboard_async,
    load_clip_as_preview,
)

# ── Dataset ───────────────────────────────────────────────────────────────────
from .dataset import (
    save_as_dataset,
)

# ── Defaults ──────────────────────────────────────────────────────────────────
from .defaults import (
    apply_defaults_async,
    apply_field_defaults_async,
    _apply_field_defaults,
    _apply_password_fields,
)

__all__ = [
    # core
    "PREVIEW_TTL",
    "_serialize", "_deserialize",
    "_cache_store", "_cache_load", "_new_preview_key",
    "_field_meta", "_source_hints", "_analyze",
    "_preview_json", "_resolve_model",
    # upload
    "preview_async", "confirm_upload_async", "reanalyze_async",
    # edit
    "_edit",
    "delete_columns_async", "replace_values_async", "fill_na_async",
    "convert_date_async", "rename_column_async", "drop_duplicates_async",
    "sort_data_async", "convert_dtype_async", "normalize_text_async",
    # filters
    "_build_mask",
    "filter_rows_count_async", "filter_rows_delete_async",
    "filter_rows_replace_async", "filter_unique_values_async",
    # clipboard
    "save_clipboard_async", "load_clip_as_preview",
    # dataset
    "save_as_dataset",
    # defaults
    "apply_defaults_async", "apply_field_defaults_async",
    "_apply_field_defaults", "_apply_password_fields",
]
