#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from rooms.models import Room, EntranceExit, PlayerProfile
from django.contrib.auth.models import User
from django.test import Client

print("=== DEBUGGING NORTH DOOR IN BASE ===")

try:
    # Get the user and verify current room
    user = User.objects.get(username='su')
    profile = user.player_profile
    print(f'Usuario: {user.username}')
    print(f'Habitacion actual: {profile.current_room.name} (ID: {profile.current_room.id})')
    print(f'Energia: {profile.energy}')

    # Get the north door in base
    base_room = Room.objects.get(name='base')
    north_entrance = base_room.entrance_exits.filter(face='NORTH').first()

    if north_entrance:
        print(f'\nPuerta Norte Base (ID: {north_entrance.id}):')
        print(f'  Nombre: {north_entrance.name}')
        print(f'  Habilitada: {north_entrance.enabled}')
        print(f'  Tiene conexion: {north_entrance.connection is not None}')

        if north_entrance.connection:
            conn = north_entrance.connection
            print(f'  Conexion ID: {conn.id}')
            print(f'  Desde: {conn.from_room.name}')
            print(f'  Hacia: {conn.to_room.name}')
            print(f'  Bidireccional: {conn.bidirectional}')
            print(f'  Costo energia: {conn.energy_cost}')
            print(f'  Habitacion destino activa: {conn.to_room.is_active}')
        else:
            print(f'  [ERROR] La puerta norte NO tiene conexion!')
    else:
        print(f'[ERROR] No se encontro puerta NORTE en habitacion base!')

    # Test the API endpoint for north door
    print(f'\n=== PRUEBA API PUERTA NORTE ===')
    client = Client()
    client.login(username='su', password='password')

    if north_entrance:
        url = f'/rooms/api/entrance/{north_entrance.id}/use/'
        print(f'Probando URL: {url}')

        response = client.post(url, {}, content_type='application/json')
        print(f'Response status: {response.status_code}')

        if response.status_code == 200:
            data = response.json()
            print(f'Response data: {data}')
        else:
            print(f'Error response: {response.content.decode()}')

    # Test transition manager
    print(f'\n=== PRUEBA TRANSITION MANAGER ===')
    from rooms.transition_manager import get_room_transition_manager
    manager = get_room_transition_manager()

    if north_entrance:
        result = manager.attempt_transition(profile, north_entrance)
        print(f'Resultado:')
        print(f'  Success: {result["success"]}')
        print(f'  Message: {result.get("message", "N/A")}')
        if not result["success"]:
            print(f'  Reason: {result.get("reason", "N/A")}')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()