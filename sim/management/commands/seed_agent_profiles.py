# sim/management/commands/seed_agent_profiles.py
"""
Crea los perfiles de agente simulado del sistema (is_preset=True).
Idempotente — safe ejecutar múltiples veces.

Uso:
    python manage.py seed_agent_profiles

BOT-2 (2026-03-22): añadidos BOT_PRESETS + _seed_bot_presets().
Fix: data.pop() reemplazado por data.get() para evitar mutación de dicts en PRESETS.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from sim.models import SimAgentProfile

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Perfiles base del sistema (tier × canal)
# ─────────────────────────────────────────────────────────────────────────────

PRESETS = [
    # ── Inbound ──────────────────────────────────────────────────────────────
    {
        'name': 'Inbound — Top',        'tier': 'top',   'canal': 'inbound',
        'description': 'Agente de alto rendimiento: AHT bajo, sin hold, sin cortes, alta disponibilidad.',
        'aht_factor': 0.85, 'acw_factor': 0.80, 'available_pct': 0.92,
        'answer_rate': 0.99, 'hold_rate': 0.02, 'hold_dur_s': 20,
        'transfer_rate': 0.02, 'corte_rate': 0.01,
        'conv_rate': 0.0, 'agenda_rate': 0.0,
        'break_freq': 0.5, 'break_dur_s': 240, 'shrinkage': 0.06,
    },
    {
        'name': 'Inbound — Alto',       'tier': 'alto',  'canal': 'inbound',
        'description': 'Agente experimentado: levemente sobre el promedio en velocidad y disponibilidad.',
        'aht_factor': 0.95, 'acw_factor': 0.90, 'available_pct': 0.87,
        'answer_rate': 0.97, 'hold_rate': 0.05, 'hold_dur_s': 30,
        'transfer_rate': 0.04, 'corte_rate': 0.03,
        'conv_rate': 0.0, 'agenda_rate': 0.0,
        'break_freq': 0.8, 'break_dur_s': 270, 'shrinkage': 0.08,
    },
    {
        'name': 'Inbound — Medio',      'tier': 'medio', 'canal': 'inbound',
        'description': 'Agente promedio del equipo: calibrado con datos Banca Telefónica.',
        'aht_factor': 1.05, 'acw_factor': 1.05, 'available_pct': 0.80,
        'answer_rate': 0.93, 'hold_rate': 0.10, 'hold_dur_s': 35,
        'transfer_rate': 0.07, 'corte_rate': 0.08,
        'conv_rate': 0.0, 'agenda_rate': 0.0,
        'break_freq': 1.2, 'break_dur_s': 300, 'shrinkage': 0.10,
    },
    {
        'name': 'Inbound — Bajo',       'tier': 'bajo',  'canal': 'inbound',
        'description': 'Agente nuevo o bajo rendimiento: AHT alto, frecuentes holds y breaks.',
        'aht_factor': 1.30, 'acw_factor': 1.25, 'available_pct': 0.70,
        'answer_rate': 0.85, 'hold_rate': 0.18, 'hold_dur_s': 50,
        'transfer_rate': 0.12, 'corte_rate': 0.15,
        'conv_rate': 0.0, 'agenda_rate': 0.0,
        'break_freq': 2.0, 'break_dur_s': 360, 'shrinkage': 0.16,
    },
    # ── Outbound ─────────────────────────────────────────────────────────────
    {
        'name': 'Outbound — Top Ventas', 'tier': 'top',  'canal': 'outbound',
        'description': 'Agente top ventas: conversión 2.5%, SPH alto, sin cortes.',
        'aht_factor': 0.88, 'acw_factor': 0.80, 'available_pct': 0.92,
        'answer_rate': 0.99, 'hold_rate': 0.01, 'hold_dur_s': 15,
        'transfer_rate': 0.01, 'corte_rate': 0.01,
        'conv_rate': 0.025, 'agenda_rate': 0.15,
        'break_freq': 0.5, 'break_dur_s': 240, 'shrinkage': 0.06,
        'skills': ['PORTABILIDAD', 'LINEA NUEVA'],
        'skill_priority': {'PORTABILIDAD': 1, 'LINEA NUEVA': 2},
    },
    {
        'name': 'Outbound — Alto',       'tier': 'alto', 'canal': 'outbound',
        'description': 'Agente con buen desempeño: conversión 1.5%, agenda alta.',
        'aht_factor': 0.95, 'acw_factor': 0.90, 'available_pct': 0.87,
        'answer_rate': 0.97, 'hold_rate': 0.03, 'hold_dur_s': 20,
        'transfer_rate': 0.02, 'corte_rate': 0.03,
        'conv_rate': 0.015, 'agenda_rate': 0.13,
        'break_freq': 0.8, 'break_dur_s': 270, 'shrinkage': 0.08,
        'skills': ['PORTABILIDAD'],
        'skill_priority': {'PORTABILIDAD': 1},
    },
    {
        'name': 'Outbound — Medio',      'tier': 'medio', 'canal': 'outbound',
        'description': 'Agente promedio: calibrado con SPH 0.128 Conduent/ENTEL.',
        'aht_factor': 1.05, 'acw_factor': 1.05, 'available_pct': 0.80,
        'answer_rate': 0.93, 'hold_rate': 0.08, 'hold_dur_s': 30,
        'transfer_rate': 0.04, 'corte_rate': 0.08,
        'conv_rate': 0.008, 'agenda_rate': 0.10,
        'break_freq': 1.2, 'break_dur_s': 300, 'shrinkage': 0.10,
        'skills': ['PORTABILIDAD'],
        'skill_priority': {'PORTABILIDAD': 1},
    },
    {
        'name': 'Outbound — Bajo',       'tier': 'bajo', 'canal': 'outbound',
        'description': 'Agente nuevo o bajo rendimiento: conversión casi nula, corta llamadas.',
        'aht_factor': 1.30, 'acw_factor': 1.20, 'available_pct': 0.70,
        'answer_rate': 0.85, 'hold_rate': 0.15, 'hold_dur_s': 45,
        'transfer_rate': 0.08, 'corte_rate': 0.18,
        'conv_rate': 0.003, 'agenda_rate': 0.05,
        'break_freq': 2.0, 'break_dur_s': 360, 'shrinkage': 0.16,
        'skills': ['PORTABILIDAD'],
        'skill_priority': {'PORTABILIDAD': 1},
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# BOT-2: Perfiles preset para BotInstances en ACD
# Mapping specialization → tier:
#   communication_handler → top   (relación con cliente, velocidad, conv alta)
#   gtd_processor         → alto  (productivo, buen TMO, convierte menos)
#   project_manager       → alto  (metódico, hold moderado)
#   task_executor         → medio (volumen alto, AHT estándar)
#   calendar_optimizer    → medio (agenda_rate mayor que el resto)
#   general_assistant     → medio (comodín)
# ─────────────────────────────────────────────────────────────────────────────

BOT_PRESETS = [
    {
        'bot_specialization': 'communication_handler',
        'name':        'Bot — Communication Handler',
        'description': 'Bot especializado en comunicación. Perfil top: TMO rápido, alta conversión.',
        'tier':        'top',
        'canal':       'inbound',
        'aht_factor':     0.85,
        'acw_factor':     0.85,
        'available_pct':  0.92,
        'answer_rate':    0.97,
        'hold_rate':      0.02,
        'hold_dur_s':     20,
        'transfer_rate':  0.02,
        'corte_rate':     0.01,
        'conv_rate':      0.025,
        'agenda_rate':    0.15,
        'break_freq':     0.5,
        'break_dur_s':    180,
        'shrinkage':      0.06,
        'skills':         [],
        'skill_priority': {},
    },
    {
        'bot_specialization': 'gtd_processor',
        'name':        'Bot — GTD Processor',
        'description': 'Bot procesador GTD. Perfil alto: buen TMO, bajo hold, moderada conversión.',
        'tier':        'alto',
        'canal':       'inbound',
        'aht_factor':     0.95,
        'acw_factor':     0.90,
        'available_pct':  0.87,
        'answer_rate':    0.96,
        'hold_rate':      0.05,
        'hold_dur_s':     25,
        'transfer_rate':  0.03,
        'corte_rate':     0.03,
        'conv_rate':      0.015,
        'agenda_rate':    0.12,
        'break_freq':     0.8,
        'break_dur_s':    240,
        'shrinkage':      0.08,
        'skills':         [],
        'skill_priority': {},
    },
    {
        'bot_specialization': 'project_manager',
        'name':        'Bot — Project Manager',
        'description': 'Bot gestor de proyectos. Perfil alto: metódico, hold moderado.',
        'tier':        'alto',
        'canal':       'inbound',
        'aht_factor':     0.95,
        'acw_factor':     1.00,
        'available_pct':  0.87,
        'answer_rate':    0.95,
        'hold_rate':      0.07,
        'hold_dur_s':     35,
        'transfer_rate':  0.05,
        'corte_rate':     0.03,
        'conv_rate':      0.012,
        'agenda_rate':    0.14,
        'break_freq':     0.8,
        'break_dur_s':    260,
        'shrinkage':      0.09,
        'skills':         [],
        'skill_priority': {},
    },
    {
        'bot_specialization': 'task_executor',
        'name':        'Bot — Task Executor',
        'description': 'Bot ejecutor de tareas. Perfil medio: volumen alto, AHT estándar.',
        'tier':        'medio',
        'canal':       'inbound',
        'aht_factor':     1.05,
        'acw_factor':     1.05,
        'available_pct':  0.80,
        'answer_rate':    0.94,
        'hold_rate':      0.10,
        'hold_dur_s':     30,
        'transfer_rate':  0.04,
        'corte_rate':     0.08,
        'conv_rate':      0.008,
        'agenda_rate':    0.10,
        'break_freq':     1.0,
        'break_dur_s':    300,
        'shrinkage':      0.10,
        'skills':         [],
        'skill_priority': {},
    },
    {
        'bot_specialization': 'calendar_optimizer',
        'name':        'Bot — Calendar Optimizer',
        'description': 'Bot optimizador de calendario. Perfil medio: agenda_rate mayor.',
        'tier':        'medio',
        'canal':       'inbound',
        'aht_factor':     1.05,
        'acw_factor':     1.00,
        'available_pct':  0.82,
        'answer_rate':    0.95,
        'hold_rate':      0.08,
        'hold_dur_s':     30,
        'transfer_rate':  0.04,
        'corte_rate':     0.06,
        'conv_rate':      0.006,
        'agenda_rate':    0.22,
        'break_freq':     1.0,
        'break_dur_s':    300,
        'shrinkage':      0.10,
        'skills':         [],
        'skill_priority': {},
    },
    {
        'bot_specialization': 'general_assistant',
        'name':        'Bot — General Assistant',
        'description': 'Bot asistente general. Perfil medio: comodín para todas las tareas.',
        'tier':        'medio',
        'canal':       'inbound',
        'aht_factor':     1.05,
        'acw_factor':     1.05,
        'available_pct':  0.80,
        'answer_rate':    0.93,
        'hold_rate':      0.10,
        'hold_dur_s':     30,
        'transfer_rate':  0.04,
        'corte_rate':     0.08,
        'conv_rate':      0.008,
        'agenda_rate':    0.10,
        'break_freq':     1.0,
        'break_dur_s':    300,
        'shrinkage':      0.10,
        'skills':         [],
        'skill_priority': {},
    },
]


class Command(BaseCommand):
    help = 'Crea los perfiles de agente simulado predefinidos del sistema (is_preset=True).'

    def handle(self, *args, **options):
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            self.stderr.write('No hay superusuario en el sistema. Crea uno primero.')
            return

        self._seed_base_presets(superuser)
        self._seed_bot_presets(superuser)   # BOT-2

    def _seed_base_presets(self, superuser):
        """Crea/actualiza los 8 perfiles base (tier × canal)."""
        created = updated = 0

        for data in PRESETS:
            # .get() en lugar de .pop() — no muta el dict; safe para tests/doble llamada
            skills         = data.get('skills', [])
            skill_priority = data.get('skill_priority', {})

            _, is_new = SimAgentProfile.objects.update_or_create(
                name=data['name'],
                is_preset=True,
                defaults={
                    **{k: v for k, v in data.items() if k not in ('skills', 'skill_priority')},
                    'skills':         skills,
                    'skill_priority': skill_priority,
                    'is_preset':      True,
                    'created_by':     superuser,
                },
            )
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'SimAgentProfile base: {created} creados, {updated} actualizados.'
            )
        )

    def _seed_bot_presets(self, superuser):
        """
        BOT-2: Crea/actualiza 6 perfiles preset para BotInstances en ACD.
        Idempotente — lookup por bot_specialization + is_preset=True.
        """
        created = updated = 0

        for data in BOT_PRESETS:
            spec = data['bot_specialization']
            _, is_new = SimAgentProfile.objects.update_or_create(
                bot_specialization=spec,
                is_preset=True,
                defaults={**data, 'created_by': superuser},
            )
            label = 'CREADO  ' if is_new else 'OK      '
            name  = data['name']
            self.stdout.write(f'  [{label}] {name}  ({spec})')
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'SimAgentProfile bots: {created} creados, {updated} actualizados.'
            )
        )
