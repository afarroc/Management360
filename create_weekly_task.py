#!/usr/bin/env python
"""
Script para crear una tarea programada de lunes a viernes
"""

import os
import sys
import django
from datetime import time, date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth.models import User
from events.models import Task, TaskStatus, TaskSchedule

def create_weekly_task():
    """Crea una tarea programada de lunes a viernes"""

    try:
        # Obtener o crear usuario administrador
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            print("Usuario administrador creado")

        # Obtener estado de tarea "To Do"
        try:
            todo_status = TaskStatus.objects.get(status_name='To Do')
        except TaskStatus.DoesNotExist:
            # Crear estado si no existe
            todo_status = TaskStatus.objects.create(
                status_name='To Do',
                color='#6c757d',
                active=True
            )
            print("Estado 'To Do' creado")

        # Crear la tarea base
        task = Task.objects.create(
            title='Revisión diaria de tareas pendientes',
            description='Tarea programada automáticamente para revisar y organizar las tareas pendientes del día',
            important=True,
            done=False,
            task_status=todo_status,
            assigned_to=admin_user,
            host=admin_user
        )
        print(f"Tarea creada: {task.title}")

        # Crear la programación semanal (lunes a viernes)
        today = date.today()
        schedule = TaskSchedule.objects.create(
            task=task,
            host=admin_user,
            recurrence_type='weekly',
            # Días de lunes a viernes
            monday=True,
            tuesday=True,
            wednesday=True,
            thursday=True,
            friday=True,
            saturday=False,
            sunday=False,
            # Hora de inicio: 9:00 AM
            start_time=time(9, 0),
            # Duración: 30 minutos
            duration=timedelta(minutes=30),
            # Fecha de inicio: hoy
            start_date=today,
            # Sin fecha de fin (indefinido)
            end_date=None,
            is_active=True
        )
        print(f"Programación creada: {schedule.get_selected_days_display()} a las {schedule.start_time}")

        # Generar las primeras ocurrencias
        occurrences = schedule.generate_occurrences(limit=10)
        print(f"Próximas {len(occurrences)} ocurrencias generadas:")
        for i, occ in enumerate(occurrences, 1):
            print(f"  {i}. {occ['date'].strftime('%d/%m/%Y')} - {occ['start_time'].strftime('%H:%M')} a {occ['end_time'].strftime('%H:%M')}")

        # Crear los programas de tarea para las ocurrencias
        programs = schedule.create_task_programs(occurrences)
        print(f"Se crearon {len(programs)} programas de tarea")

        print("\n[SUCCESS] Tarea programada exitosamente de lunes a viernes a las 9:00 AM")
        print(f"ID de tarea: {task.id}")
        print(f"ID de programacion: {schedule.id}")

        return task, schedule

    except Exception as e:
        print(f"[ERROR] Error al crear la tarea programada: {e}")
        return None, None

if __name__ == '__main__':
    create_weekly_task()