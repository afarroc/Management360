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
from rooms.models import Room, EntranceExit

def test_buttons_simple():
    """Prueba simple de botones sin caracteres Unicode"""

    print("=== PRUEBA SIMPLE DE BOTONES ===\n")

    # Obtener datos
    try:
        room = Room.objects.get(id=3)
        user = User.objects.get(username='su')
        print(f"Habitacion: {room.name} (ID: {room.id})")
    except Exception as e:
        print(f"ERROR: {e}")
        return

    # Obtener entradas
    entrances = EntranceExit.objects.filter(room=room)
    print(f"Entradas encontradas: {entrances.count()}")

    for entrance in entrances[:3]:  # Solo primeras 3
        print(f"  - {entrance.name} (ID: {entrance.id}, Conexion: {entrance.connection is not None})")

    # Crear cliente
    client = Client()
    login_result = client.login(username='su', password='su')
    print(f"Login exitoso: {login_result}")

    # Probar URLs
    if entrances.exists():
        entrance = entrances.first()

        # Probar editar
        edit_url = f'/rooms/entrance-exits/{entrance.id}/edit/'
        response = client.get(edit_url, follow=True)
        print(f"Editar {entrance.name}: HTTP {response.status_code}")

        # Probar eliminar
        delete_url = f'/rooms/entrance-exits/{entrance.id}/delete/'
        response = client.get(delete_url, follow=True)
        print(f"Eliminar {entrance.name}: HTTP {response.status_code}")

        # Probar API
        api_url = f'/rooms/api/entrance/{entrance.id}/use/'
        response = client.post(api_url, {}, content_type='application/json')
        print(f"Usar {entrance.name}: HTTP {response.status_code}")

    print("\n=== FIN PRUEBA SIMPLE ===")

if __name__ == '__main__':
    test_buttons_simple()