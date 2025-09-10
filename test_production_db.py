#!/usr/bin/env python
"""
Script para probar y diagnosticar la base de datos de producción
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django con settings de producción
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
os.environ.setdefault('DATABASE_URL', 'postgresql://admin:S6JxbChtQ5AaMxnRERyVBROxNW33KOdb@dpg-d30a9ler433s73813g9g-a.oregon-postgres.render.com/projects_364w')
os.environ.setdefault('SECRET_KEY', 'django-insecure-test-key-for-production-debug')
os.environ.setdefault('DEBUG', 'False')
os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1')

# Agregar el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def test_production_connection():
    """Prueba la conexión a la base de datos de producción"""
    print("=== CONEXION A BASE DE DATOS DE PRODUCCION ===")

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"[OK] Conexion exitosa: {version[0]}")
    except Exception as e:
        print(f"[ERROR] Error de conexion: {e}")
        return False

    return True

def check_tables():
    """Verifica qué tablas existen en la base de datos"""
    print("\n=== VERIFICACIÓN DE TABLAS ===")

    critical_tables = [
        'auth_user', 'auth_group', 'auth_permission',
        'django_session', 'django_content_type', 'django_admin_log'
    ]

    # Agregar tablas específicas de events que deberían existir
    events_tables = [
        'events_creditaccount', 'events_event', 'events_project',
        'events_task', 'events_status', 'events_projectstatus', 'events_taskstatus'
    ]

    all_critical = critical_tables + events_tables
    existing_tables = []
    missing_tables = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            all_tables = [row[0] for row in cursor.fetchall()]

            for table in all_critical:
                if table in all_tables:
                    existing_tables.append(table)
                else:
                    missing_tables.append(table)

            print(f"[INFO] Total de tablas en BD: {len(all_tables)}")
            print(f"[OK] Tablas criticas existentes: {len(existing_tables)}")
            print(f"[ERROR] Tablas criticas faltantes: {len(missing_tables)}")

            if existing_tables:
                print(f"Tablas OK: {', '.join(existing_tables)}")

            if missing_tables:
                print(f"[CRITICAL] Tablas faltantes: {', '.join(missing_tables)}")

            # Verificar específicamente las tablas de events
            events_existing = [t for t in existing_tables if t.startswith('events_')]
            events_missing = [t for t in missing_tables if t.startswith('events_')]

            if events_missing:
                print(f"\n[CRITICAL] Faltan {len(events_missing)} tablas de events:")
                for table in events_missing:
                    print(f"  - {table}")
                print("Esto indica que la migración de events NO se aplicó en producción")

    except Exception as e:
        print(f"[ERROR] Error al verificar tablas: {e}")

    return existing_tables, missing_tables

def run_migrations():
    """Ejecuta las migraciones en la base de datos de producción"""
    print("\n=== EJECUTANDO MIGRACIONES ===")

    try:
        # Ejecutar migraciones en orden correcto
        print("Paso 1: Migraciones Django core...")
        execute_from_command_line(['manage.py', 'migrate', 'contenttypes', '--no-input'])
        execute_from_command_line(['manage.py', 'migrate', 'auth', '--no-input'])
        execute_from_command_line(['manage.py', 'migrate', 'sessions', '--no-input'])
        execute_from_command_line(['manage.py', 'migrate', 'admin', '--no-input'])

        print("Paso 2: Migración específica de events (CRÍTICA)...")
        execute_from_command_line(['manage.py', 'migrate', 'events', '--no-input'])

        print("Paso 3: Todas las migraciones restantes...")
        execute_from_command_line(['manage.py', 'migrate', '--no-input'])

        print("Paso 4: Sincronización forzada...")
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--no-input'])

        print("[OK] Migraciones completadas")

    except Exception as e:
        print(f"[ERROR] Error en migraciones: {e}")

def force_events_migration():
    """Fuerza específicamente la migración de events"""
    print("\n=== FUERZA MIGRACIÓN DE EVENTS ===")

    try:
        print("Aplicando migración de events específicamente...")
        execute_from_command_line(['manage.py', 'migrate', 'events', '0001', '--no-input'])
        print("[OK] Migración de events aplicada")

        # Verificar que la tabla creditaccount se creó
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'events_creditaccount'
                );
            """)
            exists = cursor.fetchone()[0]

            if exists:
                print("[OK] Tabla events_creditaccount creada exitosamente")
            else:
                print("[ERROR] Tabla events_creditaccount NO se creó")

    except Exception as e:
        print(f"[ERROR] Error al forzar migración de events: {e}")

def test_auth_user():
    """Prueba específicamente la tabla auth_user"""
    print("\n=== PRUEBA DE TABLA AUTH_USER ===")

    try:
        from django.contrib.auth.models import User

        # Verificar que la tabla existe
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM auth_user")
            count = cursor.fetchone()[0]
            print(f"[OK] Tabla auth_user existe - {count} usuarios")

        # Intentar crear un usuario de prueba
        if count == 0:
            print("Creando usuario de prueba...")
            user = User.objects.create_user(
                username='test_user',
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User'
            )
            user.save()
            print(f"[OK] Usuario de prueba creado: {user.username}")

        # Verificar que podemos consultar usuarios
        users = User.objects.all()
        print(f"[OK] Consulta de usuarios funciona - {users.count()} usuarios encontrados")

        # Limpiar usuario de prueba
        if count == 0:
            User.objects.filter(username='test_user').delete()
            print("[OK] Usuario de prueba eliminado")

    except Exception as e:
        print(f"[ERROR] Error con tabla auth_user: {e}")

def main():
    """Función principal"""
    print("=== DIAGNOSTICO DE BASE DE DATOS DE PRODUCCION ===")
    print("=" * 50)

    # Probar conexión
    if not test_production_connection():
        return

    # Verificar tablas existentes
    existing, missing = check_tables()

    # Si faltan tablas críticas, ejecutar migraciones
    if missing:
        print(f"\n[WARNING] Faltan {len(missing)} tablas criticas. Ejecutando migraciones...")

        # Verificar si faltan tablas de events específicamente
        events_missing = [t for t in missing if t.startswith('events_')]
        if events_missing:
            print(f"[CRITICAL] Faltan tablas de events: {events_missing}")
            print("Aplicando migración de events específicamente...")
            force_events_migration()

        # Ejecutar todas las migraciones
        run_migrations()

        # Verificar nuevamente después de migraciones
        print("\n=== VERIFICACION DESPUES DE MIGRACIONES ===")
        check_tables()

    # Probar tabla auth_user específicamente
    test_auth_user()

    print("\n" + "=" * 50)
    print("[FIN] DIAGNOSTICO COMPLETADO")

if __name__ == '__main__':
    main()