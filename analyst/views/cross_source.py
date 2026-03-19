# analyst/views/cross_source.py
"""
Vistas para CrossSource: cruce configurable entre dos fuentes de datos.

GET   /analyst/cross/              → lista + panel HTML
POST  /analyst/cross/create/       → crear cruce
POST  /analyst/cross/{id}/update/  → actualizar configuración
POST  /analyst/cross/{id}/run/     → ejecutar cruce → StoredDataset
POST  /analyst/cross/{id}/delete/  → eliminar cruce + resultado
GET   /analyst/cross/api/          → lista JSON (para selectores)
POST  /analyst/cross/api/columns/  → columnas de una fuente (para el builder)
"""

import json
import re
import logging
import math
import uuid as _uuid_mod

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from analyst.models import CrossSource, StoredDataset, AnalystBase, ETLSource

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Serialización JSON segura
# ─────────────────────────────────────────────────────────────────────────────

def _json_safe(obj):
    """Convierte recursivamente cualquier objeto a tipos Python primitivos."""
    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, str):
        return obj
    if isinstance(obj, _uuid_mod.UUID):
        return str(obj)
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(i) for i in obj]
    try:
        f = float(obj)
        if math.isnan(f) or math.isinf(f):
            return None
        if float(int(f)) == f:
            return int(f)
        return f
    except (TypeError, ValueError):
        pass
    return str(obj)


def _safe_json_str(obj) -> str:
    """
    Serializa a JSON string estrictamente valido para uso inline en <script>.
    ensure_ascii=True escapa U+2028/U+2029. Regex limpia NaN/Infinity.
    """
    cleaned = _json_safe(obj)
    result  = json.dumps(cleaned, ensure_ascii=True, allow_nan=True)
    result  = re.sub(r'\bNaN\b',       'null', result)
    result  = re.sub(r'\bInfinity\b',  'null', result)
    result  = re.sub(r'\b-Infinity\b', 'null', result)
    result  = result.replace('</', '<\/')
    return result

def _cross_row(cs: CrossSource) -> dict:
    cfg = cs.config or {}
    return {
        'id':             str(cs.id),
        'name':           cs.name,
        'description':    cs.description,
        'operation':      cfg.get('operation', ''),
        'operation_label': cs.operation_label,
        'left_type':      cfg.get('left',  {}).get('type',  ''),
        'right_type':     cfg.get('right', {}).get('type',  ''),
        'left_alias':     cfg.get('left',  {}).get('alias', ''),
        'right_alias':    cfg.get('right', {}).get('alias', ''),
        'has_result':     cs.has_result,
        'last_run_at':    cs.last_run_at.isoformat() if cs.last_run_at else None,
        'last_row_count': cs.last_row_count,
        'result_id':      str(cs.last_result_id) if cs.last_result_id else None,
        'result_name':    cs.last_result.name if cs.last_result else None,
        'created_at':     cs.created_at.isoformat(),
        'updated_at':     cs.updated_at.isoformat(),
        'config':         cfg,
    }


def _validate_config(config: dict) -> str | None:
    """Valida el config del cruce. Devuelve mensaje de error o None si es válido."""
    op = config.get('operation', '')
    if op not in ('left_join', 'inner_join', 'outer_join', 'concat'):
        return f"Operación inválida: '{op}'. Válidas: left_join, inner_join, outer_join, concat."

    for side in ('left', 'right'):
        src = config.get(side, {})
        if not src.get('type'):
            return f"Falta 'type' en la fuente {side}."
        if not src.get('id'):
            return f"Falta 'id' en la fuente {side}."
        valid_types = {'stored_dataset', 'analyst_base', 'etl_source', 'clip'}
        if src['type'] not in valid_types:
            return f"Tipo inválido '{src['type']}' en fuente {side}."

    if op != 'concat' and not config.get('on'):
        return "Se requiere al menos un par 'on' para joins (no aplica para concat)."

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Vistas HTML
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def cross_list(request):
    """Panel principal de CrossSource."""
    crosses   = CrossSource.objects.filter(
        created_by=request.user
    ).select_related('last_result').order_by('-updated_at')

    datasets  = StoredDataset.objects.filter(
        created_by=request.user
    ).exclude(
        source_file__startswith='analyst_base:'
    ).order_by('name').values('id', 'name', 'rows', 'col_count', 'columns', 'dtype_map')

    bases     = AnalystBase.objects.filter(
        created_by=request.user
    ).order_by('name').values('id', 'name', 'row_count', 'schema', 'category')

    etl_sources = ETLSource.objects.filter(
        created_by=request.user
    ).order_by('name').values('id', 'name', 'model_path', 'analyst_base_id')

    from analyst.utils.clipboard import DataFrameClipboard
    try:
        clips = DataFrameClipboard.list_clips(request) or []
    except Exception:
        clips = []

    return render(request, 'analyst/cross_source.html', {
        'crosses':          crosses,
        'datasets_json':    _safe_json_str(list(datasets)),
        'bases_json':       _safe_json_str(list(bases)),
        'etl_sources_json': _safe_json_str(list(etl_sources)),
        'clips_json':       _safe_json_str(clips),
    })


# ─────────────────────────────────────────────────────────────────────────────
# API — CRUD
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def cross_create(request):
    """Crea un CrossSource con su configuración."""
    try:
        body   = json.loads(request.body)
        name   = str(body.get('name', '')).strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio.'}, status=400)

        config = body.get('config', {})
        err    = _validate_config(config)
        if err:
            return JsonResponse({'success': False, 'error': err}, status=400)

        cs = CrossSource.objects.create(
            name        = name,
            description = str(body.get('description', '')).strip(),
            config      = config,
            created_by  = request.user,
        )
        logger.info("CrossSource creado: %s por %s", cs.id, request.user)
        return JsonResponse({'success': True, 'cross': _cross_row(cs)})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        logger.error("cross_create: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def cross_update(request, cross_id):
    """Actualiza nombre, descripción y configuración de un CrossSource."""
    cs = get_object_or_404(CrossSource, id=cross_id, created_by=request.user)
    try:
        body = json.loads(request.body)
        name = str(body.get('name', cs.name)).strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio.'}, status=400)

        config = body.get('config', cs.config)
        err    = _validate_config(config)
        if err:
            return JsonResponse({'success': False, 'error': err}, status=400)

        cs.name        = name
        cs.description = str(body.get('description', cs.description)).strip()
        cs.config      = config
        cs.save(update_fields=['name', 'description', 'config', 'updated_at'])
        return JsonResponse({'success': True, 'cross': _cross_row(cs)})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        logger.error("cross_update %s: %s", cross_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def cross_delete(request, cross_id):
    """Elimina un CrossSource y su último resultado si existe."""
    cs = get_object_or_404(CrossSource, id=cross_id, created_by=request.user)
    name = cs.name

    if cs.last_result:
        from django.core.cache import cache
        cache.delete(cs.last_result.cache_key)
        cs.last_result.delete()

    cs.delete()
    logger.info("CrossSource eliminado: %s ('%s') por %s", cross_id, name, request.user)
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────────────────────────────────────
# API — Ejecución
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def cross_run(request, cross_id):
    """
    Ejecuta el cruce → guarda resultado como StoredDataset.
    Devuelve preview de las primeras 100 filas + metadata.
    """
    cs = get_object_or_404(CrossSource, id=cross_id, created_by=request.user)
    try:
        from analyst.services.cross_engine import execute_cross, save_cross_result

        body        = json.loads(request.body) if request.body else {}
        # Permitir override de config en runtime (opcional)
        run_config  = body.get('config', cs.config)
        err         = _validate_config(run_config)
        if err:
            return JsonResponse({'success': False, 'error': err}, status=400)

        df = execute_cross(run_config, request=request, user=request.user)

        # Límite de seguridad
        if len(df) > 500_000:
            df = df.head(500_000)
            logger.warning("CrossSource %s: resultado truncado a 500k filas", cross_id)

        ds = save_cross_result(cs, df, request.user)

        # Preview — primeras 100 filas, valores JSON-safe
        preview_df = df.head(100).astype(object).where(pd.notnull(df.head(100)), None)
        preview_rows = preview_df.to_dict('records')

        return JsonResponse({
            'success': True,
            'cross':   _cross_row(cs),
            'dataset': {
                'id':       str(ds.id),
                'name':     ds.name,
                'rows':     ds.rows,
                'col_count': ds.col_count,
                'columns':  ds.columns,
            },
            'preview': {
                'columns': list(df.columns),
                'rows':    preview_rows,
                'total':   len(df),
            },
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        logger.error("cross_run %s: %s", cross_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# API — Metadatos / selectores
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_GET
def crosses_api(request):
    """Lista JSON de todos los CrossSource del usuario."""
    crosses = CrossSource.objects.filter(
        created_by=request.user
    ).select_related('last_result').order_by('name')
    return JsonResponse({'success': True, 'crosses': [_cross_row(cs) for cs in crosses]})


@login_required
@require_POST
def cross_columns_api(request):
    """
    Devuelve las columnas de una fuente para el builder de UI.
    POST { "type": "...", "id": "..." }
    """
    try:
        body       = json.loads(request.body)
        src_type   = body.get('type', '')
        src_id     = body.get('id',   '')
        if not src_type or not src_id:
            return JsonResponse({'success': False, 'error': 'type e id requeridos.'}, status=400)

        from analyst.services.cross_engine import get_source_columns
        cols = get_source_columns(
            {'type': src_type, 'id': src_id},
            request=request, user=request.user
        )
        return JsonResponse({'success': True, 'columns': cols})

    except Exception as e:
        logger.error("cross_columns_api: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def cross_preview(request, cross_id):
    """Devuelve el resultado almacenado paginado."""
    cs = get_object_or_404(CrossSource, id=cross_id, created_by=request.user)
    if not cs.last_result:
        return JsonResponse({'success': False, 'error': 'Sin resultado disponible. Ejecuta el cruce primero.'}, status=404)

    try:
        from analyst.services.cross_engine import _load_stored_dataset
        df = _load_stored_dataset(str(cs.last_result_id), request.user)

        page      = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 50)), 500)
        search    = request.GET.get('search', '').strip()

        if search:
            mask = df.astype(str).apply(
                lambda col: col.str.contains(search, case=False, na=False)
            ).any(axis=1)
            df = df[mask]

        total      = len(df)
        total_pages = max(1, -(-total // page_size))
        page        = min(max(1, page), total_pages)
        start       = (page - 1) * page_size
        end         = min(start + page_size, total)

        rows = df.iloc[start:end].astype(object).where(pd.notnull(df.iloc[start:end]), None).to_dict('records')

        return JsonResponse({
            'success': True,
            'columns': list(df.columns),
            'rows':    rows,
            'pagination': {
                'total_rows':  total,
                'page':        page,
                'page_size':   page_size,
                'total_pages': total_pages,
                'start':       start + 1,
                'end':         end,
            },
        })

    except Exception as e:
        logger.error("cross_preview %s: %s", cross_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
