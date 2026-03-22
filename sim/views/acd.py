# sim/views/acd.py
"""
SIM-7a — ACD Simulator.

Motor de enrutamiento + endpoints para sesión multi-agente.

Endpoints Trainer:
  GET  /sim/acd/                              → panel trainer HTML
  POST /sim/acd/sessions/create/              → crear sesión ACD
  GET  /sim/acd/sessions/<id>/state/          → estado completo (KPIs + grid agentes)
  POST /sim/acd/sessions/<id>/start/          → iniciar (crea GTR subyacente)
  POST /sim/acd/sessions/<id>/pause/          → pausar
  POST /sim/acd/sessions/<id>/resume/         → reanudar
  POST /sim/acd/sessions/<id>/stop/           → finalizar
  POST /sim/acd/sessions/<id>/slots/add/      → agregar slot de agente
  POST /sim/acd/sessions/<id>/slots/<sid>/remove/ → quitar slot
  POST /sim/acd/sessions/<id>/slots/<sid>/control/ → forzar estado de un slot
  GET  /sim/acd/sessions/<id>/interactions/   → feed interacciones paginado
  GET  /sim/acd/sessions/api/                 → lista sesiones del usuario

Endpoints Agente OJT:
  GET  /sim/acd/agent/<slot_id>/              → pantalla agente (básico/intermedio/avanzado)
  GET  /sim/acd/agent/<slot_id>/poll/         → poll: obtener interacción activa + estado
  POST /sim/acd/agent/<slot_id>/action/       → registrar acción (answer, tipify, hold, etc.)
"""

import json
import logging
import random
import uuid as _uuid
from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from sim.models import (
    SimAccount, SimAgentProfile,
    ACDSession, ACDAgentSlot, ACDInteraction, ACDAgentAction,
)
from sim import gtr_engine as engine
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger(__name__)


# ─── Row helpers ──────────────────────────────────────────────────────────────

def _session_row(s: ACDSession) -> dict:
    return {
        'id':            str(s.id),
        'name':          s.name,
        'account_id':    str(s.account_id),
        'account_name':  s.account.name,
        'dialing_mode':  s.dialing_mode,
        'dialing_label': s.get_dialing_mode_display(),
        'canal':         s.canal,
        'clock_speed':   s.clock_speed,
        'sim_date':      str(s.sim_date) if s.sim_date else None,
        'status':        s.status,
        'status_label':  s.get_status_display(),
        'gtr_session_id':s.gtr_session_id,
        'slot_count':    s.slot_count,
        'active_agents': s.active_agents,
        'started_at':    s.started_at.isoformat(),
        'finished_at':   s.finished_at.isoformat() if s.finished_at else None,
    }


def _slot_row(slot: ACDAgentSlot) -> dict:
    s = slot.stats or {}
    return {
        'id':          str(slot.id),
        'slot_number': slot.slot_number,
        'agent_type':  slot.agent_type,
        'name':        slot.name,
        'skill':       slot.skill,
        'status':      slot.status,
        'status_label':slot.get_status_display(),
        'level':       slot.level,
        'level_label': slot.get_level_display(),
        'user_id':     slot.user_id,
        'profile_id':  str(slot.profile_id) if slot.profile_id else None,
        'profile_tier':slot.profile.tier if slot.profile else None,
        # KPIs acumulados
        'atendidas':   s.get('atendidas', 0),
        'ventas':      s.get('ventas', 0),
        'no_contacto': s.get('no_contacto', 0),
        'aht_s':       slot.aht_s,
        'aht_min':     round(slot.aht_s / 60, 2),
        'hold_count':  s.get('hold_count', 0),
        'transfer_count':   s.get('transfer_count', 0),
        'conference_count': s.get('conference_count', 0),

      
      
    }


def _interaction_row(ix: ACDInteraction) -> dict:
    return {
        'id':            str(ix.id),
        'canal':         ix.canal,
        'skill':         ix.skill,
        'lead_id':       ix.lead_id,
        'status':        ix.status,
        'status_label':  ix.get_status_display(),
        'slot_id':       str(ix.slot_id) if ix.slot_id else None,
        'slot_name':     ix.slot.name if ix.slot else None,
        'queued_at':     ix.queued_at.isoformat(),
        'answered_at':   ix.answered_at.isoformat() if ix.answered_at else None,
        'ended_at':      ix.ended_at.isoformat() if ix.ended_at else None,
        'wait_s':        ix.wait_s,
        'duration_s':    ix.duration_s,
        'acw_s':         ix.acw_s,
        'hold_s':        ix.hold_s,
        'tipificacion':  ix.tipificacion,
    }


# ─── ACD State response ───────────────────────────────────────────────────────

def _acd_state(session: ACDSession, gtr_state: dict = None) -> dict:
    """Estado completo de la sesión ACD para el panel del trainer."""
    slots = list(session.slots.select_related('user', 'profile').order_by('slot_number'))
    interactions = ACDInteraction.objects.filter(
        session=session
    ).exclude(status__in=['completed', 'abandoned', 'rejected']).select_related('slot')

    # KPIs globales
    all_ix = ACDInteraction.objects.filter(session=session)
    total       = all_ix.count()
    atendidas   = all_ix.filter(status='completed').count()
    ventas      = all_ix.filter(tipificacion__icontains='venta').count()
    en_cola     = all_ix.filter(status__in=['queued','ringing']).count()
    en_llamada  = all_ix.filter(status='on_call').count()
    en_acw      = slots_in_status(slots, 'acw')
    disponibles = slots_in_status(slots, 'available')
    en_break    = slots_in_status(slots, 'break')
    ausentes    = slots_in_status(slots, 'absent')

    return {
        'session':    _session_row(session),
        'slots':      [_slot_row(s) for s in slots],
        'queue':      [_interaction_row(ix) for ix in interactions if ix.status in ('queued','ringing')],
        'kpis': {
            'total':       total,
            'atendidas':   atendidas,
            'na_pct':      round(atendidas / total * 100, 1) if total else 0,
            'ventas':      ventas,
            'en_cola':     en_cola,
            'en_llamada':  en_llamada,
            'en_acw':      en_acw,
            'disponibles': disponibles,
            'en_break':    en_break,
            'ausentes':    ausentes,
        },
        'gtr': gtr_state or {},
    }


def slots_in_status(slots, status):
    return sum(1 for s in slots if s.status == status)


# ─── Routing engine ───────────────────────────────────────────────────────────

def _route_interaction(session: ACDSession, interaction: ACDInteraction) -> ACDAgentSlot | None:
    """
    Encuentra el mejor slot disponible para una interacción.
    Prioriza:
      1. Mismo skill que la interacción
      2. Agentes reales OJT primero (para que practiquen)
      3. Menor carga acumulada
    """
    available = list(
        session.slots.filter(status='available').select_related('user', 'profile')
    )
    if not available:
        return None

    # Filtrar por skill si hay match
    skill_match = [s for s in available if s.skill == interaction.skill]
    pool = skill_match if skill_match else available

    # Preferir agentes reales para práctica
    real_slots = [s for s in pool if s.agent_type == 'real']
    if real_slots:
        pool = real_slots

    # Menor carga (atendidas acumuladas)
    pool.sort(key=lambda s: s.stats.get('atendidas', 0))
    return pool[0]


def _generate_acd_interactions(session: ACDSession, n: int = 5) -> list:
    """
    Genera N interacciones sintéticas para encolar en la sesión ACD.
    Usa la configuración de la cuenta.
    """
    from sim.generators.base import weighted_choice, synthetic_lead_id

    try:
        account_config = session.account.config or {}
        cfg = account_config.get(session.canal, {})
    except Exception:
        cfg = {}

    # Fallbacks por canal para que skill sea siempre coherente con la cuenta
    if session.canal == 'inbound':
        default_skills = {'GENERAL': {'weight': 1.0}}
    elif session.canal == 'outbound':
        default_skills = {'OUTBOUND': {'weight': 1.0}}
    else:  # digital
        default_skills = {'DIGITAL': {'weight': 1.0}}

    skills_cfg = cfg.get('skills', default_skills)
    skill_weights = {k: v.get('weight', 1.0) for k, v in skills_cfg.items()}

    interactions = []
    for i in range(n):
        skill  = weighted_choice(skill_weights)
        lead   = synthetic_lead_id(session.canal, random.randint(1, 999999))
        ix = ACDInteraction.objects.create(
            session      = session,
            canal        = session.canal,
            skill        = skill,
            lead_id      = lead,
            status       = 'queued',
            is_simulated = True,
        )
        interactions.append(ix)
    return interactions


# ─── SIM-7e helpers ───────────────────────────────────────────────────────────

# Segundos simulados estimados por ciclo de routing (clock_speed × poll_real_s ≈ 60).
# Usado en _tick_simulated_breaks para convertir break_freq [breaks/h] a P(break/tick).
SIM_TICK_S = 60


def _get_account_tmo_acw(session: ACDSession) -> tuple:
    """
    Retorna (tmo_s, acw_s) base desde la config de la cuenta según canal.
    SIM-7e — antes hardcodeados en _resolve_simulated_slot (313/18 inbound siempre).
    """
    try:
        cfg = (session.account.config or {}).get(session.canal, {})
    except Exception:
        cfg = {}
    if session.canal == 'inbound':
        return cfg.get('tmo_s', 313), cfg.get('acw_s', 18)
    elif session.canal == 'outbound':
        return cfg.get('tmo_s', 180), cfg.get('acw_s', 12)
    elif session.canal == 'digital':
        return cfg.get('duration_s', 240), cfg.get('acw_s', 10)
    return 313, 18


def _resolve_tipificacion(session: ACDSession, conv_rate: float, agenda_rate: float) -> str:
    """
    Tipificación realista basada en la config de la cuenta y el canal.
    SIM-7e — antes solo retornaba 'Venta' o 'Atendida' ignorando la cuenta.
    """
    from sim.generators.base import weighted_choice
    try:
        cfg = (session.account.config or {}).get(session.canal, {})
    except Exception:
        cfg = {}

    if session.canal == 'inbound':
        all_tipifs = {}
        for skill_data in cfg.get('skills', {}).values():
            all_tipifs.update(skill_data.get('tipificaciones', {}))
        if all_tipifs:
            return weighted_choice(all_tipifs)

    elif session.canal == 'outbound':
        contact_rate = cfg.get('contact_rate', 0.276)
        if random.random() > contact_rate:
            no_contact = cfg.get('tipif_no_contacto', {})
            return weighted_choice(no_contact) if no_contact else 'No contesta'
        tipif_contacto = cfg.get('tipif_contacto', {})
        if tipif_contacto:
            return weighted_choice(tipif_contacto)
        r = random.random()
        if r < conv_rate:
            return 'Venta'
        if r < conv_rate + agenda_rate:
            return 'Agenda'
        return 'No interesado'

    elif session.canal == 'digital':
        tipifs = {}
        tipifs.update(cfg.get('tipificaciones_bxi', {}))
        tipifs.update(cfg.get('tipificaciones_app', {}))
        if not tipifs:
            tipifs = cfg.get('tipificaciones', {})
        if tipifs:
            return weighted_choice(tipifs)

    # fallback genérico
    if random.random() < conv_rate:
        return 'Venta'
    return 'Atendida'


def _tick_simulated_breaks(session: ACDSession):
    """
    Aplica breaks espontáneos y retornos a agentes simulados según su perfil.
    Llamado en cada ciclo de routing — diferencia tiers en sesiones largas.

    SIM-7e — implementa break_freq y break_dur_s del SimAgentProfile que antes no se usaban.

    P(ir a break en este tick)  = break_freq [breaks/h] × SIM_TICK_S / 3600
    P(volver de break en tick)  = SIM_TICK_S / break_dur_s
    """
    for slot in session.slots.filter(agent_type__in=('simulated', 'bot')).select_related('profile'):  # BOT-2
        profile = slot.profile
        if not profile:
            continue
        if slot.status == 'available':
            p_break = profile.break_freq * SIM_TICK_S / 3600
            if random.random() < p_break:
                slot.status = 'break'
                slot.save(update_fields=['status'])
        elif slot.status == 'break':
            p_return = SIM_TICK_S / max(profile.break_dur_s, SIM_TICK_S)
            if random.random() < p_return:
                slot.status = 'available'
                slot.save(update_fields=['status'])


def _resolve_simulated_slot(slot: ACDAgentSlot, interaction: ACDInteraction,
                             _from_transfer: bool = False):
    """
    Resuelve automáticamente una interacción para un agente simulado
    según su perfil conductual (SimAgentProfile).

    SIM-7e: usa TMO/ACW de la cuenta, tipificaciones reales por canal,
    transfer_rate activo y available_pct post-llamada.
    """
    profile = slot.profile
    now = timezone.now()
    session = slot.session  # FK — cacheado tras el primer acceso

    # Parámetros conductuales del perfil (defaults = agente medio sin perfil)
    answer_rate   = profile.answer_rate   if profile else 0.93
    conv_rate     = profile.conv_rate     if profile else 0.008
    agenda_rate   = profile.agenda_rate   if profile else 0.128
    hold_rate     = profile.hold_rate     if profile else 0.05
    hold_dur_s    = profile.hold_dur_s    if profile else 30
    aht_factor    = profile.aht_factor    if profile else 1.0
    acw_factor    = profile.acw_factor    if profile else 1.0
    corte_rate    = profile.corte_rate    if profile else 0.05
    transfer_rate = profile.transfer_rate if profile else 0.04
    available_pct = profile.available_pct if profile else 0.85

    # TMO/ACW base desde la cuenta según canal (SIM-7e)
    base_tmo_account, base_acw_account = _get_account_tmo_acw(session)

    # Rechaza?
    if random.random() > answer_rate:
        interaction.status   = 'rejected'
        interaction.ended_at = now
        interaction.save(update_fields=['status', 'ended_at'])
        slot.status = 'available'
        slot.save(update_fields=['status'])
        return

    # Atiende
    interaction.answered_at = now
    interaction.status = 'on_call'

    base_tmo = base_tmo_account * aht_factor
    dur_s = max(30, int(random.gauss(base_tmo, base_tmo * 0.15)))

    hold_s = 0
    if random.random() < hold_rate:
        hold_s = max(10, int(random.gauss(hold_dur_s, hold_dur_s * 0.3)))

    acw_base = base_acw_account * acw_factor
    acw_s = max(5, int(random.gauss(acw_base, acw_base * 0.3)))

    if random.random() < corte_rate:
        acw_s = 0

    # Transferencia (SIM-7e — transfer_rate antes leído pero nunca aplicado)
    if not _from_transfer and random.random() < transfer_rate:
        target = ACDAgentSlot.objects.filter(
            session=session, status='available'
        ).exclude(id=slot.id).first()
        if target:
            interaction.slot = target
            interaction.save(update_fields=['slot'])
            target.status = 'ringing'
            target.save(update_fields=['status'])
            stats = slot.stats or {}
            stats['transfer_count'] = stats.get('transfer_count', 0) + 1
            slot.stats  = stats
            slot.status = 'available'
            slot.save(update_fields=['stats', 'status'])
            # Resolver en el destino si también es simulado
            if target.agent_type in ('simulated', 'bot'):  # BOT-2
                _resolve_simulated_slot(target, interaction, _from_transfer=True)
            return

    # Tipificación rica por canal (SIM-7e — antes solo 'Venta' o 'Atendida')
    tipif = _resolve_tipificacion(session, conv_rate, agenda_rate)

    interaction.duration_s   = dur_s
    interaction.hold_s       = hold_s
    interaction.acw_s        = acw_s
    interaction.tipificacion = tipif
    interaction.status       = 'completed'
    interaction.ended_at     = now + timedelta(seconds=dur_s + acw_s)
    interaction.save()

    # Stats del slot
    stats = slot.stats or {}
    stats['atendidas'] = stats.get('atendidas', 0) + 1
    stats['tmo_sum_s'] = stats.get('tmo_sum_s', 0) + dur_s
    stats['tmo_count'] = stats.get('tmo_count', 0) + 1
    if tipif == 'Venta':
        stats['ventas'] = stats.get('ventas', 0) + 1
    if hold_s:
        stats['hold_count'] = stats.get('hold_count', 0) + 1
    slot.stats = stats
    # Post-llamada: vuelve a available o toma break según available_pct del perfil (SIM-7e)
    slot.status = 'available' if random.random() < available_pct else 'break'
    slot.save(update_fields=['stats', 'status'])


# ═══════════════════════════════════════════════════════════════════════════════
# VIEWS — Trainer
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def acd_panel(request):
    """Panel HTML del trainer ACD."""
    sessions  = ACDSession.objects.filter(
        created_by=request.user
    ).select_related('account').order_by('-started_at')[:20]
    accounts  = SimAccount.objects.filter(
        created_by=request.user, is_active=True
    ).order_by('name')
    profiles  = SimAgentProfile.objects.all().order_by('tier', 'canal', 'name')

    users = User.objects.filter(is_active=True).order_by('username')

    return render(request, 'sim/acd_trainner.html', {
        'sessions':      sessions,
        'accounts':      accounts,
        'profiles':      profiles,
        'users':         users,
        'dialing_modes': [
            ('predictive',  '⚡ Predictivo'),
            ('progressive', '➡️ Progresivo'),
            ('manual',      '🖐 Manual'),
        ],
        'agent_levels': [
            ('basic',        'Básico — botones'),
            ('intermediate', 'Intermedio — tipificación'),
            ('advanced',     'Avanzado — multi-skill'),
        ],
    })


@login_required
@require_GET
def acd_sessions_api(request):
    sessions = ACDSession.objects.filter(
        created_by=request.user
    ).select_related('account').order_by('-started_at')[:50]
    return JsonResponse({'success': True, 'sessions': [_session_row(s) for s in sessions]})


@login_required
@require_POST
def acd_session_create(request):
    try:
        body = json.loads(request.body)
        name = (body.get('name') or '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'El nombre es requerido.'}, status=400)

        account = get_object_or_404(SimAccount, id=body['account_id'], created_by=request.user)

        session = ACDSession.objects.create(
            name         = name,
            account      = account,
            dialing_mode = body.get('dialing_mode', 'progressive'),
            canal        = account.canal,
            clock_speed  = int(body.get('clock_speed', 15)),
            thresholds   = body.get('thresholds', {}),
            config       = body.get('config', {}),
            created_by   = request.user,
        )
        logger.info("ACDSession created: %s | %s", session.id, session.name)
        return JsonResponse({'success': True, 'session': _session_row(session)})
    except Exception as e:
        logger.error("acd_session_create: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def acd_session_start(request, session_id):
    """Inicia la sesión: crea la GTR subyacente y pone todos los slots en available."""
    session = get_object_or_404(ACDSession, id=session_id, created_by=request.user)
    try:
        body     = json.loads(request.body)
        sim_date = date.fromisoformat(body.get('sim_date', str(date.today())))

        # Crear sesión GTR subyacente
        gtr = engine.create_session(
            account     = session.account,
            user        = request.user,
            clock_speed = session.clock_speed,
            sim_date    = sim_date,
            thresholds  = session.thresholds or None,
        )

        session.gtr_session_id = gtr.session_id
        session.sim_date       = sim_date
        session.status         = 'active'
        session.save(update_fields=['gtr_session_id', 'sim_date', 'status'])

        # Activar todos los slots configurados
        session.slots.filter(status='offline').update(status='available')

        # Generar primera tanda de interacciones en cola
        _generate_acd_interactions(session, n=max(3, session.slot_count))

        gtr_state = engine._state_response(gtr, [], [])
        return JsonResponse({
            'success':   True,
            'session':   _session_row(session),
            'gtr_state': gtr_state,
        })
    except Exception as e:
        logger.error("acd_session_start: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def acd_session_state(request, session_id):
    """Estado completo de la sesión: KPIs + grid agentes + cola."""
    session = get_object_or_404(ACDSession, id=session_id, created_by=request.user)

    gtr_state = {}
    if session.gtr_session_id:
        try:
            gtr_state = engine.tick(session.gtr_session_id)
        except Exception as e:
            logger.warning("ACD GTR tick error: %s", e)

    # Capturar estado ANTES del routing — la cola es visible un tick completo
    state = _acd_state(session, gtr_state)

    # Routing después del snapshot para evitar parpadeo de cola
    if session.status == 'active':
        try:
            _do_routing(session, gtr_state)
        except Exception as e:
            logger.warning("ACD routing error: %s", e)

    return JsonResponse({'success': True, **state})


def _do_routing(session: ACDSession, gtr_state: dict):
    """
    Motor de enrutamiento: asigna interacciones en cola a slots disponibles.
    Modo predictivo/progresivo: automático.
    Modo manual: solo outbound, el agente decide.
    """
    if session.dialing_mode == 'manual' and session.canal == 'outbound':
        return  # el agente controla el marcado

    # SIM-7e — breaks espontáneos en agentes simulados antes del routing
    _tick_simulated_breaks(session)

    queued = list(ACDInteraction.objects.filter(
        session=session, status='queued'
    ).select_related('slot')[:20])

    if not queued:
        # Generar más interacciones si la cola está vacía
        available_count = session.slots.filter(status='available').count()
        if available_count > 0:
            _generate_acd_interactions(session, n=available_count + 2)
        return

    for ix in queued:
        slot = _route_interaction(session, ix)
        if not slot:
            break

        ix.slot        = slot
        ix.assigned_at = timezone.now()
        ix.status      = 'ringing'
        ix.save(update_fields=['slot', 'assigned_at', 'status'])

        slot.status = 'ringing'
        slot.save(update_fields=['status'])

        # Simulated agents: resolve immediately
        if slot.agent_type in ('simulated', 'bot'):  # BOT-2
            _resolve_simulated_slot(slot, ix)


@login_required
@require_POST
def acd_session_pause(request, session_id):
    session = get_object_or_404(ACDSession, id=session_id, created_by=request.user)
    session.status = 'paused'
    session.save(update_fields=['status'])
    if session.gtr_session_id:
        engine.pause_session(session.gtr_session_id)
    return JsonResponse({'success': True, 'session': _session_row(session)})


@login_required
@require_POST
def acd_session_resume(request, session_id):
    session = get_object_or_404(ACDSession, id=session_id, created_by=request.user)
    session.status = 'active'
    session.save(update_fields=['status'])
    if session.gtr_session_id:
        engine.resume_session(session.gtr_session_id)
    return JsonResponse({'success': True, 'session': _session_row(session)})


@login_required
@require_POST
def acd_session_stop(request, session_id):
    session = get_object_or_404(ACDSession, id=session_id, created_by=request.user)
    session.status      = 'finished'
    session.finished_at = timezone.now()
    session.save(update_fields=['status', 'finished_at'])
    if session.gtr_session_id:
        try:
            engine.persist_session(session.gtr_session_id)
        except Exception as e:
            logger.warning("ACD persist error: %s", e)
    return JsonResponse({'success': True})


@login_required
@require_POST
def acd_slot_add(request, session_id):
    session = get_object_or_404(ACDSession, id=session_id, created_by=request.user)
    try:
        body = json.loads(request.body)
        next_num = (session.slots.order_by('-slot_number').first().slot_number + 1
                    if session.slots.exists() else 1)

        agent_type = body.get('agent_type', 'simulated')
        user_id    = body.get('user_id')
        profile_id = body.get('profile_id')

        slot = ACDAgentSlot.objects.create(
            session      = session,
            slot_number  = next_num,
            agent_type   = agent_type,
            user         = User.objects.get(id=user_id) if user_id else None,
            profile      = SimAgentProfile.objects.get(id=profile_id) if profile_id else None,
            display_name = body.get('display_name', ''),
            skill        = body.get('skill', ''),
            level        = body.get('level', 'basic'),
            status       = 'available' if session.status == 'active' else 'offline',
            stats        = {},
        )
        return JsonResponse({'success': True, 'slot': _slot_row(slot)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def acd_slot_remove(request, session_id, slot_id):
    session = get_object_or_404(ACDSession, id=session_id, created_by=request.user)
    slot    = get_object_or_404(ACDAgentSlot, id=slot_id, session=session)
    # No eliminar si tiene interacciones activas
    if slot.acd_interactions.filter(status__in=['on_call', 'ringing', 'acw']).exists():
        return JsonResponse({'success': False, 'error': 'Agente con interacción activa.'}, status=400)
    slot.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def acd_slot_control(request, session_id, slot_id):
    """Trainer fuerza estado de un slot: break, return, absent, available."""
    session = get_object_or_404(ACDSession, id=session_id, created_by=request.user)
    slot    = get_object_or_404(ACDAgentSlot, id=slot_id, session=session)
    try:
        body   = json.loads(request.body)
        status = body.get('status')
        if status not in ['available', 'break', 'absent', 'offline']:
            return JsonResponse({'success': False, 'error': 'Estado inválido.'}, status=400)
        slot.status = status
        slot.save(update_fields=['status'])
        return JsonResponse({'success': True, 'slot': _slot_row(slot)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def acd_interactions(request, session_id):
    session = get_object_or_404(ACDSession, id=session_id, created_by=request.user)
    since   = request.GET.get('since', None)
    qs = ACDInteraction.objects.filter(session=session).select_related('slot')
    if since:
        qs = qs.filter(queued_at__gt=since)
    qs = qs.order_by('-queued_at')[:100]
    return JsonResponse({
        'success':      True,
        'interactions': [_interaction_row(ix) for ix in qs],
        'count':        qs.count(),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# VIEWS — Agente OJT
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def acd_agent_panel(request, slot_id):
    """Pantalla del agente OJT."""
    slot = get_object_or_404(
        ACDAgentSlot.objects.select_related('session', 'session__account', 'profile'),
        id=slot_id, user=request.user
    )
    tipificaciones = _get_tipificaciones(slot.session)
    return render(request, 'sim/acd_agent.html', {
        'slot':           slot,
        'session':        slot.session,
        'tipificaciones': tipificaciones,
        'level':          slot.level,
    })


@login_required
@require_GET
def acd_agent_poll(request, slot_id):
    """
    Poll del agente (cada 2s):
    - Estado del slot
    - Interacción activa (si existe)
    - Próxima en cola (para preview en pantalla básica)
    - Reloj GTR
    """
    slot = get_object_or_404(ACDAgentSlot, id=slot_id, user=request.user)
    session = slot.session

    # Interacción activa
    active_ix = ACDInteraction.objects.filter(
        slot=slot, status__in=['ringing', 'on_call', 'acw']
    ).first()

    # Próxima en cola (preview)
    next_queued = None
    if not active_ix and slot.status == 'available':
        next_queued = ACDInteraction.objects.filter(
            session=session, status='queued'
        ).first()

    # Reloj GTR
    gtr_time = '09:00'
    if session.gtr_session_id:
        gtr_sess = engine.load_session(session.gtr_session_id)
        if gtr_sess:
            h, m = gtr_sess.sim_time()
            gtr_time = f"{h:02d}:{m:02d}"
    # Slots disponibles para transfer/conference (nivel avanzado)
    available_slots = []
    if slot.level == 'advanced':
        qs_slots = ACDAgentSlot.objects.filter(
            session=session
        ).exclude(id=slot.id).select_related('user', 'profile')
        available_slots = [
            {'id': str(s.id), 'name': s.name,
             'status': s.status, 'skill': s.skill,
             'can_transfer': s.status not in ('absent', 'offline')}
            for s in qs_slots
        ]

    return JsonResponse({
        'success':         True,
        'slot':            _slot_row(slot),
        'active':          _interaction_row(active_ix) if active_ix else None,
        'next_queued':     _interaction_row(next_queued) if next_queued else None,
        'gtr_time':        gtr_time,
        'session_status':  session.status,
        'available_slots': available_slots,
    })


@login_required
@require_POST
def acd_agent_action(request, slot_id):
    """Registra una acción del agente OJT."""
    slot = get_object_or_404(ACDAgentSlot, id=slot_id, user=request.user)
    try:
        body        = json.loads(request.body)
        action_type = body.get('action_type', '')
        params      = body.get('params', {})
        ix_id       = body.get('interaction_id')

        # Obtener tiempo GTR actual
        gtr_time = '09:00'
        if slot.session.gtr_session_id:
            gtr_sess = engine.load_session(slot.session.gtr_session_id)
            if gtr_sess:
                h, m = gtr_sess.sim_time()
                gtr_time = f"{h:02d}:{m:02d}"

        ix = None
        if ix_id:
            ix = get_object_or_404(ACDInteraction, id=ix_id, slot=slot)

        now = timezone.now()

        # ── Procesar acción ───────────────────────────────────────────────────
        if action_type == 'answer' and ix:
            ix.answered_at = now
            ix.status      = 'on_call'
            ix.save(update_fields=['answered_at', 'status'])
            slot.status = 'on_call'
            slot.save(update_fields=['status'])

        elif action_type == 'reject' and ix:
            ix.status   = 'rejected'
            ix.ended_at = now
            ix.save(update_fields=['status', 'ended_at'])
            slot.status = 'available'
            slot.save(update_fields=['status'])

        elif action_type == 'hold' and ix:
            ix.status = 'on_call'   # sigue on_call, hold es visual
            ix.save(update_fields=['status'])

        elif action_type == 'tipify' and ix:
            ix.tipificacion     = params.get('tipificacion', '')
            ix.sub_tipificacion = params.get('sub_tipificacion', '')
            ix.notes            = params.get('notes', '')
            ix.save(update_fields=['tipificacion', 'sub_tipificacion', 'notes'])

        elif action_type == 'end_acw' and ix:
            ix.status   = 'completed'
            ix.ended_at = now
            dur_s = int((now - ix.answered_at).total_seconds()) if ix.answered_at else 0
            ix.duration_s = dur_s
            ix.save(update_fields=['status', 'ended_at', 'duration_s'])
            # Actualizar stats del slot
            stats = slot.stats or {}
            stats['atendidas'] = stats.get('atendidas', 0) + 1
            stats['tmo_sum_s'] = stats.get('tmo_sum_s', 0) + dur_s
            stats['tmo_count'] = stats.get('tmo_count', 0) + 1
            slot.stats  = stats
            slot.status = 'available'
            slot.save(update_fields=['stats', 'status'])

        elif action_type == 'break':
            slot.status = 'break'
            slot.save(update_fields=['status'])

        elif action_type == 'return':
            slot.status = 'available'
            slot.save(update_fields=['status'])

        elif action_type == 'transfer' and ix:
            to_slot_id = params.get('to_slot_id')
            if to_slot_id:
                try:
                    to_slot = ACDAgentSlot.objects.get(id=to_slot_id, session=slot.session)
                    # Fix C: no transferir a agentes no operativos
                    if to_slot.status in ('absent', 'offline'):
                        return JsonResponse(
                            {'success': False, 'error': 'El agente destino no está disponible.'},
                            status=400
                        )
                    ix.slot = to_slot
                    ix.save(update_fields=['slot'])
                    to_slot.status = 'ringing'
                    to_slot.save(update_fields=['status'])
                    slot.status = 'available'
                    stats = slot.stats or {}
                    stats['transfer_count'] = stats.get('transfer_count', 0) + 1
                    slot.stats = stats
                    slot.save(update_fields=['status', 'stats'])
                except ACDAgentSlot.DoesNotExist:
                    pass

        elif action_type == 'unhold' and ix:
            hold_dur = int(params.get('hold_s', 0))
            ix.hold_s = (ix.hold_s or 0) + hold_dur
            ix.save(update_fields=['hold_s'])
            stats = slot.stats or {}
            stats['hold_count'] = stats.get('hold_count', 0) + 1
            slot.stats = stats
            slot.save(update_fields=['stats'])

        elif action_type == 'conference' and ix:
            with_slot_id = params.get('with_slot_id')
            if with_slot_id:
                try:
                    with_slot = ACDAgentSlot.objects.get(id=with_slot_id, session=slot.session)
                    # Fix C: no conferenciar con agentes no operativos
                    if with_slot.status in ('absent', 'offline'):
                        return JsonResponse(
                            {'success': False, 'error': 'El agente destino no está disponible.'},
                            status=400
                        )
                except ACDAgentSlot.DoesNotExist:
                    pass
            stats = slot.stats or {}
            stats['conference_count'] = stats.get('conference_count', 0) + 1
            slot.stats = stats
            slot.save(update_fields=['stats'])

        elif action_type == 'change_skill':
            new_skill = params.get('skill', '')
            if new_skill:
                slot.skill = new_skill
                slot.save(update_fields=['skill'])


        # Registrar acción
        if ix:
            ACDAgentAction.objects.create(
                interaction = ix,
                slot        = slot,
                action_type = action_type,
                params      = params,
                sim_time    = gtr_time,
            )

        return JsonResponse({
            'success':     True,
            'slot':        _slot_row(slot),
            'interaction': _interaction_row(ix) if ix else None,
        })
    except Exception as e:
        logger.error("acd_agent_action: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ─── Helpers ──────────────────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════════════════════
# BOT-2 — Registro de BotInstances como slots ACD
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def acd_add_bots(request, pk):
    """
    BOT-2: Registra BotInstances activos como ACDAgentSlots (agent_type='bot')
    dentro de una ACDSession existente.

    POST /sim/acd/<pk>/bots/add/
    Body: {"bot_ids": [1, 2, 3], "canal": "inbound"}   # canal opcional

    Respuesta:
        {"success": true,
         "created": [{"slot_id", "slot_number", "bot_id", "bot_name",
                       "profile", "tier", "display_name"}],
         "errors":  [{"bot_id", "error"}]}
    """
    from bots.models import BotInstance  # import local — evita circular en apps.py

    try:
        session = get_object_or_404(ACDSession, pk=pk, created_by=request.user)

        if session.status not in ('config', 'active'):
            return JsonResponse(
                {'success': False, 'error': 'La sesión no acepta cambios en este estado.'},
                status=400,
            )

        data    = json.loads(request.body)
        bot_ids = data.get('bot_ids', [])
        canal   = data.get('canal') or session.canal

        if not bot_ids:
            return JsonResponse({'success': False, 'error': 'bot_ids requerido.'}, status=400)

        last_slot_number = (
            session.slots.order_by('-slot_number')
                         .values_list('slot_number', flat=True)
                         .first()
            or 0
        )

        created_list = []
        error_list   = []

        for i, bot_id in enumerate(bot_ids, start=1):
            result = _register_bot_slot(
                session=session,
                bot_id=bot_id,
                canal=canal,
                slot_number=last_slot_number + i,
            )
            if result['ok']:
                created_list.append(result['data'])
            else:
                error_list.append({'bot_id': bot_id, 'error': result['error']})

        return JsonResponse({'success': True, 'created': created_list, 'errors': error_list})

    except Exception as e:
        logger.error("acd_add_bots: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def _register_bot_slot(session: ACDSession, bot_id: int, canal: str, slot_number: int) -> dict:
    """
    BOT-2: Crea un ACDAgentSlot(agent_type='bot') para el BotInstance dado.

    Lookup de perfil: bot_specialization + canal exacto → fallback sin canal.
    Devuelve {'ok': True, 'data': {...}} o {'ok': False, 'error': str}.
    """
    from bots.models import BotInstance

    try:
        bot = (
            BotInstance.objects
            .select_related('generic_user__user')
            .get(pk=bot_id, is_active=True)
        )
    except BotInstance.DoesNotExist:
        return {'ok': False, 'error': 'Bot no encontrado o inactivo.'}

    # Perfil: canal exacto → fallback cualquier canal
    profile = (
        SimAgentProfile.objects
        .filter(bot_specialization=bot.specialization, canal=canal, is_preset=True)
        .first()
    )
    if profile is None:
        profile = (
            SimAgentProfile.objects
            .filter(bot_specialization=bot.specialization, is_preset=True)
            .first()
        )
    if profile is None:
        return {
            'ok': False,
            'error': (
                f'Sin SimAgentProfile para specialization="{bot.specialization}". '
                'Ejecutar: python manage.py seed_agent_profiles'
            ),
        }

    slot = ACDAgentSlot.objects.create(
        session=session,
        slot_number=slot_number,
        agent_type='bot',
        user=bot.generic_user.user,
        profile=profile,
        display_name=bot.name,
        skill=profile.skills[0] if profile.skills else '',
        # Consistente con acd_slot_add: offline hasta que la sesión arranque
        status='available' if session.status == 'active' else 'offline',
        stats={},
    )

    return {
        'ok': True,
        'data': {
            'slot_id':      str(slot.id),
            'slot_number':  slot.slot_number,
            'bot_id':       bot_id,
            'bot_name':     bot.name,
            'profile':      profile.name,
            'tier':         profile.tier,
            'display_name': slot.display_name,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────

def _get_tipificaciones(session: ACDSession) -> list:
    """Retorna lista de tipificaciones configuradas en la cuenta."""
    try:
        account_config = session.account.config or {}
        cfg = account_config.get(session.canal, {})
        if session.canal == 'inbound':
            skills = cfg.get('skills', {})
            tipifs = set()
            for skill_data in skills.values():
                tipifs.update(skill_data.get('tipificaciones', {}).keys())
            if tipifs:
                return sorted(tipifs)
        elif session.canal == 'outbound':
            tipifs = sorted(cfg.get('tipif_contacto', {}).keys())
            if tipifs:
                return tipifs
        elif session.canal == 'digital':
            tipifs = set()
            tipifs.update(cfg.get('tipificaciones_bxi', {}).keys())
            tipifs.update(cfg.get('tipificaciones_app', {}).keys())
            if tipifs:
                return sorted(tipifs)
    except Exception:
        pass
    return ['Atendida', 'Venta', 'No interesado', 'Agenda', 'Corta llamada', 'Transferir']
