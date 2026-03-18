# sim/migrations/0004_add_acd.py
"""
SIM-7a — ACD Simulator.
Agrega: ACDSession, ACDAgentSlot, ACDInteraction, ACDAgentAction.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('sim', '0004_remove_simagent_unique_agent_per_account_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ACDSession',
            fields=[
                ('id',             models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('name',           models.CharField(max_length=200, verbose_name='Nombre')),
                ('dialing_mode',   models.CharField(max_length=15, default='progressive', choices=[
                                       ('predictive','Predictivo'),('progressive','Progresivo'),('manual','Manual')])),
                ('canal',          models.CharField(max_length=20, choices=[
                                       ('inbound','Inbound Voz'),('outbound','Outbound Discador'),
                                       ('digital','Digital (Chat/Mail/App)'),('mixed','Mixto')], default='inbound')),
                ('clock_speed',    models.IntegerField(default=15)),
                ('sim_date',       models.DateField(null=True, blank=True)),
                ('status',         models.CharField(max_length=10, default='config', choices=[
                                       ('config','Configurando'),('active','Activa'),
                                       ('paused','Pausada'),('finished','Finalizada')])),
                ('gtr_session_id', models.CharField(max_length=100, blank=True)),
                ('thresholds',     models.JSONField(default=dict)),
                ('config',         models.JSONField(default=dict)),
                ('started_at',     models.DateTimeField(auto_now_add=True)),
                ('finished_at',    models.DateTimeField(null=True, blank=True)),
                ('account',        models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                       related_name='acd_sessions', to='sim.simaccount')),
                ('created_by',     models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                       related_name='acd_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Sesión ACD', 'verbose_name_plural': 'Sesiones ACD',
                     'ordering': ['-started_at']},
        ),
        migrations.CreateModel(
            name='ACDAgentSlot',
            fields=[
                ('id',           models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('slot_number',  models.IntegerField(default=1)),
                ('agent_type',   models.CharField(max_length=10, default='simulated', choices=[
                                     ('real','OJT Real'),('simulated','Simulado')])),
                ('display_name', models.CharField(max_length=100, blank=True)),
                ('skill',        models.CharField(max_length=100, blank=True)),
                ('status',       models.CharField(max_length=12, default='offline', choices=[
                                     ('offline','Offline'),('available','Disponible'),
                                     ('ringing','Timbrando'),('on_call','En Llamada'),
                                     ('acw','Post-llamada'),('break','Break'),('absent','Ausente')])),
                ('level',        models.CharField(max_length=15, default='basic', choices=[
                                     ('basic','Básico'),('intermediate','Intermedio'),
                                     ('advanced','Avanzado')])),
                ('stats',        models.JSONField(default=dict)),
                ('session',      models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                     related_name='slots', to='sim.acdsession')),
                ('user',         models.ForeignKey(null=True, blank=True,
                                     on_delete=django.db.models.deletion.SET_NULL,
                                     related_name='acd_slots', to=settings.AUTH_USER_MODEL)),
                ('profile',      models.ForeignKey(null=True, blank=True,
                                     on_delete=django.db.models.deletion.SET_NULL,
                                     related_name='acd_slots', to='sim.simagentprofile')),
            ],
            options={'verbose_name': 'Slot de agente ACD', 'verbose_name_plural': 'Slots de agente ACD',
                     'ordering': ['session', 'slot_number'],
                     'unique_together': {('session', 'slot_number')}},
        ),
        migrations.CreateModel(
            name='ACDInteraction',
            fields=[
                ('id',               models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('canal',            models.CharField(max_length=20, choices=[
                                         ('inbound','Inbound Voz'),('outbound','Outbound Discador'),
                                         ('digital','Digital (Chat/Mail/App)'),('mixed','Mixto')])),
                ('skill',            models.CharField(max_length=100, blank=True)),
                ('lead_id',          models.CharField(max_length=50, blank=True)),
                ('status',           models.CharField(max_length=12, default='queued', choices=[
                                         ('queued','En cola'),('ringing','Timbrando'),
                                         ('on_call','En llamada'),('acw','Post-llamada'),
                                         ('completed','Completada'),('abandoned','Abandonada'),
                                         ('rejected','Rechazada')])),
                ('queued_at',        models.DateTimeField(auto_now_add=True)),
                ('assigned_at',      models.DateTimeField(null=True, blank=True)),
                ('answered_at',      models.DateTimeField(null=True, blank=True)),
                ('ended_at',         models.DateTimeField(null=True, blank=True)),
                ('duration_s',       models.IntegerField(default=0)),
                ('acw_s',            models.IntegerField(default=0)),
                ('hold_s',           models.IntegerField(default=0)),
                ('tipificacion',     models.CharField(max_length=200, blank=True)),
                ('sub_tipificacion', models.CharField(max_length=200, blank=True)),
                ('notes',            models.TextField(blank=True)),
                ('is_simulated',     models.BooleanField(default=True)),
                ('session',          models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                         related_name='acd_interactions', to='sim.acdsession')),
                ('slot',             models.ForeignKey(null=True, blank=True,
                                         on_delete=django.db.models.deletion.SET_NULL,
                                         related_name='acd_interactions', to='sim.acdagentslot')),
            ],
            options={'verbose_name': 'Interacción ACD', 'verbose_name_plural': 'Interacciones ACD',
                     'ordering': ['-queued_at']},
        ),
        migrations.AddIndex(
            model_name='acdinteraction',
            index=models.Index(fields=['session', 'status'], name='sim_acdint_sess_status'),
        ),
        migrations.AddIndex(
            model_name='acdinteraction',
            index=models.Index(fields=['slot', 'queued_at'], name='sim_acdint_slot_queued'),
        ),
        migrations.CreateModel(
            name='ACDAgentAction',
            fields=[
                ('id',          models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('action_type', models.CharField(max_length=15, choices=[
                                    ('answer','Atender'),('reject','Rechazar'),
                                    ('hold','Hold'),('unhold','Retomar'),
                                    ('transfer','Transferir'),('tipify','Tipificar'),
                                    ('end_acw','Finalizar ACW'),('break','Ir a Break'),
                                    ('return','Volver de Break'),('note','Nota')])),
                ('params',      models.JSONField(default=dict)),
                ('sim_time',    models.CharField(max_length=5, blank=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('interaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='agent_actions', to='sim.acdinteraction')),
                ('slot',        models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='agent_actions', to='sim.acdagentslot')),
            ],
            options={'verbose_name': 'Acción de agente ACD', 'verbose_name_plural': 'Acciones de agente ACD',
                     'ordering': ['created_at']},
        ),
    ]
