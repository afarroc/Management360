# analyst/migrations/0011_add_dashboard.py
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0010_alter_crosssource_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('id',          models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('name',        models.CharField(max_length=200, verbose_name='Nombre')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('is_public',   models.BooleanField(default=False, verbose_name='Público')),
                ('layout',      models.JSONField(default=list, verbose_name='Layout')),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('created_by',  models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dashboards',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Dashboard',
                'verbose_name_plural': 'Dashboards',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='DashboardWidget',
            fields=[
                ('id',          models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('widget_type', models.CharField(max_length=20, choices=[
                    ('kpi_card',  'KPI / Indicador'),
                    ('table',     'Tabla'),
                    ('bar_chart', 'Gráfico de barras'),
                    ('line_chart','Gráfico de líneas'),
                    ('pie_chart', 'Gráfico de pastel'),
                    ('text',      'Texto / Nota'),
                ])),
                ('title',       models.CharField(max_length=200, blank=True)),
                ('source',      models.JSONField(default=dict, blank=True)),
                ('config',      models.JSONField(default=dict, blank=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('dashboard',   models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='widgets',
                    to='analyst.dashboard',
                )),
            ],
            options={
                'verbose_name': 'Widget',
                'verbose_name_plural': 'Widgets',
                'ordering': ['created_at'],
            },
        ),
    ]
