# analyst/views/analyst_base.py
"""
Vistas para AnalystBase: bases de datos dinámicas gestionadas por el analista.
Todas las acciones sobre datos devuelven JSON. Solo base_list y base_detail
renderizan HTML.
"""

import io
import json
import logging

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from analyst.models import AnalystBase, StoredDataset
from analyst.services.base_validator import BaseValidator

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

_PAGE_SIZE  = 50
_MAX_PAGE   = 500

# Tipos de campo disponibles para el schema builder en la UI
FIELD_TYPE_INFO = [
    {'type': 'text',     'label': 'Texto',          'icon': '🔤'},
    {'type': 'number',   'label': 'Número entero',  'icon': '🔢'},
    {'type': 'decimal',  'label': 'Decimal',        'icon': '📊'},
    {'type': 'date',     'label': 'Fecha',          'icon': '📅'},
    {'type': 'datetime', 'label': 'Fecha y hora',   'icon': '🕐'},
    {'type': 'boolean',  'label': 'Sí / No',        'icon': '☑️'},
    {'type': 'choice',   'label': 'Opciones fijas', 'icon': '📋'},
    {'type': 'email',    'label': 'Email',          'icon': '✉️'},
    {'type': 'phone',    'label': 'Teléfono',       'icon': '📞'},
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _base_row(base: AnalystBase) -> dict:
    """Dict serializable de un AnalystBase para respuestas JSON."""
    return {
        'id':          str(base.id),
        'name':        base.name,
        'description': base.description,
        'category':    base.category,
        'category_label': dict(AnalystBase.CATEGORIES).get(base.category, base.category),
        'schema':      base.schema,
        'row_count':   base.row_count,
        'col_count':   len(base.schema),
        'created_at':  base.created_at.isoformat(),
        'updated_at':  base.updated_at.isoformat(),
        'has_data':    base.dataset_id is not None,
        'dataset_id':  str(base.dataset_id) if base.dataset_id else None,
    }


def _paginate(df: pd.DataFrame, page: int, page_size: int) -> dict:
    """Paginación simple de un DataFrame; devuelve dict con rows + meta."""
    total   = len(df)
    p       = max(1, page)
    ps      = min(max(1, page_size), _MAX_PAGE)
    pages   = max(1, -(-total // ps))  # ceil division
    p       = min(p, pages)
    start   = (p - 1) * ps
    end     = min(start + ps, total)
    rows    = df.iloc[start:end].where(pd.notnull(df.iloc[start:end]), None).to_dict('records')
    return {
        'rows':       rows,
        'pagination': {
            'total_rows':  total,
            'page':        p,
            'page_size':   ps,
            'total_pages': pages,
            'start':       start + 1,
            'end':         end,
        }
    }


def _validate_schema(schema: list) -> list:
    """
    Valida y limpia la lista de columnas enviada desde la UI.
    Lanza ValueError si hay problemas.
    """
    if not isinstance(schema, list) or len(schema) == 0:
        raise ValueError("El schema debe tener al menos una columna.")

    valid_types = set(AnalystBase.FIELD_TYPES)
    names_seen  = set()
    cleaned     = []

    for i, col in enumerate(schema):
        name = str(col.get('name', '')).strip().lower().replace(' ', '_')
        if not name:
            raise ValueError(f"Columna {i+1}: el nombre no puede estar vacío.")
        if name in names_seen:
            raise ValueError(f"Nombre de columna duplicado: '{name}'.")
        names_seen.add(name)

        ftype = col.get('type', 'text')
        if ftype not in valid_types:
            raise ValueError(f"Tipo inválido '{ftype}' en columna '{name}'.")

        if ftype == 'choice':
            choices = col.get('choices', [])
            if not isinstance(choices, list) or len(choices) == 0:
                raise ValueError(f"Columna '{name}' de tipo choice necesita al menos una opción.")

        cleaned.append({
            'name':       name,
            'label':      str(col.get('label', name)).strip() or name,
            'type':       ftype,
            'required':   bool(col.get('required', False)),
            'unique':     bool(col.get('unique', False)),
            'choices':    [str(c) for c in col.get('choices', [])],
            'default':    col.get('default', None),
            'max_length': col.get('max_length', None),
            'min_value':  col.get('min_value', None),
            'max_value':  col.get('max_value', None),
        })

    return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# Vistas HTML
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def base_list(request):
    """Panel principal de AnalystBase."""
    bases = AnalystBase.objects.filter(
        created_by=request.user
    ).select_related('dataset').order_by('-updated_at')

    return render(request, 'analyst/analyst_base.html', {
        'bases':       bases,
        'categories':  AnalystBase.CATEGORIES,
        'field_types': FIELD_TYPE_INFO,
    })


# ─────────────────────────────────────────────────────────────────────────────
# API — CRUD de bases
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def base_create(request):
    """Crea un AnalystBase nuevo con su schema."""
    try:
        body   = json.loads(request.body)
        name   = str(body.get('name', '')).strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio.'}, status=400)

        schema = _validate_schema(body.get('schema', []))

        base = AnalystBase.objects.create(
            name        = name,
            description = str(body.get('description', '')).strip(),
            category    = str(body.get('category', 'otro')),
            schema      = schema,
            created_by  = request.user,
        )
        logger.info("AnalystBase creado: %s por %s", base.id, request.user)
        return JsonResponse({'success': True, 'base': _base_row(base)})

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        logger.error("base_create: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def base_schema_update(request, base_id):
    """
    Actualiza el schema de una base.
    ⚠️  Si ya hay datos, solo se permiten:
       - Agregar columnas nuevas (opcionales)
       - Cambiar label, required, choices
    No se puede eliminar ni renombrar columnas con datos existentes.
    """
    base = get_object_or_404(AnalystBase, id=base_id, created_by=request.user)
    try:
        body       = json.loads(request.body)
        new_schema = _validate_schema(body.get('schema', []))

        if base.row_count > 0:
            existing_names = {c['name'] for c in base.schema}
            new_names      = {c['name'] for c in new_schema}

            removed = existing_names - new_names
            if removed:
                return JsonResponse({
                    'success': False,
                    'error':   f"No se pueden eliminar columnas con datos: {', '.join(removed)}. "
                               "Exporta los datos primero."
                }, status=400)

            # Agregar columnas nuevas al DataFrame existente (con valor None)
            added = new_names - existing_names
            if added:
                df = BaseValidator.load_dataframe(base)
                for col_name in added:
                    df[col_name] = None
                BaseValidator.save_dataframe(base, df, request.user)

        base.schema = new_schema
        base.save(update_fields=['schema', 'updated_at'])
        return JsonResponse({'success': True, 'base': _base_row(base)})

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.error("base_schema_update %s: %s", base_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def base_delete(request, base_id):
    """Elimina una base y su StoredDataset asociado."""
    base = get_object_or_404(AnalystBase, id=base_id, created_by=request.user)
    name = base.name

    # Eliminar dataset (también limpia Redis via signal o manualmente)
    if base.dataset:
        from django.core.cache import cache
        cache.delete(base.dataset.cache_key)
        base.dataset.delete()

    base.delete()
    logger.info("AnalystBase eliminado: %s ('%s') por %s", base_id, name, request.user)
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────────────────────────────────────
# API — Datos (lectura, paginación)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_GET
def base_data(request, base_id):
    """Devuelve filas paginadas + schema de la base."""
    base = get_object_or_404(AnalystBase, id=base_id, created_by=request.user)

    page      = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', _PAGE_SIZE))
    search    = request.GET.get('search', '').strip()

    df = BaseValidator.load_dataframe(base)

    # Búsqueda global simple (convierte todo a str)
    if search and not df.empty:
        mask = df.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        df = df[mask]

    result = _paginate(df, page, page_size)
    return JsonResponse({
        'success': True,
        'schema':  base.schema,
        **result,
    })


# ─────────────────────────────────────────────────────────────────────────────
# API — Escritura de filas
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def base_row_add(request, base_id):
    """Agrega una sola fila validando contra el schema."""
    base = get_object_or_404(AnalystBase, id=base_id, created_by=request.user)
    try:
        body = json.loads(request.body)
        row  = body.get('row', {})

        cleaned, errors = BaseValidator.validate_row(row, base.schema)
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        df = BaseValidator.load_dataframe(base)

        # Verificar unicidad
        unique_errors = BaseValidator.check_unique(df, [cleaned], base.schema)
        if unique_errors:
            return JsonResponse({'success': False, 'errors': unique_errors}, status=400)

        # Append
        new_row_df = pd.DataFrame([cleaned], columns=[c['name'] for c in base.schema])
        df = pd.concat([df, new_row_df], ignore_index=True)

        BaseValidator.save_dataframe(base, df, request.user)
        return JsonResponse({
            'success':   True,
            'row_count': len(df),
            'message':   'Fila agregada correctamente.',
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        logger.error("base_row_add %s: %s", base_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def base_row_edit(request, base_id):
    """Edita una fila existente identificada por su índice (0-based)."""
    base = get_object_or_404(AnalystBase, id=base_id, created_by=request.user)
    try:
        body      = json.loads(request.body)
        row_index = int(body.get('row_index', -1))
        row_data  = body.get('row', {})

        df = BaseValidator.load_dataframe(base)
        if row_index < 0 or row_index >= len(df):
            return JsonResponse({'success': False, 'error': 'Índice de fila inválido.'}, status=400)

        cleaned, errors = BaseValidator.validate_row(row_data, base.schema)
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        # Para check_unique, excluir la fila que se edita
        df_without = df.drop(index=row_index).reset_index(drop=True)
        unique_errors = BaseValidator.check_unique(df_without, [cleaned], base.schema)
        if unique_errors:
            return JsonResponse({'success': False, 'errors': unique_errors}, status=400)

        for col, val in cleaned.items():
            df.at[row_index, col] = val

        BaseValidator.save_dataframe(base, df, request.user)
        return JsonResponse({'success': True, 'message': 'Fila actualizada.'})

    except Exception as e:
        logger.error("base_row_edit %s: %s", base_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def base_row_delete(request, base_id):
    """Elimina una o varias filas por sus índices (0-based)."""
    base = get_object_or_404(AnalystBase, id=base_id, created_by=request.user)
    try:
        body    = json.loads(request.body)
        indices = body.get('indices', [])
        if not indices:
            return JsonResponse({'success': False, 'error': 'No se enviaron índices.'}, status=400)

        df = BaseValidator.load_dataframe(base)
        invalid = [i for i in indices if i < 0 or i >= len(df)]
        if invalid:
            return JsonResponse({'success': False,
                                  'error': f'Índices fuera de rango: {invalid}'}, status=400)

        df = df.drop(index=indices).reset_index(drop=True)
        BaseValidator.save_dataframe(base, df, request.user)

        return JsonResponse({
            'success':   True,
            'row_count': len(df),
            'message':   f'{len(indices)} fila(s) eliminada(s).',
        })

    except Exception as e:
        logger.error("base_row_delete %s: %s", base_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# API — Importación masiva CSV / Excel
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def base_bulk_import(request, base_id):
    """
    Importa filas desde CSV o Excel validando contra el schema.
    Modos:
      - mode=append  (default): agrega al final
      - mode=replace:           reemplaza todos los datos
    """
    base = get_object_or_404(AnalystBase, id=base_id, created_by=request.user)
    file = request.FILES.get('file')
    mode = request.POST.get('mode', 'append')

    if not file:
        return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo.'}, status=400)

    try:
        ext = file.name.rsplit('.', 1)[-1].lower()
        if ext == 'csv':
            try:
                df_raw = pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                df_raw = pd.read_csv(file, encoding='latin-1')
        elif ext in ('xls', 'xlsx'):
            df_raw = pd.read_excel(file)
        else:
            return JsonResponse(
                {'success': False, 'error': 'Solo se aceptan archivos CSV, XLS o XLSX.'},
                status=400
            )

        # Normalizar nombres de columna
        df_raw.columns = [str(c).strip().lower().replace(' ', '_') for c in df_raw.columns]

        df_clean, row_errors = BaseValidator.validate_dataframe(df_raw, base.schema)

        if len(df_clean) == 0 and len(row_errors) > 0:
            return JsonResponse({
                'success': False,
                'error':   'Ninguna fila pasó la validación.',
                'row_errors': row_errors[:20],
            }, status=400)

        # Unicidad
        existing_df = BaseValidator.load_dataframe(base)
        if mode == 'append':
            unique_errors = BaseValidator.check_unique(
                existing_df, df_clean.to_dict('records'), base.schema
            )
            if unique_errors:
                return JsonResponse({
                    'success': False,
                    'error':   'Violaciones de unicidad encontradas.',
                    'unique_errors': unique_errors[:10],
                }, status=400)
            final_df = pd.concat([existing_df, df_clean], ignore_index=True)
        else:  # replace
            final_df = df_clean

        BaseValidator.save_dataframe(base, final_df, request.user)

        return JsonResponse({
            'success':       True,
            'imported_rows': len(df_clean),
            'skipped_rows':  len(row_errors),
            'total_rows':    len(final_df),
            'row_errors':    row_errors[:10],
            'message':       f'{len(df_clean)} filas importadas correctamente.',
        })

    except Exception as e:
        logger.error("base_bulk_import %s: %s", base_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# API — Export
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_GET
def base_export(request, base_id):
    """Descarga todos los datos de la base como CSV."""
    base = get_object_or_404(AnalystBase, id=base_id, created_by=request.user)
    df   = BaseValidator.load_dataframe(base)

    buf = io.StringIO()
    df.to_csv(buf, index=False, encoding='utf-8-sig')
    buf.seek(0)

    filename = f"{base.name.replace(' ', '_')}.csv"
    response = HttpResponse(buf.read(), content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ─────────────────────────────────────────────────────────────────────────────
# API — Metadatos (para el ETL, CrossSource, etc.)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_GET
def base_columns_api(request, base_id):
    """Devuelve el schema de la base (para selectores en ETL/CrossSource)."""
    base = get_object_or_404(AnalystBase, id=base_id, created_by=request.user)
    return JsonResponse({
        'success': True,
        'base_id': str(base.id),
        'name':    base.name,
        'schema':  base.schema,
        'columns': [{'name': c['name'], 'label': c['label'], 'type': c['type']}
                    for c in base.schema],
    })


@login_required
@require_GET
def bases_api(request):
    """Lista todas las bases del usuario (para selectores en otros módulos)."""
    bases = AnalystBase.objects.filter(created_by=request.user).order_by('name')
    return JsonResponse({
        'success': True,
        'bases': [_base_row(b) for b in bases],
    })


# ─────────────────────────────────────────────────────────────────────────────
# API — Importación desde texto (clipboard, JSON, dataset existente)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def base_bulk_import_raw(request, base_id):
    """
    Importa filas desde fuentes de texto:
      source = 'clipboard' → texto tabular (TSV/CSV pegado del portapapeles)
      source = 'json'      → array JSON de objetos
      source = 'dataset'   → UUID de un StoredDataset existente del usuario
    """
    import json as _json
    base = get_object_or_404(AnalystBase, id=base_id, created_by=request.user)

    try:
        body   = _json.loads(request.body)
        source = body.get('source', 'clipboard')
        mode   = body.get('mode', 'append')

        # ── Construir DataFrame según la fuente ──────────────────────────────
        if source == 'clipboard':
            text       = body.get('text', '').strip()
            has_header = bool(body.get('has_header', True))
            if not text:
                return JsonResponse({'success': False, 'error': 'No se recibió texto.'}, status=400)

            # Detectar separador
            first_line = text.split('\n')[0]
            sep = '\t' if '\t' in first_line else (';' if ';' in first_line else ',')

            lines = [l for l in text.split('\n') if l.strip()]
            rows  = [l.split(sep) for l in lines]

            if has_header and len(rows) > 1:
                headers  = [h.strip().strip('"').lower().replace(' ', '_') for h in rows[0]]
                df_raw   = pd.DataFrame(rows[1:], columns=headers)
            elif has_header:
                return JsonResponse({'success': False, 'error': 'Solo hay encabezado, sin datos.'}, status=400)
            else:
                df_raw = pd.DataFrame(rows)

        elif source == 'json':
            text = body.get('text', '').strip()
            if not text:
                return JsonResponse({'success': False, 'error': 'No se recibió JSON.'}, status=400)
            try:
                raw = _json.loads(text)
            except _json.JSONDecodeError as e:
                return JsonResponse({'success': False, 'error': f'JSON inválido: {e}'}, status=400)

            # Normalizar estructura
            if isinstance(raw, dict):
                # buscar la primera lista dentro del dict
                for v in raw.values():
                    if isinstance(v, list):
                        raw = v
                        break
                else:
                    return JsonResponse({'success': False, 'error': 'No se encontró un array en el JSON.'}, status=400)

            if not isinstance(raw, list) or not raw:
                return JsonResponse({'success': False, 'error': 'El JSON debe ser un array no vacío.'}, status=400)

            if isinstance(raw[0], list):
                # Array de arrays → primera fila = headers
                headers = [str(h).strip().lower().replace(' ', '_') for h in raw[0]]
                df_raw  = pd.DataFrame(raw[1:], columns=headers)
            else:
                df_raw = pd.DataFrame(raw)
                df_raw.columns = [str(c).strip().lower().replace(' ', '_') for c in df_raw.columns]

        elif source == 'clip':
            clip_key = body.get('clip_key', '').strip()
            if not clip_key:
                return JsonResponse({'success': False, 'error': 'clip_key requerido.'}, status=400)
            from analyst.utils.clipboard import DataFrameClipboard
            import pickle as _pickle2, base64 as _b642
            df_raw, _meta = DataFrameClipboard.retrieve_df(request, clip_key)
            if df_raw is None:
                return JsonResponse({'success': False, 'error': f"Clip '{clip_key}' no encontrado o expirado."}, status=404)
            df_raw.columns = [str(c).strip().lower().replace(' ', '_') for c in df_raw.columns]

        elif source == 'dataset':
            dataset_id = body.get('dataset_id')
            if not dataset_id:
                return JsonResponse({'success': False, 'error': 'dataset_id requerido.'}, status=400)
            try:
                ds = StoredDataset.objects.get(id=dataset_id, created_by=request.user)
            except StoredDataset.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Dataset no encontrado o sin acceso.'}, status=403)

            # Deserializar
            import pickle as _pickle, base64 as _b64
            cached = __import__('django.core.cache', fromlist=['cache']).cache.get(ds.cache_key)
            if cached:
                df_raw = _pickle.loads(_b64.b64decode(cached['data'].encode()))
            elif ds.data_blob:
                df_raw = _pickle.loads(_b64.b64decode(ds.data_blob.encode()))
            else:
                return JsonResponse({'success': False, 'error': 'Dataset sin datos disponibles.'}, status=400)
            df_raw.columns = [str(c).strip().lower().replace(' ', '_') for c in df_raw.columns]

        else:
            return JsonResponse({'success': False, 'error': f'Fuente desconocida: {source}'}, status=400)

        # ── Validar y guardar ────────────────────────────────────────────────
        df_clean, row_errors = BaseValidator.validate_dataframe(df_raw, base.schema)

        if len(df_clean) == 0 and len(row_errors) > 0:
            return JsonResponse({
                'success':    False,
                'error':      'Ninguna fila pasó la validación.',
                'row_errors': row_errors[:20],
            }, status=400)

        existing_df = BaseValidator.load_dataframe(base)

        if mode == 'append':
            unique_errors = BaseValidator.check_unique(
                existing_df, df_clean.to_dict('records'), base.schema
            )
            if unique_errors:
                return JsonResponse({
                    'success':       False,
                    'error':         'Violaciones de unicidad encontradas.',
                    'unique_errors': unique_errors[:10],
                }, status=400)
            final_df = pd.concat([existing_df, df_clean], ignore_index=True)
        else:
            final_df = df_clean

        BaseValidator.save_dataframe(base, final_df, request.user)

        return JsonResponse({
            'success':       True,
            'imported_rows': len(df_clean),
            'skipped_rows':  len(row_errors),
            'total_rows':    len(final_df),
            'row_errors':    row_errors[:10],
            'message':       f'{len(df_clean)} filas importadas correctamente.',
        })

    except Exception as e:
        logger.error("base_bulk_import_raw %s: %s", base_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# API — Listar fuentes disponibles (StoredDatasets + Clipboard)
# Usado por los selectores de importación en el template
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_GET
def sources_api(request):
    """
    Devuelve StoredDatasets y clips del portapapeles del usuario actual.
    Respuesta:
    {
      "datasets": [{id, name, rows, col_count, columns, source_file, created_at}],
      "clips":    [{key, rows, cols, filename, description, created_at}]
    }
    """
    from analyst.utils.clipboard import DataFrameClipboard

    # StoredDatasets — excluir los que son espejo de AnalystBase
    datasets_qs = StoredDataset.objects.filter(
        created_by=request.user
    ).exclude(
        source_file__startswith='analyst_base:'
    ).order_by('-created_at').values(
        'id', 'name', 'rows', 'col_count', 'columns', 'source_file', 'created_at'
    )

    datasets = [
        {
            'id':          str(d['id']),
            'name':        d['name'],
            'rows':        d['rows'],
            'col_count':   d['col_count'],
            'columns':     d['columns'] or [],
            'source_file': d['source_file'] or '',
            'created_at':  d['created_at'].isoformat(),
        }
        for d in datasets_qs
    ]

    # Portapapeles
    try:
        clips = DataFrameClipboard.list_clips(request)
        clips_list = [
            {
                'key':         c.get('key', ''),
                'rows':        c.get('rows', 0),
                'cols':        c.get('cols', 0),
                'filename':    c.get('filename', ''),
                'description': c.get('description', ''),
                'created_at':  str(c.get('created_at', '')),
            }
            for c in (clips or [])
        ]
    except Exception as e:
        logger.warning("sources_api: error leyendo clips: %s", e)
        clips_list = []

    return JsonResponse({
        'success':  True,
        'datasets': datasets,
        'clips':    clips_list,
    })


# ─────────────────────────────────────────────────────────────────────────────
# API — Columnas de un Clip (para inferir schema desde clip guardado)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def clip_columns_api(request):
    """
    Devuelve las columnas e información de tipo de un clip del portapapeles.
    POST { clip_key: "..." }
    """
    import json as _json
    try:
        body     = _json.loads(request.body)
        clip_key = body.get('clip_key', '').strip()
        if not clip_key:
            return JsonResponse({'success': False, 'error': 'clip_key requerido.'}, status=400)

        from analyst.utils.clipboard import DataFrameClipboard
        df, _meta = DataFrameClipboard.retrieve_df(request, clip_key)
        if df is None:
            return JsonResponse({'success': False, 'error': 'Clip no encontrado.'}, status=404)

        def _guess_type(series):
            dt = str(series.dtype).lower()
            if 'int'   in dt: return 'number'
            if 'float' in dt: return 'decimal'
            if 'bool'  in dt: return 'boolean'
            # Try string-based inference on first non-null
            sample = series.dropna().astype(str)
            if sample.empty: return 'text'
            v = sample.iloc[0].strip()
            import re as _re
            if _re.match(r'^\d{4}-\d{2}-\d{2}T', v): return 'datetime'
            if _re.match(r'^\d{4}-\d{2}-\d{2}$', v): return 'date'
            if _re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', v): return 'email'
            return 'text'

        columns = [
            {'name': str(c).strip().lower().replace(' ', '_'), 'type': _guess_type(df[c])}
            for c in df.columns
        ]

        return JsonResponse({'success': True, 'columns': columns, 'rows': len(df)})

    except Exception as e:
        logger.error("clip_columns_api: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
