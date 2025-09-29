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

print("=== FIXING BIDIRECTIONAL CONNECTIONS ===")

try:
    with transaction.atomic():
        # Get rooms
        base_room = Room.objects.get(name='base')
        oficina_room = Room.objects.get(name='oficina')
        oficina2_room = Room.objects.get(name='oficina2')

        print(f'Rooms: Base({base_room.id}), Oficina({oficina_room.id}), Oficina2({oficina2_room.id})')

        # Get entrances
        base_north = EntranceExit.objects.get(name='Puerta Norte Base', room=base_room)
        base_east = EntranceExit.objects.get(name='Puerta Este Base', room=base_room)
        oficina_south = EntranceExit.objects.get(name='Puerta Sur Oficina', room=oficina_room)
        oficina2_west = EntranceExit.objects.get(name='Puerta Oeste Oficina2', room=oficina2_room)

        print(f'Entrances: Base North({base_north.id}), Base East({base_east.id}), Oficina South({oficina_south.id}), Oficina2 West({oficina2_west.id})')

        # Delete existing connections
        RoomConnection.objects.filter(
            from_room__in=[base_room, oficina_room, oficina2_room],
            to_room__in=[base_room, oficina_room, oficina2_room]
        ).delete()

        print('Deleted existing connections')

        # Create bidirectional connections
        # Base <-> Oficina
        conn_base_to_oficina = RoomConnection.objects.create(
            from_room=base_room,
            to_room=oficina_room,
            entrance=base_north,
            bidirectional=True,
            energy_cost=5
        )

        conn_oficina_to_base = RoomConnection.objects.create(
            from_room=oficina_room,
            to_room=base_room,
            entrance=oficina_south,
            bidirectional=True,
            energy_cost=5
        )

        # Base <-> Oficina2
        conn_base_to_oficina2 = RoomConnection.objects.create(
            from_room=base_room,
            to_room=oficina2_room,
            entrance=base_east,
            bidirectional=True,
            energy_cost=5
        )

        conn_oficina2_to_base = RoomConnection.objects.create(
            from_room=oficina2_room,
            to_room=base_room,
            entrance=oficina2_west,
            bidirectional=True,
            energy_cost=5
        )

        print(f'Created bidirectional connections:')
        print(f'  Base <-> Oficina: {conn_base_to_oficina.id} and {conn_oficina_to_base.id}')
        print(f'  Base <-> Oficina2: {conn_base_to_oficina2.id} and {conn_oficina2_to_base.id}')

    # Verify
    print('\n=== VERIFICATION ===')
    print('Connections from Base:')
    for conn in RoomConnection.objects.filter(from_room=base_room):
        print(f'  {conn.id}: {conn.from_room.name} -> {conn.to_room.name} via {conn.entrance.name}')

    print('\nConnections from Oficina:')
    for conn in RoomConnection.objects.filter(from_room=oficina_room):
        print(f'  {conn.id}: {conn.from_room.name} -> {conn.to_room.name} via {conn.entrance.name}')

    print('\nConnections from Oficina2:')
    for conn in RoomConnection.objects.filter(from_room=oficina2_room):
        print(f'  {conn.id}: {conn.from_room.name} -> {conn.to_room.name} via {conn.entrance.name}')

    print('\nChecking entrances in Oficina (room 1):')
    oficina_room = Room.objects.get(id=1)
    for entrance in oficina_room.entrance_exits.all():
        has_connection = RoomConnection.objects.filter(entrance=entrance).exists()
        print(f'  {entrance.id}: {entrance.name} ({entrance.face}) - Has Connection: {has_connection}')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()