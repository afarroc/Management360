"""
Utilidades para el sistema multi-bot
Gestión de concurrencia, colas y coordinación
"""

from collections import deque
from django.utils import timezone
from django.db import transaction
from .models import (
    BotInstance, BotTaskAssignment, ResourceLock,
    BotCoordinator, BotLog, BotCommunication
)
import logging

logger = logging.getLogger(__name__)

class BotTaskQueue:
    """Sistema de colas distribuidas para asignación de tareas a bots"""

    def __init__(self):
        self.queues = {
            'urgent': deque(),
            'high': deque(),
            'medium': deque(),
            'low': deque()
        }

    def add_task(self, task_data, priority='medium'):
        """
        Agrega una tarea a la cola correspondiente

        Args:
            task_data (dict): {
                'type': str,  # Tipo de tarea (process_inbox, create_project, etc.)
                'object_id': int,  # ID del objeto relacionado
                'priority': int,  # 1-10
                'deadline': datetime,  # Opcional
                'metadata': dict  # Datos adicionales
            }
            priority (str): Nivel de prioridad de la cola
        """
        if priority not in self.queues:
            priority = 'medium'

        self.queues[priority].append(task_data)
        logger.info(f"Tarea agregada a cola {priority}: {task_data['type']}")

    def get_next_task(self, bot_instance):
        """
        Obtiene la siguiente tarea apropiada para un bot

        Args:
            bot_instance (BotInstance): Instancia del bot

        Returns:
            dict or None: Datos de la tarea o None si no hay tareas disponibles
        """
        # Verificar si el bot puede tomar tareas
        if not bot_instance.can_take_task('any'):
            return None

        # Buscar tarea en orden de prioridad
        for priority in ['urgent', 'high', 'medium', 'low']:
            if not self.queues[priority]:
                continue

            # Revisar cada tarea en la cola
            for i, task in enumerate(self.queues[priority]):
                if self._can_assign_to_bot(task, bot_instance):
                    # Remover de la cola y retornar
                    self.queues[priority].remove(task)
                    logger.info(f"Tarea asignada a {bot_instance.name}: {task['type']}")
                    return task

        return None

    def _can_assign_to_bot(self, task, bot):
        """Verifica si una tarea puede asignarse a un bot específico"""
        # Verificar especialización
        if bot.specialization != 'general_assistant':
            compatible_tasks = bot._get_compatible_tasks()
            if task['type'] not in compatible_tasks:
                return False

        # Verificar deadline si existe
        if task.get('deadline') and task['deadline'] < timezone.now():
            return False  # Tarea expirada

        return True

    def get_queue_status(self):
        """Retorna el estado actual de todas las colas"""
        return {
            priority: len(queue)
            for priority, queue in self.queues.items()
        }

class DistributedLockManager:
    """Gestor de bloqueos distribuidos para recursos"""

    @staticmethod
    def acquire_lock(resource_type, resource_id, bot_instance, lock_type='exclusive', timeout_minutes=5):
        """
        Intenta adquirir un bloqueo para un recurso

        Args:
            resource_type (str): Tipo de recurso (project, task, event, etc.)
            resource_id (int): ID del recurso
            bot_instance (BotInstance): Bot que solicita el bloqueo
            lock_type (str): Tipo de bloqueo
            timeout_minutes (int): Minutos antes de expirar

        Returns:
            ResourceLock or None: El bloqueo adquirido o None si hay conflicto
        """
        return ResourceLock.acquire_lock(
            resource_type, resource_id, bot_instance,
            lock_type, timeout_minutes
        )

    @staticmethod
    def release_lock(resource_type, resource_id, bot_instance):
        """
        Libera un bloqueo de recurso

        Args:
            resource_type (str): Tipo de recurso
            resource_id (int): ID del recurso
            bot_instance (BotInstance): Bot que libera el bloqueo

        Returns:
            bool: True si se liberó correctamente
        """
        try:
            lock = ResourceLock.objects.get(
                resource_type=resource_type,
                resource_id=resource_id,
                bot_instance=bot_instance,
                is_active=True
            )
            lock.release()
            return True
        except ResourceLock.DoesNotExist:
            return False

class BotCoordinatorService:
    """Servicio de coordinación de bots múltiples"""

    def __init__(self):
        self.task_queue = BotTaskQueue()
        self.lock_manager = DistributedLockManager()

    def get_or_create_coordinator(self):
        """Obtiene o crea el coordinador principal"""
        coordinator, created = BotCoordinator.objects.get_or_create(
            defaults={'name': 'Main Bot Coordinator'}
        )
        return coordinator

    def assign_task_to_bot(self, task_data):
        """
        Asigna una tarea al bot más apropiado

        Args:
            task_data (dict): Datos de la tarea

        Returns:
            BotTaskAssignment or None: Asignación creada o None si falla
        """
        # Determinar prioridad de cola
        priority = self._calculate_queue_priority(task_data)

        # Agregar a la cola
        self.task_queue.add_task(task_data, priority)

        # Intentar asignar inmediatamente
        available_bot = self._find_available_bot(task_data)
        if available_bot:
            return self._create_task_assignment(task_data, available_bot)

        # Si no hay bot disponible, queda en cola
        logger.info(f"Tarea encolada (sin bot disponible): {task_data['type']}")
        return None

    def _calculate_queue_priority(self, task_data):
        """Calcula la prioridad de cola basada en los datos de la tarea"""
        priority_score = task_data.get('priority', 5)

        if task_data.get('deadline'):
            hours_until_deadline = (task_data['deadline'] - timezone.now()).total_seconds() / 3600
            if hours_until_deadline < 1:
                return 'urgent'
            elif hours_until_deadline < 24:
                return 'high'

        if priority_score >= 8:
            return 'high'
        elif priority_score >= 6:
            return 'medium'
        else:
            return 'low'

    def _find_available_bot(self, task_data):
        """Encuentra el bot más apropiado para una tarea"""
        available_bots = BotInstance.objects.filter(
            is_active=True,
            current_status__in=['idle', 'working']
        ).order_by('-priority_level')  # Bots de mayor prioridad primero

        for bot in available_bots:
            if bot.can_take_task(task_data['type'], task_data.get('priority', 1)):
                return bot

        return None

    def _create_task_assignment(self, task_data, bot):
        """Crea una asignación de tarea para un bot"""
        assignment = BotTaskAssignment.objects.create(
            bot_instance=bot,
            task_type=task_data['type'],
            task_id=task_data['object_id'],
            priority=task_data.get('priority', 1),
            deadline=task_data.get('deadline'),
            assignment_reason=task_data.get('reason', ''),
            result_data=task_data.get('metadata', {})
        )

        # Actualizar estado del bot
        bot.update_status('working', f"Processing {task_data['type']}")

        logger.info(f"Tarea asignada: {bot.name} -> {task_data['type']}")
        return assignment

    def process_completed_task(self, assignment, result_data=None, error=None):
        """
        Procesa una tarea completada

        Args:
            assignment (BotTaskAssignment): Asignación completada
            result_data (dict): Resultado de la tarea
            error (str): Mensaje de error si falló
        """
        with transaction.atomic():
            if error:
                assignment.fail_task(error)
                assignment.bot_instance.error_count += 1
            else:
                assignment.complete_task(result_data)
                assignment.bot_instance.tasks_completed_today += 1

            assignment.bot_instance.update_status('idle')

            # Log de la actividad
            BotLog.objects.create(
                bot_instance=assignment.bot_instance,
                category='task',
                message=f"Task {assignment.task_type} {'completed' if not error else 'failed'}",
                details={
                    'task_id': assignment.task_id,
                    'result': result_data,
                    'error': error
                },
                task_assignment=assignment,
                related_object_type=assignment.task_type.split('_')[0],  # ej: 'inbox' de 'process_inbox'
                related_object_id=assignment.task_id
            )

    def check_system_health(self):
        """Verifica la salud del sistema de bots"""
        coordinator = self.get_or_create_coordinator()

        # Contar bots activos
        active_bots = BotInstance.objects.filter(is_active=True)
        coordinator.active_bots_count = active_bots.count()
        coordinator.save()

        # Verificar bots sin heartbeat reciente (5 minutos)
        stale_threshold = timezone.now() - timezone.timedelta(minutes=5)
        stale_bots = active_bots.filter(last_heartbeat__lt=stale_threshold)

        for bot in stale_bots:
            logger.warning(f"Bot {bot.name} sin heartbeat reciente")
            # Podría enviar notificación o intentar reiniciar

        # Calcular carga del sistema
        system_load = coordinator.get_system_load()

        # Auto-escalado si está habilitado
        if coordinator.should_scale_up():
            self._scale_up_bots()
        elif coordinator.should_scale_down():
            self._scale_down_bots()

        return {
            'active_bots': coordinator.active_bots_count,
            'system_load': system_load,
            'stale_bots': stale_bots.count(),
            'queue_status': self.task_queue.get_queue_status()
        }

    def _scale_up_bots(self):
        """Escala hacia arriba creando más bots"""
        logger.info("Iniciando escalado hacia arriba de bots")
        # Lógica para crear nuevos bots
        # Esto dependerá de la implementación específica

    def _scale_down_bots(self):
        """Escala hacia abajo deteniendo bots inactivos"""
        logger.info("Iniciando escalado hacia abajo de bots")
        # Lógica para detener bots inactivos

    def send_bot_message(self, sender_bot, recipient_bot, message_type, content, priority='medium'):
        """
        Envía un mensaje entre bots

        Args:
            sender_bot (BotInstance): Bot remitente
            recipient_bot (BotInstance or None): Bot destinatario (None para broadcast)
            message_type (str): Tipo de mensaje
            content (str): Contenido del mensaje
            priority (str): Prioridad del mensaje
        """
        message = BotCommunication.objects.create(
            sender=sender_bot,
            recipient=recipient_bot,
            message_type=message_type,
            subject=f"{message_type} from {sender_bot.name}",
            content=content,
            priority=priority
        )

        logger.info(f"Mensaje enviado: {sender_bot.name} -> {recipient_bot.name if recipient_bot else 'All'}")
        return message

# Instancia global del coordinador
bot_coordinator = BotCoordinatorService()

def get_bot_coordinator():
    """Obtiene la instancia global del coordinador de bots"""
    return bot_coordinator