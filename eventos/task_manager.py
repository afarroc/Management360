from django.db.models import Q
from .models import Task, TaskStatus, Project, Event

class TaskManager:
    def __init__(self, user):
        self.user = user
        self.user_tasks = self.get_user_tasks()
        self.active_status = self.get_active_status()

    def get_user_tasks(self):
        if hasattr(self.user, 'profile') and hasattr(self.user.profile, 'role') and self.user.profile.role == 'SU':
            return Task.objects.all().order_by('-updated_at').select_related('task_status', 'project', 'event')
        else:
            return Task.objects.filter(
                Q(assigned_to=self.user) | Q(project__assigned_to=self.user) | Q(event__assigned_to=self.user)
            ).distinct().order_by('-updated_at').select_related('task_status', 'project', 'event')

    def get_active_status(self):
        return TaskStatus.objects.get(status_name='En Curso')

    def get_task_data(self, task):
        return {
            'task': task,
            'project': task.project,
            'event': task.event,
            'status': task.task_status
        }

    def get_task_by_id(self, task_id):
        try:
            task = Task.objects.get(id=task_id)
            task_data = self.get_task_data(task)
            active_task_data = task_data if task.task_status_id == self.active_status.id else None
            return task_data, active_task_data
        except Task.DoesNotExist:
            return None, None

    def get_all_tasks(self):
        tasks = []
        active_tasks = []
        for task in self.user_tasks:
            task_data = self.get_task_data(task)
            tasks.append(task_data)
            if task.task_status_id == self.active_status.id:
                active_tasks.append(task_data)
        
        return tasks, active_tasks

    def get_active_tasks(self):
        return [task for task in self.user_tasks if task.task_status_id == self.active_status.id]
