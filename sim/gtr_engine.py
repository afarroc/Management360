# sim/gtr_engine.py
"""
GTR Engine — simulación intraday en tiempo acelerado.

Arquitectura:
  - Una sesión GTR = un día simulado corriendo en clock acelerado
  - Estado persistido en Redis (cache) con TTL
  - El cliente hace polling cada N segundos
  - El engine genera interacciones por franja horaria según el clock

Clock speeds:
  1x   → tiempo real (no práctico, solo referencia)
  5x   → 1 min real = 5 min simulados
  15x  → 1 min real = 15 min simulados  ← recomendado
  60x  → 1 min real = 1 hora simulada   ← demo rápido

Formato clave Redis:
  gtr:session:{session_id}        → estado completo
  gtr:interactions:{session_id}   → lista de interacciones acumuladas
  TTL: 4 horas
"""

import time
import uuid
import json
import logging
import random
from datetime import datetime, date, timedelta
from typing import Optional

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

GTR_TTL = 60 * 60 * 4   # 4 hours

# ── Thresholds para alertas ───────────────────────────────────────────────────
DEFAULT_THRESHOLDS = {
    'sl_min':        80.0,   # SL% mínimo antes de alerta
    'abandon_max':   8.0,    # Abandono% máximo
    'na_min':        85.0,   # Atención% mínimo
    'queue_max':     15,     # Llamadas en cola estimadas
}

DEFAULT_THRESHOLDS_OUTBOUND = {
    'contact_min':   22.0,   # Contactabilidad% mínima
    'conv_min':       0.5,   # Conversión% mínima (ventas/contactos)
    'no_contact_max': 75.0,  # No contacto% máximo
}

CLOCK_SPEEDS = {
    1:  1,
    5:  5,
    15: 15,
    60: 60,
}


def _session_key(sid: str) -> str:
    return f"gtr:session:{sid}"

def _interactions_key(sid: str) -> str:
    return f"gtr:interactions:{sid}"


class GTRSession:
    """
    Encapsula el estado de una sesión GTR.
    Se serializa/deserializa desde Redis.
    """
    def __init__(self, session_id: str, account_id: str, account_name: str,
                 sim_date: date, clock_speed: int = 15,
                 thresholds: dict = None, canal: str = 'inbound',
                 user_id: int = None):
        self.session_id   = session_id
        self.account_id   = str(account_id)
        self.account_name = account_name
        self.sim_date     = sim_date
        self.clock_speed  = clock_speed
        self.canal        = canal
        self.user_id      = user_id
        self.thresholds   = thresholds or DEFAULT_THRESHOLDS.copy()

        # State
        self.status         = 'running'   # running | paused | finished
        self.started_at_real = time.time()
        self.paused_elapsed  = 0.0        # accumulated paused seconds
        self.paused_at       = None

        # Cumulative KPIs
        self.kpis = {
            'entrantes':   0,
            'atendidas':   0,
            'abandonadas': 0,
            'ventas':      0,
            'agenda':      0,
            'no_contacto': 0,
            'tmo_sum_s':   0,
            'tmo_count':   0,
        }

        # Alerts log
        self.alerts = []

        # Last simulated hour processed
        self.last_sim_hour = 8   # start at 8 AM
        self.last_sim_min  = 0

    # ── Clock ─────────────────────────────────────────────────────────────────

    def elapsed_real_s(self) -> float:
        """Segundos reales transcurridos desde el inicio (excluyendo pausa)."""
        if self.paused_at:
            return self.paused_at - self.started_at_real - self.paused_elapsed
        return time.time() - self.started_at_real - self.paused_elapsed

    def sim_time(self) -> tuple:
        """Hora simulada actual (hour, minute) basada en clock_speed."""
        real_elapsed = self.elapsed_real_s()
        sim_minutes  = int(real_elapsed * self.clock_speed / 60)
        sim_hour     = 9 + sim_minutes // 60
        sim_minute   = sim_minutes % 60
        # Cap at 18:00
        if sim_hour >= 18:
            sim_hour   = 18
            sim_minute = 0
            self.status = 'finished'
        return sim_hour, sim_minute

    def sim_minutes_total(self) -> int:
        """Total de minutos simulados desde apertura (9 AM base)."""
        h, m = self.sim_time()
        return (h - 9) * 60 + m

    def sim_progress_pct(self) -> float:
        """Progreso del día 0-100% (9AM=0%, 18PM=100%)."""
        return min(100.0, self.sim_minutes_total() / 540 * 100)

    # ── KPI helpers ───────────────────────────────────────────────────────────

    @property
    def total(self) -> int:
        return self.kpis['entrantes']

    @property
    def na_pct(self) -> float:
        if self.kpis['entrantes'] == 0: return 100.0
        return round(self.kpis['atendidas'] / self.kpis['entrantes'] * 100, 1)

    @property
    def sl_pct(self) -> float:
        """SL estimado — simplificado: atendidas que no abandonaron × factor."""
        if self.kpis['atendidas'] == 0: return 100.0
        # Rough SL: assume 87% of answered calls are within threshold (calibrated)
        return round(min(99.9, self.na_pct * 0.873), 1)

    @property
    def abandon_pct(self) -> float:
        if self.kpis['entrantes'] == 0: return 0.0
        return round(self.kpis['abandonadas'] / self.kpis['entrantes'] * 100, 1)

    @property
    def aht_s(self) -> int:
        if self.kpis['tmo_count'] == 0: return 0
        return int(self.kpis['tmo_sum_s'] / self.kpis['tmo_count'])

    # ── Outbound KPI properties ───────────────────────────────────────────────

    @property
    def contact_pct(self) -> float:
        """Contactabilidad% = contactos / marcaciones × 100."""
        if self.kpis['entrantes'] == 0: return 0.0
        contactos = (self.kpis['atendidas'] + self.kpis['ventas'] +
                     self.kpis['agenda'])
        return round(contactos / self.kpis['entrantes'] * 100, 1)

    @property
    def conv_pct(self) -> float:
        """Conversión% = ventas / contactos × 100."""
        contactos = (self.kpis['atendidas'] + self.kpis['ventas'] +
                     self.kpis['agenda'])
        if contactos == 0: return 0.0
        return round(self.kpis['ventas'] / contactos * 100, 2)

    @property
    def no_contact_pct(self) -> float:
        """No contacto% = no_contacto / marcaciones × 100."""
        if self.kpis['entrantes'] == 0: return 0.0
        return round(self.kpis['no_contacto'] / self.kpis['entrantes'] * 100, 1)

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            'session_id':       self.session_id,
            'account_id':       self.account_id,
            'account_name':     self.account_name,
            'sim_date':         str(self.sim_date),
            'clock_speed':      self.clock_speed,
            'canal':            self.canal,
            'user_id':          self.user_id,
            'thresholds':       self.thresholds,
            'status':           self.status,
            'started_at_real':  self.started_at_real,
            'paused_elapsed':   self.paused_elapsed,
            'paused_at':        self.paused_at,
            'kpis':             self.kpis,
            'alerts':           self.alerts[-20:],  # keep last 20
            'last_sim_hour':    self.last_sim_hour,
            'last_sim_min':     self.last_sim_min,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'GTRSession':
        s = cls.__new__(cls)
        s.session_id       = d['session_id']
        s.account_id       = d['account_id']
        s.account_name     = d['account_name']
        s.sim_date         = date.fromisoformat(d['sim_date'])
        s.clock_speed      = d['clock_speed']
        s.canal            = d['canal']
        s.user_id          = d.get('user_id')
        s.thresholds       = d['thresholds']
        s.status           = d['status']
        s.started_at_real  = d['started_at_real']
        s.paused_elapsed   = d['paused_elapsed']
        s.paused_at        = d['paused_at']
        s.kpis             = d['kpis']
        s.alerts           = d['alerts']
        s.last_sim_hour    = d['last_sim_hour']
        s.last_sim_min     = d['last_sim_min']
        return s


# ── Session persistence ───────────────────────────────────────────────────────

def save_session(session: GTRSession):
    cache.set(_session_key(session.session_id), session.to_dict(), timeout=GTR_TTL)

def load_session(session_id: str) -> Optional[GTRSession]:
    d = cache.get(_session_key(session_id))
    if not d: return None
    return GTRSession.from_dict(d)

def delete_session(session_id: str):
    cache.delete(_session_key(session_id))
    cache.delete(_interactions_key(session_id))

def add_interactions(session_id: str, new_rows: list):
    """Append interactions to the session's interaction list in cache."""
    key  = _interactions_key(session_id)
    existing = cache.get(key) or []
    existing.extend(new_rows)
    # Keep last 2000 interactions to avoid memory bloat
    if len(existing) > 2000:
        existing = existing[-2000:]
    cache.set(key, existing, timeout=GTR_TTL)

def get_interactions(session_id: str, since_index: int = 0) -> list:
    key  = _interactions_key(session_id)
    rows = cache.get(key) or []
    return rows[since_index:]


# ── GTR Engine ───────────────────────────────────────────────────────────────

def persist_session(session_id: str) -> Optional['SimRun']:
    """
    SIM-6a: Persiste todas las interacciones GTR en Redis → Interaction en BD.
    Crea un SimRun con canal 'gtr' para identificar el origen.
    Limpia Redis al finalizar.

    Llamado desde:
      - tick() cuando session.status == 'finished' (auto-finish 18:00)
      - gtr_stop view (parada manual)
    """
    session = load_session(session_id)
    if not session:
        return None

    rows = get_interactions(session_id)
    if not rows:
        delete_session(session_id)
        return None

    try:
        from django.contrib.auth import get_user_model
        from sim.models import SimAccount, Interaction, SimRun

        User    = get_user_model()
        account = SimAccount.objects.get(id=session.account_id)
        user    = User.objects.get(id=session.user_id) if session.user_id else None

        sim_dt = datetime.combine(session.sim_date, datetime.min.time())

        # Crear SimRun GTR
        run = SimRun.objects.create(
            account       = account,
            date_from     = session.sim_date,
            date_to       = session.sim_date,
            canales       = [session.canal, 'gtr'],
            status        = 'running',
            triggered_by  = user,
        )

        # Convertir dicts Redis → Interaction objects
        batch = []
        for row in rows:
            hora_str = row.get('hora', '09:00:00')
            try:
                hora_inicio = datetime.strptime(
                    f"{session.sim_date} {hora_str}", "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                hora_inicio = sim_dt.replace(hour=9)

            dur_s    = int(row.get('duracion_s', 0))
            acw_s    = int(row.get('acw_s', 0))
            hora_fin = hora_inicio + timedelta(seconds=dur_s + acw_s)

            batch.append(Interaction(
                account      = account,
                canal        = row.get('canal', session.canal),
                skill        = row.get('skill', ''),
                sub_canal    = row.get('sub_canal', ''),
                fecha        = session.sim_date,
                hora_inicio  = hora_inicio,
                hora_fin     = hora_fin,
                duracion_s   = dur_s,
                acw_s        = acw_s,
                tipificacion = row.get('tipificacion', ''),
                status       = row.get('status', 'atendida'),
                lead_id      = '',
                intento_num  = 1,
                is_simulated = True,
            ))

        # bulk_create en batches de 2000
        BATCH = 2000
        for i in range(0, len(batch), BATCH):
            Interaction.objects.bulk_create(batch[i:i+BATCH], ignore_conflicts=True)

        run.status                 = 'done'
        run.interactions_generated = len(batch)
        run.finished_at            = timezone.now()
        run.save(update_fields=['status', 'interactions_generated', 'finished_at'])

        logger.info(
            "GTR persisted: session=%s | %d interactions → BD | run=%s",
            session_id, len(batch), run.id
        )

    except Exception as exc:
        logger.error("persist_session failed for %s: %s", session_id, exc, exc_info=True)
        run = None
    finally:
        delete_session(session_id)

    return run


def create_session(account, user, clock_speed: int = 15,
                    sim_date: date = None,
                    thresholds: dict = None) -> GTRSession:
    """Create and persist a new GTR session."""
    sid      = str(uuid.uuid4())
    sim_date = sim_date or date.today()
    clock_speed = CLOCK_SPEEDS.get(clock_speed, 15)

    session = GTRSession(
        session_id   = sid,
        account_id   = str(account.id),
        account_name = account.name,
        sim_date     = sim_date,
        clock_speed  = clock_speed,
        thresholds   = thresholds or DEFAULT_THRESHOLDS.copy(),
        canal        = account.canal,
        user_id      = user.id if user else None,
    )
    save_session(session)
    logger.info("GTR session created: %s | account=%s | speed=%dx", sid, account.name, clock_speed)
    return session


def tick(session_id: str) -> dict:
    """
    Process one tick: generate interactions for newly elapsed sim-time.
    Called on every client poll.
    Returns: updated state dict + new interactions + alerts.
    """
    session = load_session(session_id)
    if not session:
        return {'error': 'session_not_found'}

    if session.status == 'finished':
        return _state_response(session, [], [])

    if session.status == 'paused':
        return _state_response(session, [], [])

    # Current simulated time
    cur_hour, cur_min = session.sim_time()

    # What time window needs to be generated?
    last_h = session.last_sim_hour
    last_m = session.last_sim_min

    if cur_hour < last_h or (cur_hour == last_h and cur_min <= last_m):
        # No new time elapsed
        return _state_response(session, [], [])

    # Generate interactions for the elapsed window
    new_interactions = _generate_window(session, last_h, last_m, cur_hour, cur_min)

    # Update session KPIs
    _update_kpis(session, new_interactions)

    # Update pointer
    session.last_sim_hour = cur_hour
    session.last_sim_min  = cur_min

    # Check thresholds → generate alerts
    new_alerts = _check_alerts(session)
    session.alerts.extend(new_alerts)

    save_session(session)
    add_interactions(session_id, new_interactions)

    # Auto-persist cuando el día simulado termina (18:00)
    if session.status == 'finished':
        try:
            persist_session(session_id)
        except Exception as e:
            logger.error("GTR auto-persist failed for %s: %s", session_id, e, exc_info=True)

    return _state_response(session, new_interactions, new_alerts)


def pause_session(session_id: str) -> dict:
    session = load_session(session_id)
    if not session: return {'error': 'not_found'}
    if session.status == 'running':
        session.status    = 'paused'
        session.paused_at = time.time()
        save_session(session)
    return _state_response(session, [], [])


def resume_session(session_id: str) -> dict:
    session = load_session(session_id)
    if not session: return {'error': 'not_found'}
    if session.status == 'paused' and session.paused_at:
        session.paused_elapsed += time.time() - session.paused_at
        session.paused_at       = None
        session.status          = 'running'
        save_session(session)
    return _state_response(session, [], [])


def inject_event(session_id: str, event_type: str, params: dict) -> dict:
    """
    Inject a manual event into the simulation.

    Eventos discretos (originales):
      'agent_absent'  | 'volume_spike' | 'sl_drop' | 'reset_kpis'

    Controles continuos (SIM-6b):
      'set_vol_pct'      -> params: {pct: 80}       % del volumen base (10-300)
      'set_aht'          -> params: {factor: 1.3}   multiplicador sobre AHT base
      'set_acw'          -> params: {factor: 1.5}   multiplicador sobre ACW base
      'set_hold_rate'    -> params: {rate: 0.15}    fraccion de llamadas en hold
      'agent_break'      -> params: {n: 3}           enviar N agentes a break
      'agent_return'     -> params: {n: 2}           devolver N agentes de break
      'set_skill_weight' -> params: {skill:'PLD', weight:0.8}  inbound only
    """
    session = load_session(session_id)
    if not session: return {'error': 'not_found'}

    msg = None

    # Eventos discretos (originales)
    if event_type == 'volume_spike':
        pct = int(params.get('pct', 30))
        msg = f"🔺 Pico de volumen +{pct}% inyectado manualmente"
        session.kpis['_spike_factor'] = 1 + pct / 100
        session.kpis['_spike_ticks']  = 3

    elif event_type == 'agent_absent':
        n = int(params.get('n', 3))
        msg = f"🚨 {n} agentes marcados ausentes"
        session.kpis['_absent_agents'] = session.kpis.get('_absent_agents', 0) + n

    elif event_type == 'sl_drop':
        msg = "⚠️ Caida de SL inyectada — AHT elevado por 2 ticks"
        session.kpis['_high_aht_ticks'] = 2

    elif event_type == 'reset_kpis':
        for k in ['entrantes','atendidas','abandonadas','ventas','agenda','no_contacto','tmo_sum_s','tmo_count']:
            session.kpis[k] = 0
        msg = "🔄 KPIs reiniciados"

    # Controles continuos (SIM-6b)
    elif event_type == 'set_vol_pct':
        pct = max(10, min(300, int(params.get('pct', 100))))
        session.kpis['_vol_override'] = pct / 100
        msg = f"📊 Volumen ajustado a {pct}% del base"

    elif event_type == 'set_aht':
        factor = max(0.3, min(3.0, float(params.get('factor', 1.0))))
        session.kpis['_aht_override'] = factor
        msg = f"⏱ AHT ajustado a {factor:.2f}x base"

    elif event_type == 'set_acw':
        factor = max(0.3, min(3.0, float(params.get('factor', 1.0))))
        session.kpis['_acw_override'] = factor
        msg = f"📋 ACW ajustado a {factor:.2f}x base"

    elif event_type == 'set_hold_rate':
        rate = max(0.0, min(0.8, float(params.get('rate', 0.05))))
        session.kpis['_hold_rate_override'] = rate
        msg = f"⏸ Hold rate fijado en {rate*100:.0f}%"

    elif event_type == 'agent_break':
        n = max(1, int(params.get('n', 1)))
        current = session.kpis.get('_agents_on_break', 0)
        session.kpis['_agents_on_break'] = current + n
        msg = f"☕ {n} agente(s) a break ({current+n} total en break)"

    elif event_type == 'agent_return':
        n = max(1, int(params.get('n', 1)))
        current = session.kpis.get('_agents_on_break', 0)
        session.kpis['_agents_on_break'] = max(0, current - n)
        msg = f"✅ {n} agente(s) retornaron ({max(0,current-n)} en break)"

    elif event_type == 'set_skill_weight':
        skill  = str(params.get('skill', '')).strip()
        weight = max(0.0, min(1.0, float(params.get('weight', 0.5))))
        if skill:
            overrides = session.kpis.get('_skill_overrides', {})
            overrides[skill] = weight
            session.kpis['_skill_overrides'] = overrides
            msg = f"🎯 Skill '{skill}' -> peso {weight:.2f}"

    alert = None
    if msg:
        alert = {'ts': datetime.now().strftime('%H:%M:%S'), 'type': 'event',
                 'level': 'info', 'msg': msg}
        session.alerts.append(alert)
        save_session(session)

    return _state_response(session, [], [alert] if alert else [])


# ── Internal helpers ──────────────────────────────────────────────────────────

def _generate_window(session: GTRSession, from_h: int, from_m: int,
                      to_h: int, to_m: int) -> list:
    """Dispatcher: enruta al generador correcto según canal."""
    if session.canal == 'outbound':
        return _generate_window_outbound(session, from_h, from_m, to_h, to_m)
    return _generate_window_inbound(session, from_h, from_m, to_h, to_m)


def _generate_window_inbound(session: GTRSession, from_h: int, from_m: int,
                              to_h: int, to_m: int) -> list:
    """Generate inbound interactions for the time window [from → to]."""
    from sim.generators import inbound as inb_gen
    from sim.generators.base import weighted_choice, gaussian_duration

    # Minutes elapsed in this window
    mins_elapsed = (to_h - from_h) * 60 + (to_m - from_m)
    if mins_elapsed <= 0:
        return []

    # Get account config
    try:
        from sim.models import SimAccount, SimAgent
        account = SimAccount.objects.get(id=session.account_id)
        cfg_inbound = account.config.get('inbound', {})
    except Exception:
        cfg_inbound = {}

    # Intraday weight for current hour
    INTRADAY = cfg_inbound.get('intraday', {
        9:0.123,10:0.135,11:0.136,12:0.116,
        13:0.102,14:0.096,15:0.096,16:0.109,17:0.087
    })
    hour_weight = INTRADAY.get(from_h, 0.10)

    # Volume for this window
    base_vol     = cfg_inbound.get('weekday_vol', 1490)
    vol_per_min  = base_vol * hour_weight / 60
    spike        = session.kpis.get('_spike_factor', 1.0)
    vol_override = session.kpis.get('_vol_override', 1.0)   # SIM-6b
    expected_vol = vol_per_min * mins_elapsed * spike * vol_override
    expected_vol = max(0.0, expected_vol)
    vol = max(0, int(random.gauss(expected_vol, max(0.1, expected_vol * 0.10))))

    # Decay spike
    if session.kpis.get('_spike_ticks', 0) > 0:
        session.kpis['_spike_ticks'] -= 1
        if session.kpis['_spike_ticks'] <= 0:
            session.kpis['_spike_factor'] = 1.0

    if vol == 0:
        return []

    abandon_rate = cfg_inbound.get('abandon_rate', 0.039)
    if session.kpis.get('_high_aht_ticks', 0) > 0:
        abandon_rate *= 1.8
        session.kpis['_high_aht_ticks'] -= 1

    # SIM-6b: apply hold_rate_override
    hold_rate_override = session.kpis.get('_hold_rate_override', None)

    # SIM-6b: AHT/ACW overrides
    tmo_mean = cfg_inbound.get('tmo_s', 313) * session.kpis.get('_aht_override', 1.0)
    acw_mean = cfg_inbound.get('acw_s', 18)  * session.kpis.get('_acw_override', 1.0)

    # SIM-6b: skill weight overrides
    skills_cfg    = cfg_inbound.get('skills', {'PLD': {'weight':1.0,'tipificaciones':{'CONSULTA':1.0}}})
    skill_overrides = session.kpis.get('_skill_overrides', {})
    skill_weights = {}
    for k, v in skills_cfg.items():
        skill_weights[k] = skill_overrides.get(k, v['weight'])

    interactions = []
    sim_dt = datetime.combine(session.sim_date, datetime.min.time()).replace(
        hour=from_h, minute=from_m
    )

    for i in range(vol):
        offset    = random.randint(0, mins_elapsed * 60)
        hora      = sim_dt + timedelta(seconds=offset)
        abandoned = random.random() < abandon_rate
        skill     = weighted_choice(skill_weights)
        tipif     = weighted_choice(skills_cfg[skill]['tipificaciones'])

        if abandoned:
            dur    = random.randint(5, 30)
            acw    = 0
            status = 'abandonada'
        else:
            high_aht = session.kpis.get('_high_aht_ticks', 0) > 0
            dur    = gaussian_duration(tmo_mean * (1.4 if high_aht else 1.0), 0.15, 60, 900)
            # SIM-6b: hold time si hold_rate_override activo
            effective_hold = hold_rate_override if hold_rate_override is not None else 0.0
            if effective_hold > 0 and random.random() < effective_hold:
                dur += gaussian_duration(30, 0.40, 10, 180)
            acw    = gaussian_duration(acw_mean, 0.30, 5, 120)
            status = 'atendida'

        interactions.append({
            'hora':         hora.strftime('%H:%M:%S'),
            'canal':        'inbound',
            'skill':        skill,
            'tipificacion': tipif,
            'duracion_s':   dur,
            'acw_s':        acw,
            'status':       status,
        })

    return interactions


def _generate_window_outbound(session: GTRSession, from_h: int, from_m: int,
                               to_h: int, to_m: int) -> list:
    """
    Generate outbound interactions for the time window [from → to].
    Calibrado con Conduent/ENTEL — contactabilidad 27.6%, conv 0.84%.
    """
    from sim.generators.base import weighted_choice, gaussian_duration

    mins_elapsed = (to_h - from_h) * 60 + (to_m - from_m)
    if mins_elapsed <= 0:
        return []

    try:
        from sim.models import SimAccount
        account  = SimAccount.objects.get(id=session.account_id)
        cfg_out  = account.config.get('outbound', {})
    except Exception:
        cfg_out = {}

    # Intraday outbound
    INTRADAY = cfg_out.get('intraday', {
        8:0.06, 9:0.10, 10:0.13, 11:0.13,
        12:0.11, 13:0.10, 14:0.10, 15:0.10,
        16:0.09, 17:0.07, 18:0.01,
    })
    hour_weight  = INTRADAY.get(from_h, 0.10)
    base_daily   = cfg_out.get('daily_marcaciones', 131400)
    vol_per_min  = base_daily * hour_weight / 60
    spike        = session.kpis.get('_spike_factor', 1.0)
    vol_override = session.kpis.get('_vol_override', 1.0)   # SIM-6b
    expected_vol = vol_per_min * mins_elapsed * spike * vol_override
    expected_vol = max(0.0, expected_vol)
    vol          = max(0, int(random.gauss(expected_vol, max(0.1, expected_vol * 0.08))))

    # Decay spike
    if session.kpis.get('_spike_ticks', 0) > 0:
        session.kpis['_spike_ticks'] -= 1
        if session.kpis['_spike_ticks'] <= 0:
            session.kpis['_spike_factor'] = 1.0

    if vol == 0:
        return []

    contact_rate = cfg_out.get('contact_rate', 0.276)
    conv_rate    = cfg_out.get('conv_rate',    0.0084)
    agenda_rate  = cfg_out.get('agenda_rate',  0.128)

    # SIM-6b: reducir contactabilidad por agentes en break + ausentes
    absent = session.kpis.get('_absent_agents', 0) + session.kpis.get('_agents_on_break', 0)
    if absent > 0:
        contact_rate *= max(0.5, 1 - absent / 100)

    tipif_contacto = cfg_out.get('tipif_contacto', {
        'Cliente corta llamada':         0.415,
        'Cliente ocupado':               0.229,
        'No venta - No interesado':      0.188,
        'Agenda (Usuario)':              0.090,
        'Agenda (Titular)':              0.032,
        'Venta':                         0.008,
        'No venta - No volver a llamar': 0.012,
        'No venta - Otro':               0.026,
    })
    tipif_no_contacto = cfg_out.get('tipif_no_contacto', {
        'No contesta':        0.524,
        'Buzon de voz':       0.328,
        'Timeout conclusion': 0.053,
        'Desconectada':       0.034,
        'Ocupado':            0.061,
    })
    productos = cfg_out.get('producto', {'PORTABILIDAD': 0.92, 'LINEA NUEVA': 0.08})

    interactions = []
    sim_dt = datetime.combine(session.sim_date, datetime.min.time()).replace(
        hour=from_h, minute=from_m
    )

    for i in range(vol):
        offset     = random.randint(0, mins_elapsed * 60)
        hora       = sim_dt + timedelta(seconds=offset)
        is_contact = random.random() < contact_rate
        producto   = weighted_choice(productos)

        if is_contact:
            tipif = weighted_choice(tipif_contacto)
            if tipif == 'Venta':
                status = 'venta'
                dur    = gaussian_duration(300, 0.20, 120, 720)
            elif 'Agenda' in tipif:
                status = 'agenda'
                dur    = gaussian_duration(240, 0.20, 60, 600)
            elif 'corta' in tipif.lower():
                status = 'atendida'
                dur    = gaussian_duration(45, 0.30, 10, 120)
            else:
                status = 'rechazo'
                dur    = gaussian_duration(180, 0.20, 60, 600)
            acw = gaussian_duration(30, 0.30, 10, 120)
        else:
            tipif  = weighted_choice(tipif_no_contacto)
            status = 'no_contacto'
            dur    = gaussian_duration(25, 0.25, 5, 90)
            acw    = 0

        interactions.append({
            'hora':         hora.strftime('%H:%M:%S'),
            'canal':        'outbound',
            'skill':        producto,
            'tipificacion': tipif,
            'duracion_s':   dur,
            'acw_s':        acw,
            'status':       status,
        })

    return interactions


def _update_kpis(session: GTRSession, interactions: list):
    for row in interactions:
        st = row['status']
        session.kpis['entrantes']   += 1
        if st == 'atendida':
            session.kpis['atendidas']  += 1
            session.kpis['tmo_sum_s']  += row['duracion_s'] + row['acw_s']
            session.kpis['tmo_count']  += 1
        elif st == 'abandonada':
            session.kpis['abandonadas'] += 1
        elif st == 'venta':
            session.kpis['atendidas']  += 1
            session.kpis['ventas']     += 1
            session.kpis['tmo_sum_s']  += row['duracion_s']
            session.kpis['tmo_count']  += 1
        elif st == 'agenda':
            session.kpis['atendidas']  += 1
            session.kpis['agenda']     += 1
        elif st == 'no_contacto':
            session.kpis['no_contacto'] += 1


def _check_alerts(session: GTRSession) -> list:
    alerts = []
    now    = datetime.now().strftime('%H:%M:%S')
    h, m   = session.sim_time()
    sim_ts = f"{h:02d}:{m:02d}"

    if session.kpis['entrantes'] < 20:
        return []

    if session.canal == 'outbound':
        thr = session.thresholds
        # Alerta contactabilidad baja
        if session.contact_pct < thr.get('contact_min', 22.0):
            alerts.append({
                'ts': now, 'sim_ts': sim_ts, 'type': 'contact',
                'level': 'danger',
                'msg': f"⚠️ Contactabilidad {session.contact_pct:.1f}% < umbral {thr.get('contact_min', 22.0)}%"
            })
        # Alerta conversión baja
        if session.conv_pct < thr.get('conv_min', 0.5):
            alerts.append({
                'ts': now, 'sim_ts': sim_ts, 'type': 'conv',
                'level': 'warning',
                'msg': f"📉 Conversión {session.conv_pct:.2f}% < umbral {thr.get('conv_min', 0.5)}%"
            })
        # Alerta no contacto alto
        if session.no_contact_pct > thr.get('no_contact_max', 75.0):
            alerts.append({
                'ts': now, 'sim_ts': sim_ts, 'type': 'no_contact',
                'level': 'warning',
                'msg': f"📵 No contacto {session.no_contact_pct:.1f}% > umbral {thr.get('no_contact_max', 75.0)}%"
            })
        return alerts

    # Inbound alerts
    thr = session.thresholds
    if session.sl_pct < thr['sl_min']:
        alerts.append({
            'ts': now, 'sim_ts': sim_ts, 'type': 'sl',
            'level': 'danger',
            'msg': f"⚠️ SL {session.sl_pct:.1f}% < umbral {thr['sl_min']}%"
        })

    if session.abandon_pct > thr['abandon_max']:
        alerts.append({
            'ts': now, 'sim_ts': sim_ts, 'type': 'abandon',
            'level': 'warning',
            'msg': f"📞 Abandono {session.abandon_pct:.1f}% > umbral {thr['abandon_max']}%"
        })

    if session.na_pct < thr['na_min']:
        alerts.append({
            'ts': now, 'sim_ts': sim_ts, 'type': 'na',
            'level': 'warning',
            'msg': f"📉 Atención {session.na_pct:.1f}% < umbral {thr['na_min']}%"
        })

    return alerts


def _state_response(session: GTRSession, new_rows: list, new_alerts: list) -> dict:
    h, m = session.sim_time()

    # KPIs base — comunes a todos los canales
    kpis = {
        'entrantes':   session.kpis['entrantes'],
        'atendidas':   session.kpis['atendidas'],
        'abandonadas': session.kpis['abandonadas'],
        'ventas':      session.kpis['ventas'],
        'agenda':      session.kpis['agenda'],
        'no_contacto': session.kpis['no_contacto'],
        'na_pct':      session.na_pct,
        'sl_pct':      session.sl_pct,
        'abandon_pct': session.abandon_pct,
        'aht_s':       session.aht_s,
        'aht_min':     round(session.aht_s / 60, 2),
        # Outbound
        'contact_pct':    session.contact_pct,
        'conv_pct':       session.conv_pct,
        'no_contact_pct': session.no_contact_pct,
    }

    return {
        'session_id':    session.session_id,
        'status':        session.status,
        'canal':         session.canal,
        'sim_time':      f"{h:02d}:{m:02d}",
        'sim_progress':  round(session.sim_progress_pct(), 1),
        'clock_speed':   session.clock_speed,
        'kpis':          kpis,
        'new_interactions':      len(new_rows),
        'new_interactions_data': new_rows[-50:],
        'new_alerts':    new_alerts,
        'all_alerts':    session.alerts[-10:],
        'thresholds':    session.thresholds,
        # SIM-6b: estado actual de los controles (para sync de sliders al reconectar)
        'controls': {
            'vol_pct':        round(session.kpis.get('_vol_override', 1.0) * 100),
            'aht_factor':     round(session.kpis.get('_aht_override', 1.0), 2),
            'acw_factor':     round(session.kpis.get('_acw_override', 1.0), 2),
            'hold_rate':      round(session.kpis.get('_hold_rate_override', 0.0), 2),
            'agents_on_break':session.kpis.get('_agents_on_break', 0),
            'skill_overrides':session.kpis.get('_skill_overrides', {}),
        },
    }
