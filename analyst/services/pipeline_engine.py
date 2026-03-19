# analyst/services/pipeline_engine.py
"""
Motor de ejecucion de Pipelines.

Itera los pasos en orden, aplicando cada transformacion al DataFrame
usando la misma logica que data_upload_async/edit.py.

Uso:
    engine = PipelineEngine(pipeline, input_dataset, user)
    result_ds, error = engine.run()
"""

import time
import logging
import pickle
import base64
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from django.core.cache import cache
from django.utils import timezone as dj_tz

from analyst.models import Pipeline, PipelineRun, StoredDataset
from analyst.utils.clipboard import DataFrameClipboard

logger = logging.getLogger(__name__)

# ─── Serialization (same as _core.py) ────────────────────────────────────────

def _serialize(df: pd.DataFrame) -> str:
    return base64.b64encode(pickle.dumps(df)).decode()

def _deserialize(s: str) -> pd.DataFrame:
    return pickle.loads(base64.b64decode(s.encode()))

def _load_dataset(ds: StoredDataset) -> pd.DataFrame | None:
    raw = cache.get(ds.cache_key)
    if raw:
        try:
            return _deserialize(raw['data'])
        except Exception:
            pass
    if ds.data_blob:
        try:
            return _deserialize(ds.data_blob)
        except Exception:
            pass
    return None

def _save_dataset(df: pd.DataFrame, name: str, user, source_ds: StoredDataset) -> StoredDataset:
    """Persist transformed DataFrame as a new StoredDataset."""
    import uuid as _uuid
    cache_key = StoredDataset.make_cache_key(str(_uuid.uuid4()))
    blob      = _serialize(df)
    dtype_map = {str(c): str(df.dtypes[c]) for c in df.columns}

    ds = StoredDataset.objects.create(
        name        = name,
        cache_key   = cache_key,
        rows        = len(df),
        col_count   = len(df.columns),
        columns     = list(df.columns.astype(str)),
        dtype_map   = dtype_map,
        source_file = f"pipeline:{source_ds.id}",
        data_blob   = blob,
        created_by  = user,
    )
    cache.set(cache_key, {'data': blob, 'meta': {}}, timeout=None)
    return ds


# ─── Step executors ───────────────────────────────────────────────────────────

def _step_delete_columns(df: pd.DataFrame, params: dict):
    cols = params.get('columns', [])
    missing = [c for c in cols if c not in df.columns]
    if missing:
        return None, f"Columnas no encontradas: {missing}"
    return df.drop(columns=cols), None


def _step_rename_column(df: pd.DataFrame, params: dict):
    old, new = params.get('old_name'), params.get('new_name', '').strip()
    if not old or not new:
        return None, "Se requieren old_name y new_name."
    if old not in df.columns:
        return None, f"Columna '{old}' no existe."
    if new in df.columns:
        return None, f"Columna '{new}' ya existe."
    return df.rename(columns={old: new}), None


def _step_replace_values(df: pd.DataFrame, params: dict):
    col = params.get('column')
    old_val = params.get('old_value', '')
    new_val = params.get('new_value', '')
    if not col or col not in df.columns:
        return None, f"Columna '{col}' no encontrada."
    mask = df[col].isna() if old_val == '' else df[col].astype(str) == str(old_val)
    df = df.copy()
    df.loc[mask, col] = new_val if new_val != '' else None
    return df, None


def _step_fill_na(df: pd.DataFrame, params: dict):
    col      = params.get('column')
    strategy = params.get('strategy', 'value')
    value    = params.get('value', '')
    if not col or col not in df.columns:
        return None, f"Columna '{col}' no encontrada."
    df = df.copy()
    if strategy == 'value':
        df[col] = df[col].fillna(value)
    elif strategy == 'mean':
        df[col] = df[col].fillna(pd.to_numeric(df[col], errors='coerce').mean())
    elif strategy == 'median':
        df[col] = df[col].fillna(pd.to_numeric(df[col], errors='coerce').median())
    elif strategy == 'mode':
        mode = df[col].mode()
        df[col] = df[col].fillna(mode[0] if not mode.empty else value)
    elif strategy == 'ffill':
        df[col] = df[col].ffill()
    elif strategy == 'bfill':
        df[col] = df[col].bfill()
    else:
        return None, f"Estrategia desconocida: '{strategy}'."
    return df, None


def _step_convert_date(df: pd.DataFrame, params: dict):
    col    = params.get('column')
    fmt    = params.get('format', 'infer')
    if not col or col not in df.columns:
        return None, f"Columna '{col}' no encontrada."
    df = df.copy()
    try:
        if fmt == 'infer':
            df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors='coerce')
        else:
            df[col] = pd.to_datetime(df[col], format=fmt, errors='coerce')
    except Exception as e:
        return None, f"Error convirtiendo fecha: {e}"
    return df, None


def _step_convert_dtype(df: pd.DataFrame, params: dict):
    col    = params.get('column')
    target = params.get('target_type', 'str')
    coerce = params.get('coerce', True)
    if not col or col not in df.columns:
        return None, f"Columna '{col}' no encontrada."
    df = df.copy()
    errors = 'coerce' if coerce else 'raise'
    try:
        if target == 'int':
            df[col] = pd.to_numeric(df[col], errors=errors).astype('Int64')
        elif target == 'float':
            df[col] = pd.to_numeric(df[col], errors=errors)
        elif target == 'str':
            df[col] = df[col].astype(str)
        elif target == 'bool':
            df[col] = df[col].map({'true': True, 'false': False, True: True, False: False,
                                    '1': True, '0': False, 1: True, 0: False})
        else:
            return None, f"Tipo desconocido: '{target}'."
    except Exception as e:
        return None, f"Error convirtiendo tipo: {e}"
    return df, None


def _step_normalize_text(df: pd.DataFrame, params: dict):
    col = params.get('column')
    ops = params.get('ops', ['lower', 'strip'])
    if not col or col not in df.columns:
        return None, f"Columna '{col}' no encontrada."
    df = df.copy()
    s = df[col].astype(str)
    if 'lower'          in ops: s = s.str.lower()
    if 'upper'          in ops: s = s.str.upper()
    if 'strip'          in ops: s = s.str.strip()
    if 'remove_accents' in ops:
        import unicodedata
        s = s.apply(lambda x: unicodedata.normalize('NFD', x)
                    .encode('ascii', 'ignore').decode())
    if 'remove_spaces'  in ops: s = s.str.replace(r'\s+', ' ', regex=True).str.strip()
    if 'remove_special' in ops: s = s.str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
    df[col] = s
    return df, None


def _step_drop_duplicates(df: pd.DataFrame, params: dict):
    cols   = params.get('columns') or None
    keep   = params.get('keep', 'first')
    before = len(df)
    df = df.drop_duplicates(subset=cols, keep=keep).reset_index(drop=True)
    logger.info("drop_duplicates: %d → %d rows", before, len(df))
    return df, None


def _step_sort_data(df: pd.DataFrame, params: dict):
    col = params.get('column')
    asc = params.get('ascending', True)
    if not col or col not in df.columns:
        return None, f"Columna '{col}' no encontrada."
    return df.sort_values(col, ascending=asc).reset_index(drop=True), None


def _apply_filter_mask(df: pd.DataFrame, col: str, lookup: str,
                        value: str, negate: bool) -> pd.Series:
    s = df[col]
    if lookup == 'exact':        mask = s.astype(str) == str(value)
    elif lookup == 'contains':   mask = s.astype(str).str.contains(str(value), na=False)
    elif lookup == 'startswith': mask = s.astype(str).str.startswith(str(value))
    elif lookup == 'endswith':   mask = s.astype(str).str.endswith(str(value))
    elif lookup == 'gt':         mask = pd.to_numeric(s, errors='coerce') > float(value)
    elif lookup == 'gte':        mask = pd.to_numeric(s, errors='coerce') >= float(value)
    elif lookup == 'lt':         mask = pd.to_numeric(s, errors='coerce') < float(value)
    elif lookup == 'lte':        mask = pd.to_numeric(s, errors='coerce') <= float(value)
    elif lookup == 'isnull':     mask = s.isna()
    elif lookup == 'notnull':    mask = s.notna()
    else: mask = pd.Series([False] * len(df), index=df.index)
    return ~mask if negate else mask


def _step_filter_delete(df: pd.DataFrame, params: dict):
    col    = params.get('column')
    lookup = params.get('lookup', 'exact')
    value  = params.get('value', '')
    negate = params.get('negate', False)
    if not col or col not in df.columns:
        return None, f"Columna '{col}' no encontrada."
    mask   = _apply_filter_mask(df, col, lookup, value, negate)
    before = len(df)
    df     = df[~mask].reset_index(drop=True)
    logger.info("filter_delete: removed %d rows", before - len(df))
    return df, None


def _step_filter_replace(df: pd.DataFrame, params: dict):
    col         = params.get('column')
    lookup      = params.get('lookup', 'exact')
    value       = params.get('value', '')
    negate      = params.get('negate', False)
    replace_col = params.get('replace_col', col)
    replace_val = params.get('replace_value', '')
    if not col or col not in df.columns:
        return None, f"Columna '{col}' no encontrada."
    if replace_col not in df.columns:
        return None, f"Columna de reemplazo '{replace_col}' no encontrada."
    mask = _apply_filter_mask(df, col, lookup, value, negate)
    df   = df.copy()
    df.loc[mask, replace_col] = replace_val if replace_val != '' else None
    return df, None


# ─── Step dispatch table ──────────────────────────────────────────────────────

_STEP_EXECUTORS = {
    'delete_columns':  _step_delete_columns,
    'rename_column':   _step_rename_column,
    'replace_values':  _step_replace_values,
    'fill_na':         _step_fill_na,
    'convert_date':    _step_convert_date,
    'convert_dtype':   _step_convert_dtype,
    'normalize_text':  _step_normalize_text,
    'drop_duplicates': _step_drop_duplicates,
    'sort_data':       _step_sort_data,
    'filter_delete':   _step_filter_delete,
    'filter_replace':  _step_filter_replace,
}


# ─── Engine ───────────────────────────────────────────────────────────────────

class PipelineEngine:
    """Execute a Pipeline against a StoredDataset."""

    def __init__(self, pipeline: Pipeline, input_dataset: StoredDataset, user):
        self.pipeline       = pipeline
        self.input_dataset  = input_dataset
        self.user           = user

    def run(self, output_name: str = None, runtime_params: dict = None) -> tuple:
        """
        Execute all steps in order.

        Returns: (result_StoredDataset, error_string | None)
        """
        from analyst.models import PipelineRun

        run = PipelineRun.objects.create(
            pipeline       = self.pipeline,
            input_dataset  = self.input_dataset,
            status         = 'running',
            triggered_by   = self.user,
            started_at     = dj_tz.now(),
            runtime_params = runtime_params or {},
        )

        t0 = time.time()
        df = _load_dataset(self.input_dataset)
        if df is None:
            run.status    = 'error'
            run.error_msg = f"Dataset '{self.input_dataset.name}' no disponible."
            run.finished_at = dj_tz.now()
            run.save()
            return None, run.error_msg

        steps = sorted(self.pipeline.steps, key=lambda s: s.get('order', 0))

        for i, step in enumerate(steps):
            step_type = step.get('type', '')
            params    = {**step.get('params', {}), **(runtime_params or {}).get(step_type, {})}
            executor  = _STEP_EXECUTORS.get(step_type)

            if executor is None:
                run.status    = 'error'
                run.error_msg = f"Paso {i+1}: tipo desconocido '{step_type}'."
                run.steps_completed = i
                run.finished_at     = dj_tz.now()
                run.duration_s      = time.time() - t0
                run.save()
                return None, run.error_msg

            try:
                result, err = executor(df, params)
            except Exception as exc:
                err = str(exc)
                result = None

            if err:
                label = step.get('label') or step_type
                run.status    = 'error'
                run.error_msg = f"Paso {i+1} '{label}': {err}"
                run.steps_completed = i
                run.finished_at     = dj_tz.now()
                run.duration_s      = time.time() - t0
                run.save()
                return None, run.error_msg

            df = result
            logger.info("Pipeline '%s' step %d/%d (%s) OK — %d rows",
                        self.pipeline.name, i+1, len(steps), step_type, len(df))

        # All steps done — persist result
        name = output_name or f"{self.input_dataset.name} — {self.pipeline.name}"
        result_ds = _save_dataset(df, name, self.user, self.input_dataset)

        run.status          = 'done'
        run.result_dataset  = result_ds
        run.steps_completed = len(steps)
        run.finished_at     = dj_tz.now()
        run.duration_s      = time.time() - t0
        run.save()

        logger.info("Pipeline '%s' completado: %d pasos, %d rows, %.2fs",
                    self.pipeline.name, len(steps), len(df), run.duration_s)
        return result_ds, None
