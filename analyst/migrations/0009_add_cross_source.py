# analyst/migrations/0009_add_cross_source.py
# Ejecutar: python manage.py migrate analyst

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    # Ajusta al nombre real de tu última migración
    dependencies = [
        ('analyst', '0008_etlsource_analyst_base_alter_etlsource_model_path'),  # ← cambiar si difiere
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CrossSource',
            fields=[
                ('id',             models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name',           models.CharField(max_length=200, verbose_name='Nombre')),
                ('description',    models.TextField(blank=True, verbose_name='Descripción')),
                ('config',         models.JSONField(verbose_name='Configuración del cruce')),
                ('last_run_at',    models.DateTimeField(blank=True, null=True)),
                ('last_row_count', models.IntegerField(default=0)),
                ('created_at',     models.DateTimeField(auto_now_add=True)),
                ('updated_at',     models.DateTimeField(auto_now=True)),
                ('last_result',    models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='cross_sources',
                    to='analyst.storeddataset',
                    verbose_name='Último resultado',
                )),
                ('created_by',     models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='cross_sources',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Creado por',
                )),
            ],
            options={
                'verbose_name':        'Cruce de datos',
                'verbose_name_plural': 'Cruces de datos',
                'ordering':            ['-updated_at'],
            },
        ),
    ]
