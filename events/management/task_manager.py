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
