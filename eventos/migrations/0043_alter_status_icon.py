# Generated by Django 5.0.4 on 2024-06-14 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0042_profile_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='status',
            name='icon',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
