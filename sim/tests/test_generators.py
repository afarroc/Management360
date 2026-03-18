# sim/tests/test_generators.py
"""
Tests unitarios para los generadores del simulador.
No requieren base de datos — usan SimpleTestCase.

Cobertura:
  generators/base.py    → weighted_choice, gaussian_duration, intraday_slot,
                          daily_volume, synthetic_lead_id, agent_tmo_factor,
                          agent_sph_factor, is_working_day, generate_agent_pool
  generators/inbound.py → _get_config, generate_day
  generators/outbound.py→ generate_day (domingo, contacto, tipificaciones)
  generators/digital.py → _match_tmo, generate_day
"""

import random
from datetime import datetime, date
from collections import Counter

from django.test import SimpleTestCase

from sim.generators.base import (
    weighted_choice, gaussian_duration, intraday_slot,
    daily_volume, synthetic_lead_id,
    agent_tmo_factor, agent_sph_factor,
    is_working_day, generate_agent_pool,
)
from sim.generators import inbound as inb
from sim.generators import outbound as out
from sim.generators import digital as dig


# ─── helpers ────────────────────────────────────────────────────────────────

MONDAY    = datetime(2026, 3, 16)   # weekday=0
TUESDAY   = datetime(2026, 3, 17)   # weekday=1
SATURDAY  = datetime(2026, 3, 21)   # weekday=5
SUNDAY    = datetime(2026, 3, 22)   # weekday=6

INTRADAY = {9: 0.123, 10: 0.135, 11: 0.136,
            12: 0.116, 13: 0.102, 14: 0.096,
            15: 0.096, 16: 0.109, 17: 0.087}

AGENT_POOL = [
    {'codigo': 'AGT-001', 'turno': 'MANANA', 'antiguedad': 'senior',
     'sph_base': 0.128, 'adherencia_base': 0.95, 'tmo_factor': 1.0},
    {'codigo': 'AGT-002', 'turno': 'MANANA', 'antiguedad': 'junior',
     'sph_base': 0.091, 'adherencia_base': 0.93, 'tmo_factor': 1.15},
]

REQUIRED_INTERACTION_FIELDS = {
    'canal', 'skill', 'sub_canal', 'fecha', 'hora_inicio', 'hora_fin',
    'duracion_s', 'acw_s', 'tipificacion', 'status',
    'lead_id', 'agent_codigo', 'intento_num', 'is_simulated',
}


# ═══════════════════════════════════════════════════════════════════════════════
# base.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestWeightedChoice(SimpleTestCase):

    def test_returns_key_from_dict(self):
        weights = {'A': 0.6, 'B': 0.3, 'C': 0.1}
        for _ in range(100):
            result = weighted_choice(weights)
            self.assertIn(result, weights)

    def test_single_option_always_returned(self):
        for _ in range(50):
            self.assertEqual(weighted_choice({'X': 1.0}), 'X')

    def test_approximate_distribution(self):
        """Peso 0.7 debe ganar en ~70% de los casos (tolerancia amplia)."""
        weights = {'HIGH': 0.7, 'LOW': 0.3}
        counts  = Counter(weighted_choice(weights) for _ in range(2000))
        ratio   = counts['HIGH'] / 2000
        self.assertGreater(ratio, 0.60)
        self.assertLess(ratio,    0.80)

    def test_unequal_weights_not_crashing(self):
        """Pesos que no suman 1.0 no deben lanzar excepción."""
        weights = {'A': 3, 'B': 7}
        for _ in range(50):
            self.assertIn(weighted_choice(weights), weights)


class TestGaussianDuration(SimpleTestCase):

    def test_returns_int(self):
        self.assertIsInstance(gaussian_duration(300), int)

    def test_within_bounds(self):
        for _ in range(500):
            val = gaussian_duration(300, 0.15, min_s=60, max_s=600)
            self.assertGreaterEqual(val, 60)
            self.assertLessEqual(val,   600)

    def test_custom_bounds(self):
        for _ in range(200):
            val = gaussian_duration(100, 0.30, min_s=10, max_s=200)
            self.assertGreaterEqual(val, 10)
            self.assertLessEqual(val,   200)

    def test_mean_approximately_respected(self):
        samples = [gaussian_duration(300, 0.15, min_s=10, max_s=1000)
                   for _ in range(1000)]
        avg = sum(samples) / len(samples)
        self.assertGreater(avg, 260)
        self.assertLess(avg,    340)


class TestIntradaySlot(SimpleTestCase):

    def test_returns_datetime(self):
        result = intraday_slot(INTRADAY, MONDAY)
        self.assertIsInstance(result, datetime)

    def test_hour_within_intraday_keys(self):
        for _ in range(200):
            result = intraday_slot(INTRADAY, MONDAY)
            self.assertIn(result.hour, INTRADAY)

    def test_minute_and_second_in_range(self):
        for _ in range(100):
            result = intraday_slot(INTRADAY, MONDAY)
            self.assertGreaterEqual(result.minute, 0)
            self.assertLessEqual(result.minute,   59)
            self.assertGreaterEqual(result.second, 0)
            self.assertLessEqual(result.second,   59)

    def test_date_preserved(self):
        result = intraday_slot(INTRADAY, MONDAY)
        self.assertEqual(result.date(), MONDAY.date())


class TestDailyVolume(SimpleTestCase):

    def test_non_negative(self):
        for wd in range(7):
            self.assertGreaterEqual(daily_volume(1490, wd), 0)

    def test_weekend_lower_than_weekday(self):
        """Promedio fin de semana debe ser menor al de lunes."""
        weekday_avg = sum(daily_volume(1490, 0) for _ in range(200)) / 200
        weekend_avg = sum(daily_volume(1490, 6) for _ in range(200)) / 200
        self.assertLess(weekend_avg, weekday_avg)

    def test_sunday_is_reduced(self):
        """Domingo con factor 0.59 debería dar ~59% del volumen weekday."""
        weekday_avg = sum(daily_volume(1490, 0) for _ in range(500)) / 500
        sunday_avg  = sum(daily_volume(1490, 6) for _ in range(500)) / 500
        ratio       = sunday_avg / weekday_avg
        self.assertGreater(ratio, 0.45)
        self.assertLess(ratio,    0.75)

    def test_returns_int(self):
        self.assertIsInstance(daily_volume(1000, 0), int)


class TestSyntheticLeadId(SimpleTestCase):

    def test_inbound_prefix(self):
        self.assertTrue(synthetic_lead_id('inbound', 1).startswith('CLI-'))

    def test_outbound_prefix(self):
        self.assertTrue(synthetic_lead_id('outbound', 1).startswith('LID-'))

    def test_digital_prefix(self):
        self.assertTrue(synthetic_lead_id('digital', 1).startswith('DIG-'))

    def test_unknown_canal_prefix(self):
        self.assertTrue(synthetic_lead_id('unknown', 1).startswith('GEN-'))

    def test_index_zero_padded_8_digits(self):
        result = synthetic_lead_id('inbound', 42)
        self.assertEqual(result, 'CLI-00000042')

    def test_unique_per_index(self):
        ids = [synthetic_lead_id('inbound', i) for i in range(100)]
        self.assertEqual(len(set(ids)), 100)


class TestAgentFactors(SimpleTestCase):

    def test_tmo_factor_senior(self):
        self.assertEqual(agent_tmo_factor('senior'), 1.0)

    def test_tmo_factor_junior(self):
        self.assertEqual(agent_tmo_factor('junior'), 1.15)

    def test_tmo_factor_unknown(self):
        self.assertEqual(agent_tmo_factor('trainee'), 1.0)

    def test_sph_factor_senior(self):
        self.assertEqual(agent_sph_factor('senior'), 1.0)

    def test_sph_factor_junior(self):
        self.assertAlmostEqual(agent_sph_factor('junior'), 0.71)

    def test_sph_factor_unknown(self):
        self.assertEqual(agent_sph_factor('otro'), 1.0)


class TestIsWorkingDay(SimpleTestCase):

    def test_monday_is_working(self):
        self.assertTrue(is_working_day(MONDAY))

    def test_friday_is_working(self):
        friday = datetime(2026, 3, 20)
        self.assertTrue(is_working_day(friday))

    def test_sunday_is_not_working(self):
        self.assertFalse(is_working_day(SUNDAY))

    def test_saturday_not_working_by_default(self):
        self.assertFalse(is_working_day(SATURDAY))

    def test_saturday_working_when_enabled(self):
        self.assertTrue(is_working_day(SATURDAY, include_saturday=True))


class TestGenerateAgentPool(SimpleTestCase):

    def setUp(self):
        self.pool = generate_agent_pool(
            n_agents=20, turnos=['MANANA', 'TARDE'],
            sph_base=0.128, adherencia_base=0.931
        )

    def test_correct_count(self):
        self.assertEqual(len(self.pool), 20)

    def test_required_fields_present(self):
        required = {'codigo', 'turno', 'antiguedad', 'sph_base',
                    'adherencia_base', 'tmo_factor'}
        for agent in self.pool:
            self.assertTrue(required.issubset(agent.keys()))

    def test_turno_from_list(self):
        for agent in self.pool:
            self.assertIn(agent['turno'], ['MANANA', 'TARDE'])

    def test_antiguedad_valid(self):
        for agent in self.pool:
            self.assertIn(agent['antiguedad'], ['senior', 'junior'])

    def test_adherencia_within_real_range(self):
        for agent in self.pool:
            self.assertGreaterEqual(agent['adherencia_base'], 0.696)
            self.assertLessEqual(agent['adherencia_base'],    0.999)

    def test_sph_positive(self):
        for agent in self.pool:
            self.assertGreater(agent['sph_base'], 0)

    def test_codigo_format(self):
        for agent in self.pool:
            self.assertTrue(agent['codigo'].startswith('AGT-'))


# ═══════════════════════════════════════════════════════════════════════════════
# generators/inbound.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestInboundGetConfig(SimpleTestCase):

    def test_defaults_present_without_override(self):
        cfg = inb._get_config({})
        self.assertIn('weekday_vol', cfg)
        self.assertIn('skills', cfg)
        self.assertIn('intraday', cfg)

    def test_override_replaces_value(self):
        cfg = inb._get_config({'weekday_vol': 999})
        self.assertEqual(cfg['weekday_vol'], 999)

    def test_skills_preserved_when_not_overridden(self):
        cfg = inb._get_config({'weekday_vol': 500})
        self.assertIn('PLD', cfg['skills'])


class TestInboundGenerateDay(SimpleTestCase):

    def setUp(self):
        random.seed(42)
        self.rows = inb.generate_day(MONDAY, AGENT_POOL, {}, lead_offset=0)

    def test_returns_list(self):
        self.assertIsInstance(self.rows, list)

    def test_volume_reasonable_for_weekday(self):
        """Debe generar entre 800 y 2500 interacciones en un lunes."""
        self.assertGreater(len(self.rows), 800)
        self.assertLess(len(self.rows),    2500)

    def test_all_required_fields_present(self):
        for row in self.rows[:20]:
            missing = REQUIRED_INTERACTION_FIELDS - set(row.keys())
            self.assertEqual(missing, set(), msg=f"Campos faltantes: {missing}")

    def test_canal_is_inbound(self):
        for row in self.rows[:50]:
            self.assertEqual(row['canal'], 'inbound')

    def test_status_valid(self):
        valid = {'atendida', 'abandonada'}
        for row in self.rows[:100]:
            self.assertIn(row['status'], valid)

    def test_fecha_matches_date(self):
        for row in self.rows[:20]:
            self.assertEqual(row['fecha'], MONDAY.date())

    def test_is_simulated_true(self):
        for row in self.rows[:20]:
            self.assertTrue(row['is_simulated'])

    def test_lead_id_prefix(self):
        for row in self.rows[:20]:
            self.assertTrue(row['lead_id'].startswith('CLI-'))

    def test_abandoned_has_no_agent(self):
        abandoned = [r for r in self.rows if r['status'] == 'abandonada']
        self.assertTrue(len(abandoned) > 0, "Debería haber llamadas abandonadas")
        for row in abandoned:
            self.assertIsNone(row['agent_codigo'])

    def test_abandoned_acw_is_zero(self):
        for row in self.rows:
            if row['status'] == 'abandonada':
                self.assertEqual(row['acw_s'], 0)

    def test_duration_positive(self):
        for row in self.rows[:50]:
            self.assertGreater(row['duracion_s'], 0)

    def test_hora_fin_after_hora_inicio(self):
        for row in self.rows[:50]:
            self.assertGreater(row['hora_fin'], row['hora_inicio'])

    def test_skill_in_config(self):
        valid_skills = set(inb.DEFAULT_CONFIG['skills'].keys())
        for row in self.rows[:50]:
            self.assertIn(row['skill'], valid_skills)

    def test_weekend_lower_volume(self):
        random.seed(42)
        weekday_rows = inb.generate_day(MONDAY,   AGENT_POOL, {})
        weekend_rows = inb.generate_day(SATURDAY, AGENT_POOL, {})
        self.assertLess(len(weekend_rows), len(weekday_rows))

    def test_abandon_rate_roughly_calibrated(self):
        """Tasa de abandono global debe estar cerca del 3.9% (±3pp)."""
        abandonadas = sum(1 for r in self.rows if r['status'] == 'abandonada')
        rate = abandonadas / len(self.rows)
        self.assertGreater(rate, 0.01)
        self.assertLess(rate,    0.12)


# ═══════════════════════════════════════════════════════════════════════════════
# generators/outbound.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestOutboundGenerateDay(SimpleTestCase):

    def setUp(self):
        random.seed(42)
        self.rows = out.generate_day(MONDAY, AGENT_POOL, {}, lead_offset=0)

    def test_sunday_returns_empty(self):
        rows = out.generate_day(SUNDAY, AGENT_POOL, {})
        self.assertEqual(rows, [])

    def test_returns_list(self):
        self.assertIsInstance(self.rows, list)

    def test_volume_high_for_outbound(self):
        """Outbound genera ~131k marcaciones; testeamos escala, no número exacto."""
        self.assertGreater(len(self.rows), 50_000)
        self.assertLess(len(self.rows),    200_000)

    def test_all_required_fields_present(self):
        for row in self.rows[:20]:
            missing = REQUIRED_INTERACTION_FIELDS - set(row.keys())
            self.assertEqual(missing, set(), msg=f"Campos faltantes: {missing}")

    def test_canal_is_outbound(self):
        for row in self.rows[:50]:
            self.assertEqual(row['canal'], 'outbound')

    def test_status_valid(self):
        valid = {'venta', 'agenda', 'atendida', 'rechazo', 'no_contacto'}
        for row in self.rows[:200]:
            self.assertIn(row['status'], valid)

    def test_no_contacto_has_no_agent(self):
        no_contact = [r for r in self.rows[:500] if r['status'] == 'no_contacto']
        self.assertTrue(len(no_contact) > 0)
        for row in no_contact:
            self.assertIsNone(row['agent_codigo'])

    def test_no_contacto_acw_is_zero(self):
        for row in self.rows[:200]:
            if row['status'] == 'no_contacto':
                self.assertEqual(row['acw_s'], 0)

    def test_contact_rate_approximately_correct(self):
        """Contactabilidad real ~27.6% — toleramos ±5pp."""
        sample = self.rows[:5000]
        contacts = sum(1 for r in sample if r['status'] != 'no_contacto')
        rate = contacts / len(sample)
        self.assertGreater(rate, 0.20)
        self.assertLess(rate,    0.35)

    def test_lead_id_prefix(self):
        for row in self.rows[:20]:
            self.assertTrue(row['lead_id'].startswith('LID-'))

    def test_is_simulated_true(self):
        for row in self.rows[:20]:
            self.assertTrue(row['is_simulated'])

    def test_fecha_matches_date(self):
        for row in self.rows[:20]:
            self.assertEqual(row['fecha'], MONDAY.date())

    def test_duration_positive(self):
        for row in self.rows[:50]:
            self.assertGreater(row['duracion_s'], 0)

    def test_intento_num_between_1_and_5(self):
        for row in self.rows[:100]:
            self.assertGreaterEqual(row['intento_num'], 1)
            self.assertLessEqual(row['intento_num'],    5)

    def test_ventas_exist(self):
        ventas = [r for r in self.rows if r['status'] == 'venta']
        self.assertTrue(len(ventas) > 0, "Debería haber ventas en un día completo")

    def test_saturday_lower_volume(self):
        random.seed(42)
        monday_rows   = out.generate_day(MONDAY,   AGENT_POOL, {})
        saturday_rows = out.generate_day(SATURDAY, AGENT_POOL, {})
        self.assertLess(len(saturday_rows), len(monday_rows))


# ═══════════════════════════════════════════════════════════════════════════════
# generators/digital.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestDigitalMatchTmo(SimpleTestCase):

    def setUp(self):
        self.tmo_map = dig.DEFAULT_CONFIG['tmo_by_tipif']

    def test_exact_key_match(self):
        cfg = dig._match_tmo('BXI_ACTIVACION USUARIO NUEVO', self.tmo_map)
        self.assertEqual(cfg['mean'], 240)

    def test_partial_key_match_case_insensitive(self):
        cfg = dig._match_tmo('APP_INCIDENCIA CON EL LOGUEO', self.tmo_map)
        self.assertEqual(cfg['mean'], 320)   # matches 'INCIDENCIA'

    def test_fallback_to_default(self):
        cfg = dig._match_tmo('TIPIF_DESCONOCIDA', self.tmo_map)
        self.assertEqual(cfg['mean'], dig.DEFAULT_CONFIG['tmo_by_tipif']['DEFAULT']['mean'])


class TestDigitalGenerateDay(SimpleTestCase):

    def setUp(self):
        random.seed(42)
        self.rows = dig.generate_day(MONDAY, AGENT_POOL, {}, lead_offset=0)

    def test_returns_list(self):
        self.assertIsInstance(self.rows, list)

    def test_volume_reasonable(self):
        """Volumen diario digital ~203 (±varianza)."""
        self.assertGreater(len(self.rows), 80)
        self.assertLess(len(self.rows),    400)

    def test_all_required_fields_present(self):
        for row in self.rows:
            missing = REQUIRED_INTERACTION_FIELDS - set(row.keys())
            self.assertEqual(missing, set(), msg=f"Campos faltantes: {missing}")

    def test_canal_is_digital(self):
        for row in self.rows:
            self.assertEqual(row['canal'], 'digital')

    def test_status_always_atendida(self):
        for row in self.rows:
            self.assertEqual(row['status'], 'atendida')

    def test_sub_canal_bxi_or_app(self):
        for row in self.rows:
            self.assertIn(row['sub_canal'], {'bxi', 'app'})

    def test_bxi_tipif_prefix(self):
        bxi_rows = [r for r in self.rows if r['sub_canal'] == 'bxi']
        self.assertTrue(len(bxi_rows) > 0)
        for row in bxi_rows:
            self.assertTrue(row['tipificacion'].startswith('BXI_'))

    def test_app_tipif_prefix(self):
        app_rows = [r for r in self.rows if r['sub_canal'] == 'app']
        self.assertTrue(len(app_rows) > 0)
        for row in app_rows:
            self.assertTrue(row['tipificacion'].startswith('APP_'))

    def test_bxi_is_majority(self):
        """BXI = 84.9% del canal digital."""
        bxi_count = sum(1 for r in self.rows if r['sub_canal'] == 'bxi')
        ratio = bxi_count / len(self.rows)
        self.assertGreater(ratio, 0.70)
        self.assertLess(ratio,    0.95)

    def test_lead_id_prefix(self):
        for row in self.rows:
            self.assertTrue(row['lead_id'].startswith('DIG-'))

    def test_is_simulated_true(self):
        for row in self.rows:
            self.assertTrue(row['is_simulated'])

    def test_fecha_matches_date(self):
        for row in self.rows:
            self.assertEqual(row['fecha'], MONDAY.date())

    def test_duration_positive(self):
        for row in self.rows:
            self.assertGreater(row['duracion_s'], 0)

    def test_hora_fin_after_hora_inicio(self):
        for row in self.rows:
            self.assertGreater(row['hora_fin'], row['hora_inicio'])

    def test_skill_is_canales_digitales(self):
        for row in self.rows:
            self.assertEqual(row['skill'], 'CANALES DIGITALES')
