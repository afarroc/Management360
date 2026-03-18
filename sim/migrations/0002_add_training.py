# sim/migrations/0002_add_training.py
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('sim', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingScenario',
            fields=[
                ('id',               models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('name',             models.CharField(max_length=200, verbose_name='Nombre')),
                ('description',      models.TextField(blank=True, verbose_name='Descripción')),
                ('canal',            models.CharField(max_length=20, default='inbound', choices=[
                                         ('inbound','Inbound Voz'),('outbound','Outbound Discador'),
                                         ('digital','Digital (Chat/Mail/App)'),('mixed','Mixto')])),
                ('difficulty',       models.CharField(max_length=10, default='medium', choices=[
                                         ('easy','Básico'),('medium','Intermedio'),('hard','Avanzado')])),
                ('clock_speed',      models.IntegerField(default=15)),
                ('thresholds',       models.JSONField(default=dict)),
                ('events',           models.JSONField(default=list)),
                ('expected_actions', models.JSONField(default=list)),
                ('is_public',        models.BooleanField(default=False)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('updated_at',       models.DateTimeField(auto_now=True)),
                ('account',          models.ForeignKey(null=True, blank=True,
                                         on_delete=django.db.models.deletion.SET_NULL,
                                         related_name='training_scenarios',
                                         to='sim.simaccount',
                                         verbose_name='Cuenta simulada')),
                ('created_by',       models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                         related_name='training_scenarios',
                                         to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name':        'Escenario de training',
                'verbose_name_plural': 'Escenarios de training',
                'ordering':            ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='TrainingSession',
            fields=[
                ('id',               models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('gtr_session_id',   models.CharField(max_length=100, blank=True)),
                ('sim_date',         models.DateField(null=True, blank=True)),
                ('status',           models.CharField(max_length=15, default='active', choices=[
                                         ('active','En curso'),('completed','Completada'),
                                         ('abandoned','Abandonada')])),
                ('score',            models.IntegerField(default=0)),
                ('score_detail',     models.JSONField(default=dict)),
                ('alerts_count',     models.IntegerField(default=0)),
                ('events_responded', models.IntegerField(default=0)),
                ('actions_log',      models.JSONField(default=list)),
                ('final_kpis',       models.JSONField(default=dict)),
                ('trainer_notes',    models.TextField(blank=True)),
                ('started_at',       models.DateTimeField(auto_now_add=True)),
                ('finished_at',      models.DateTimeField(null=True, blank=True)),
                ('scenario',         models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                         related_name='sessions', to='sim.trainingscenario')),
                ('trainee',          models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                         related_name='training_sessions',
                                         to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name':        'Sesión de training',
                'verbose_name_plural': 'Sesiones de training',
                'ordering':            ['-started_at'],
            },
        ),
    ]
