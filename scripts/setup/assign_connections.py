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

print("=== ASSIGNING CONNECTIONS TO ENTRANCES ===")

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

        # Get connections
        conn_base_to_oficina = RoomConnection.objects.get(from_room=base_room, to_room=oficina_room)
        conn_oficina_to_base = RoomConnection.objects.get(from_room=oficina_room, to_room=base_room)
        conn_base_to_oficina2 = RoomConnection.objects.get(from_room=base_room, to_room=oficina2_room)
        conn_oficina2_to_base = RoomConnection.objects.get(from_room=oficina2_room, to_room=base_room)

        print(f'Connections: Base->Oficina({conn_base_to_oficina.id}), Oficina->Base({conn_oficina_to_base.id}), Base->Oficina2({conn_base_to_oficina2.id}), Oficina2->Base({conn_oficina2_to_base.id})')

        # Assign connections to entrances
        base_north.connection = conn_base_to_oficina
        base_north.save()
        print(f'Assigned connection to Base North entrance')

        base_east.connection = conn_base_to_oficina2
        base_east.save()
        print(f'Assigned connection to Base East entrance')

        oficina_south.connection = conn_oficina_to_base
        oficina_south.save()
        print(f'Assigned connection to Oficina South entrance')

        oficina2_west.connection = conn_oficina2_to_base
        oficina2_west.save()
        print(f'Assigned connection to Oficina2 West entrance')

    # Verify
    print('\n=== VERIFICATION ===')
    print('Entrances with connections:')
    for entrance in EntranceExit.objects.filter(connection__isnull=False):
        print(f'  {entrance.id}: {entrance.name} in {entrance.room.name} -> Connection: {entrance.connection.id} ({entrance.connection.to_room.name})')

    print('\nEntrances without connections:')
    for entrance in EntranceExit.objects.filter(connection__isnull=True):
        print(f'  {entrance.id}: {entrance.name} in {entrance.room.name}')

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()