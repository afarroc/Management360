#!/usr/bin/env python
"""
Script para probar la activación de bots usando el servidor real
"""
import requests
import json
import os
import django

# Configurar Django para obtener la configuración
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client

def test_bot_activation_real():
    print("=== Test: Activación de Bots (Servidor Real) ===")

    # Crear usuario admin
    try:
        admin_user = User.objects.get(username='admin_real')
        print("[OK] Usuario admin ya existe")
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser(
            username='admin_real',
            email='admin_real@example.com',
            password='adminpass123'
        )
        print("[OK] Usuario admin creado")

    # Usar Django test client que debería funcionar con ALLOWED_HOSTS
    client = Client()

    # Login
    login_success = client.login(username='admin_real', password='adminpass123')
    print(f"[OK] Login exitoso: {login_success}")

    # Probar activación del bot de proyectos
    print("\n--- Probando activación del Bot de Proyectos ---")

    # Usar override_settings para forzar ALLOWED_HOSTS
    from django.test import override_settings

    with override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1', '192.168.18.46', '192.168.18.47']):
        response = client.post(
            '/events/root/activate-bot/',
            data={
                'bot_id': 'project_bot',
                'tasks[]': ['create_project']
            }
        )

    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        try:
            data = json.loads(response.content.decode())
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get('success'):
                print("[OK] Bot activado exitosamente")
                print(f"Bot: {data.get('bot_name')}")
                print(f"Tareas ejecutadas: {len(data.get('executed_tasks', []))}")
            else:
                print(f"[ERROR] Error en activación: {data.get('error', 'Unknown error')}")
        except:
            print(f"Raw response: {response.content.decode()}")
    else:
        print(f"[ERROR] Status code: {response.status_code}")
        print(f"Response: {response.content.decode()[:500]}...")

    print("\n=== Test completado ===")

if __name__ == '__main__':
    test_bot_activation_real()