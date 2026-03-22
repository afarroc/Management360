"""
sim/migrations/0007_bot2_acd.py

BOT-2: Agrega bot_specialization a SimAgentProfile + registra cambio de
choices en ACDAgentSlot.agent_type.

Corregido: depende de 0006 (no 0004 como indicaba el DEV_REFERENCE desactualizado).
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sim', '0006_rename_sim_acdint_sess_status_sim_acdinte_session_03abee_idx_and_more'),
    ]

    operations = [
        # ── 1. Nuevo campo en SimAgentProfile ──────────────────────────────────
        migrations.AddField(
            model_name='simagentprofile',
            name='bot_specialization',
            field=models.CharField(
                blank=True,
                max_length=50,
                help_text=(
                    'Especialización de BotInstance compatible con este perfil. '
                    'Valores: gtd_processor | project_manager | task_executor | '
                    'calendar_optimizer | communication_handler | general_assistant. '
                    'Vacío = perfil de uso general.'
                ),
            ),
        ),
        # ── 2. Registrar cambio de choices en ACDAgentSlot.agent_type ──────────
        # Sin DDL en MariaDB — solo actualiza el estado del grafo de migraciones.
        migrations.AlterField(
            model_name='acdagentslot',
            name='agent_type',
            field=models.CharField(
                choices=[
                    ('real',      'OJT Real'),
                    ('simulated', 'Simulado'),
                    ('bot',       'Bot FTE'),
                ],
                default='simulated',
                max_length=10,
            ),
        ),
    ]
