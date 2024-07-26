# Generated by Django 5.0.6 on 2024-07-15 05:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0072_alter_task_created_at_alter_task_updated_at'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='host',
            field=models.ForeignKey(default=3, on_delete=django.db.models.deletion.CASCADE, related_name='hosted_tasks', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]