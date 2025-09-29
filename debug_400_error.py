#!/usr/bin/env python
import os
import sys

# Configurar Django ANTES de cualquier import
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append('.')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import json

def debug_400_error():
    """Capturar exactamente el error 400"""

    print("DEBUG: ERROR 400 EN ACTUALIZACIÓN")
    print("=" * 50)

    # Crear cliente y login
    client = Client()
    login_success = client.login(username='su', password='su')
    print(f"LOGIN: {'OK' if login_success else 'FAIL'}")

    if not login_success:
        return

    # Obtener token CSRF
    response = client.get('/rooms/rooms/crud/')
    import re
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode('utf-8'))
    csrf_token = csrf_match.group(1) if csrf_match else 'dummy_token'

    # Datos que causan el error
    problematic_data = {
        'name': 'Habitacion Editada por Test',
        'room_type': 'OFFICE',
        'description': None,
        'capacity': None,
        'permissions': 'public',
        'is_active': True,
        'length': 30,
        'width': 30,
        'height': 10,
        'color_primary': '#2196f3',
        'color_secondary': '#1976d2',
        'material_type': 'CONCRETE',
        'opacity': 1.0
    }

    print("Enviando datos problemáticos...")
    response = client.put('/rooms/api/crud/rooms/2/', json.dumps(problematic_data), content_type='application/json', HTTP_X_CSRFTOKEN=csrf_token)

    print(f"HTTP Status: {response.status_code}")

    if response.status_code == 400:
        try:
            error_data = response.json()
            print("Error data:")
            print(json.dumps(error_data, indent=2))
        except:
            print("Raw error response:")
            print(response.content.decode('utf-8'))
    else:
        print("No error - response:")
        print(response.content.decode('utf-8')[:200])

if __name__ == '__main__':
    debug_400_error()