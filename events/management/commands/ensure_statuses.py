"""
Comando para asegurar que existan los estados por defecto
Ejecutar: python manage.py ensure_statuses
"""

from django.core.management.base import BaseCommand
from events.utils.status_utils import ensure_default_statuses


class Command(BaseCommand):
    help = 'Ensure default statuses exist for events, projects, and tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress output messages',
        )

    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        
        if not quiet:
            self.stdout.write(self.style.NOTICE('Checking default statuses...'))
        
        result = ensure_default_statuses()
        
        if not quiet:
            self.stdout.write(self.style.SUCCESS(
                f"✓ Created: {len(result['created'])} statuses"
            ))
            
            for status in result['created']:
                self.stdout.write(f"  + {status}")
            
            self.stdout.write(self.style.SUCCESS(
                f"✓ Existing: {len(result['existing'])} statuses"
            ))
            
            if result['failed']:
                self.stdout.write(self.style.ERROR(
                    f"✗ Failed: {len(result['failed'])} statuses"
                ))
                for failure in result['failed']:
                    self.stdout.write(f"  - {failure}")
            else:
                self.stdout.write(self.style.SUCCESS("✓ No failures"))
        
        return len(result['failed'])