# Generated by Django 5.0.6 on 2024-07-06 03:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0059_alter_projectstatus_icon_alter_status_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='project_status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='eventos.projectstatus'),
            preserve_default=False,
        ),
    ]
