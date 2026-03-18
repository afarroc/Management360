# sim/tests/test_gtr_engine.py
"""
Tests unitarios para gtr_engine.py.
Usa mocks de cache y time para no depender de Redis ni de tiempo real.

Cobertura:
  GTRSession.__init__       → estado inicial
  GTRSession.sim_time       → cálculo de hora simulada, cap 18:00
  GTRSession.sim_progress   → 0% a 100%
  GTRSession.kpi properties → na_pct, sl_pct, abandon_pct, aht_s (incluye division/0)
  GTRSession.to_dict/from_dict → roundtrip completo
  _update_kpis              → todos los estados de interacción
  _check_alerts             → umbral mínimo datos, alertas SL, abandono, atención
  inject_event              → 4 tipos de evento
  add_interactions          → cap en 2000 entradas
  get_interactions          → slicing por since_index
  _session_key / _interactions_key → formato de clave Redis
"""

import time
from datetime import date
from unittest.mock import patch, MagicMock

from django.test import SimpleTestCase

from sim.gtr_engine import (
    GTRSession, DEFAULT_THRESHOLDS,
    _session_key, _interactions_key,
    save_session, load_session, delete_session,
    add_interactions, get_interactions,
    pause_session, resume_session, inject_event,
    _update_kpis, _check_alerts, _state_response,
)


# ─── helpers ────────────────────────────────────────────────────────────────

def make_session(**kwargs) -> GTRSession:
    defaults = dict(
        session_id='test-session-001',
        account_id='acct-0000-1111',
        account_name='Banca Inbound Test',
        sim_date=date(2026, 3, 16),
        clock_speed=15,
        canal='inbound',
    )
    defaults.update(kwargs)
    return GTRSession(**defaults)


def make_interaction(status='atendida', duracion_s=313, acw_s=18) -> dict:
    return {
        'canal':        'inbound',
        'skill':        'PLD',
        'tipificacion': 'CUOTA MENSUAL',
        'duracion_s':   duracion_s,
        'acw_s':        acw_s,
        'status':       status,
        'hora':         '10:30:00',
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GTRSession — inicialización
# ═══════════════════════════════════════════════════════════════════════════════

class TestGTRSessionInit(SimpleTestCase):

    def setUp(self):
        self.s = make_session()

    def test_session_id_stored(self):
        self.assertEqual(self.s.session_id, 'test-session-001')

    def test_status_is_running(self):
        self.assertEqual(self.s.status, 'running')

    def test_last_sim_hour_starts_at_8(self):
        self.assertEqual(self.s.last_sim_hour, 8)

    def test_kpis_all_zero(self):
        for key in ('entrantes', 'atendidas', 'abandonadas', 'ventas',
                    'agenda', 'no_contacto', 'tmo_sum_s', 'tmo_count'):
            self.assertEqual(self.s.kpis[key], 0)

    def test_alerts_empty(self):
        self.assertEqual(self.s.alerts, [])

    def test_default_thresholds_applied(self):
        self.assertEqual(self.s.thresholds['sl_min'], DEFAULT_THRESHOLDS['sl_min'])

    def test_custom_thresholds_applied(self):
        s = make_session(thresholds={'sl_min': 75.0, 'abandon_max': 10.0,
                                      'na_min': 80.0, 'queue_max': 20})
        self.assertEqual(s.thresholds['sl_min'], 75.0)

    def test_paused_elapsed_zero(self):
        self.assertEqual(self.s.paused_elapsed, 0.0)

    def test_paused_at_is_none(self):
        self.assertIsNone(self.s.paused_at)


# ═══════════════════════════════════════════════════════════════════════════════
# GTRSession — clock
# ═══════════════════════════════════════════════════════════════════════════════

class TestGTRSessionClock(SimpleTestCase):

    def test_sim_time_at_start_is_nine(self):
        s = make_session(clock_speed=15)
        with patch('sim.gtr_engine.time') as mock_time:
            mock_time.time.return_value = s.started_at_real
            h, m = s.sim_time()
        self.assertEqual(h, 9)
        self.assertEqual(m, 0)

    def test_sim_time_one_minute_real_clock15(self):
        """1 min real × 15 = 15 min simulados → 9:15."""
        s = make_session(clock_speed=15)
        with patch('sim.gtr_engine.time') as mock_time:
            mock_time.time.return_value = s.started_at_real + 60
            h, m = s.sim_time()
        self.assertEqual(h, 9)
        self.assertEqual(m, 15)

    def test_sim_time_clock60_one_minute_equals_one_hour(self):
        """1 min real × 60 = 60 min simulados → 10:00."""
        s = make_session(clock_speed=60)
        with patch('sim.gtr_engine.time') as mock_time:
            mock_time.time.return_value = s.started_at_real + 60
            h, m = s.sim_time()
        self.assertEqual(h, 10)
        self.assertEqual(m, 0)

    def test_sim_time_capped_at_18(self):
        """Clock que supera las 18:00 queda en 18:00 y status=finished."""
        s = make_session(clock_speed=60)
        # 9 horas simuladas = 540 min / 60 speed = 540 seg reales
        with patch('sim.gtr_engine.time') as mock_time:
            mock_time.time.return_value = s.started_at_real + 600
            h, m = s.sim_time()
        self.assertEqual(h, 18)
        self.assertEqual(m, 0)
        self.assertEqual(s.status, 'finished')

    def test_sim_progress_zero_at_start(self):
        s = make_session(clock_speed=15)
        with patch('sim.gtr_engine.time') as mock_time:
            mock_time.time.return_value = s.started_at_real
            pct = s.sim_progress_pct()
        self.assertAlmostEqual(pct, 0.0, delta=1.0)

    def test_sim_progress_fifty_percent_at_midday(self):
        """A las 13:30 simuladas (50% del día 9h–18h) → ~50%."""
        s = make_session(clock_speed=60)
        # 4.5 horas simuladas = 270 min / 60 speed = 270 seg reales
        with patch('sim.gtr_engine.time') as mock_time:
            mock_time.time.return_value = s.started_at_real + 270
            pct = s.sim_progress_pct()
        self.assertGreater(pct, 45.0)
        self.assertLess(pct,    55.0)

    def test_sim_minutes_total_at_nine(self):
        s = make_session(clock_speed=15)
        with patch('sim.gtr_engine.time') as mock_time:
            mock_time.time.return_value = s.started_at_real
            mins = s.sim_minutes_total()
        self.assertEqual(mins, 0)

    def test_elapsed_real_excludes_paused_time(self):
        s = make_session()
        s.paused_elapsed = 30.0
        with patch('sim.gtr_engine.time') as mock_time:
            mock_time.time.return_value = s.started_at_real + 90
            elapsed = s.elapsed_real_s()
        self.assertAlmostEqual(elapsed, 60.0, delta=1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# GTRSession — KPI properties
# ═══════════════════════════════════════════════════════════════════════════════

class TestGTRSessionKPIs(SimpleTestCase):

    def test_na_pct_zero_entrantes_returns_100(self):
        s = make_session()
        self.assertEqual(s.na_pct, 100.0)

    def test_na_pct_calculated(self):
        s = make_session()
        s.kpis['entrantes'] = 100
        s.kpis['atendidas'] = 87
        self.assertAlmostEqual(s.na_pct, 87.0, delta=0.1)

    def test_sl_pct_zero_atendidas_returns_100(self):
        s = make_session()
        self.assertEqual(s.sl_pct, 100.0)

    def test_sl_pct_below_na_pct(self):
        s = make_session()
        s.kpis['entrantes'] = 100
        s.kpis['atendidas'] = 90
        self.assertLess(s.sl_pct, s.na_pct)

    def test_sl_pct_max_99_9(self):
        s = make_session()
        s.kpis['entrantes'] = 100
        s.kpis['atendidas'] = 100
        self.assertLessEqual(s.sl_pct, 99.9)

    def test_abandon_pct_zero_entrantes_returns_zero(self):
        s = make_session()
        self.assertEqual(s.abandon_pct, 0.0)

    def test_abandon_pct_calculated(self):
        s = make_session()
        s.kpis['entrantes']  = 100
        s.kpis['abandonadas'] = 4
        self.assertAlmostEqual(s.abandon_pct, 4.0, delta=0.1)

    def test_aht_s_zero_count_returns_zero(self):
        s = make_session()
        self.assertEqual(s.aht_s, 0)

    def test_aht_s_calculated(self):
        s = make_session()
        s.kpis['tmo_sum_s'] = 3310
        s.kpis['tmo_count'] = 10
        self.assertEqual(s.aht_s, 331)

    def test_total_property(self):
        s = make_session()
        s.kpis['entrantes'] = 55
        self.assertEqual(s.total, 55)


# ═══════════════════════════════════════════════════════════════════════════════
# GTRSession — serialización
# ═══════════════════════════════════════════════════════════════════════════════

class TestGTRSessionSerialization(SimpleTestCase):

    def setUp(self):
        self.s = make_session()
        self.s.kpis['entrantes'] = 42
        self.s.kpis['atendidas'] = 38
        self.s.alerts = [{'ts': '10:00:00', 'msg': 'test alert'}]

    def test_to_dict_contains_required_keys(self):
        d = self.s.to_dict()
        for key in ('session_id', 'account_id', 'account_name', 'sim_date',
                    'clock_speed', 'canal', 'thresholds', 'status',
                    'kpis', 'alerts', 'last_sim_hour', 'last_sim_min'):
            self.assertIn(key, d)

    def test_from_dict_roundtrip(self):
        d  = self.s.to_dict()
        s2 = GTRSession.from_dict(d)
        self.assertEqual(s2.session_id,   self.s.session_id)
        self.assertEqual(s2.account_name, self.s.account_name)
        self.assertEqual(s2.clock_speed,  self.s.clock_speed)
        self.assertEqual(s2.status,       self.s.status)
        self.assertEqual(s2.kpis['entrantes'], 42)
        self.assertEqual(s2.kpis['atendidas'], 38)
        self.assertEqual(s2.canal,        self.s.canal)

    def test_sim_date_serialized_as_string(self):
        d = self.s.to_dict()
        self.assertIsInstance(d['sim_date'], str)

    def test_alerts_capped_at_20(self):
        self.s.alerts = [{'msg': f'alert {i}'} for i in range(30)]
        d = self.s.to_dict()
        self.assertLessEqual(len(d['alerts']), 20)

    def test_from_dict_restores_date(self):
        d  = self.s.to_dict()
        s2 = GTRSession.from_dict(d)
        self.assertEqual(s2.sim_date, date(2026, 3, 16))


# ═══════════════════════════════════════════════════════════════════════════════
# _update_kpis
# ═══════════════════════════════════════════════════════════════════════════════

class TestUpdateKpis(SimpleTestCase):

    def setUp(self):
        self.s = make_session()

    def test_atendida_increments_entrantes_and_atendidas(self):
        _update_kpis(self.s, [make_interaction('atendida', 313, 18)])
        self.assertEqual(self.s.kpis['entrantes'], 1)
        self.assertEqual(self.s.kpis['atendidas'], 1)

    def test_atendida_updates_tmo(self):
        _update_kpis(self.s, [make_interaction('atendida', 300, 20)])
        self.assertEqual(self.s.kpis['tmo_sum_s'],  320)
        self.assertEqual(self.s.kpis['tmo_count'],  1)

    def test_abandonada_increments_abandonadas(self):
        _update_kpis(self.s, [make_interaction('abandonada', 15, 0)])
        self.assertEqual(self.s.kpis['entrantes'],  1)
        self.assertEqual(self.s.kpis['abandonadas'], 1)
        self.assertEqual(self.s.kpis['atendidas'],   0)

    def test_venta_increments_ventas_and_atendidas(self):
        _update_kpis(self.s, [make_interaction('venta', 350, 0)])
        self.assertEqual(self.s.kpis['ventas'],    1)
        self.assertEqual(self.s.kpis['atendidas'], 1)

    def test_agenda_increments_agenda_and_atendidas(self):
        _update_kpis(self.s, [make_interaction('agenda', 240, 0)])
        self.assertEqual(self.s.kpis['agenda'],    1)
        self.assertEqual(self.s.kpis['atendidas'], 1)

    def test_no_contacto_increments_no_contacto(self):
        _update_kpis(self.s, [make_interaction('no_contacto', 25, 0)])
        self.assertEqual(self.s.kpis['no_contacto'], 1)
        self.assertEqual(self.s.kpis['atendidas'],   0)

    def test_multiple_interactions(self):
        rows = [
            make_interaction('atendida',   300, 18),
            make_interaction('abandonada', 12,  0),
            make_interaction('atendida',   280, 15),
        ]
        _update_kpis(self.s, rows)
        self.assertEqual(self.s.kpis['entrantes'],  3)
        self.assertEqual(self.s.kpis['atendidas'],  2)
        self.assertEqual(self.s.kpis['abandonadas'], 1)


# ═══════════════════════════════════════════════════════════════════════════════
# _check_alerts
# ═══════════════════════════════════════════════════════════════════════════════

class TestCheckAlerts(SimpleTestCase):

    def _session_with_kpis(self, entrantes, atendidas, abandonadas):
        s = make_session()
        s.kpis['entrantes']  = entrantes
        s.kpis['atendidas']  = atendidas
        s.kpis['abandonadas'] = abandonadas
        return s

    def test_no_alerts_when_less_than_20_entrantes(self):
        s = self._session_with_kpis(10, 9, 1)
        with patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            alerts = _check_alerts(s)
        self.assertEqual(alerts, [])

    def test_sl_alert_when_below_threshold(self):
        """SL bajo el umbral (80%) debe generar alerta tipo 'sl'."""
        s = self._session_with_kpis(entrantes=100, atendidas=50, abandonadas=50)
        # na_pct = 50% → sl_pct ≈ 43.65% < 80%
        with patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            alerts = _check_alerts(s)
        types = [a['type'] for a in alerts]
        self.assertIn('sl', types)

    def test_abandon_alert_when_above_threshold(self):
        """Abandono sobre el umbral (8%) debe generar alerta tipo 'abandon'."""
        s = self._session_with_kpis(entrantes=100, atendidas=80, abandonadas=20)
        # abandon_pct = 20% > 8%
        with patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            alerts = _check_alerts(s)
        types = [a['type'] for a in alerts]
        self.assertIn('abandon', types)

    def test_no_alerts_when_kpis_healthy(self):
        """SL ~87%, abandono ~4%, na ~96% → sin alertas."""
        s = self._session_with_kpis(entrantes=100, atendidas=96, abandonadas=4)
        with patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            alerts = _check_alerts(s)
        self.assertEqual(alerts, [])

    def test_alert_has_required_keys(self):
        s = self._session_with_kpis(entrantes=100, atendidas=40, abandonadas=60)
        with patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            alerts = _check_alerts(s)
        if alerts:
            for a in alerts:
                for key in ('ts', 'type', 'level', 'msg'):
                    self.assertIn(key, a)


# ═══════════════════════════════════════════════════════════════════════════════
# inject_event
# ═══════════════════════════════════════════════════════════════════════════════

class TestInjectEvent(SimpleTestCase):

    def _patched_inject(self, event_type, params=None):
        s = make_session()
        with patch('sim.gtr_engine.load_session', return_value=s), \
             patch('sim.gtr_engine.save_session'), \
             patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            result = inject_event('test-session-001', event_type, params or {})
        return result, s

    def test_volume_spike_sets_factor(self):
        _, s = self._patched_inject('volume_spike', {'pct': 30})
        self.assertAlmostEqual(s.kpis['_spike_factor'], 1.3, delta=0.01)
        self.assertEqual(s.kpis['_spike_ticks'], 3)

    def test_volume_spike_adds_alert(self):
        _, s = self._patched_inject('volume_spike', {'pct': 20})
        self.assertTrue(len(s.alerts) > 0)
        self.assertIn('Pico', s.alerts[-1]['msg'])

    def test_agent_absent_accumulates(self):
        _, s = self._patched_inject('agent_absent', {'n': 5})
        self.assertEqual(s.kpis['_absent_agents'], 5)

    def test_agent_absent_accumulates_on_second_call(self):
        s = make_session()
        s.kpis['_absent_agents'] = 3
        with patch('sim.gtr_engine.load_session', return_value=s), \
             patch('sim.gtr_engine.save_session'), \
             patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            inject_event('test-session-001', 'agent_absent', {'n': 2})
        self.assertEqual(s.kpis['_absent_agents'], 5)

    def test_sl_drop_sets_high_aht_ticks(self):
        _, s = self._patched_inject('sl_drop')
        self.assertEqual(s.kpis['_high_aht_ticks'], 2)

    def test_reset_kpis_clears_counters(self):
        s = make_session()
        s.kpis['entrantes'] = 500
        s.kpis['atendidas'] = 450
        s.kpis['ventas']    = 10
        with patch('sim.gtr_engine.load_session', return_value=s), \
             patch('sim.gtr_engine.save_session'), \
             patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            inject_event('test-session-001', 'reset_kpis', {})
        self.assertEqual(s.kpis['entrantes'], 0)
        self.assertEqual(s.kpis['atendidas'], 0)
        self.assertEqual(s.kpis['ventas'],    0)

    def test_unknown_event_returns_no_error(self):
        result, _ = self._patched_inject('tipo_desconocido')
        self.assertNotIn('error', result)

    def test_not_found_session_returns_error(self):
        with patch('sim.gtr_engine.load_session', return_value=None):
            result = inject_event('no-existe', 'volume_spike', {})
        self.assertEqual(result.get('error'), 'not_found')


# ═══════════════════════════════════════════════════════════════════════════════
# Persistence helpers (mocked cache)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionKeys(SimpleTestCase):

    def test_session_key_format(self):
        self.assertEqual(_session_key('abc-123'), 'gtr:session:abc-123')

    def test_interactions_key_format(self):
        self.assertEqual(_interactions_key('abc-123'), 'gtr:interactions:abc-123')


class TestInteractionsPersistence(SimpleTestCase):

    def test_add_interactions_appends(self):
        store = {}
        def mock_get(key):  return store.get(key)
        def mock_set(key, val, timeout=None): store[key] = val

        with patch('sim.gtr_engine.cache') as mc:
            mc.get.side_effect  = mock_get
            mc.set.side_effect  = mock_set
            add_interactions('sid-1', [{'row': 1}, {'row': 2}])
            add_interactions('sid-1', [{'row': 3}])
            result = get_interactions('sid-1')

        self.assertEqual(len(result), 3)

    def test_get_interactions_since_index(self):
        rows = [{'i': i} for i in range(10)]
        with patch('sim.gtr_engine.cache') as mc:
            mc.get.return_value = rows
            result = get_interactions('sid-x', since_index=5)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]['i'], 5)

    def test_add_interactions_caps_at_2000(self):
        big_list = [{'i': i} for i in range(1990)]
        store    = {_interactions_key('sid-cap'): big_list}

        def mock_get(key):  return store.get(key, [])
        def mock_set(key, val, timeout=None): store[key] = val

        with patch('sim.gtr_engine.cache') as mc:
            mc.get.side_effect  = mock_get
            mc.set.side_effect  = mock_set
            add_interactions('sid-cap', [{'i': i} for i in range(50)])

        saved = store[_interactions_key('sid-cap')]
        self.assertLessEqual(len(saved), 2000)

    def test_get_interactions_empty_when_no_cache(self):
        with patch('sim.gtr_engine.cache') as mc:
            mc.get.return_value = None
            result = get_interactions('sid-vacio')
        self.assertEqual(result, [])


# ═══════════════════════════════════════════════════════════════════════════════
# save/load/delete session (mocked cache)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionPersistence(SimpleTestCase):

    def test_save_and_load_roundtrip(self):
        store = {}
        def mock_set(key, val, timeout=None): store[key] = val
        def mock_get(key):  return store.get(key)

        s = make_session()
        s.kpis['entrantes'] = 77

        with patch('sim.gtr_engine.cache') as mc:
            mc.set.side_effect = mock_set
            mc.get.side_effect = mock_get
            save_session(s)
            loaded = load_session(s.session_id)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.kpis['entrantes'], 77)
        self.assertEqual(loaded.session_id, s.session_id)

    def test_load_missing_session_returns_none(self):
        with patch('sim.gtr_engine.cache') as mc:
            mc.get.return_value = None
            result = load_session('no-existe')
        self.assertIsNone(result)

    def test_delete_session_calls_cache_delete(self):
        with patch('sim.gtr_engine.cache') as mc:
            delete_session('sid-del')
        self.assertEqual(mc.delete.call_count, 2)


# ═══════════════════════════════════════════════════════════════════════════════
# _state_response
# ═══════════════════════════════════════════════════════════════════════════════

class TestStateResponse(SimpleTestCase):

    def test_required_keys_present(self):
        s = make_session()
        with patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            resp = _state_response(s, [], [])

        for key in ('session_id', 'status', 'sim_time', 'sim_progress',
                    'clock_speed', 'kpis', 'new_interactions',
                    'new_alerts', 'all_alerts', 'thresholds'):
            self.assertIn(key, resp)

    def test_kpis_subkeys_present(self):
        s = make_session()
        with patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            resp = _state_response(s, [], [])

        for key in ('entrantes', 'atendidas', 'abandonadas',
                    'na_pct', 'sl_pct', 'abandon_pct', 'aht_s', 'aht_min'):
            self.assertIn(key, resp['kpis'])

    def test_new_interactions_count(self):
        s = make_session()
        rows = [make_interaction() for _ in range(5)]
        with patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            resp = _state_response(s, rows, [])
        self.assertEqual(resp['new_interactions'], 5)

    def test_sim_time_string_format(self):
        s = make_session()
        with patch('sim.gtr_engine.time') as mt:
            mt.time.return_value = s.started_at_real
            resp = _state_response(s, [], [])
        # debe ser "HH:MM"
        self.assertRegex(resp['sim_time'], r'^\d{2}:\d{2}$')
