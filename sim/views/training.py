# sim/views/training.py
"""
SIM-5 — Training Mode.

Endpoints:
  GET  /sim/training/                                → Panel HTML
  GET  /sim/training/scenarios/api/                  → Lista JSON
  POST /sim/training/scenarios/create/               → Crear escenario
  POST /sim/training/scenarios/<id>/update/          → Editar escenario
  POST /sim/training/scenarios/<id>/delete/          → Eliminar
  POST /sim/training/scenarios/<id>/start/           → Iniciar sesión GTR + TrainingSession
  GET  /sim/training/sessions/api/                   → Sesiones del usuario
  POST /sim/training/sessions/<id>/complete/         → Finalizar + calcular score
  POST /sim/training/sessions/<id>/action/           → Registrar acción del trainee
  POST /sim/training/sessions/<id>/notes/            → Notas del trainer
"""

import json
import logging
import uuid as _uuid
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from sim.models import SimAccount, TrainingScenario, TrainingSession
from sim import gtr_engine as engine

logger = logging.getLogger(__name__)


# ─── Row helpers ──────────────────────────────────────────────────────────────

def _scenario_row(s: TrainingScenario, user=None) -> dict:
    return {
        'id':           str(s.id),
        'name':         s.name,
        'description':  s.description,
        'canal':        s.canal,
        'canal_label':  s.get_canal_display(),
        'difficulty':   s.difficulty,
        'difficulty_label': s.get_difficulty_display(),
        'account_id':   str(s.account_id) if s.account_id else None,
        'account_name': s.account.name if s.account else None,
        'clock_speed':  s.clock_speed,
        'thresholds':   s.thresholds,
        'events':       s.events,
        'expected_actions': s.expected_actions,
        'is_public':    s.is_public,
        'event_count':  s.event_count,
        'session_count':s.session_count,
        'is_mine':      s.created_by_id == (user.id if user else None),
        'created_at':   s.created_at.isoformat(),
        'updated_at':   s.updated_at.isoformat(),
    }


def _session_row(ts: TrainingSession) -> dict:
    return {
        'id':               str(ts.id),
        'scenario_id':      str(ts.scenario_id),
        'scenario_name':    ts.scenario.name,
        'scenario_canal':   ts.scenario.canal,
        'difficulty':       ts.scenario.difficulty,
        'difficulty_label': ts.scenario.get_difficulty_display(),
        'trainee':          ts.trainee.username,
        'gtr_session_id':   ts.gtr_session_id,
        'sim_date':         str(ts.sim_date) if ts.sim_date else None,
        'status':           ts.status,
        'status_label':     ts.get_status_display(),
        'score':            ts.score,
        'score_detail':     ts.score_detail,
        'alerts_count':     ts.alerts_count,
        'events_responded': ts.events_responded,
        'actions_log':      ts.actions_log,
        'final_kpis':       ts.final_kpis,
        'trainer_notes':    ts.trainer_notes,
        'started_at':       ts.started_at.isoformat(),
        'finished_at':      ts.finished_at.isoformat() if ts.finished_at else None,
    }


# ─── Score calculator ─────────────────────────────────────────────────────────

def _calculate_score(ts: TrainingSession, gtr_state: dict) -> dict:
    """
    Calcula el score de la sesión basado en:
    - KPIs finales vs thresholds del escenario
    - Alertas generadas (negativo)
    - Eventos respondidos (positivo)
    - Acciones registradas (positivo)
    """
    kpis = gtr_state.get('kpis', {})
    thr  = ts.scenario.thresholds
    canal = ts.scenario.canal

    score  = 100
    detail = {'base': 100}

    # ── Penalización por alertas ──────────────────────────────────────────────
    n_alerts = ts.alerts_count
    alert_penalty = min(40, n_alerts * 8)
    score -= alert_penalty
    detail['alert_penalty'] = -alert_penalty

    # ── KPIs finales ──────────────────────────────────────────────────────────
    if canal == 'outbound':
        contact = kpis.get('contact_pct', 0)
        contact_min = thr.get('contact_min', 22)
        if contact >= contact_min:
            score += 10
            detail['contact_bonus'] = 10
        else:
            penalty = min(20, int((contact_min - contact) * 2))
            score -= penalty
            detail['contact_penalty'] = -penalty

        ventas = kpis.get('ventas', 0)
        if ventas > 0:
            conv_bonus = min(10, ventas // 10)
            score += conv_bonus
            detail['conv_bonus'] = conv_bonus
    else:
        sl = kpis.get('sl_pct', 0)
        sl_min = thr.get('sl_min', 80)
        if sl >= sl_min:
            score += 10
            detail['sl_bonus'] = 10
        else:
            penalty = min(20, int((sl_min - sl) * 1.5))
            score -= penalty
            detail['sl_penalty'] = -penalty

    # ── Acciones registradas ──────────────────────────────────────────────────
    n_actions = len(ts.actions_log)
    action_bonus = min(15, n_actions * 5)
    score += action_bonus
    detail['action_bonus'] = action_bonus

    # ── Eventos respondidos ───────────────────────────────────────────────────
    responded_bonus = ts.events_responded * 5
    score += responded_bonus
    detail['events_responded_bonus'] = responded_bonus

    score = max(0, min(100, score))
    detail['total'] = score
    return detail


# ═══════════════════════════════════════════════════════════════════════════════
# Views
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def training_panel(request):
    """Panel HTML de Training Mode."""
    # Escenarios propios + públicos
    scenarios = TrainingScenario.objects.filter(
        created_by=request.user
    ) | TrainingScenario.objects.filter(is_public=True)
    scenarios = scenarios.distinct().select_related('account', 'created_by')

    # Sesiones recientes del usuario
    my_sessions = TrainingSession.objects.filter(
        trainee=request.user
    ).select_related('scenario').order_by('-started_at')[:20]

    # Cuentas disponibles para crear escenarios
    accounts = SimAccount.objects.filter(
        created_by=request.user, is_active=True
    ).order_by('name')

    return render(request, 'sim/training.html', {
        'scenarios':   scenarios,
        'my_sessions': my_sessions,
        'accounts':    accounts,
        'canal_choices': [
            ('inbound',  'Inbound Voz'),
            ('outbound', 'Outbound Discador'),
        ],
        'difficulty_choices': [
            ('easy',   'Básico'),
            ('medium', 'Intermedio'),
            ('hard',   'Avanzado'),
        ],
        'clock_speeds': [
            {'value': 5,  'label': '5×'},
            {'value': 15, 'label': '15× (recomendado)'},
            {'value': 60, 'label': '60× (demo)'},
        ],
        'event_types': [
            ('volume_spike',  '🔺 Pico de volumen'),
            ('agent_absent',  '🚨 Agentes ausentes'),
            ('sl_drop',       '⚠️ Caída de SL'),
            ('reset_kpis',    '🔄 Reiniciar KPIs'),
        ],
    })


@login_required
@require_GET
def scenario_list_api(request):
    scenarios = (
        TrainingScenario.objects.filter(created_by=request.user) |
        TrainingScenario.objects.filter(is_public=True)
    ).distinct().select_related('account', 'created_by')
    return JsonResponse({
        'success':   True,
        'scenarios': [_scenario_row(s, request.user) for s in scenarios],
    })


@login_required
@require_POST
def scenario_create(request):
    try:
        body = json.loads(request.body)
        name = (body.get('name') or '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'El nombre es requerido.'}, status=400)

        account_id = body.get('account_id') or None
        account    = None
        if account_id:
            account = get_object_or_404(SimAccount, id=account_id, created_by=request.user)

        scenario = TrainingScenario.objects.create(
            name             = name,
            description      = (body.get('description') or '').strip(),
            canal            = body.get('canal', 'inbound'),
            difficulty       = body.get('difficulty', 'medium'),
            account          = account,
            clock_speed      = int(body.get('clock_speed', 15)),
            thresholds       = body.get('thresholds', {}),
            events           = body.get('events', []),
            expected_actions = body.get('expected_actions', []),
            is_public        = bool(body.get('is_public', False)),
            created_by       = request.user,
        )
        logger.info("TrainingScenario created: %s by %s", scenario.id, request.user)
        return JsonResponse({'success': True, 'scenario': _scenario_row(scenario, request.user)})
    except Exception as e:
        logger.error("scenario_create: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def scenario_update(request, scenario_id):
    scenario = get_object_or_404(TrainingScenario, id=scenario_id, created_by=request.user)
    try:
        body = json.loads(request.body)

        account_id = body.get('account_id') or None
        account    = None
        if account_id:
            account = get_object_or_404(SimAccount, id=account_id, created_by=request.user)

        scenario.name             = (body.get('name') or scenario.name).strip()
        scenario.description      = (body.get('description') or '').strip()
        scenario.canal            = body.get('canal', scenario.canal)
        scenario.difficulty       = body.get('difficulty', scenario.difficulty)
        scenario.account          = account
        scenario.clock_speed      = int(body.get('clock_speed', scenario.clock_speed))
        scenario.thresholds       = body.get('thresholds', scenario.thresholds)
        scenario.events           = body.get('events', scenario.events)
        scenario.expected_actions = body.get('expected_actions', scenario.expected_actions)
        scenario.is_public        = bool(body.get('is_public', scenario.is_public))
        scenario.save()
        return JsonResponse({'success': True, 'scenario': _scenario_row(scenario, request.user)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def scenario_delete(request, scenario_id):
    scenario = get_object_or_404(TrainingScenario, id=scenario_id, created_by=request.user)
    scenario.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def session_start(request, scenario_id):
    """
    Crea una TrainingSession + la sesión GTR subyacente.
    Devuelve session_id (TrainingSession) y gtr_session_id para el cliente GTR.
    """
    scenario = get_object_or_404(
        TrainingScenario.objects.filter(
            created_by=request.user
        ) | TrainingScenario.objects.filter(is_public=True),
        id=scenario_id,
    )
    try:
        body     = json.loads(request.body)
        sim_date_s = body.get('sim_date', str(date.today()))
        sim_date   = date.fromisoformat(sim_date_s)

        # Cuenta: preferir la del escenario, fallback a primera del usuario
        account = scenario.account
        if not account:
            account = SimAccount.objects.filter(
                created_by=request.user, is_active=True,
                canal=scenario.canal
            ).first()
            if not account:
                return JsonResponse(
                    {'success': False,
                     'error': 'No hay cuenta sim disponible para este canal. Crea una primero.'},
                    status=400)

        thresholds = scenario.thresholds or None

        gtr_session = engine.create_session(
            account     = account,
            user        = request.user,
            clock_speed = scenario.clock_speed,
            sim_date    = sim_date,
            thresholds  = thresholds,
        )

        ts = TrainingSession.objects.create(
            scenario       = scenario,
            trainee        = request.user,
            gtr_session_id = gtr_session.session_id,
            sim_date       = sim_date,
            status         = 'active',
        )

        logger.info("TrainingSession started: %s | scenario=%s | user=%s",
                    ts.id, scenario.name, request.user)

        return JsonResponse({
            'success':        True,
            'session':        _session_row(ts),
            'gtr_session_id': gtr_session.session_id,
            'gtr_state':      engine._state_response(gtr_session, [], []),
            'scenario':       _scenario_row(scenario, request.user),
        })
    except Exception as e:
        logger.error("session_start: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def session_list_api(request):
    sessions = TrainingSession.objects.filter(
        trainee=request.user
    ).select_related('scenario').order_by('-started_at')[:50]
    return JsonResponse({
        'success':  True,
        'sessions': [_session_row(s) for s in sessions],
    })


@login_required
@require_POST
def session_complete(request, session_id):
    """
    Finaliza la sesión, captura KPIs y calcula score.
    Body: { "gtr_session_id": "..." }  → se usa para obtener estado final del GTR.
    """
    ts = get_object_or_404(TrainingSession, id=session_id, trainee=request.user)
    try:
        body = json.loads(request.body)

        # Obtener estado final del GTR
        gtr_state = {}
        gtr_sid   = ts.gtr_session_id or body.get('gtr_session_id', '')
        if gtr_sid:
            gtr_session = engine.load_session(gtr_sid)
            if gtr_session:
                gtr_state = engine._state_response(gtr_session, [], [])
                # Parar la sesión GTR
                engine.delete_session(gtr_sid)

        # Actualizar contadores desde body (el cliente sabe cuántas alertas hubo)
        ts.alerts_count     = int(body.get('alerts_count', ts.alerts_count))
        ts.events_responded = int(body.get('events_responded', ts.events_responded))
        ts.final_kpis       = gtr_state.get('kpis', {})

        # Calcular score
        score_detail = _calculate_score(ts, gtr_state)
        ts.score        = score_detail['total']
        ts.score_detail = score_detail
        ts.status       = 'completed'
        ts.finished_at  = timezone.now()
        ts.save()

        logger.info("TrainingSession completed: %s | score=%d | user=%s",
                    ts.id, ts.score, request.user)

        return JsonResponse({'success': True, 'session': _session_row(ts)})
    except Exception as e:
        logger.error("session_complete: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def session_log_action(request, session_id):
    """Registra una acción del trainee durante la sesión activa."""
    ts = get_object_or_404(TrainingSession, id=session_id, trainee=request.user)
    if ts.status != 'active':
        return JsonResponse({'success': False, 'error': 'La sesión no está activa.'}, status=400)
    try:
        body   = json.loads(request.body)
        action = (body.get('action') or '').strip()
        if not action:
            return JsonResponse({'success': False, 'error': 'Acción vacía.'}, status=400)

        entry = {
            'sim_time':  body.get('sim_time', ''),
            'real_ts':   datetime.now().isoformat(),
            'action':    action,
            'event_ref': body.get('event_ref', None),
        }
        ts.actions_log = ts.actions_log + [entry]

        # Si el trainee referencia un evento del escenario → incrementar contador
        if entry['event_ref'] is not None:
            ts.events_responded = ts.events_responded + 1

        ts.save(update_fields=['actions_log', 'events_responded'])
        return JsonResponse({'success': True, 'entry': entry, 'total_actions': len(ts.actions_log)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def session_trainer_notes(request, session_id):
    """El trainer (creador del escenario) agrega notas a una sesión completada."""
    ts = get_object_or_404(TrainingSession, id=session_id)
    # Solo el creador del escenario puede agregar notas
    if ts.scenario.created_by != request.user and ts.trainee != request.user:
        return JsonResponse({'success': False, 'error': 'Sin permiso.'}, status=403)
    try:
        body  = json.loads(request.body)
        notes = (body.get('notes') or '').strip()
        ts.trainer_notes = notes
        ts.save(update_fields=['trainer_notes'])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
