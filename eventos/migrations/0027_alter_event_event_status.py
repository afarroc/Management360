# Generated by Django 5.0.4 on 2024-05-08 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0026_alter_estado_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='event_status',
            field=models.IntegerField(default=0),
        ),
    ]
