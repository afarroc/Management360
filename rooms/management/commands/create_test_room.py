from django.core.management.base import BaseCommand
from rooms.models import Room

class Command(BaseCommand):
    help = 'Create a test room with ID 1'

    def handle(self, *args, **kwargs):
        room, created = Room.objects.get_or_create(
            id=1,
            defaults={
                'name': 'Test Room',
                'description': 'This is a test room.',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Test room created successfully.'))
        else:
            self.stdout.write(self.style.WARNING('Test room already exists.'))
