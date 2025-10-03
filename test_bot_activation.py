#!/usr/bin/env python
"""
Script simple para probar la activación de bots sin usar el test suite completo
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import json

def test_bot_activation():
    print("=== Test: Activación de Bots ===")

    # Crear cliente
    client = Client()

    # Crear usuario admin
    try:
        admin_user = User.objects.create_superuser(
            username='test_admin',
            email='test_admin@example.com',
            password='testpass123'
        )
        print("[OK] Usuario admin creado")
    except:
        admin_user = User.objects.get(username='test_admin')
        print("[OK] Usuario admin ya existe")

    # Login
    login_success = client.login(username='test_admin', password='testpass123')
    print(f"[OK] Login exitoso: {login_success}")

    # Probar activación del bot de proyectos
    print("\n--- Probando activación del Bot de Proyectos ---")
    response = client.post(
        '/events/activate_bot/',
        {
            'bot_id': 'project_bot',
            'tasks[]': ['create_project']
        },
        content_type='application/x-www-form-urlencoded'
    )

    print(f"Status code: {response.status_code}")
    if response.content:
        try:
            data = json.loads(response.content.decode())
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get('success'):
                print("[OK] Bot activado exitosamente")
            else:
                print(f"[ERROR] Error en activación: {data.get('error', 'Unknown error')}")
        except:
            print(f"Raw response: {response.content.decode()}")
    else:
        print("No response content")

    print("\n=== Test completado ===")

if __name__ == '__main__':
    test_bot_activation()