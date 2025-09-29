import time
import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import schedule
except ImportError:
    raise ImportError("schedule is required. Install with: pip install schedule")


class Command(BaseCommand):
    help = 'Run scheduled CX email processing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=settings.EMAIL_CHECK_INTERVAL,
            help=f'Check interval in seconds (default: {settings.EMAIL_CHECK_INTERVAL})',
        )
        parser.add_argument(
            '--max-emails',
            type=int,
            default=50,
            help='Maximum emails to process per run (default: 50)',
        )

    def handle(self, *args, **options):
        if not settings.EMAIL_RECEPTION_ENABLED:
            self.stdout.write(
                self.style.WARNING('Email reception is disabled in settings. Exiting...')
            )
            return

        interval = options['interval']
        max_emails = options['max_emails']

        self.stdout.write(
            self.style.SUCCESS(f'Starting scheduled CX email processing every {interval} seconds')
        )
        self.stdout.write('Press Ctrl+C to stop')

        # Programar la tarea
        def process_emails():
            try:
                self.stdout.write(f'[{datetime.now()}] Processing CX emails...')
                call_command('process_cx_emails', max_emails=max_emails)
                self.stdout.write(f'[{datetime.now()}] Processing completed')
            except Exception as e:
                logger.error(f'Error in scheduled email processing: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(f'[{datetime.now()}] Error: {str(e)}')
                )

        # Ejecutar inmediatamente la primera vez
        process_emails()

        # Programar ejecuciones periódicas
        schedule.every(interval).seconds.do(process_emails)

        # Mantener el proceso corriendo
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('\nScheduled CX email processing stopped by user')
            )
        except Exception as e:
            logger.error(f'Unexpected error in scheduler: {str(e)}')
            raise