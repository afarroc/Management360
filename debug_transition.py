#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from rooms.models import Room, EntranceExit, RoomConnection, PlayerProfile
from rooms.transition_manager import get_room_transition_manager

print("=== DEBUGGING TRANSITION ===")

try:
    # Get the entrance that's failing
    entrance = EntranceExit.objects.get(id=18)  # Puerta Norte Base
    print(f'Entrance: {entrance.name} (ID: {entrance.id})')
    print(f'Room: {entrance.room.name}')
    print(f'Enabled: {entrance.enabled}')
    print(f'Has connection: {entrance.connection is not None}')

    if entrance.connection:
        conn = entrance.connection
        print(f'Connection ID: {conn.id}')
        print(f'From room: {conn.from_room.name}')
        print(f'To room: {conn.to_room.name}')
        print(f'Bidirectional: {conn.bidirectional}')
        print(f'Energy cost: {conn.energy_cost}')

        # Test the target room determination
        manager = get_room_transition_manager()
        target_room = manager._determine_target_room(entrance.room, conn)
        print(f'Target room from {entrance.room.name}: {target_room.name if target_room else "None"}')
        print(f'Target room active: {target_room.is_active if target_room else "N/A"}')

    # Check if there's a user/player profile
    try:
        # Get first user
        from django.contrib.auth.models import User
        user = User.objects.first()
        if user:
            print(f'\nUser: {user.username}')
            try:
                profile = user.player_profile
                print(f'Player profile exists')
                print(f'Current room: {profile.current_room.name if profile.current_room else "None"}')
                print(f'Energy: {profile.energy}')
            except PlayerProfile.DoesNotExist:
                print(f'No player profile for user {user.username}')
        else:
            print('No users found')
    except Exception as e:
        print(f'Error checking user: {e}')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()