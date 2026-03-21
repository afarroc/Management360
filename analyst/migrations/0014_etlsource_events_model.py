# analyst/migrations/0014_etlsource_events_model.py
# EVENTS-AI-3: agrega campo events_model a ETLSource
# Campo de texto simple (no FK) — el modelo events no requiere objeto de cuenta.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0013_etlsource_sim_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='etlsource',
            name='events_model',
            field=models.CharField(
                blank=True,
                choices=[
                    ('inbox',    'GTD Inbox (InboxItem)'),
                    ('tasks',    'Tareas (Task)'),
                    ('projects', 'Proyectos (Project)'),
                    ('events',   'Agenda (Event)'),
                ],
                default='',
                max_length=20,
                verbose_name='Modelo Events',
            ),
        ),
    ]
