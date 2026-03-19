# analyst/views/pipeline.py
"""
Pipeline — vistas SPA.

GET   /analyst/pipelines/                        → lista + panel HTML
POST  /analyst/pipelines/create/                 → crear pipeline
POST  /analyst/pipelines/<id>/update/            → actualizar nombre/desc/steps
POST  /analyst/pipelines/<id>/delete/            → eliminar
POST  /analyst/pipelines/<id>/steps/add/         → agregar paso
POST  /analyst/pipelines/<id>/steps/reorder/     → reordenar pasos
POST  /analyst/pipelines/<id>/steps/<idx>/delete/ → eliminar paso
POST  /analyst/pipelines/<id>/run/               → ejecutar pipeline
GET   /analyst/pipelines/<id>/runs/              → historial de ejecuciones
GET   /analyst/pipelines/api/                    → lista JSON
"""

import json
import logging
import math
import uuid as _uuid_mod

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from analyst.models import (
    Pipeline, PipelineRun, StoredDataset,
    AnalystBase, CrossSource, PIPELINE_STEP_TYPES,
)
from analyst.services.pipeline_engine import PipelineEngine

logger = logging.getLogger(__name__)


# ─── JSON helpers ─────────────────────────────────────────────────────────────

def _json_safe(obj):
    if obj is None: return None
    if isinstance(obj, bool): return obj
    if isinstance(obj, int): return obj
    if isinstance(obj, float): return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, str): return obj
    if isinstance(obj, _uuid_mod.UUID): return str(obj)
    if hasattr(obj, 'isoformat'): return obj.isoformat()
    if isinstance(obj, dict): return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [_json_safe(i) for i in obj]
    try:
        f = float(obj)
        if math.isnan(f) or math.isinf(f): return None
        return int(f) if float(int(f)) == f else f
    except (TypeError, ValueError): pass
    return str(obj)


def _safe_json_str(obj) -> str:
    import re as _re
    result = json.dumps(_json_safe(obj), ensure_ascii=True, allow_nan=True)
    result = _re.sub(r'\bNaN\b',       'null', result)
    result = _re.sub(r'\bInfinity\b',  'null', result)
    result = _re.sub(r'\b-Infinity\b', 'null', result)
    return result.replace('</', r'<\/')


# ─── Row helpers ──────────────────────────────────────────────────────────────

def _pipeline_row(p: Pipeline) -> dict:
    last_run = p.runs.order_by('-created_at').first()
    return {
        'id':          str(p.id),
        'name':        p.name,
        'description': p.description,
        'step_count':  p.step_count,
        'steps':       p.steps,
        'source_dataset': str(p.source_dataset_id) if p.source_dataset_id else None,
        'created_at':  p.created_at.isoformat(),
        'updated_at':  p.updated_at.isoformat(),
        'last_run':    {
            'status':     last_run.status,
            'duration_s': last_run.duration_s,
            'created_at': last_run.created_at.isoformat(),
        } if last_run else None,
    }


def _run_row(r: PipelineRun) -> dict:
    return {
        'id':               str(r.id),
        'pipeline':         str(r.pipeline_id),
        'input_dataset':    str(r.input_dataset_id),
        'result_dataset':   str(r.result_dataset_id) if r.result_dataset_id else None,
        'status':           r.status,
        'status_label':     r.get_status_display(),
        'error_msg':        r.error_msg,
        'steps_completed':  r.steps_completed,
        'duration_s':       round(r.duration_s, 2),
        'created_at':       r.created_at.isoformat(),
        'started_at':       r.started_at.isoformat() if r.started_at else None,
        'finished_at':      r.finished_at.isoformat() if r.finished_at else None,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Views
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def pipeline_list(request):
    pipelines = Pipeline.objects.filter(
        created_by=request.user
    ).prefetch_related('runs').order_by('-updated_at')

    datasets = StoredDataset.objects.filter(
        created_by=request.user
    ).order_by('name')

    return render(request, 'analyst/pipeline.html', {
        'pipelines':       pipelines,
        'pipeline_count':  pipelines.count(),
        'step_types_json': _safe_json_str([
            {'value': k, 'label': v} for k, v in PIPELINE_STEP_TYPES
        ]),
        'datasets_json': _safe_json_str([
            {'id': str(d.id), 'name': d.name, 'columns': list(d.columns)}
            for d in datasets
        ]),
    })


@login_required
@require_GET
def pipeline_api(request):
    pipelines = Pipeline.objects.filter(created_by=request.user).order_by('-updated_at')
    return JsonResponse({'success': True, 'pipelines': [_pipeline_row(p) for p in pipelines]})


@login_required
@require_POST
def pipeline_create(request):
    try:
        body = json.loads(request.body)
        name = str(body.get('name', '')).strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Nombre requerido.'}, status=400)

        p = Pipeline.objects.create(
            name           = name,
            description    = str(body.get('description', '')).strip(),
            steps          = body.get('steps', []),
            source_dataset_id = body.get('source_dataset') or None,
            created_by     = request.user,
        )
        logger.info("Pipeline creado: %s por %s", p.id, request.user)
        return JsonResponse({'success': True, 'pipeline': _pipeline_row(p)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def pipeline_update(request, pipeline_id):
    p = get_object_or_404(Pipeline, id=pipeline_id, created_by=request.user)
    try:
        body = json.loads(request.body)
        if 'name'        in body: p.name        = str(body['name']).strip() or p.name
        if 'description' in body: p.description = str(body['description']).strip()
        if 'steps'       in body: p.steps       = body['steps']
        p.save()
        return JsonResponse({'success': True, 'pipeline': _pipeline_row(p)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def pipeline_delete(request, pipeline_id):
    p = get_object_or_404(Pipeline, id=pipeline_id, created_by=request.user)
    p.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def step_add(request, pipeline_id):
    """Append a step to the pipeline."""
    p = get_object_or_404(Pipeline, id=pipeline_id, created_by=request.user)
    try:
        body      = json.loads(request.body)
        step_type = body.get('type', '')
        if step_type not in dict(PIPELINE_STEP_TYPES):
            return JsonResponse({'success': False, 'error': f"Tipo desconocido: '{step_type}'."}, status=400)

        steps = list(p.steps)
        new_step = {
            'order':  len(steps),
            'type':   step_type,
            'label':  str(body.get('label', '')).strip() or step_type,
            'params': body.get('params', {}),
        }
        steps.append(new_step)
        p.steps = steps
        p.save(update_fields=['steps', 'updated_at'])
        return JsonResponse({'success': True, 'pipeline': _pipeline_row(p), 'step': new_step})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def step_delete(request, pipeline_id, step_index):
    """Delete a step by its order index."""
    p = get_object_or_404(Pipeline, id=pipeline_id, created_by=request.user)
    try:
        steps = list(p.steps)
        if step_index < 0 or step_index >= len(steps):
            return JsonResponse({'success': False, 'error': 'Indice fuera de rango.'}, status=400)
        steps.pop(step_index)
        # Re-number
        for i, s in enumerate(steps):
            s['order'] = i
        p.steps = steps
        p.save(update_fields=['steps', 'updated_at'])
        return JsonResponse({'success': True, 'pipeline': _pipeline_row(p)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def step_reorder(request, pipeline_id):
    """Reorder steps. POST: { "order": [old_idx0, old_idx1, ...] }"""
    p = get_object_or_404(Pipeline, id=pipeline_id, created_by=request.user)
    try:
        body  = json.loads(request.body)
        order = body.get('order', [])
        steps = list(p.steps)
        if sorted(order) != list(range(len(steps))):
            return JsonResponse({'success': False, 'error': 'Indices invalidos.'}, status=400)
        new_steps = [steps[i] for i in order]
        for i, s in enumerate(new_steps):
            s['order'] = i
        p.steps = new_steps
        p.save(update_fields=['steps', 'updated_at'])
        return JsonResponse({'success': True, 'pipeline': _pipeline_row(p)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def pipeline_run(request, pipeline_id):
    """Execute a pipeline against a dataset."""
    p = get_object_or_404(Pipeline, id=pipeline_id, created_by=request.user)
    try:
        body       = json.loads(request.body)
        dataset_id = body.get('dataset_id')
        output_name = str(body.get('output_name', '')).strip() or None
        runtime_params = body.get('runtime_params', {})

        if not dataset_id:
            return JsonResponse({'success': False, 'error': 'dataset_id requerido.'}, status=400)

        ds = get_object_or_404(StoredDataset, id=dataset_id, created_by=request.user)

        if not p.steps:
            return JsonResponse({'success': False, 'error': 'El pipeline no tiene pasos.'}, status=400)

        engine = PipelineEngine(p, ds, request.user)
        result_ds, error = engine.run(output_name=output_name, runtime_params=runtime_params)

        if error:
            return JsonResponse({'success': False, 'error': error}, status=422)

        run = p.runs.order_by('-created_at').first()
        return JsonResponse({
            'success':        True,
            'pipeline':       _pipeline_row(p),
            'run':            _run_row(run),
            'result_dataset': {
                'id':        str(result_ds.id),
                'name':      result_ds.name,
                'rows':      result_ds.rows,
                'col_count': result_ds.col_count,
            },
        })

    except Exception as e:
        logger.error("pipeline_run %s: %s", pipeline_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def pipeline_runs(request, pipeline_id):
    """Return run history for a pipeline."""
    p    = get_object_or_404(Pipeline, id=pipeline_id, created_by=request.user)
    runs = p.runs.order_by('-created_at')[:50]
    return JsonResponse({'success': True, 'runs': [_run_row(r) for r in runs]})
