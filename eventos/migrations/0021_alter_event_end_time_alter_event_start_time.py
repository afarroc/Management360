# Generated by Django 5.0.4 on 2024-05-08 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0020_event_eventattendee_event_attendees'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='end_time',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_time',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
