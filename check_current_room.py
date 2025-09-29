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

print("=== VERIFICANDO HABITACION ACTUAL DEL USUARIO ===")

try:
    # Get the user
    user = User.objects.get(username='su')
    print(f'Usuario: {user.username}')

    # Get player profile
    profile = user.player_profile
    print(f'Habitacion actual: {profile.current_room.name} (ID: {profile.current_room.id})')
    print(f'Energia: {profile.energy}')

    # Show entrances in current room
    print(f'\nEntradas en {profile.current_room.name}:')
    entrances = profile.current_room.entrance_exits.all()
    for entrance in entrances:
        enabled = "[HABILITADA]" if entrance.enabled else "[DESHABILITADA]"
        connected = "[CONECTADA]" if entrance.connection else "[SIN CONEXION]"
        clickable = "[CLICABLE]" if entrance.enabled and entrance.connection else "[NO CLICABLE]"

        print(f'  ID {entrance.id}: {entrance.name} ({entrance.face})')
        print(f'    Estado: {enabled} | {connected} | {clickable}')

        if entrance.connection:
            conn = entrance.connection
            target_room = conn.to_room if conn.from_room == entrance.room else (conn.from_room if conn.bidirectional else "N/A")
            print(f'    Conecta a: {target_room.name if hasattr(target_room, "name") else target_room}')
        print()

    # Check if "este" door exists
    east_entrance = entrances.filter(face='EAST').first()
    if east_entrance:
        print(f'[INFO] Puerta ESTE encontrada: {east_entrance.name} (ID: {east_entrance.id})')
        if east_entrance.connection:
            print(f'[INFO] Conecta a: {east_entrance.connection.to_room.name}')
        else:
            print(f'[ERROR] La puerta ESTE no tiene conexion!')
    else:
        print(f'[ERROR] No se encontro puerta ESTE en {profile.current_room.name}')

    # Show available transitions
    from rooms.transition_manager import get_room_transition_manager
    manager = get_room_transition_manager()
    transitions = manager.get_available_transitions(profile)

    print(f'\nTransiciones disponibles desde {profile.current_room.name}:')
    if transitions:
        for trans in transitions:
            print(f'  {trans["entrance"].name} -> {trans["target_room"].name} (costo: {trans["energy_cost"]})')
    else:
        print('  [NINGUNA]')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()