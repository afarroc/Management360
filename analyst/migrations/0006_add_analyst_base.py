# analyst/migrations/0006_add_analyst_base.py

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0005_etlsource_etljob'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 1. Crear modelo AnalystBase ──────────────────────────────────────
        migrations.CreateModel(
            name='AnalystBase',
            fields=[
                ('id',          models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name',        models.CharField(max_length=200, verbose_name='Nombre')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('category',    models.CharField(
                    blank=True, max_length=50,
                    choices=[
                        ('ventas',      'Ventas'),
                        ('calidad',     'Calidad'),
                        ('rrhh',        'RRHH'),
                        ('operaciones', 'Operaciones'),
                        ('finanzas',    'Finanzas'),
                        ('marketing',   'Marketing'),
                        ('otro',        'Otro'),
                    ],
                    verbose_name='Categoría',
                )),
                ('schema',     models.JSONField(default=list, verbose_name='Schema')),
                ('row_count',  models.IntegerField(default=0, verbose_name='Registros')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('dataset',    models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='analyst_base',
                    to='analyst.storeddataset',
                    verbose_name='Dataset',
                )),
                ('created_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='analyst_bases',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Creado por',
                )),
            ],
            options={
                'verbose_name':        'Base de datos analista',
                'verbose_name_plural': 'Bases de datos analista',
                'ordering':            ['-updated_at'],
            },
        ),

        # ── 2. Agregar FK analyst_base a ETLSource ───────────────────────────
        migrations.AddField(
            model_name='etlsource',
            name='analyst_base',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='etl_sources',
                to='analyst.analystbase',
                verbose_name='Base de datos analista',
            ),
        ),
    ]
