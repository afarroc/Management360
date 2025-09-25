#!/usr/bin/env python3
"""
Script simple para crear una tarea básica sin programaciones
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import Task, TaskStatus, Project, Status

def create_simple_task():
    """Crear una tarea simple para pruebas"""

    try:
        # Obtener usuario admin
        user = User.objects.get(username='admin')
        print(f"Usuario encontrado: {user.username}")

        # Obtener estado de tarea por defecto
        task_status = TaskStatus.objects.filter(status_name='To Do').first()
        if not task_status:
            task_status = TaskStatus.objects.first()
        print(f"Estado de tarea: {task_status.status_name}")

        # Obtener o crear un proyecto/evento básico
        project = Project.objects.filter(host=user).first()
        if not project:
            # Crear un evento básico
            event_status = Status.objects.filter(status_name='Created').first()
            if not event_status:
                event_status = Status.objects.first()

            from events.models import Event
            event = Event.objects.create(
                title='Proyecto de Prueba',
                event_status=event_status,
                host=user,
                assigned_to=user
            )
            print(f"Evento creado: {event.title}")

            # Crear proyecto
            from events.models import ProjectStatus
            project_status = ProjectStatus.objects.filter(status_name='Created').first()
            if not project_status:
                project_status = ProjectStatus.objects.first()

            project = Project.objects.create(
                title='Proyecto de Prueba',
                event=event,
                host=user,
                assigned_to=user,
                project_status=project_status
            )
            print(f"Proyecto creado: {project.title}")

        # Crear tarea
        task = Task.objects.create(
            title='Tarea de Prueba para Programación',
            description='Esta es una tarea creada para probar la creación de programaciones recurrentes.',
            host=user,
            assigned_to=user,
            project=project,
            event=project.event,
            task_status=task_status,
            ticket_price=0.07
        )

        print("\n[SUCCESS] TAREA CREADA EXITOSAMENTE")
        print(f"ID: {task.id}")
        print(f"Titulo: {task.title}")
        print(f"Proyecto: {project.title}")
        print(f"Estado: {task_status.status_name}")

        return task.id

    except Exception as e:
        print(f"[ERROR] Error al crear tarea: {e}")
        return None

if __name__ == "__main__":
    task_id = create_simple_task()
    if task_id:
        print(f"\n[INFO] ID de tarea para usar en pruebas: {task_id}")
    else:
        print("\n[ERROR] No se pudo crear la tarea")