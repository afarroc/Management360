# Generated by Django 5.0.6 on 2024-07-11 00:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0068_alter_event_attendees_alter_project_attendees'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='task_status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='eventos.taskstatus'),
            preserve_default=False,
        ),
    ]
