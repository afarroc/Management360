# analyst/migrations/0013_etlsource_sim_account.py
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    SIM-4 — Agrega sim_account FK a ETLSource.
    Permite usar SimAccount como fuente nativa en el ETL Manager.
    """

    dependencies = [
        ('analyst', '0012_add_pipeline'),
        ('sim',     '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='etlsource',
            name='sim_account',
            field=models.ForeignKey(
                'sim.SimAccount',
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='etl_sources',
                verbose_name='Cuenta Sim',
            ),
        ),
    ]
