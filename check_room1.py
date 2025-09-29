#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from rooms.models import Room, EntranceExit, RoomConnection

print("=== CHECKING ROOM 1 (oficina) ===")
try:
    room1 = Room.objects.get(id=1)
    print(f'Room: {room1.name} (ID: {room1.id})')

    print('\nEntrances in room 1:')
    for entrance in room1.entrance_exits.all():
        has_connection = RoomConnection.objects.filter(entrance=entrance).exists()
        print(f'  {entrance.id}: {entrance.name} ({entrance.face}) - Has Connection: {has_connection}')

    print('\nAll connections:')
    for conn in RoomConnection.objects.all():
        print(f'  {conn.id}: {conn.from_room.name} -> {conn.to_room.name} via {conn.entrance.name} (bidirectional: {conn.bidirectional})')

    print('\nConnections TO room 1:')
    to_connections = RoomConnection.objects.filter(to_room=room1)
    print(f'  Found {to_connections.count()} connections to room 1')
    for conn in to_connections:
        print(f'    {conn.id}: {conn.from_room.name} -> {conn.to_room.name} (bidirectional: {conn.bidirectional})')

    print('\nConnections FROM room 1:')
    from_connections = RoomConnection.objects.filter(from_room=room1)
    print(f'  Found {from_connections.count()} connections from room 1')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()