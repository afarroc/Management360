from django.db.models import Q
from ..models import Project, Task, ProjectStatus

class ProjectManager:
    def __init__(self, user):
        self.user = user
        self.user_projects = self.get_user_projects()
        self.tasks_by_project = self.get_tasks_by_project()
        self.active_status = self.get_active_status()

    def get_user_projects(self):
        if hasattr(self.user, 'profile') and hasattr(self.user.profile, 'role') and self.user.profile.role == 'SU':
            return Project.objects.all().order_by('-updated_at')
        else:
            return Project.objects.filter(
                Q(assigned_to=self.user) | Q(attendees=self.user)
            ).distinct().order_by('-updated_at')

    def get_tasks_by_project(self):
        tasks = Task.objects.filter(project_id__in=self.user_projects.values_list('id', flat=True)).select_related('task_status')

        tasks_by_project = {}
        for task in tasks:
            if task.project_id not in tasks_by_project:
                tasks_by_project[task.project_id] = []
            tasks_by_project[task.project_id].append(task)
        
        return tasks_by_project

    def get_active_status(self):
        try:
            return ProjectStatus.objects.get(status_name='In Progress')
        except ProjectStatus.DoesNotExist:
            # Manejar la excepción cuando no existe el estado 'in_progress'
            print("El estado 'in_progress' no existe en la base de datos.")
            # Puedes crear el estado si no existe
            # ProjectStatus.objects.create(status_name='in_progress')
            return None
        except ProjectStatus.MultipleObjectsReturned:
            # Manejar la excepción cuando hay múltiples estados 'in_progress'
            print("Hay múltiples estados 'in_progress' en la base de datos.")
            return None
        except Exception as e:
            # Manejar cualquier otra excepción
            print(f"Ocurrió un error: {e}")
            return None

    def get_project_data(self, project_id):
        project = self.user_projects.filter(id=project_id).first()
        tasks = self.tasks_by_project.get(project_id, [])
        tasks_in_progress = [task for task in tasks if task.task_status.status_name == 'In Progress']
        return {
            'project': project,
            'count_tasks': len(tasks),
            'count_tasks_in_progress': len(tasks_in_progress),
            'tasks': tasks
        }

    def get_all_projects(self):
        projects = []
        active_projects = []
        for project in self.user_projects:
            project_data = self.get_project_data(project.id)
            projects.append(project_data)
            if project.project_status_id == self.active_status.id:
                active_projects.append(project_data)

        return projects, active_projects

    def create_project(self, title, description=None, project_status=None, assigned_to=None, ticket_price=0.07):
        """
        Crear un nuevo proyecto usando el ProjectManager con procedimientos correctos
        """
        from ..models import Project, ProjectStatus, ProjectState, Event, Status
        from django.utils import timezone
        from django.db import transaction, IntegrityError
        import logging

        logger = logging.getLogger(__name__)

        # Obtener el estado por defecto si no se especifica
        if project_status is None:
            try:
                project_status = ProjectStatus.objects.get(status_name='Created')
            except ProjectStatus.DoesNotExist:
                # Si no existe 'Created', usar el primero disponible
                project_status = ProjectStatus.objects.first()
                if not project_status:
                    raise ValueError("No hay estados de proyecto disponibles")

        # Usar el usuario del manager si no se especifica assigned_to
        if assigned_to is None:
            assigned_to = self.user

        # Crear el proyecto
        project = Project.objects.create(
            title=title,
            description=description or '',
            project_status=project_status,
            host=self.user,  # El host es siempre el usuario del manager
            assigned_to=assigned_to,
            ticket_price=ticket_price
        )

        # Crear el estado inicial del proyecto
        ProjectState.objects.create(
            project=project,
            status=project_status,
            start_time=timezone.now()
        )

        logger.info(f"Project '{title}' created successfully by ProjectManager for user {self.user.username}")
        return project
