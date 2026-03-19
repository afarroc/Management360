# analyst/migrations/0012_add_pipeline.py
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0011_add_dashboard'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pipeline',
            fields=[
                ('id',          models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('name',        models.CharField(max_length=200, verbose_name='Nombre')),
                ('description', models.TextField(blank=True, verbose_name='Descripcion')),
                ('steps',       models.JSONField(default=list, verbose_name='Pasos')),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('source_dataset', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='pipelines',
                    to='analyst.storeddataset',
                    verbose_name='Dataset origen',
                )),
                ('created_by',  models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pipelines',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Pipeline',
                'verbose_name_plural': 'Pipelines',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='PipelineRun',
            fields=[
                ('id',               models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('status',           models.CharField(max_length=20, default='idle', choices=[
                    ('idle','Inactivo'),('running','Ejecutando'),
                    ('done','Completado'),('error','Error'),
                ])),
                ('error_msg',        models.TextField(blank=True)),
                ('steps_completed',  models.PositiveIntegerField(default=0)),
                ('duration_s',       models.FloatField(default=0.0)),
                ('runtime_params',   models.JSONField(default=dict, blank=True)),
                ('started_at',       models.DateTimeField(null=True, blank=True)),
                ('finished_at',      models.DateTimeField(null=True, blank=True)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('pipeline',         models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='runs',
                    to='analyst.pipeline',
                )),
                ('input_dataset',    models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pipeline_runs_as_input',
                    to='analyst.storeddataset',
                    verbose_name='Dataset entrada',
                )),
                ('result_dataset',   models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='pipeline_runs_as_result',
                    to='analyst.storeddataset',
                    verbose_name='Dataset resultado',
                )),
                ('triggered_by',     models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pipeline_runs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Ejecucion de pipeline',
                'verbose_name_plural': 'Ejecuciones de pipeline',
                'ordering': ['-created_at'],
            },
        ),
    ]
