# Generated by Django 5.0.4 on 2024-05-08 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0021_alter_event_end_time_alter_event_start_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='max_attendees',
            field=models.IntegerField(default=0),
        ),
    ]
