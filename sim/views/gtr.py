# sim/views/gtr.py
"""
Endpoints GTR — Simulación en tiempo real.

POST /sim/gtr/start/                  → crear sesión GTR
GET  /sim/gtr/<sid>/tick/             → poll: avanzar clock + obtener estado
POST /sim/gtr/<sid>/pause/            → pausar
POST /sim/gtr/<sid>/resume/           → reanudar
POST /sim/gtr/<sid>/event/            → inyectar evento (spike, ausencia, etc.)
DELETE /sim/gtr/<sid>/stop/           → terminar sesión
GET  /sim/gtr/<sid>/state/            → estado completo sin avanzar
GET  /sim/gtr/<sid>/interactions/     → feed de interacciones paginado
GET  /sim/                            → panel GTR HTML
"""

import json
import logging
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from sim.models import SimAccount
from sim import gtr_engine as engine

logger = logging.getLogger(__name__)


@login_required
def gtr_panel(request):
    """Panel HTML del simulador GTR."""
    accounts = SimAccount.objects.filter(
        created_by=request.user, is_active=True
    ).exclude(canal='mixed').order_by('name')  # mixed needs all channels active

    all_accounts = SimAccount.objects.filter(
        created_by=request.user, is_active=True
    ).order_by('name')

    return render(request, 'sim/gtr.html', {
        'accounts':     all_accounts,
        'clock_speeds': [
            {'value': 5,  'label': '5×  (1 min → 5 min sim)'},
            {'value': 15, 'label': '15× (1 min → 15 min sim) — recomendado'},
            {'value': 60, 'label': '60× (1 min → 1 hora sim) — demo rápido'},
        ],
        'default_thresholds':          engine.DEFAULT_THRESHOLDS,
        'default_thresholds_outbound': engine.DEFAULT_THRESHOLDS_OUTBOUND,
    })


@login_required
@require_POST
def gtr_start(request):
    """Crea una nueva sesión GTR."""
    try:
        body        = json.loads(request.body)
        account_id  = body.get('account_id')
        clock_speed = int(body.get('clock_speed', 15))
        sim_date_s  = body.get('sim_date', str(date.today()))
        thresholds  = body.get('thresholds', None)

        account = get_object_or_404(SimAccount, id=account_id, created_by=request.user)
        sim_date = date.fromisoformat(sim_date_s)

        session = engine.create_session(
            account     = account,
            user        = request.user,
            clock_speed = clock_speed,
            sim_date    = sim_date,
            thresholds  = thresholds,
        )
        return JsonResponse({'success': True, 'session_id': session.session_id,
                             'state': engine._state_response(session, [], [])})
    except Exception as e:
        logger.error("gtr_start: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def gtr_tick(request, session_id):
    """
    Poll endpoint — avanza el clock y devuelve el nuevo estado.
    Llamado cada ~3-5 segundos por el cliente.
    """
    state = engine.tick(session_id)
    if 'error' in state:
        return JsonResponse({'success': False, **state}, status=404)
    return JsonResponse({'success': True, **state})


@login_required
@require_GET
def gtr_state(request, session_id):
    """Estado completo sin avanzar el clock."""
    session = engine.load_session(session_id)
    if not session:
        return JsonResponse({'success': False, 'error': 'session_not_found'}, status=404)
    return JsonResponse({'success': True, **engine._state_response(session, [], [])})


@login_required
@require_POST
def gtr_pause(request, session_id):
    state = engine.pause_session(session_id)
    if 'error' in state:
        return JsonResponse({'success': False, **state}, status=404)
    return JsonResponse({'success': True, **state})


@login_required
@require_POST
def gtr_resume(request, session_id):
    state = engine.resume_session(session_id)
    if 'error' in state:
        return JsonResponse({'success': False, **state}, status=404)
    return JsonResponse({'success': True, **state})


@login_required
@require_POST
def gtr_event(request, session_id):
    """
    Inyecta un evento manual en la simulación.
    Body: { "type": "volume_spike", "params": {"pct": 30} }
    """
    try:
        body = json.loads(request.body)
        state = engine.inject_event(
            session_id = session_id,
            event_type = body.get('type', ''),
            params     = body.get('params', {}),
        )
        if 'error' in state:
            return JsonResponse({'success': False, **state}, status=404)
        return JsonResponse({'success': True, **state})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def gtr_stop(request, session_id):
    """Termina la sesión GTR, persiste interacciones en BD y limpia Redis."""
    try:
        engine.persist_session(session_id)
    except Exception as e:
        logger.warning("gtr_stop persist error for %s: %s", session_id, e)
        engine.delete_session(session_id)
    return JsonResponse({'success': True})


@login_required
@require_GET
def gtr_interactions(request, session_id):
    """
    Devuelve las interacciones acumuladas.
    ?since=N   → solo las N en adelante (para feed incremental)
    """
    try:
        since = int(request.GET.get('since', 0))
        rows  = engine.get_interactions(session_id, since)
        return JsonResponse({
            'success':      True,
            'interactions': rows,
            'count':        len(rows),
            'next_since':   since + len(rows),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
