#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from events.models import Task, Project, TaskStatus
from events.management.task_manager import TaskManager
from django.contrib.auth.models import User

def create_test_task():
    try:
        # Obtener el proyecto y usuario
        project = Project.objects.get(id=1)
        user = User.objects.get(id=1)

        # Crear TaskManager para el usuario
        task_manager = TaskManager(user)

        # Crear una nueva tarea usando TaskManager
        task = task_manager.create_task(
            title='Nueva Tarea de Prueba Kanban',
            description='Esta es una tarea de prueba para el Kanban del proyecto',
            important=False,
            project=project,
            event=project.event,  # Asignar el evento del proyecto si existe
            task_status=None,  # Usará 'To Do' por defecto
            assigned_to=user,
            ticket_price=0.07
        )

        print(f'Tarea creada exitosamente: {task.title} - Estado: {task.task_status.status_name}')

        # Verificar tareas del proyecto
        tasks = Task.objects.filter(project=project)
        print(f'Total de tareas en el proyecto "{project.title}": {tasks.count()}')
        for t in tasks:
            print(f'  - {t.title} ({t.task_status.status_name})')

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    create_test_task()