"""
EVENTS-BUG-FK — v3 (versión final corregida)

Cambios respecto a v2:
  - _KNOWN_FK_COLUMNS completado con TODOS los modelos documentados en EVENTS_DEV_REFERENCE.md
  - MODIFY COLUMN ahora detecta IS_NULLABLE y usa NULL/NOT NULL correctamente
  - IS_NULLABLE también se preserva en el ADD CONSTRAINT generado

Estado de la DB al ejecutar:
  - Los 26 constraints ya fueron DROPpeados en el intento fallido (DDL auto-commit en MariaDB)
  - Las columnas siguen siendo INT, accounts_user.id es BIGINT → errno 150 resuelto aquí
  - Esta migración no está registrada en django_migrations

Instrucciones:
  1. Reemplaza events/migrations/0004_fix_fk_auth_user_to_accounts_user.py con este archivo
  2. python manage.py migrate events
"""

from django.db import migrations


_DELETE_RULE_MAP = {
    'CASCADE':     'ON DELETE CASCADE',
    'SET NULL':    'ON DELETE SET NULL',
    'RESTRICT':    'ON DELETE RESTRICT',
    'NO ACTION':   'ON DELETE NO ACTION',
    'SET DEFAULT': 'ON DELETE SET DEFAULT',
}

# ---------------------------------------------------------------------------
# Lista completa de columnas FK → auth_user en la app events.
# Fuente: EVENTS_DEV_REFERENCE.md + output del intento fallido.
# Formato: (tabla, columna, delete_rule, nullable)
#
# nullable=True  → la columna admite NULL (assigned_to, etc.)
# nullable=False → la columna es NOT NULL (host, created_by, user en M2M, etc.)
#
# Este fallback se usa para columnas cuyo constraint ya fue DROPpeado
# y ya no aparece en information_schema.
# ---------------------------------------------------------------------------
_KNOWN_FK_COLUMNS = [
    # CreditAccount (OneToOne → user)
    ('events_creditaccount',             'user_id',        'RESTRICT',   False),

    # Event
    ('events_event',                     'host_id',        'RESTRICT',   False),
    ('events_event',                     'assigned_to_id', 'RESTRICT',   True),

    # EventAttendee (M2M through)
    ('events_eventattendee',             'user_id',        'RESTRICT',   False),

    # EventHistory (audit log)
    ('events_eventhistory',              'editor_id',      'RESTRICT',   False),

    # GTD automático
    ('events_gtdclassificationpattern',  'created_by_id',  'RESTRICT',   False),
    ('events_gtdlearningentry',          'user_id',        'RESTRICT',   False),
    ('events_gtdprocessingsettings',     'created_by_id',  'RESTRICT',   False),

    # InboxItem
    ('events_inboxitem',                 'created_by_id',  'RESTRICT',   False),
    ('events_inboxitem',                 'assigned_to_id', 'RESTRICT',   True),

    # InboxItem — colaboración
    ('events_inboxitemauthorization',    'user_id',        'RESTRICT',   False),
    ('events_inboxitemauthorization',    'granted_by_id',  'RESTRICT',   False),
    ('events_inboxitemclassification',   'user_id',        'RESTRICT',   False),
    ('events_inboxitemhistory',          'user_id',        'RESTRICT',   False),

    # Message (legacy — en events/models.py, pertenece a chat)
    ('events_message',                   'user_id',        'RESTRICT',   False),

    # Project
    ('events_project',                   'host_id',        'RESTRICT',   False),
    ('events_project',                   'assigned_to_id', 'RESTRICT',   True),

    # ProjectAttendee (M2M through)
    ('events_projectattendee',           'user_id',        'RESTRICT',   False),

    # ProjectHistory (audit log — patrón igual a EventHistory)
    ('events_projecthistory',            'editor_id',      'RESTRICT',   False),

    # Reminder
    ('events_reminder',                  'user_id',        'RESTRICT',   False),

    # Task
    ('events_task',                      'host_id',        'RESTRICT',   False),
    ('events_task',                      'assigned_to_id', 'RESTRICT',   True),

    # TaskHistory
    ('events_taskhistory',               'user_id',        'RESTRICT',   False),

    # TaskSchedule
    ('events_taskschedule',              'host_id',        'RESTRICT',   False),

    # Room (legacy — en events/models.py, pertenece a rooms)
    # Si la tabla no existe se salta automáticamente.
    ('events_room',                      'host_id',        'RESTRICT',   True),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_accounts_user_id_type(cursor):
    """Tipo exacto de accounts_user.id (ej: 'bigint(20)', 'int(11)')."""
    cursor.execute("""
        SELECT COLUMN_TYPE
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'accounts_user'
          AND COLUMN_NAME  = 'id'
    """)
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(
            "No se encontró accounts_user.id en information_schema. "
            "Verifica que la migración de 'accounts' esté aplicada."
        )
    return row[0]


def _get_column_info(cursor, table, column):
    """
    Retorna (COLUMN_TYPE, IS_NULLABLE) o None si la columna no existe.
    IS_NULLABLE: 'YES' o 'NO'
    """
    cursor.execute("""
        SELECT COLUMN_TYPE, IS_NULLABLE
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = %s
          AND COLUMN_NAME  = %s
    """, [table, column])
    return cursor.fetchone()  # (type, 'YES'/'NO') o None


def _table_exists(cursor, table):
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
    """, [table])
    return cursor.fetchone()[0] > 0


def _constraint_exists(cursor, table, constraint_name):
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA    = DATABASE()
          AND TABLE_NAME      = %s
          AND CONSTRAINT_NAME = %s
          AND CONSTRAINT_TYPE = 'FOREIGN KEY'
    """, [table, constraint_name])
    return cursor.fetchone()[0] > 0


def _get_remaining_auth_user_fks(cursor):
    """
    FK de events_* que AÚN apuntan a auth_user (no fueron dropeadas).
    Retorna dict: {(table, column): (constraint_name, delete_rule)}
    """
    cursor.execute("""
        SELECT
            KCU.TABLE_NAME,
            KCU.COLUMN_NAME,
            KCU.CONSTRAINT_NAME,
            RC.DELETE_RULE
        FROM information_schema.KEY_COLUMN_USAGE AS KCU
        JOIN information_schema.REFERENTIAL_CONSTRAINTS AS RC
            ON  RC.CONSTRAINT_SCHEMA = KCU.TABLE_SCHEMA
            AND RC.CONSTRAINT_NAME   = KCU.CONSTRAINT_NAME
            AND RC.TABLE_NAME        = KCU.TABLE_NAME
        WHERE KCU.TABLE_SCHEMA           = DATABASE()
          AND KCU.TABLE_NAME             LIKE 'events_%'
          AND KCU.REFERENCED_TABLE_NAME  = 'auth_user'
        ORDER BY KCU.TABLE_NAME
    """)
    result = {}
    for table, column, constraint, delete_rule in cursor.fetchall():
        result[(table, column)] = (constraint, delete_rule)
    return result


# ---------------------------------------------------------------------------
# Migración principal
# ---------------------------------------------------------------------------

def _fix_fk_constraints(apps, schema_editor):
    from django.db import connection

    with connection.cursor() as cursor:

        # 1. Tipo de accounts_user.id
        accounts_id_type = _get_accounts_user_id_type(cursor)
        accounts_base = accounts_id_type.split('(')[0].lower()
        print(f"  [EVENTS-BUG-FK] accounts_user.id → {accounts_id_type}")

        # 2. Constraints que aún quedan en auth_user (puede ser 0 tras el intento fallido)
        remaining = _get_remaining_auth_user_fks(cursor)
        print(f"  [EVENTS-BUG-FK] Constraints aún en auth_user: {len(remaining)}")

        # 3. Construir lista unificada de trabajo
        #    Empezar con los detectados en information_schema (tienen constraint_name real)
        to_process = []  # (table, column, constraint_name, delete_rule, nullable, needs_drop)
        processed = set()

        for (table, column), (constraint_name, delete_rule) in remaining.items():
            # Para las FK aún activas, necesitamos saber si es nullable
            col_info = _get_column_info(cursor, table, column)
            nullable = (col_info[1] == 'YES') if col_info else False
            to_process.append((table, column, constraint_name, delete_rule, nullable, True))
            processed.add((table, column))

        # Agregar las ya dropeadas desde _KNOWN_FK_COLUMNS
        for table, column, delete_rule, nullable in _KNOWN_FK_COLUMNS:
            if (table, column) not in processed:
                # Nombre de constraint compatible con Django (máx 64 chars)
                raw = f"{table}_{column}_fk_accounts"
                constraint_name = raw[:64]
                to_process.append((table, column, constraint_name, delete_rule, nullable, False))
                processed.add((table, column))

        print(f"  [EVENTS-BUG-FK] Columnas totales a procesar: {len(to_process)}")

        # 4. Procesar cada columna
        for table, column, constraint_name, delete_rule, nullable, needs_drop in to_process:

            on_delete_sql = _DELETE_RULE_MAP.get(delete_rule, 'ON DELETE RESTRICT')

            # Verificar que la tabla existe
            if not _table_exists(cursor, table):
                print(f"    ⚠  {table} no existe — saltando")
                continue

            # 4a. Verificar la columna
            col_info = _get_column_info(cursor, table, column)
            if col_info is None:
                print(f"    ⚠  {table}.{column} no existe — saltando")
                continue

            col_type, col_nullable_str = col_info
            col_base = col_type.split('(')[0].lower()
            # Preferir info en vivo sobre el valor hardcodeado en _KNOWN_FK_COLUMNS
            is_nullable = (col_nullable_str == 'YES')

            # 4b. DROP si el constraint sigue en pie
            if needs_drop and _constraint_exists(cursor, table, constraint_name):
                cursor.execute(
                    f"ALTER TABLE `{table}` DROP FOREIGN KEY `{constraint_name}`"
                )
                print(f"    DROP  {table}.{column}  ({constraint_name})")

            # 4c. ALTER COLUMN si el tipo base no coincide
            if col_base != accounts_base:
                null_clause = 'NULL' if is_nullable else 'NOT NULL'
                print(f"    ALTER {table}.{column}  {col_type} → {accounts_id_type} {null_clause}")
                cursor.execute(
                    f"ALTER TABLE `{table}` "
                    f"MODIFY COLUMN `{column}` {accounts_id_type} {null_clause}"
                )

            # 4d. ADD CONSTRAINT → accounts_user
            cursor.execute(f"""
                ALTER TABLE `{table}`
                ADD CONSTRAINT `{constraint_name}`
                    FOREIGN KEY (`{column}`)
                    REFERENCES `accounts_user` (`id`)
                    {on_delete_sql}
            """)
            print(f"    ✓  {table}.{column} → accounts_user  ({on_delete_sql})")

    print("  [EVENTS-BUG-FK] Completado.")


def _reverse_fk_constraints(apps, schema_editor):
    """
    Rollback de emergencia — dev only.
    NO revierte ALTER COLUMN (sería peligroso con datos existentes).
    """
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT KCU.TABLE_NAME, KCU.COLUMN_NAME, KCU.CONSTRAINT_NAME, RC.DELETE_RULE
            FROM information_schema.KEY_COLUMN_USAGE AS KCU
            JOIN information_schema.REFERENTIAL_CONSTRAINTS AS RC
                ON  RC.CONSTRAINT_SCHEMA = KCU.TABLE_SCHEMA
                AND RC.CONSTRAINT_NAME   = KCU.CONSTRAINT_NAME
                AND RC.TABLE_NAME        = KCU.TABLE_NAME
            WHERE KCU.TABLE_SCHEMA           = DATABASE()
              AND KCU.TABLE_NAME             LIKE 'events_%'
              AND KCU.REFERENCED_TABLE_NAME  = 'accounts_user'
        """)
        rows = cursor.fetchall()

    if not rows:
        return

    with connection.cursor() as cursor:
        for table, column, constraint_name, delete_rule in rows:
            on_delete_sql = _DELETE_RULE_MAP.get(delete_rule, 'ON DELETE RESTRICT')
            cursor.execute(
                f"ALTER TABLE `{table}` DROP FOREIGN KEY `{constraint_name}`"
            )
            cursor.execute(f"""
                ALTER TABLE `{table}`
                ADD CONSTRAINT `{constraint_name}`
                    FOREIGN KEY (`{column}`)
                    REFERENCES `auth_user` (`id`)
                    {on_delete_sql}
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_alter_gtdclassificationpattern_options_and_more'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            _fix_fk_constraints,
            reverse_code=_reverse_fk_constraints,
        ),
    ]
