"""
0004_uuid_primary_keys.py

Swap de PK int → UUID en BitacoraEntry y BitacoraAttachment.

Requisito: migración 0003 aplicada (campo uuid_new poblado en ambas tablas).

Secuencia de operaciones en BD (MariaDB):
  1. Agregar columnas UUID temporales en tablas dependientes (M2M, attachment)
  2. Poblar con los UUIDs de la entrada padre
  3. Drop de FKs y PKs antiguas
  4. Renombrar columnas uuid_new → id
  5. Establecer nuevas PKs y FKs
  6. Sincronizar estado Django via SeparateDatabaseAndState
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


def swap_pks_forward(apps, schema_editor):
    db = schema_editor.connection
    cursor = db.cursor()

    # ── 1. Columna UUID temporal en M2M tags ─────────────────────────────────
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraentry_tags`
        ADD COLUMN `new_bitacoraentry_id` uuid DEFAULT NULL
    """)

    # ── 2. Poblar con el uuid_new de la entrada padre ─────────────────────────
    cursor.execute("""
        UPDATE `bitacora_bitacoraentry_tags` t
        JOIN `bitacora_bitacoraentry` e ON t.`bitacoraentry_id` = e.`id`
        SET t.`new_bitacoraentry_id` = e.`uuid_new`
    """)

    # ── 3. Columna UUID temporal en attachment (entry_id) ─────────────────────
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraattachment`
        ADD COLUMN `new_entry_id` uuid DEFAULT NULL
    """)

    # Poblar attachment entry_id (0 filas, pero necesario para el tipo)
    cursor.execute("""
        UPDATE `bitacora_bitacoraattachment` a
        JOIN `bitacora_bitacoraentry` e ON a.`entry_id` = e.`id`
        SET a.`new_entry_id` = e.`uuid_new`
    """)

    # ── 4. Drop FKs que referencian bitacoraentry.id ──────────────────────────
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraentry_tags`
        DROP FOREIGN KEY `bitacora_bitacoraent_bitacoraentry_id_69ac99cf_fk_bitacora_`
    """)
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraentry_tags`
        DROP INDEX `bitacora_bitacoraentry_t_bitacoraentry_id_tag_id_2193c4d2_uniq`
    """)
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraattachment`
        DROP FOREIGN KEY `bitacora_bitacoraatt_entry_id_4bec8fe6_fk_bitacora_`
    """)

    # ── 5. Swap PK en bitacoraentry ───────────────────────────────────────────
    # Quitar AUTO_INCREMENT antes de drop
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraentry`
        MODIFY COLUMN `id` bigint(20) NOT NULL
    """)
    cursor.execute("ALTER TABLE `bitacora_bitacoraentry` DROP PRIMARY KEY")
    cursor.execute("ALTER TABLE `bitacora_bitacoraentry` DROP COLUMN `id`")
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraentry`
        CHANGE COLUMN `uuid_new` `id` uuid NOT NULL
    """)
    cursor.execute("ALTER TABLE `bitacora_bitacoraentry` ADD PRIMARY KEY (`id`)")

    # ── 6. Actualizar M2M tags ────────────────────────────────────────────────
    cursor.execute("ALTER TABLE `bitacora_bitacoraentry_tags` DROP COLUMN `bitacoraentry_id`")
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraentry_tags`
        CHANGE COLUMN `new_bitacoraentry_id` `bitacoraentry_id` uuid NOT NULL
    """)
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraentry_tags`
        ADD UNIQUE KEY `bitacora_bitacoraentry_t_bitacoraentry_id_tag_id_uniq`
            (`bitacoraentry_id`, `tag_id`)
    """)
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraentry_tags`
        ADD CONSTRAINT `bitacora_bitacoraent_bitacoraentry_id_fk`
        FOREIGN KEY (`bitacoraentry_id`) REFERENCES `bitacora_bitacoraentry` (`id`)
    """)

    # ── 7. Actualizar attachment entry_id ────────────────────────────────────
    cursor.execute("ALTER TABLE `bitacora_bitacoraattachment` DROP COLUMN `entry_id`")
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraattachment`
        CHANGE COLUMN `new_entry_id` `entry_id` uuid NOT NULL
    """)
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraattachment`
        ADD CONSTRAINT `bitacora_bitacoraatt_entry_id_fk`
        FOREIGN KEY (`entry_id`) REFERENCES `bitacora_bitacoraentry` (`id`)
    """)

    # ── 8. Swap PK en bitacoraattachment ─────────────────────────────────────
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraattachment`
        MODIFY COLUMN `id` bigint(20) NOT NULL
    """)
    cursor.execute("ALTER TABLE `bitacora_bitacoraattachment` DROP PRIMARY KEY")
    cursor.execute("ALTER TABLE `bitacora_bitacoraattachment` DROP COLUMN `id`")
    cursor.execute("""
        ALTER TABLE `bitacora_bitacoraattachment`
        CHANGE COLUMN `uuid_new` `id` uuid NOT NULL
    """)
    cursor.execute("ALTER TABLE `bitacora_bitacoraattachment` ADD PRIMARY KEY (`id`)")

    cursor.close()


def swap_pks_reverse(apps, schema_editor):
    # Reverse no implementado — operación destructiva en PK
    # Para revertir: restaurar desde backup_pre_0004.json
    raise NotImplementedError(
        "La migración 0004 no es reversible. "
        "Restaurar desde backup: python manage.py loaddata backup_pre_0004.json"
    )


class Migration(migrations.Migration):

    dependencies = [
        ('bitacora', '0003_refactor_conventions'),
    ]

    operations = [
        # ── Base de datos: ejecutar swap SQL ─────────────────────────────────
        migrations.RunPython(swap_pks_forward, swap_pks_reverse),

        # ── Estado Django: sincronizar sin tocar BD ───────────────────────────
        migrations.SeparateDatabaseAndState(
            state_operations=[

                # Eliminar uuid_new de ambos modelos (ya no existe en BD)
                migrations.RemoveField(
                    model_name='bitacoraentry',
                    name='uuid_new',
                ),
                migrations.RemoveField(
                    model_name='bitacoraattachment',
                    name='uuid_new',
                ),

                # Declarar id como UUIDField en ambos modelos
                migrations.AlterField(
                    model_name='bitacoraentry',
                    name='id',
                    field=models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name='bitacoraattachment',
                    name='id',
                    field=models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
            ],
            database_operations=[],  # BD ya modificada arriba
        ),
    ]
