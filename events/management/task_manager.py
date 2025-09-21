from django.db.models import Q
from ..models import Task, TaskStatus
import logging
logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, user):
        self.user = user
        self.user_tasks = self.get_user_tasks()
        self.active_status = self.get_active_status()

    def get_user_tasks(self):
        if (
            hasattr(self.user, 'cv') and 
            hasattr(self.user.cv, 'role') and 
            self.user.cv.role == 'SU'
        ):
            logger.info(f"User {self.user.username} has role 'SU'. Fetching all tasks.")
            return Task.objects.all().order_by('-updated_at').select_related('task_status', 'project', 'event')
        else:
            logger.info(f"User {self.user.username} does not have role 'SU'. Fetching assigned tasks.")
            return Task.objects.filter(
                Q(assigned_to=self.user) | 
                Q(project__assigned_to=self.user) | 
                Q(event__assigned_to=self.user)
            ).distinct().order_by('-updated_at').select_related('task_status', 'project', 'event')

    def get_active_status(self):
        # Attempt to retrieve the 'in_progress' status
        try:
            return TaskStatus.objects.get(status_name='In Progress')
        # Handle the exception when the status does not exist
        except TaskStatus.DoesNotExist:
            print("The 'in_progress' status does not exist in the database.")
            return None
        # Handle the exception when multiple 'in_progress' statuses are found
        except TaskStatus.MultipleObjectsReturned:
            print("Multiple 'in_progress' statuses found in the database.")
            return None
        # Catch any other unexpected exceptions
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_task_data(self, task_id):
        task = self.user_tasks.filter(id=task_id).first()

        return {
            'task': task,
            'project': task.project,
            'event': task.event,
            'status': task.task_status
        }

    def get_all_tasks(self):
        tasks = []
        active_tasks = []
        for task in self.user_tasks:
            task_data = self.get_task_data(task.id)
            tasks.append(task_data)
            if task.task_status_id == self.active_status.id:
                active_tasks.append(task_data)
        
        return tasks, active_tasks

    def get_active_tasks(self):
        return [task for task in self.user_tasks if task.task_status_id == self.active_status.id]

    def create_task(self, title, description=None, important=False, project=None, event=None,
                    task_status=None, assigned_to=None, ticket_price=0.07):
        """
        Crear una nueva tarea usando el TaskManager con procedimientos correctos
        """
        from ..models import Task, TaskStatus, TaskState, Event, Status
        from django.utils import timezone
        from django.db import transaction, IntegrityError

        # Obtener el estado por defecto si no se especifica
        if task_status is None:
            try:
                task_status = TaskStatus.objects.get(status_name='To Do')
            except TaskStatus.DoesNotExist:
                # Si no existe 'To Do', usar el primero disponible
                task_status = TaskStatus.objects.first()
                if not task_status:
                    raise ValueError("No hay estados de tarea disponibles")

        # Usar el usuario del manager si no se especifica assigned_to
        if assigned_to is None:
            assigned_to = self.user

        # Si no hay evento, crear uno automáticamente (igual que en event_create)
        if not event:
            try:
                status = Status.objects.get(status_name='Created')
                with transaction.atomic():
                    new_event = Event.objects.create(
                        title=title,
                        event_status=status,
                        host=self.user,
                        assigned_to=self.user,
                    )
                    event = new_event
                    logger.info(f"Created event '{title}' for task '{title}'")
            except Status.DoesNotExist:
                logger.error("Status 'Created' not found when creating task")
                raise ValueError("Estado 'Created' no encontrado")
            except IntegrityError as e:
                logger.error(f"Error creating event for task: {e}")
                raise ValueError(f"Error al crear el evento para la tarea: {e}")

        # Crear la tarea
        task = Task.objects.create(
            title=title,
            description=description or '',
            important=important,
            project=project,
            event=event,
            task_status=task_status,
            assigned_to=assigned_to,
            host=self.user,  # El host es siempre el usuario del manager
            ticket_price=ticket_price
        )

        # Crear el estado inicial de la tarea
        TaskState.objects.create(
            task=task,
            status=task_status,
            start_time=timezone.now()
        )

        logger.info(f"Task '{title}' created successfully by TaskManager for user {self.user.username}")
        return task
