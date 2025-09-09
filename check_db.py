#!/usr/bin/env python
"""
Script de diagnóstico para verificar el estado de la base de datos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append(os.path.dirname(__file__))
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def check_database():
    """Verifica el estado de la base de datos"""
    print("=== DIAGNÓSTICO DE BASE DE DATOS ===")

    # Verificar conexión
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Conexión a la base de datos: OK")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    # Verificar tablas críticas
    critical_tables = ['auth_user', 'django_session', 'django_content_type']
    for table in critical_tables:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ Tabla {table}: OK ({count} registros)")
        except Exception as e:
            print(f"❌ Tabla {table}: ERROR - {e}")

    # Verificar migraciones
    print("\n=== ESTADO DE MIGRACIONES ===")
    try:
        from django.core.management.commands.showmigrations import Command
        cmd = Command()
        # Simular el comando showmigrations
        execute_from_command_line(['manage.py', 'showmigrations'])
    except Exception as e:
        print(f"❌ Error al verificar migraciones: {e}")

if __name__ == '__main__':
    check_database()