# Generated by Django 5.0.6 on 2024-07-25 02:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0079_taskprogram'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskprogram',
            name='task',
            field=models.ForeignKey(default=4, on_delete=django.db.models.deletion.CASCADE, to='eventos.task'),
            preserve_default=False,
        ),
    ]
