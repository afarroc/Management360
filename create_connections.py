#!/usr/bin/env python
import os
import sys
import django
from django.db import transaction

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from rooms.models import Room, EntranceExit, RoomConnection

print("=== CREATING ROOM CONNECTIONS ===")

try:
    with transaction.atomic():
        # Get the rooms
        base_room = Room.objects.get(name='base')
        oficina_room = Room.objects.get(name='oficina')
        oficina2_room = Room.objects.get(name='oficina2')

        print(f'Rooms found: Base({base_room.id}), Oficina({oficina_room.id}), Oficina2({oficina2_room.id})')

        # Delete existing connections for base room
        deleted_count = RoomConnection.objects.filter(from_room=base_room).delete()
        print(f'Deleted {deleted_count[0]} existing connections')

        # Create entrances if they don't exist
        base_north, created = EntranceExit.objects.get_or_create(
            name='Puerta Norte Base',
            room=base_room,
            face='NORTH',
            defaults={
                'description': 'Salida hacia Oficina',
                'enabled': True
            }
        )
        print(f'Base North entrance: {"created" if created else "exists"} (ID: {base_north.id})')

        base_east, created = EntranceExit.objects.get_or_create(
            name='Puerta Este Base',
            room=base_room,
            face='EAST',
            defaults={
                'description': 'Salida hacia Oficina2',
                'enabled': True
            }
        )
        print(f'Base East entrance: {"created" if created else "exists"} (ID: {base_east.id})')

        oficina_south, created = EntranceExit.objects.get_or_create(
            name='Puerta Sur Oficina',
            room=oficina_room,
            face='SOUTH',
            defaults={
                'description': 'Entrada desde Base',
                'enabled': True
            }
        )
        print(f'Oficina South entrance: {"created" if created else "exists"} (ID: {oficina_south.id})')

        oficina2_west, created = EntranceExit.objects.get_or_create(
            name='Puerta Oeste Oficina2',
            room=oficina2_room,
            face='WEST',
            defaults={
                'description': 'Entrada desde Base',
                'enabled': True
            }
        )
        print(f'Oficina2 West entrance: {"created" if created else "exists"} (ID: {oficina2_west.id})')

        # Create connections
        conn1 = RoomConnection.objects.create(
            from_room=base_room,
            to_room=oficina_room,
            entrance=base_north,
            bidirectional=True,
            energy_cost=5
        )
        print(f'Created connection: Base -> Oficina (ID: {conn1.id})')

        conn2 = RoomConnection.objects.create(
            from_room=base_room,
            to_room=oficina2_room,
            entrance=base_east,
            bidirectional=True,
            energy_cost=5
        )
        print(f'Created connection: Base -> Oficina2 (ID: {conn2.id})')

        print("=== TRANSACTION COMMITTED ===")

    # Verify after transaction
    print("\n=== VERIFICATION ===")
    connections = RoomConnection.objects.filter(from_room=base_room)
    print(f'Base room has {connections.count()} connections:')
    for conn in connections:
        print(f'  {conn.id}: {conn.from_room.name} -> {conn.to_room.name} via {conn.entrance.name}')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()