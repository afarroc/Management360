# Generated by Django 5.1.7 on 2025-03-24 22:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Curriculum',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=100)),
                ('profession', models.CharField(max_length=100)),
                ('bio', models.TextField()),
                ('skills', models.TextField(help_text='Separate skills with commas')),
                ('experience', models.TextField()),
                ('education', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cv', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
