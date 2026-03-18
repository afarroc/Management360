# sim/migrations/0003_add_sim_agent_profile.py
"""
SIM-6a — Agrega SimAgentProfile.
Perfil conductual reutilizable para agentes simulados.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('sim', '0002_add_training'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SimAgentProfile',
            fields=[
                ('id',            models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('name',          models.CharField(max_length=200, verbose_name='Nombre')),
                ('description',   models.TextField(blank=True, verbose_name='Descripción')),
                ('tier',          models.CharField(max_length=10, default='medio', choices=[
                                      ('top','Top'),('alto','Alto'),('medio','Medio'),('bajo','Bajo')],
                                      verbose_name='Nivel')),
                ('canal',         models.CharField(max_length=20, default='inbound', choices=[
                                      ('inbound','Inbound Voz'),('outbound','Outbound Discador'),
                                      ('digital','Digital (Chat/Mail/App)'),('mixed','Mixto')],
                                      verbose_name='Canal')),
                # Velocidad
                ('aht_factor',    models.FloatField(default=1.0)),
                ('acw_factor',    models.FloatField(default=1.0)),
                ('available_pct', models.FloatField(default=0.85)),
                # Comportamiento
                ('answer_rate',   models.FloatField(default=0.95)),
                ('hold_rate',     models.FloatField(default=0.05)),
                ('hold_dur_s',    models.IntegerField(default=30)),
                ('transfer_rate', models.FloatField(default=0.04)),
                ('corte_rate',    models.FloatField(default=0.05)),
                # Resultados
                ('conv_rate',     models.FloatField(default=0.008)),
                ('agenda_rate',   models.FloatField(default=0.128)),
                # Ausencias
                ('break_freq',    models.FloatField(default=1.0)),
                ('break_dur_s',   models.IntegerField(default=300)),
                ('shrinkage',     models.FloatField(default=0.10)),
                # Multi-skill
                ('skills',        models.JSONField(default=list)),
                ('skill_priority',models.JSONField(default=dict)),
                # Meta
                ('is_preset',     models.BooleanField(default=False)),
                ('created_at',    models.DateTimeField(auto_now_add=True)),
                ('updated_at',    models.DateTimeField(auto_now=True)),
                ('created_by',    models.ForeignKey(
                                      on_delete=django.db.models.deletion.CASCADE,
                                      related_name='sim_agent_profiles',
                                      to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name':        'Perfil de agente simulado',
                'verbose_name_plural': 'Perfiles de agente simulado',
                'ordering':            ['tier', 'name'],
            },
        ),
    ]
