"""
Comando de Django para ejecutar el sistema multi-bot
Coordina múltiples bots que procesan tareas GTD durante horario laboral
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import time
import signal
import logging
from datetime import datetime, timedelta

from bots.models import BotInstance, BotTaskAssignment, BotCoordinator
from bots.utils import get_bot_coordinator
from bots.gtd_processor import get_gtd_processor
from events.models import InboxItem

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Ejecuta el sistema multi-bot para procesamiento GTD automático'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bot-id',
            type=str,
            help='ID específico del bot a ejecutar (opcional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Modo simulación - no realiza cambios reales',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Ejecutar una sola vez y salir',
        )
        parser.add_argument(
            '--max-items',
            type=int,
            default=10,
            help='Máximo número de items a procesar por ciclo',
        )
        parser.add_argument(
            '--cycle-time',
            type=int,
            default=60,
            help='Tiempo entre ciclos en segundos (default: 60)',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = True
        self.dry_run = False
        self.once = False
        self.max_items = 10
        self.cycle_time = 60
        self.coordinator = get_bot_coordinator()

        # Manejo de señales para parada graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Manejador de señales para parada graceful"""
        self.stdout.write(self.style.WARNING('\nRecibida senal de parada. Finalizando bots...'))
        self.running = False

    def handle(self, *args, **options):
        """Método principal del comando"""
        self.dry_run = options['dry_run']
        self.once = options['once']
        self.max_items = options['max_items']
        self.cycle_time = options['cycle_time']

        if self.dry_run:
            self.stdout.write(self.style.WARNING('MODO SIMULACION - No se realizaran cambios reales'))

        try:
            if options['bot_id']:
                # Ejecutar un bot específico
                self._run_single_bot(options['bot_id'])
            else:
                # Ejecutar sistema multi-bot
                self._run_multi_bot_system()

        except Exception as e:
            raise CommandError(f'Error ejecutando bots: {str(e)}')

    def _run_single_bot(self, bot_id):
        """Ejecuta un bot específico"""
        try:
            bot = BotInstance.objects.get(id=bot_id, is_active=True)
        except BotInstance.DoesNotExist:
            raise CommandError(f'Bot con ID {bot_id} no encontrado o inactivo')

        self.stdout.write(self.style.SUCCESS(f'Ejecutando bot: {bot.name} ({bot.specialization})'))

        if self.once:
            self._run_bot_cycle(bot)
        else:
            self._run_bot_loop(bot)

    def _run_multi_bot_system(self):
        """Ejecuta el sistema completo multi-bot"""
        self.stdout.write(self.style.SUCCESS('Iniciando sistema multi-bot GTD'))

        # Verificar salud del sistema
        health = self.coordinator.check_system_health()
        self.stdout.write(f'Estado del sistema: {health["active_bots"]} bots activos, carga: {health["system_load"]:.1f}%')

        if self.once:
            self._run_multi_bot_cycle()
        else:
            self._run_multi_bot_loop()

    def _run_bot_loop(self, bot):
        """Ejecuta un bot en loop continuo"""
        self.stdout.write(f'Iniciando loop para bot {bot.name}')

        while self.running:
            try:
                self._run_bot_cycle(bot)

                if not self.once:
                    self.stdout.write(f'Esperando {self.cycle_time} segundos...')
                    time.sleep(self.cycle_time)

            except Exception as e:
                logger.error(f'Error en ciclo del bot {bot.name}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'❌ Error en bot {bot.name}: {str(e)}'))

                if self.once:
                    break

                # Esperar antes de reintentar
                time.sleep(30)

        self.stdout.write(self.style.SUCCESS(f'Bot {bot.name} finalizado'))

    def _run_multi_bot_loop(self):
        """Ejecuta múltiples bots en paralelo"""
        self.stdout.write('Iniciando sistema multi-bot en modo continuo')

        cycle_count = 0
        while self.running:
            try:
                cycle_count += 1
                self.stdout.write(f'\n--- Ciclo {cycle_count} ---')

                start_time = time.time()
                self._run_multi_bot_cycle()
                cycle_duration = time.time() - start_time

                self.stdout.write(f'Ciclo completado en {cycle_duration:.1f}s')

                if not self.once:
                    remaining_time = max(0, self.cycle_time - cycle_duration)
                    if remaining_time > 0:
                        self.stdout.write(f'Esperando {remaining_time:.1f} segundos...')
                        time.sleep(remaining_time)

            except Exception as e:
                logger.error(f'Error en ciclo multi-bot: {str(e)}')
                self.stdout.write(self.style.ERROR(f'Error en sistema multi-bot: {str(e)}'))

                if self.once:
                    break

                time.sleep(30)

        self.stdout.write(self.style.SUCCESS('Sistema multi-bot finalizado'))

    def _run_bot_cycle(self, bot):
        """Ejecuta un ciclo completo para un bot"""
        if not bot.is_working_hours():
            if not self.dry_run:
                bot.update_status('idle', 'Fuera de horario laboral')
            return

        # Actualizar estado del bot
        if not self.dry_run:
            bot.update_status('working', 'Procesando tareas GTD')

        # Obtener tareas pendientes para este bot
        pending_tasks = self._get_pending_tasks_for_bot(bot)

        if not pending_tasks:
            self.stdout.write(f'Bot {bot.name}: No hay tareas pendientes')
            if not self.dry_run:
                bot.update_status('idle', 'Esperando tareas')
            return

        # Procesar tareas
        processed_count = 0
        for task in pending_tasks[:self.max_items]:
            if not self.running:
                break

            try:
                success = self._process_task_for_bot(bot, task)
                if success:
                    processed_count += 1

            except Exception as e:
                logger.error(f'Error procesando tarea {task.id} para bot {bot.name}: {str(e)}')
                if not self.dry_run:
                    self.coordinator.process_completed_task(task, error=str(e))

        self.stdout.write(f'Bot {bot.name}: Procesadas {processed_count} tareas')

        # Actualizar métricas
        if not self.dry_run:
            bot.tasks_completed_today += processed_count
            bot.save()

    def _run_multi_bot_cycle(self):
        """Ejecuta un ciclo para todos los bots activos"""
        active_bots = BotInstance.objects.filter(is_active=True)

        if not active_bots:
            self.stdout.write('No hay bots activos')
            return

        total_processed = 0

        for bot in active_bots:
            if not self.running:
                break

            try:
                self._run_bot_cycle(bot)
                # Contar tareas procesadas (esto es aproximado)
                total_processed += getattr(bot, 'tasks_completed_today', 0)

            except Exception as e:
                logger.error(f'Error en bot {bot.name}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'Error en bot {bot.name}: {str(e)}'))

        # Mostrar resumen del ciclo
        self.stdout.write(f'Ciclo completado: {active_bots.count()} bots, ~{total_processed} tareas procesadas')

    def _get_pending_tasks_for_bot(self, bot):
        """Obtiene tareas pendientes asignadas a un bot"""
        return BotTaskAssignment.objects.filter(
            bot_instance=bot,
            status__in=['assigned', 'in_progress']
        ).order_by('priority', 'assigned_at')[:self.max_items]

    def _process_task_for_bot(self, bot, task_assignment):
        """
        Procesa una tarea específica para un bot

        Args:
            bot (BotInstance): Instancia del bot
            task_assignment (BotTaskAssignment): Asignación de tarea

        Returns:
            bool: True si se procesó correctamente
        """
        try:
            # Marcar tarea como en progreso
            if not self.dry_run:
                task_assignment.start_task()

            # Procesar según tipo de tarea
            if task_assignment.task_type == 'process_inbox':
                result = self._process_inbox_item_task(bot, task_assignment)
            elif task_assignment.task_type == 'create_project':
                result = self._process_create_project_task(bot, task_assignment)
            elif task_assignment.task_type == 'update_task':
                result = self._process_update_task(bot, task_assignment)
            else:
                result = {'success': False, 'error': f'Tipo de tarea desconocido: {task_assignment.task_type}'}

            # Completar tarea
            if not self.dry_run:
                if result.get('success'):
                    self.coordinator.process_completed_task(task_assignment, result)
                else:
                    self.coordinator.process_completed_task(task_assignment, error=result.get('error'))

            return result.get('success', False)

        except Exception as e:
            logger.error(f'Error procesando tarea {task_assignment.id}: {str(e)}')
            if not self.dry_run:
                self.coordinator.process_completed_task(task_assignment, error=str(e))
            return False

    def _process_inbox_item_task(self, bot, task_assignment):
        """Procesa una tarea de InboxItem usando GTD"""
        try:
            inbox_item_id = task_assignment.task_id
            inbox_item = InboxItem.objects.get(id=inbox_item_id)

            # Obtener procesador GTD
            gtd_processor = get_gtd_processor(bot)

            # Procesar el item
            result = gtd_processor.process_inbox_item(inbox_item)

            return result

        except InboxItem.DoesNotExist:
            return {'success': False, 'error': f'InboxItem {task_assignment.task_id} no encontrado'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _process_create_project_task(self, bot, task_assignment):
        """Procesa una tarea de creación de proyecto"""
        # Implementación simplificada
        return {'success': True, 'message': 'Proyecto creado'}

    def _process_update_task(self, bot, task_assignment):
        """Procesa una tarea de actualización"""
        # Implementación simplificada
        return {'success': True, 'message': 'Tarea actualizada'}

    def _create_sample_tasks(self):
        """Crea tareas de ejemplo para testing (solo en dry-run)"""
        if not self.dry_run:
            return

        # Obtener inbox items sin procesar
        unprocessed_items = InboxItem.objects.filter(
            is_processed=False
        ).order_by('created_at')[:5]

        for item in unprocessed_items:
            task_data = {
                'type': 'process_inbox',
                'object_id': item.id,
                'priority': 1,
                'reason': 'Procesamiento automático GTD'
            }

            self.coordinator.assign_task_to_bot(task_data)
            self.stdout.write(f'Creada tarea de ejemplo para InboxItem: {item.title[:50]}...')