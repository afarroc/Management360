#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from rooms.models import Room

print("=== ACTIVATING ROOMS ===")

try:
    # Get the rooms that need to be active
    rooms_to_activate = ['base', 'oficina', 'oficina2']

    for room_name in rooms_to_activate:
        try:
            room = Room.objects.get(name=room_name)
            if not room.is_active:
                room.is_active = True
                room.save()
                print(f'Activated room: {room.name} (ID: {room.id})')
            else:
                print(f'Room already active: {room.name} (ID: {room.id})')
        except Room.DoesNotExist:
            print(f'Room not found: {room_name}')

    print('\n=== VERIFICATION ===')
    all_rooms = Room.objects.all()
    for room in all_rooms:
        status = "ACTIVE" if room.is_active else "INACTIVE"
        print(f'{room.id}: {room.name} - {status}')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()