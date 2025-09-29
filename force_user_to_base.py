#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from rooms.models import Room, PlayerProfile
from django.contrib.auth.models import User

print("=== FORZANDO USUARIO A HABITACION BASE ===")

try:
    # Get the user
    user = User.objects.get(username='su')
    print(f'Usuario encontrado: {user.username}')

    # Get or create player profile
    profile, created = PlayerProfile.objects.get_or_create(
        user=user,
        defaults={
            'energy': 100,
            'productivity': 50,
            'social': 50,
            'position_x': 0,
            'position_y': 0
        }
    )

    print(f'Perfil de jugador: {"creado" if created else "existente"}')

    # Get base room
    base_room = Room.objects.get(name='base')
    print(f'Habitacion base: {base_room.name} (ID: {base_room.id}, Activa: {base_room.is_active})')

    # Force user to base room
    old_room = profile.current_room.name if profile.current_room else "Ninguna"
    profile.current_room = base_room
    profile.energy = 100  # Reset energy
    profile.save()

    print(f'Cambio realizado:')
    print(f'  Antes: {old_room}')
    print(f'  Ahora: {profile.current_room.name}')
    print(f'  Energia: {profile.energy}')

    # Verify east door is accessible
    east_entrance = base_room.entrance_exits.filter(face='EAST').first()
    if east_entrance:
        print(f'\nPuerta Este en base:')
        print(f'  Nombre: {east_entrance.name}')
        print(f'  Habilitada: {east_entrance.enabled}')
        print(f'  Conectada: {east_entrance.connection is not None}')
        if east_entrance.connection:
            print(f'  Conecta a: {east_entrance.connection.to_room.name}')
    else:
        print(f'[ERROR] No se encontro puerta ESTE en habitacion base!')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()