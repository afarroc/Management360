# analyst/migrations/0002_storeddataset_report.py
#
# REEMPLAZA el archivo 0002 que fue entregado manualmente.
#
# Problema: Django ya generó 0001_initial.py que crea las tablas Report y
# StoredDataset. El 0002 manual también intentaba CreateModel en ambas →
# OperationalError: Table 'analyst_storeddataset' already exists.
#
# Solución: este 0002 no hace nada (operations vacía). Solo existe para que
# 0003_alter_... pueda declararlo como dependencia y la cadena no se rompa.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0001_initial'),
    ]

    operations = [
        # Vacío intencionalmente.
        # Las tablas ya fueron creadas por 0001_initial (auto-generado por Django).
    ]
