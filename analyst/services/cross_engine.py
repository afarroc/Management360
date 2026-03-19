# analyst/services/cross_engine.py
"""
Motor de cruce entre fuentes de datos.
Soporta: left_join, inner_join, outer_join, concat.
Fuentes: StoredDataset, AnalystBase, ETLSource, DataFrameClipboard.
"""

import logging
import re
import pickle
import base64

import pandas as pd
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Límite de filas para el resultado del cruce (no-superuser)
DEFAULT_MAX_ROWS = 200_000

# ─────────────────────────────────────────────────────────────────────────────
# Helpers de serialización
# ─────────────────────────────────────────────────────────────────────────────

def _serialize(df: pd.DataFrame) -> str:
    return base64.b64encode(pickle.dumps(df)).decode()


def _deserialize(blob: str) -> pd.DataFrame:
    return pickle.loads(base64.b64decode(blob.encode()))


# ─────────────────────────────────────────────────────────────────────────────
# Carga de fuentes
# ─────────────────────────────────────────────────────────────────────────────

def load_source(source_desc: dict, request=None, user=None) -> pd.DataFrame:
    """
    Carga un DataFrame desde cualquier tipo de fuente soportada.

    source_desc = {
        "type": "stored_dataset" | "analyst_base" | "etl_source" | "clip",
        "id":   "uuid o clip_key",
        "columns": []   # [] = todas; lista = subconjunto
    }

    Parámetros:
        request  — necesario para fuentes tipo 'clip' (usa la sesión)
        user     — necesario para verificar pertenencia de los objetos
    """
    src_type = source_desc.get('type', '').strip()
    src_id   = source_desc.get('id',   '').strip()
    columns  = source_desc.get('columns', [])

    if not src_type or not src_id:
        raise ValueError("source_desc requiere 'type' e 'id'.")

    df = _load_raw(src_type, src_id, request, user)

    # Selección de columnas
    if columns:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            logger.warning("load_source: columnas no encontradas y omitidas: %s", missing)
        available = [c for c in columns if c in df.columns]
        if available:
            df = df[available]

    return df.reset_index(drop=True)


def _load_raw(src_type: str, src_id: str, request, user) -> pd.DataFrame:
    if src_type == 'stored_dataset':
        return _load_stored_dataset(src_id, user)
    elif src_type == 'analyst_base':
        return _load_analyst_base(src_id, user)
    elif src_type == 'etl_source':
        return _load_etl_source(src_id, user)
    elif src_type == 'clip':
        return _load_clip(src_id, request)
    else:
        raise ValueError(f"Tipo de fuente desconocido: '{src_type}'. "
                         "Válidos: stored_dataset, analyst_base, etl_source, clip")


def _load_stored_dataset(ds_id: str, user) -> pd.DataFrame:
    from analyst.models import StoredDataset

    try:
        ds = StoredDataset.objects.get(id=ds_id, created_by=user)
    except StoredDataset.DoesNotExist:
        raise ValueError(f"StoredDataset '{ds_id}' no encontrado o sin acceso.")

    # Redis primero
    cached = cache.get(ds.cache_key)
    if cached:
        try:
            return _deserialize(cached['data'])
        except Exception as e:
            logger.warning("CrossEngine: error leyendo caché de dataset %s: %s", ds_id, e)

    # Fallback a data_blob
    if ds.data_blob:
        try:
            df = _deserialize(ds.data_blob)
            # Re-calentar Redis
            cache.set(ds.cache_key, {'data': ds.data_blob,
                                      'meta': {'stored_dataset_id': str(ds.id)}}, timeout=None)
            return df
        except Exception as e:
            raise ValueError(f"Error deserializando dataset '{ds.name}': {e}")

    raise ValueError(f"Dataset '{ds.name}' no tiene datos disponibles (sin caché ni data_blob).")


def _load_analyst_base(base_id: str, user) -> pd.DataFrame:
    from analyst.models import AnalystBase
    from analyst.services.base_validator import BaseValidator

    try:
        base = AnalystBase.objects.get(id=base_id, created_by=user)
    except AnalystBase.DoesNotExist:
        raise ValueError(f"AnalystBase '{base_id}' no encontrada o sin acceso.")

    df = BaseValidator.load_dataframe(base)
    if df is None:
        return pd.DataFrame(columns=[c['name'] for c in base.schema])
    return df


def _load_etl_source(source_id: str, user) -> pd.DataFrame:
    from analyst.models import ETLSource
    from analyst.views.etl_manager import _run_extraction

    try:
        src = ETLSource.objects.get(id=source_id, created_by=user)
    except ETLSource.DoesNotExist:
        raise ValueError(f"ETLSource '{source_id}' no encontrado o sin acceso.")

    df, err = _run_extraction(src, {}, user)
    if err:
        raise ValueError(f"Error extrayendo ETLSource '{src.name}': {err}")
    if df is None:
        raise ValueError(f"ETLSource '{src.name}' no devolvió datos.")
    return df


def _load_clip(clip_key: str, request) -> pd.DataFrame:
    if request is None:
        raise ValueError("Se requiere 'request' para cargar un clip del portapapeles.")
    from analyst.utils.clipboard import DataFrameClipboard
    df, _ = DataFrameClipboard.retrieve_df(request, clip_key)
    if df is None:
        raise ValueError(f"Clip '{clip_key}' no encontrado o expirado.")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Motor de cruce
# ─────────────────────────────────────────────────────────────────────────────

def execute_cross(config: dict, request=None, user=None) -> pd.DataFrame:
    """
    Ejecuta el cruce definido en `config` y devuelve el DataFrame resultante.

    config = {
      "operation":      "left_join" | "inner_join" | "outer_join" | "concat",
      "left":           { "type", "id", "alias", "columns" },
      "right":          { "type", "id", "alias", "columns" },
      "on":             [ {"left": "col_a", "right": "col_b"} ],
      "suffixes":       ["_izq", "_der"],
      "post_filters":   [ {"field", "lookup", "value", "negate"} ],
      "output_columns": []
    }
    """
    operation = config.get('operation', 'left_join')
    left_desc  = config.get('left',  {})
    right_desc = config.get('right', {})
    on_pairs   = config.get('on', [])
    suffixes   = config.get('suffixes', ['_izq', '_der'])
    post_filters  = config.get('post_filters', [])
    output_cols   = config.get('output_columns', [])

    # ── Cargar fuentes ────────────────────────────────────────────────────────
    logger.info("CrossEngine: cargando fuente izquierda %s/%s",
                left_desc.get('type'), left_desc.get('id'))
    df_left  = load_source(left_desc,  request=request, user=user)

    logger.info("CrossEngine: cargando fuente derecha %s/%s",
                right_desc.get('type'), right_desc.get('id'))
    df_right = load_source(right_desc, request=request, user=user)

    # ── Ejecutar operación ────────────────────────────────────────────────────
    if operation == 'concat':
        result = _do_concat(df_left, df_right, left_desc, right_desc)
    else:
        result = _do_merge(df_left, df_right, operation, on_pairs, suffixes,
                           left_desc, right_desc)

    # ── Post-filtros ──────────────────────────────────────────────────────────
    if post_filters:
        result = _apply_filters(result, post_filters)

    # ── Selección de columnas de salida ───────────────────────────────────────
    if output_cols:
        available = [c for c in output_cols if c in result.columns]
        if available:
            result = result[available]

    logger.info("CrossEngine: resultado %d filas × %d columnas",
                len(result), len(result.columns))

    return result.reset_index(drop=True)


def _do_merge(df_left: pd.DataFrame, df_right: pd.DataFrame,
              operation: str, on_pairs: list,
              suffixes: list, left_desc: dict, right_desc: dict) -> pd.DataFrame:
    """Realiza un merge (join) entre dos DataFrames."""

    how_map = {
        'left_join':  'left',
        'inner_join': 'inner',
        'outer_join': 'outer',
    }
    how = how_map.get(operation, 'left')

    if not on_pairs:
        raise ValueError("Se requiere al menos un par de columnas 'on' para el join.")

    # Validar columnas
    for pair in on_pairs:
        lcol = pair.get('left',  '')
        rcol = pair.get('right', '')
        if lcol not in df_left.columns:
            raise ValueError(f"Columna '{lcol}' no encontrada en la fuente izquierda. "
                             f"Columnas disponibles: {list(df_left.columns)[:10]}")
        if rcol not in df_right.columns:
            raise ValueError(f"Columna '{rcol}' no encontrada en la fuente derecha. "
                             f"Columnas disponibles: {list(df_right.columns)[:10]}")

    # Si son las mismas columnas en ambos lados, podemos usar `on=`
    same_keys = all(p['left'] == p['right'] for p in on_pairs)
    if same_keys:
        on_cols = [p['left'] for p in on_pairs]
        result = pd.merge(
            df_left, df_right,
            on=on_cols, how=how,
            suffixes=tuple(suffixes[:2]),
        )
    else:
        # Renombrar las claves del lado derecho para hacer el merge
        rename_map = {p['right']: p['left'] for p in on_pairs
                      if p['right'] != p['left']}
        df_right_renamed = df_right.rename(columns=rename_map)
        on_cols = [p['left'] for p in on_pairs]
        result = pd.merge(
            df_left, df_right_renamed,
            on=on_cols, how=how,
            suffixes=tuple(suffixes[:2]),
        )

    return result


def _do_concat(df_left: pd.DataFrame, df_right: pd.DataFrame,
               left_desc: dict, right_desc: dict) -> pd.DataFrame:
    """Concatena (apila) dos DataFrames. Agrega columna _source si los aliases difieren."""

    left_alias  = left_desc.get('alias',  'izquierda')
    right_alias = right_desc.get('alias', 'derecha')

    if left_alias != right_alias:
        df_left  = df_left.copy();  df_left['_source']  = left_alias
        df_right = df_right.copy(); df_right['_source'] = right_alias

    result = pd.concat([df_left, df_right], ignore_index=True, sort=False)
    return result


def _apply_filters(df: pd.DataFrame, filters: list) -> pd.DataFrame:
    """
    Aplica filtros post-merge al DataFrame resultado.
    Misma interfaz que los filtros de ETLSource.
    """
    _SAFE_LOOKUPS = {
        'exact', 'iexact', 'contains', 'icontains',
        'startswith', 'istartswith', 'endswith', 'iendswith',
        'gt', 'gte', 'lt', 'lte', 'isnull',
    }

    for f in filters:
        field  = str(f.get('field',  '')).strip()
        lookup = str(f.get('lookup', 'exact')).strip()
        value  = f.get('value', '')
        negate = bool(f.get('negate', False))

        if field not in df.columns or lookup not in _SAFE_LOOKUPS:
            logger.warning("CrossEngine filter ignorado: %s %s", field, lookup)
            continue

        try:
            col = df[field].astype(str)
            if   lookup == 'exact':       mask = col == str(value)
            elif lookup == 'iexact':      mask = col.str.lower() == str(value).lower()
            elif lookup == 'contains':    mask = col.str.contains(str(value), na=False)
            elif lookup == 'icontains':   mask = col.str.contains(str(value), case=False, na=False)
            elif lookup == 'startswith':  mask = col.str.startswith(str(value))
            elif lookup == 'istartswith': mask = col.str.lower().str.startswith(str(value).lower())
            elif lookup == 'endswith':    mask = col.str.endswith(str(value))
            elif lookup == 'iendswith':   mask = col.str.lower().str.endswith(str(value).lower())
            elif lookup == 'isnull':      mask = df[field].isna()
            elif lookup == 'gt':          mask = pd.to_numeric(df[field], errors='coerce') > float(value)
            elif lookup == 'gte':         mask = pd.to_numeric(df[field], errors='coerce') >= float(value)
            elif lookup == 'lt':          mask = pd.to_numeric(df[field], errors='coerce') < float(value)
            elif lookup == 'lte':         mask = pd.to_numeric(df[field], errors='coerce') <= float(value)
            else:
                continue

            df = df[~mask] if negate else df[mask]

        except Exception as e:
            logger.warning("CrossEngine filter error (%s %s): %s", field, lookup, e)
            continue

    return df


# ─────────────────────────────────────────────────────────────────────────────
# Guardar resultado
# ─────────────────────────────────────────────────────────────────────────────

def save_cross_result(cross_source, df: pd.DataFrame, user) -> 'StoredDataset':
    """
    Guarda el DataFrame resultado como StoredDataset y actualiza el CrossSource.
    Elimina el resultado anterior si existe.
    """
    from analyst.models import StoredDataset
    import uuid as _uuid

    blob = _serialize(df)
    ds_id    = _uuid.uuid4()
    perm_key = StoredDataset.make_cache_key(str(ds_id))
    col_names = [str(c) for c in df.columns]
    dtype_map = {str(c): str(df.dtypes[c]) for c in df.columns}

    # Guardar en Redis sin TTL
    cache.set(perm_key, {
        'data': blob,
        'meta': {
            'stored_dataset_id': str(ds_id),
            'cross_source_id':   str(cross_source.id),
            'filename':          f'cross:{cross_source.name}',
        }
    }, timeout=None)

    ds = StoredDataset.objects.create(
        id          = ds_id,
        name        = f'[Cruce] {cross_source.name}',
        description = f'Resultado del cruce "{cross_source.name}"',
        cache_key   = perm_key,
        rows        = len(df),
        col_count   = len(df.columns),
        columns     = col_names,
        dtype_map   = dtype_map,
        source_file = f'cross:{cross_source.id}',
        data_blob   = blob,
        created_by  = user,
    )

    # Eliminar resultado anterior
    if cross_source.last_result_id:
        try:
            old = cross_source.last_result
            cache.delete(old.cache_key)
            old.delete()
        except Exception as e:
            logger.warning("CrossEngine: no se pudo eliminar resultado anterior: %s", e)

    # Actualizar CrossSource
    cross_source.last_result   = ds
    cross_source.last_run_at   = timezone.now()
    cross_source.last_row_count = len(df)
    cross_source.save(update_fields=['last_result', 'last_run_at', 'last_row_count', 'updated_at'])

    return ds


# ─────────────────────────────────────────────────────────────────────────────
# Inspección de columnas (para el builder de UI)
# ─────────────────────────────────────────────────────────────────────────────

def get_source_columns(source_desc: dict, request=None, user=None) -> list:
    """
    Devuelve la lista de columnas de una fuente sin cargar todos los datos.
    Para StoredDataset y AnalystBase usa metadatos. Para ETLSource y clip
    carga el DataFrame completo.
    """
    src_type = source_desc.get('type', '')
    src_id   = source_desc.get('id',   '')

    if src_type == 'stored_dataset':
        from analyst.models import StoredDataset
        try:
            ds = StoredDataset.objects.get(id=src_id, created_by=user)
            return [{'name': c, 'dtype': ds.dtype_map.get(c, 'object')} for c in ds.columns]
        except StoredDataset.DoesNotExist:
            return []

    elif src_type == 'analyst_base':
        from analyst.models import AnalystBase
        try:
            base = AnalystBase.objects.get(id=src_id, created_by=user)
            return [{'name': c['name'], 'dtype': c['type']} for c in base.schema]
        except AnalystBase.DoesNotExist:
            return []

    elif src_type in ('etl_source', 'clip'):
        # Para estas fuentes necesitamos cargar el DataFrame
        try:
            df = _load_raw(src_type, src_id, request, user)
            return [{'name': str(c), 'dtype': str(df.dtypes[i])}
                    for i, c in enumerate(df.columns)]
        except Exception as e:
            logger.warning("get_source_columns error: %s", e)
            return []

    return []
