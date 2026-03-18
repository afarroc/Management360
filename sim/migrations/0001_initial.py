# sim/migrations/0001_initial.py
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SimAccount',
            fields=[
                ('id',           models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('name',         models.CharField(max_length=200, verbose_name='Nombre')),
                ('canal',        models.CharField(max_length=20, choices=[('inbound','Inbound Voz'),('outbound','Outbound Discador'),('digital','Digital (Chat/Mail/App)'),('mixed','Mixto')])),
                ('account_type', models.CharField(max_length=20, default='generic', choices=[('banking','Banca'),('telco','Telecomunicaciones'),('retail','Retail'),('generic','Genérico')])),
                ('preset',       models.CharField(max_length=50, blank=True)),
                ('config',       models.JSONField(default=dict)),
                ('is_active',    models.BooleanField(default=True)),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
                ('updated_at',   models.DateTimeField(auto_now=True)),
                ('created_by',   models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sim_accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Cuenta simulada', 'verbose_name_plural': 'Cuentas simuladas', 'ordering': ['-updated_at']},
        ),
        migrations.CreateModel(
            name='SimAgent',
            fields=[
                ('id',              models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('codigo',          models.CharField(max_length=20)),
                ('turno',           models.CharField(max_length=10, default='MANANA', choices=[('MANANA','Mañana'),('TARDE','Tarde'),('NOCHE','Noche')])),
                ('antiguedad',      models.CharField(max_length=10, default='senior', choices=[('junior','Junior (< 3 meses)'),('senior','Senior (> 3 meses)')])),
                ('sph_base',        models.FloatField(default=0.128)),
                ('adherencia_base', models.FloatField(default=0.931)),
                ('tmo_factor',      models.FloatField(default=1.0)),
                ('is_active',       models.BooleanField(default=True)),
                ('account',         models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agents', to='sim.simaccount')),
            ],
            options={'verbose_name': 'Agente simulado', 'verbose_name_plural': 'Agentes simulados', 'ordering': ['codigo']},
        ),
        migrations.AddConstraint(
            model_name='simagent',
            constraint=models.UniqueConstraint(fields=['account', 'codigo'], name='unique_agent_per_account'),
        ),
        migrations.CreateModel(
            name='Interaction',
            fields=[
                ('id',           models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('canal',        models.CharField(max_length=20, choices=[('inbound','Inbound Voz'),('outbound','Outbound Discador'),('digital','Digital (Chat/Mail/App)'),('mixed','Mixto')])),
                ('skill',        models.CharField(max_length=100, blank=True)),
                ('sub_canal',    models.CharField(max_length=50, blank=True)),
                ('fecha',        models.DateField()),
                ('hora_inicio',  models.DateTimeField()),
                ('hora_fin',     models.DateTimeField()),
                ('duracion_s',   models.IntegerField(default=0)),
                ('acw_s',        models.IntegerField(default=0)),
                ('tipificacion', models.CharField(max_length=200, blank=True)),
                ('status',       models.CharField(max_length=20, choices=[('atendida','Atendida'),('abandonada','Abandonada'),('no_contacto','No Contacto'),('venta','Venta'),('agenda','Agenda / Callback'),('rechazo','Rechazo')])),
                ('lead_id',      models.CharField(max_length=50, blank=True)),
                ('intento_num',  models.IntegerField(default=1)),
                ('is_simulated', models.BooleanField(default=True, editable=False)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('account',      models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='sim.simaccount')),
                ('agent',        models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interactions', to='sim.simagent')),
            ],
            options={'verbose_name': 'Interacción simulada', 'verbose_name_plural': 'Interacciones simuladas', 'ordering': ['hora_inicio']},
        ),
        migrations.AddIndex(
            model_name='interaction',
            index=models.Index(fields=['account', 'fecha'], name='sim_inter_acc_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='interaction',
            index=models.Index(fields=['account', 'canal', 'fecha'], name='sim_inter_canal_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='interaction',
            index=models.Index(fields=['agent', 'fecha'], name='sim_inter_agent_fecha_idx'),
        ),
        migrations.CreateModel(
            name='SimRun',
            fields=[
                ('id',                     models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('date_from',              models.DateField()),
                ('date_to',               models.DateField()),
                ('canales',               models.JSONField(default=list)),
                ('status',                models.CharField(max_length=10, default='running', choices=[('running','Ejecutando'),('done','Completado'),('error','Error')])),
                ('interactions_generated', models.IntegerField(default=0)),
                ('agents_generated',       models.IntegerField(default=0)),
                ('duration_s',            models.FloatField(default=0.0)),
                ('error_msg',             models.TextField(blank=True)),
                ('started_at',            models.DateTimeField(auto_now_add=True)),
                ('finished_at',           models.DateTimeField(null=True, blank=True)),
                ('account',               models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='runs', to='sim.simaccount')),
                ('triggered_by',          models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sim_runs', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Ejecución de simulación', 'verbose_name_plural': 'Ejecuciones de simulación', 'ordering': ['-started_at']},
        ),
    ]
