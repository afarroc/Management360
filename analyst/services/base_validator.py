# analyst/services/base_validator.py
"""
Validación de filas contra el schema de un AnalystBase y helpers
para leer/escribir el DataFrame asociado (StoredDataset).
"""

import re
import uuid
import pickle
import base64
import logging
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^[\d\s\+\-\(\)]{6,20}$')

PANDAS_DTYPE = {
    'text':     'object',
    'email':    'object',
    'phone':    'object',
    'choice':   'object',
    'date':     'object',
    'datetime': 'object',
    'boolean':  'bool',
    'number':   'Int64',
    'decimal':  'float64',
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _serialize(df: pd.DataFrame) -> str:
    return base64.b64encode(pickle.dumps(df)).decode()


def _deserialize(blob: str) -> pd.DataFrame:
    return pickle.loads(base64.b64decode(blob.encode()))


# ─────────────────────────────────────────────────────────────────────────────
# BaseValidator
# ─────────────────────────────────────────────────────────────────────────────

class BaseValidator:
    """
    Validación de datos contra el schema de un AnalystBase
    y persistencia del DataFrame asociado.
    """

    # ── Validación de una sola celda ─────────────────────────────────────────

    @classmethod
    def _coerce(cls, value: Any, col_def: Dict) -> Tuple[Any, Optional[str]]:
        """
        Convierte y valida un valor según la definición de columna.
        Devuelve (valor_convertido, mensaje_error | None).
        """
        ftype   = col_def.get('type', 'text')
        label   = col_def.get('label', col_def['name'])
        required = col_def.get('required', False)

        # Vacío / nulo
        is_empty = value is None or (isinstance(value, float) and pd.isna(value)) \
                   or str(value).strip() == ''
        if is_empty:
            if required:
                return None, f"'{label}' es obligatorio"
            default = col_def.get('default')
            return default, None

        v = str(value).strip()

        if ftype == 'text':
            max_len = col_def.get('max_length')
            if max_len and len(v) > int(max_len):
                return None, f"'{label}' excede {max_len} caracteres"
            return v, None

        if ftype == 'email':
            if not EMAIL_RE.match(v):
                return None, f"'{label}' no es un email válido"
            return v.lower(), None

        if ftype == 'phone':
            if not PHONE_RE.match(v):
                return None, f"'{label}' no es un teléfono válido"
            return re.sub(r'[\s\-\(\)]', '', v), None

        if ftype == 'choice':
            choices = col_def.get('choices', [])
            if v not in choices:
                opts = ', '.join(choices[:5])
                return None, f"'{label}' debe ser uno de: {opts}"
            return v, None

        if ftype == 'boolean':
            if isinstance(value, bool):
                return value, None
            low = v.lower()
            if low in {'true', '1', 'si', 'sí', 'yes', 'on'}:
                return True, None
            if low in {'false', '0', 'no', 'off'}:
                return False, None
            return None, f"'{label}' no es un valor booleano válido"

        if ftype == 'number':
            try:
                n = int(float(v.replace(',', '.')))
            except (ValueError, TypeError):
                return None, f"'{label}' debe ser un número entero"
            mn = col_def.get('min_value')
            mx = col_def.get('max_value')
            if mn is not None and n < mn:
                return None, f"'{label}' debe ser ≥ {mn}"
            if mx is not None and n > mx:
                return None, f"'{label}' debe ser ≤ {mx}"
            return n, None

        if ftype == 'decimal':
            try:
                n = float(v.replace(',', '.'))
            except (ValueError, TypeError):
                return None, f"'{label}' debe ser un número decimal"
            mn = col_def.get('min_value')
            mx = col_def.get('max_value')
            if mn is not None and n < mn:
                return None, f"'{label}' debe ser ≥ {mn}"
            if mx is not None and n > mx:
                return None, f"'{label}' debe ser ≤ {mx}"
            return round(n, 6), None

        if ftype == 'date':
            try:
                d = pd.to_datetime(v)
                return d.strftime('%Y-%m-%d'), None
            except Exception:
                return None, f"'{label}' no es una fecha válida (use YYYY-MM-DD)"

        if ftype == 'datetime':
            try:
                d = pd.to_datetime(v)
                return d.strftime('%Y-%m-%d %H:%M'), None
            except Exception:
                return None, f"'{label}' no es una fecha/hora válida"

        return v, None

    # ── Validación de una fila (dict) ─────────────────────────────────────────

    @classmethod
    def validate_row(
        cls, row: Dict, schema: List[Dict]
    ) -> Tuple[Dict, List[str]]:
        """
        Valida y limpia un dict de una fila contra el schema.
        Devuelve (row_limpio, lista_de_errores).
        """
        cleaned = {}
        errors  = []

        schema_map = {col['name']: col for col in schema}

        for col_def in schema:
            fname   = col_def['name']
            raw_val = row.get(fname)
            val, err = cls._coerce(raw_val, col_def)
            if err:
                errors.append(err)
            elif val is not None:
                cleaned[fname] = val

        # Advertir campos desconocidos (no errores)
        extra = set(row.keys()) - set(schema_map.keys())
        if extra:
            logger.debug("Campos desconocidos ignorados: %s", extra)

        return cleaned, errors

    # ── Validación masiva (DataFrame) ────────────────────────────────────────

    @classmethod
    def validate_dataframe(
        cls, df: pd.DataFrame, schema: List[Dict]
    ) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Valida todas las filas de un DataFrame contra el schema.
        Devuelve (df_limpio, lista de {row_idx, errors}).
        """
        col_names   = [c['name'] for c in schema]
        clean_rows  = []
        row_errors  = []

        for idx, row in df.iterrows():
            row_dict = {}
            for col in schema:
                name = col['name']
                # Busca la columna en el DF (normalizada o exacta)
                if name in df.columns:
                    row_dict[name] = row[name]
                else:
                    # intentar por label
                    label = col.get('label', '')
                    if label in df.columns:
                        row_dict[name] = row[label]
                    else:
                        row_dict[name] = None

            cleaned, errs = cls.validate_row(row_dict, schema)
            if errs:
                row_errors.append({'row': int(idx) + 1, 'errors': errs})
            else:
                clean_rows.append(cleaned)

        if clean_rows:
            out_df = pd.DataFrame(clean_rows, columns=col_names)
        else:
            out_df = pd.DataFrame(columns=col_names)

        return out_df, row_errors

    # ── Leer DataFrame de un AnalystBase ─────────────────────────────────────

    @classmethod
    def load_dataframe(cls, analyst_base) -> Optional[pd.DataFrame]:
        """
        Carga el DataFrame asociado al AnalystBase.
        Intenta Redis primero; si no, deserializa data_blob de la BD.
        """
        from analyst.models import StoredDataset

        if analyst_base.dataset is None:
            cols = [c['name'] for c in analyst_base.schema]
            return pd.DataFrame(columns=cols)

        ds = analyst_base.dataset
        # Intento Redis
        cached = cache.get(ds.cache_key)
        if cached:
            try:
                return _deserialize(cached['data'])
            except Exception as e:
                logger.warning("Error leyendo caché de AnalystBase %s: %s", analyst_base.id, e)

        # Fallback: data_blob en BD
        try:
            return _deserialize(ds.data_blob)
        except Exception as e:
            logger.error("Error deserializando data_blob de AnalystBase %s: %s", analyst_base.id, e)
            return pd.DataFrame(columns=[c['name'] for c in analyst_base.schema])

    # ── Guardar DataFrame en un AnalystBase ──────────────────────────────────

    @classmethod
    def save_dataframe(cls, analyst_base, df: pd.DataFrame, user) -> None:
        """
        Persiste el DataFrame actualizado en Redis + StoredDataset.
        Crea el StoredDataset si no existe todavía.
        """
        from analyst.models import StoredDataset

        blob      = _serialize(df)
        col_names = [str(c) for c in df.columns]
        dtype_map = {str(c): str(df.dtypes[i]) for i, c in enumerate(df.columns)}

        if analyst_base.dataset is None:
            # Primera vez: crear StoredDataset
            ds_id    = uuid.uuid4()
            perm_key = StoredDataset.make_cache_key(str(ds_id))
            ds = StoredDataset.objects.create(
                id          = ds_id,
                name        = f'[BASE] {analyst_base.name}',
                description = analyst_base.description,
                cache_key   = perm_key,
                rows        = len(df),
                col_count   = len(df.columns),
                columns     = col_names,
                dtype_map   = dtype_map,
                source_file = f'analyst_base:{analyst_base.id}',
                data_blob   = blob,
                created_by  = user,
            )
            analyst_base.dataset = ds
        else:
            ds = analyst_base.dataset
            ds.rows      = len(df)
            ds.col_count = len(df.columns)
            ds.columns   = col_names
            ds.dtype_map = dtype_map
            ds.data_blob = blob
            ds.updated_at = timezone.now()
            ds.save(update_fields=['rows', 'col_count', 'columns', 'dtype_map',
                                   'data_blob', 'updated_at'])

        # Actualizar Redis sin TTL (persistente)
        cache.set(ds.cache_key, {
            'data': blob,
            'meta': {
                'stored_dataset_id': str(ds.id),
                'analyst_base_id':   str(analyst_base.id),
                'filename':          f'analyst_base:{analyst_base.id}',
            }
        }, timeout=None)

        analyst_base.row_count = len(df)
        analyst_base.save(update_fields=['dataset', 'row_count', 'updated_at'])

    # ── Verificar unicidad ────────────────────────────────────────────────────

    @classmethod
    def check_unique(
        cls, df_existing: pd.DataFrame, new_rows: List[Dict], schema: List[Dict]
    ) -> List[str]:
        """
        Detecta violaciones de campos unique comparando nuevas filas
        contra el DataFrame existente y contra sí mismas.
        Devuelve lista de mensajes de error.
        """
        unique_cols = [c['name'] for c in schema if c.get('unique')]
        errors = []

        for col in unique_cols:
            if col not in df_existing.columns:
                continue
            existing_vals = set(df_existing[col].dropna().astype(str))
            incoming_vals = [str(r.get(col, '')) for r in new_rows if r.get(col) is not None]

            # Duplicados internos
            seen = set()
            for v in incoming_vals:
                if v in seen:
                    errors.append(f"Columna '{col}': valor '{v}' duplicado en los datos nuevos")
                seen.add(v)

            # Colisión con existentes
            for v in incoming_vals:
                if v in existing_vals:
                    errors.append(f"Columna '{col}': valor '{v}' ya existe en la base")

        return errors
