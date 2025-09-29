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

print("=== PRUEBA DE CONSISTENCIA DE NAVEGACIÓN ===")

try:
    # Get the user
    user = User.objects.get(username='su')
    profile = user.player_profile
    print(f'Usuario: {user.username}')

    # Test navigation consistency
    print(f'\n=== ESTADO INICIAL ===')
    print(f'Habitación física del jugador: {profile.current_room.name} (ID: {profile.current_room.id})')
    print(f'Energía: {profile.energy}')

    # Test Django test client to simulate navigation
    client = Client()
    client.login(username='su', password='password')

    # 1. Navigate to base room via URL (simulating direct URL access)
    print(f'\n=== ACCESO DIRECTO POR URL ===')
    response = client.get('/rooms/rooms/3/')  # Base room
    print(f'Response status: {response.status_code}')

    # Check if response contains warning about physical location mismatch
    if b'Est\xe1s f\xedsicamente en la habitaci\xf3n' in response.content:
        print(f'[WARNING] Sistema detectó inconsistencia física!')
    elif response.status_code == 200:
        print(f'[OK] Acceso directo exitoso')

    # Check current physical location vs requested room
    requested_room_id = 3  # Base room
    if profile.current_room.id != requested_room_id:
        print(f'[INCONSISTENCIA] Jugador físicamente en {profile.current_room.name} (ID: {profile.current_room.id}) pero accediendo a habitación ID {requested_room_id}')
    else:
        print(f'[OK] Ubicación física coincide con habitación solicitada')

    # 2. Test door usage via API
    print(f'\n=== USO DE PUERTA VIA API ===')
    east_entrance = EntranceExit.objects.get(name='Puerta Este Base', room__name='base')

    response = client.post(f'/rooms/api/entrance/{east_entrance.id}/use/', {}, content_type='application/json')
    print(f'API Response status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        print(f'API Response: {data}')

        if data.get('success'):
            # Refresh profile from database
            profile.refresh_from_db()
            print(f'[SUCCESS] Transición completada')
            print(f'Nueva habitación física: {profile.current_room.name} (ID: {profile.current_room.id})')
            print(f'Energía restante: {profile.energy}')
        else:
            print(f'[ERROR] Transición fallida: {data.get("message")}')
    else:
        print(f'[ERROR] API call failed: {response.content.decode()}')

    # 3. Test URL access after physical movement
    print(f'\n=== ACCESO POR URL DESPUÉS DE MOVIMIENTO ===')
    response = client.get(f'/rooms/rooms/{profile.current_room.id}/')
    print(f'Response status: {response.status_code}')

    if response.context and 'room' in response.context:
        displayed_room = response.context['room']
        print(f'Habitación mostrada: {displayed_room.name} (ID: {displayed_room.id})')

        if displayed_room.id == profile.current_room.id:
            print(f'[OK] Consistencia mantenida después del movimiento')
        else:
            print(f'[ERROR] ¡INCONSISTENCIA DESPUÉS DEL MOVIMIENTO!')

    print(f'\n=== RESUMEN FINAL ===')
    profile.refresh_from_db()
    print(f'Habitación física final: {profile.current_room.name}')
    print(f'Energía final: {profile.energy}')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()