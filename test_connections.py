#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from rooms.models import Room, EntranceExit, RoomConnection

print("=== TESTING ROOM CONNECTIONS ===")

try:
    # Check rooms
    rooms = Room.objects.all()
    print(f"Total rooms: {rooms.count()}")
    for room in rooms:
        print(f"  Room {room.id}: {room.name}")

    # Check connections
    connections = RoomConnection.objects.all()
    print(f"\nTotal connections: {connections.count()}")
    for conn in connections:
        print(f"  Connection {conn.id}: {conn.from_room.name} -> {conn.to_room.name}")

    # Check entrances
    entrances = EntranceExit.objects.all()
    print(f"\nTotal entrances: {entrances.count()}")
    for entrance in entrances:
        print(f"  Entrance {entrance.id}: {entrance.name} in {entrance.room.name}")

    print("\n=== TEST COMPLETED ===")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()