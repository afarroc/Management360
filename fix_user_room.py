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

print("=== FIXING USER CURRENT ROOM ===")

try:
    # Get the user
    user = User.objects.get(username='su')
    print(f'User: {user.username}')

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

    print(f'Player profile: {"created" if created else "exists"}')
    print(f'Current room before: {profile.current_room.name if profile.current_room else "None"}')

    # Set current room to 'base'
    base_room = Room.objects.get(name='base')
    profile.current_room = base_room
    profile.save()

    print(f'Current room after: {profile.current_room.name}')
    print(f'Room active: {profile.current_room.is_active}')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()