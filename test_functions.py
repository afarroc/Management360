#!/usr/bin/env python
"""
Script de prueba para las funciones del asistente IA
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth.models import User
from chat.functions import parse_command, logged_functions

def test_parse_command():
    """Prueba el parsing de comandos"""
    print("=== PRUEBA DE PARSING DE COMANDOS ===")

    test_commands = [
        "crea un proyecto llamado 'Mi Proyecto'",
        "lista mis proyectos",
        "actualiza proyecto 1 title='Nuevo Nombre'",
        "elimina proyecto 5",
        "este no es un comando",
    ]

    for cmd in test_commands:
        result = parse_command(cmd)
        print(f"Comando: '{cmd}'")
        print(f"Resultado: {result}")
        print("---")

def test_logged_functions():
    """Prueba las funciones logged"""
    print("\n=== PRUEBA DE FUNCIONES LOGGED ===")

    # Crear usuario de prueba
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"Usuario de prueba creado: {user.username}")

    # Probar función create_project_logged
    print("\nProbando create_project_logged...")
    try:
        result = logged_functions['create_project_logged'](user, "crea un proyecto llamado 'Proyecto de Prueba'", title="Proyecto de Prueba", description="Descripción de prueba")
        print(f"Resultado: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_parse_command()
    test_logged_functions()