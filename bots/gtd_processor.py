"""
Procesador GTD (Getting Things Done) para bots
Implementa la metodología completa de GTD para procesamiento automático de items
"""

from django.utils import timezone
from django.db import transaction
from events.models import InboxItem, Task, Project, Event, Reminder, TaskSchedule
from .models import BotInstance, BotLog
from .utils import get_bot_coordinator
import logging

logger = logging.getLogger(__name__)

class GTDProcessor:
    """Procesador GTD que implementa la metodología completa"""

    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.coordinator = get_bot_coordinator()

    def process_inbox_item(self, inbox_item):
        """
        Procesa un InboxItem usando la metodología GTD completa

        Args:
            inbox_item (InboxItem): Item del inbox a procesar

        Returns:
            dict: Resultado del procesamiento
        """
        try:
            logger.info(f"Bot {self.bot.name} procesando InboxItem {inbox_item.id}: {inbox_item.title}")

            # Fase 1: Captura (ya está capturado en el inbox)
            self._log_gtd_phase(inbox_item, 'capture', 'Item capturado en inbox')

            # Fase 2: Clarificación - ¿Es actionable?
            is_actionable = self._classify_actionable(inbox_item)

            if not is_actionable:
                # No es actionable - decidir qué hacer
                result = self._process_non_actionable(inbox_item)
            else:
                # Es actionable - aplicar regla de 2 minutos
                result = self._process_actionable(inbox_item)

            # Marcar como procesado
            inbox_item.is_processed = True
            inbox_item.processed_at = timezone.now()
            inbox_item.save()

            self._log_gtd_phase(inbox_item, 'engage', f'Procesamiento completado: {result["action"]}')

            return result

        except Exception as e:
            logger.error(f"Error procesando InboxItem {inbox_item.id}: {str(e)}")
            self._log_error(inbox_item, str(e))
            return {'success': False, 'error': str(e)}

    def _classify_actionable(self, item):
        """
        Clasifica si un item es actionable usando análisis inteligente

        Returns:
            bool: True si es actionable
        """
        # Análisis de palabras clave
        actionable_keywords = [
            'hacer', 'llamar', 'escribir', 'reunión', 'entregar', 'completar',
            'revisar', 'actualizar', 'crear', 'organizar', 'planificar'
        ]

        non_actionable_keywords = [
            'información', 'referencia', 'datos', 'backup', 'archivo',
            'algún día', 'tal vez', 'quizás'
        ]

        title_lower = item.title.lower()
        description_lower = (item.description or '').lower()

        # Contar palabras clave
        actionable_score = sum(1 for keyword in actionable_keywords
                             if keyword in title_lower or keyword in description_lower)
        non_actionable_score = sum(1 for keyword in non_actionable_keywords
                                 if keyword in title_lower or keyword in description_lower)

        # Factores adicionales
        has_due_date = bool(item.due_date)
        has_time_estimate = bool(item.estimated_time)
        has_context = bool(item.context)

        # Cálculo de score final
        score = actionable_score - non_actionable_score
        if has_due_date: score += 2
        if has_time_estimate: score += 1
        if has_context: score += 1

        is_actionable = score >= 1

        self._log_gtd_phase(item, 'clarify',
                          f'Clasificado como {"actionable" if is_actionable else "no actionable"} (score: {score})')

        return is_actionable

    def _process_actionable(self, item):
        """
        Procesa un item actionable aplicando la regla de 2 minutos
        """
        # Regla de 2 minutos: si toma menos de 2 minutos, hacerlo ahora
        if item.estimated_time and item.estimated_time <= 2:
            return self._do_it_now(item)
        else:
            return self._delegate_or_schedule(item)

    def _do_it_now(self, item):
        """
        Ejecuta la tarea inmediatamente (regla de 2 minutos)
        """
        try:
            # Simular ejecución inmediata
            # En un caso real, aquí iría la lógica específica
            success = self._execute_quick_task(item)

            if success:
                self._log_gtd_phase(item, 'engage', 'Ejecutado inmediatamente (regla 2 min)')
                return {
                    'success': True,
                    'action': 'executed_immediately',
                    'method': '2_minute_rule'
                }
            else:
                # Si no se puede ejecutar inmediatamente, delegar
                return self._delegate_or_schedule(item)

        except Exception as e:
            logger.error(f"Error ejecutando tarea inmediata: {str(e)}")
            return self._delegate_or_schedule(item)

    def _delegate_or_schedule(self, item):
        """
        Decide si delegar o convertir en proyecto/tarea
        """
        # Análisis de complejidad
        is_complex = self._analyze_complexity(item)

        if is_complex:
            # Es un proyecto - crear proyecto con subtareas
            return self._convert_to_project(item)
        else:
            # Es una tarea simple - crear tarea
            return self._convert_to_task(item)

    def _process_non_actionable(self, item):
        """
        Procesa un item no actionable
        """
        # Decisiones para items no actionable
        if self._should_delete(item):
            return self._delete_item(item)
        elif self._should_incubate(item):
            return self._incubate_item(item)
        else:
            return self._file_for_reference(item)

    def _convert_to_task(self, item):
        """
        Convierte un InboxItem en una Task
        """
        try:
            with transaction.atomic():
                # Crear tarea
                task = Task.objects.create(
                    title=item.title,
                    description=item.description or '',
                    host=self.bot.generic_user.user,
                    assigned_to=self._determine_best_assignee(item),
                    created_at=item.created_at,
                    important=item.priority == 'alta'
                )

                # Crear recordatorio si tiene due_date
                if item.due_date:
                    Reminder.objects.create(
                        title=f"Recordatorio: {item.title}",
                        description=f"Tarea: {item.description}",
                        remind_at=item.due_date,
                        task=task,
                        created_by=self.bot.generic_user.user
                    )

                # Actualizar inbox item
                item.processed_to_content_type = Task.get_content_type()
                item.processed_to_object_id = task.id
                item.save()

                self._log_gtd_phase(item, 'organize', f'Convertido a Task {task.id}')

                return {
                    'success': True,
                    'action': 'converted_to_task',
                    'task_id': task.id,
                    'method': 'single_task'
                }

        except Exception as e:
            logger.error(f"Error convirtiendo a task: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _convert_to_project(self, item):
        """
        Convierte un InboxItem en un Project con múltiples tareas
        """
        try:
            with transaction.atomic():
                # Crear proyecto
                project = Project.objects.create(
                    title=item.title,
                    description=item.description or '',
                    host=self.bot.generic_user.user,
                    assigned_to=self._determine_best_assignee(item),
                    created_at=item.created_at
                )

                # Generar subtareas automáticamente
                subtasks = self._break_down_into_subtasks(item)
                created_tasks = []

                for subtask_data in subtasks:
                    task = Task.objects.create(
                        title=subtask_data['title'],
                        description=subtask_data.get('description', ''),
                        project=project,
                        host=self.bot.generic_user.user,
                        assigned_to=subtask_data.get('assignee', self._determine_best_assignee(item)),
                        important=subtask_data.get('important', False)
                    )
                    created_tasks.append(task)

                # Actualizar inbox item
                item.processed_to_content_type = Project.get_content_type()
                item.processed_to_object_id = project.id
                item.save()

                self._log_gtd_phase(item, 'organize',
                                  f'Convertido a Project {project.id} con {len(created_tasks)} tareas')

                return {
                    'success': True,
                    'action': 'converted_to_project',
                    'project_id': project.id,
                    'tasks_created': len(created_tasks),
                    'method': 'project_with_subtasks'
                }

        except Exception as e:
            logger.error(f"Error convirtiendo a project: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _analyze_complexity(self, item):
        """
        Analiza si un item es lo suficientemente complejo para ser un proyecto
        """
        complexity_indicators = [
            'plan', 'organizar', 'coordinar', 'gestionar', 'desarrollar',
            'implementar', 'revisar', 'evaluar', 'múltiples', 'varios'
        ]

        text = (item.title + ' ' + (item.description or '')).lower()
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in text)

        # Factores adicionales
        if item.estimated_time and item.estimated_time > 60:  # Más de 1 hora
            complexity_score += 2

        return complexity_score >= 2

    def _break_down_into_subtasks(self, item):
        """
        Descompone un item complejo en subtareas manejables
        """
        # Lógica simplificada - en producción usaría IA más avanzada
        subtasks = []

        if 'reunión' in item.title.lower():
            subtasks = [
                {'title': 'Preparar agenda', 'description': 'Definir puntos a tratar'},
                {'title': 'Enviar invitaciones', 'description': 'Notificar participantes'},
                {'title': 'Preparar materiales', 'description': 'Documentos y presentaciones'},
                {'title': 'Realizar reunión', 'description': 'Conducir la reunión'},
                {'title': 'Seguimiento', 'description': 'Acciones posteriores'}
            ]
        elif 'proyecto' in item.title.lower():
            subtasks = [
                {'title': 'Definir alcance', 'description': 'Establecer límites del proyecto'},
                {'title': 'Identificar recursos', 'description': 'Personal, herramientas, presupuesto'},
                {'title': 'Crear plan', 'description': 'Cronograma y milestones'},
                {'title': 'Ejecutar', 'description': 'Implementar el plan'},
                {'title': 'Evaluar resultados', 'description': 'Revisar y ajustar'}
            ]
        else:
            # Descomposición genérica
            subtasks = [
                {'title': 'Investigar', 'description': 'Reunir información necesaria'},
                {'title': 'Planificar', 'description': 'Definir pasos a seguir'},
                {'title': 'Ejecutar', 'description': 'Realizar el trabajo'},
                {'title': 'Verificar', 'description': 'Comprobar resultados'}
            ]

        return subtasks

    def _determine_best_assignee(self, item):
        """
        Determina el mejor usuario para asignar la tarea
        """
        # Lógica simplificada - en producción consideraría expertise, carga de trabajo, etc.
        return self.bot.generic_user.user  # Por ahora asigna al bot mismo

    def _execute_quick_task(self, item):
        """
        Ejecuta una tarea rápida (regla de 2 minutos)
        """
        # Simular ejecución - en producción tendría lógica específica
        logger.info(f"Ejecutando tarea rápida: {item.title}")
        return True

    def _should_delete(self, item):
        """Determina si un item debe eliminarse"""
        delete_keywords = ['spam', 'basura', 'eliminar', 'borrar']
        text = (item.title + ' ' + (item.description or '')).lower()
        return any(keyword in text for keyword in delete_keywords)

    def _should_incubate(self, item):
        """Determina si un item debe incubarse"""
        incubate_keywords = ['algún día', 'tal vez', 'futuro', 'idea']
        text = (item.title + ' ' + (item.description or '')).lower()
        return any(keyword in text for keyword in incubate_keywords)

    def _delete_item(self, item):
        """Elimina un item (trash)"""
        item.delete()
        self._log_gtd_phase(item, 'organize', 'Eliminado (trash)')
        return {'success': True, 'action': 'deleted', 'method': 'trash'}

    def _incubate_item(self, item):
        """Incuba un item para revisión futura"""
        # Establecer fecha de revisión futura (ej: 30 días)
        item.next_review_date = timezone.now() + timezone.timedelta(days=30)
        item.save()
        self._log_gtd_phase(item, 'organize', 'Incubado para revisión futura')
        return {'success': True, 'action': 'incubated', 'method': 'someday_maybe'}

    def _file_for_reference(self, item):
        """Archiva como referencia"""
        item.gtd_category = 'no_accionable'
        item.action_type = 'archivar'
        item.save()
        self._log_gtd_phase(item, 'organize', 'Archivado como referencia')
        return {'success': True, 'action': 'archived', 'method': 'reference'}

    def _log_gtd_phase(self, inbox_item, phase, message):
        """Registra una fase del proceso GTD"""
        BotLog.objects.create(
            bot_instance=self.bot,
            category='gtd',
            message=f'GTD {phase}: {message}',
            details={'inbox_item_id': inbox_item.id, 'phase': phase},
            related_object_type='inbox_item',
            related_object_id=inbox_item.id
        )

    def _log_error(self, inbox_item, error_message):
        """Registra un error en el procesamiento"""
        BotLog.objects.create(
            bot_instance=self.bot,
            category='error',
            log_level='error',
            message=f'Error procesando InboxItem {inbox_item.id}: {error_message}',
            details={'inbox_item_id': inbox_item.id, 'error': error_message},
            related_object_type='inbox_item',
            related_object_id=inbox_item.id
        )

def get_gtd_processor(bot_instance):
    """Factory function para obtener un procesador GTD"""
    return GTDProcessor(bot_instance)