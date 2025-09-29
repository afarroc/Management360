#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from rooms.models import Room, EntranceExit, PlayerProfile
from django.contrib.auth.models import User
from django.test import Client

print("=== PRUEBA DIRECTA DEL API ===")

try:
    # Get the user and verify current room
    user = User.objects.get(username='su')
    profile = user.player_profile
    print(f'Usuario: {user.username}')
    print(f'Habitacion actual: {profile.current_room.name} (ID: {profile.current_room.id})')
    print(f'Energia: {profile.energy}')

    # Get the east door (Puerta Este Base)
    east_entrance = EntranceExit.objects.get(name='Puerta Este Base', room__name='base')
    print(f'\nPuerta Este Base (ID: {east_entrance.id}):')
    print(f'  Habilitada: {east_entrance.enabled}')
    print(f'  Tiene conexion: {east_entrance.connection is not None}')

    if east_entrance.connection:
        conn = east_entrance.connection
        print(f'  Conexion ID: {conn.id}')
        print(f'  Desde: {conn.from_room.name}')
        print(f'  Hacia: {conn.to_room.name}')
        print(f'  Bidireccional: {conn.bidirectional}')
        print(f'  Costo energia: {conn.energy_cost}')
        print(f'  Habitacion destino activa: {conn.to_room.is_active}')

    # Test the API endpoint directly using Django test client
    print(f'\n=== PRUEBA DEL API ENDPOINT ===')
    client = Client()
    client.login(username='su', password='password')  # Assuming default password

    # Test the API call
    url = f'/rooms/api/entrance/{east_entrance.id}/use/'
    print(f'Probando URL: {url}')

    response = client.post(url, {}, content_type='application/json')
    print(f'Response status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        print(f'Response data: {json.dumps(data, indent=2)}')
    else:
        print(f'Error response: {response.content.decode()}')

    # Also test the transition manager directly
    print(f'\n=== PRUEBA DEL TRANSITION MANAGER ===')
    from rooms.transition_manager import get_room_transition_manager
    manager = get_room_transition_manager()

    result = manager.attempt_transition(profile, east_entrance)
    print(f'Resultado de attempt_transition:')
    print(f'  Success: {result["success"]}')
    print(f'  Message: {result.get("message", "N/A")}')
    print(f'  Reason: {result.get("reason", "N/A")}')

    if not result["success"]:
        print(f'  Target room: {result.get("target_room", "N/A")}')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()