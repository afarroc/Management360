from django.core.management.base import BaseCommand
from rooms.models import Room, EntranceExit, RoomConnection

class Command(BaseCommand):
    help = 'Check the room setup'

    def handle(self, *args, **options):
        self.stdout.write('=== ROOMS ===')
        for room in Room.objects.filter(name__in=['Base', 'Oficina', 'Oficina2']):
            self.stdout.write(f'{room.id}: {room.name} ({room.room_type}) - Parent: {room.parent_room.name if room.parent_room else None}')

        self.stdout.write('\n=== ENTRANCES ===')
        for entrance in EntranceExit.objects.filter(room__name__in=['Base', 'Oficina', 'Oficina2']):
            self.stdout.write(f'{entrance.id}: {entrance.name} - {entrance.room.name} ({entrance.face}) - Enabled: {entrance.enabled}')

        self.stdout.write('\n=== CONNECTIONS ===')
        for conn in RoomConnection.objects.all():
            self.stdout.write(f'{conn.id}: {conn.from_room.name} -> {conn.to_room.name} via {conn.entrance.name} (Cost: {conn.energy_cost}, Bidirectional: {conn.bidirectional})')

        self.stdout.write('\nSetup check completed!')