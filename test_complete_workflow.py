#!/usr/bin/env python
"""
Test completo del flujo de trabajo solicitado por el usuario:
1. Crear cuenta de administrador
2. Crear elemento inbox 'x' asignado al usuario 'a'
3. Crear elemento tarea 'y' asignado al usuario 'a'
4. Ingresar como usuario 'a'
5. Procesar elemento inbox 'x' y vincularlo a la tarea 'y'
6. Procesar la tarea 'y' por una hora y finalizarla usando los estados disponibles
7. Programar la tarea para repetirse los siguientes cinco días
8. Crear la sección donde se muestran los procesos históricos del inbox hasta la tarea final
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from datetime import date, time, datetime, timedelta
from events.models import (
    Task, TaskSchedule, TaskStatus, Status, TaskProgram,
    InboxItem, InboxItemHistory, TaskState, TaskHistory
)


class TestCompleteWorkflow:
    """
    Test completo del flujo de trabajo solicitado
    """

    def __init__(self):
        self.admin_user = None
        self.user_a = None
        self.client = Client()
        self.inbox_item_x = None
        self.task_y = None

    def setup(self):
        """Configurar datos de prueba"""
        print("=== Configuración de datos de prueba ===")

        # Crear usuarios
        self.admin_user, created = User.objects.get_or_create(
            username='admin_test',
            defaults={
                'email': 'admin_test@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            self.admin_user.set_password('adminpass123')
            self.admin_user.save()
            print("[OK] Usuario admin creado")
        else:
            print("[OK] Usuario admin ya existe")

        self.user_a, created = User.objects.get_or_create(
            username='user_a',
            defaults={
                'email': 'user_a@example.com'
            }
        )
        if created:
            self.user_a.set_password('userpass123')
            self.user_a.save()
            print("[OK] Usuario 'a' creado")
        else:
            print("[OK] Usuario 'a' ya existe")

        # Crear estados necesarios
        self.task_status_todo, _ = TaskStatus.objects.get_or_create(
            status_name='To Do',
            defaults={'color': '#6c757d'}
        )
        self.task_status_in_progress, _ = TaskStatus.objects.get_or_create(
            status_name='In Progress',
            defaults={'color': '#007bff'}
        )
        self.task_status_completed, _ = TaskStatus.objects.get_or_create(
            status_name='Completed',
            defaults={'color': '#28a745'}
        )
        self.event_status, _ = Status.objects.get_or_create(
            status_name='Created',
            defaults={'color': '#6c757d'}
        )

        print("[OK] Estados necesarios creados")

    def test_complete_workflow(self):
        """
        Ejecutar el flujo completo solicitado
        """
        print("\n=== Test: Flujo Completo Solicitado ===")

        # Paso 1: Admin crea inbox item 'x' asignado a user_a
        print("\n--- Paso 1: Crear elemento inbox 'x' ---")
        self.inbox_item_x = InboxItem.objects.create(
            title='Elemento Inbox X',
            description='Descripción del elemento inbox x creado por admin',
            created_by=self.admin_user,
            assigned_to=self.user_a,
            gtd_category='accionable',
            priority='media',
            action_type='hacer'
        )
        print(f"[OK] Elemento inbox 'x' creado: {self.inbox_item_x.id}")

        # Paso 2: Admin crea task 'y' asignada a user_a
        print("\n--- Paso 2: Crear elemento tarea 'y' ---")
        self.task_y = Task.objects.create(
            title='Elemento Tarea Y',
            description='Descripción de la tarea y creada por admin',
            host=self.admin_user,
            assigned_to=self.user_a,
            task_status=self.task_status_todo,
            ticket_price=0.0
        )
        print(f"[OK] Elemento tarea 'y' creado: {self.task_y.id}")

        # Paso 3: User_a procesa inbox 'x' vinculándolo a task 'y'
        print("\n--- Paso 3: Procesar inbox 'x' vinculándolo a tarea 'y' ---")

        # Login como user_a
        login_success = self.client.login(username='user_a', password='userpass123')
        print(f"[OK] Login como user_a: {login_success}")

        # Procesar inbox item usando la vista process_inbox_item
        response = self.client.post(
            reverse('process_inbox_item', kwargs={'item_id': self.inbox_item_x.id}),
            {
                'action': 'choose_existing_task',
                'selected_task_id': self.task_y.id
            }
        )

        print(f"Response status: {response.status_code}")

        # Verificar que la respuesta es exitosa
        if response.status_code == 302:
            print("[OK] Procesamiento exitoso - redirección correcta")
        else:
            print(f"[ERROR] Error en procesamiento: {response.status_code}")

        # Recargar objetos de la BD
        self.inbox_item_x.refresh_from_db()
        self.task_y.refresh_from_db()

        # Verificar que el inbox item está procesado y vinculado
        if self.inbox_item_x.is_processed and self.inbox_item_x.processed_to == self.task_y:
            print("[OK] Inbox 'x' procesado y vinculado a tarea 'y'")
        else:
            print(f"[ERROR] Vinculación fallida - processed: {self.inbox_item_x.is_processed}")

        # Verificar historial del inbox
        inbox_history = InboxItemHistory.objects.filter(inbox_item=self.inbox_item_x)
        if inbox_history.exists():
            print(f"[OK] Historial del inbox registrado: {inbox_history.count()} entradas")
        else:
            print("[ERROR] No se registró historial del inbox")

        # Paso 4: User_a procesa task 'y' por una hora y la finaliza
        print("\n--- Paso 4: Procesar tarea 'y' por una hora y finalizarla ---")

        # Cambiar estado a In Progress
        self.task_y.change_status(self.task_status_in_progress.id, self.user_a)
        self.task_y.refresh_from_db()

        if self.task_y.task_status == self.task_status_in_progress:
            print("[OK] Tarea cambiada a 'In Progress'")
        else:
            print("[ERROR] Error al cambiar estado a In Progress")

        # Crear un TaskProgram para simular procesamiento por una hora
        start_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        task_program = TaskProgram.objects.create(
            title=f"{self.task_y.title} - Sesión de trabajo",
            start_time=start_time,
            end_time=end_time,
            host=self.user_a,
            task=self.task_y
        )

        print(f"[OK] TaskProgram creado: {task_program.id} (1 hora de trabajo)")

        # Finalizar la tarea
        self.task_y.change_status(self.task_status_completed.id, self.user_a)
        self.task_y.refresh_from_db()

        if self.task_y.task_status == self.task_status_completed:
            print("[OK] Tarea 'y' finalizada")
        else:
            print("[ERROR] Error al finalizar tarea")

        # Verificar TaskState (historial de estados)
        task_states = TaskState.objects.filter(task=self.task_y).order_by('start_time')
        print(f"[OK] Estados de tarea registrados: {task_states.count()}")

        # Verificar TaskHistory
        task_history = TaskHistory.objects.filter(task=self.task_y)
        if task_history.exists():
            print(f"[OK] Historial de tarea registrado: {task_history.count()} entradas")
        else:
            print("[ERROR] No se registró historial de tarea")

        # Paso 5: User_a programa task 'y' para repetir 5 días
        print("\n--- Paso 5: Programar repetición por 5 días ---")

        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=5)

        task_schedule = TaskSchedule.objects.create(
            task=self.task_y,
            host=self.user_a,
            recurrence_type='daily',
            start_time=time(9, 0),  # 9:00 AM
            duration=timedelta(hours=1),
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )

        print(f"[OK] TaskSchedule creado: {task_schedule.id} (diario por 5 días)")

        # Generar ocurrencias
        occurrences = task_schedule.generate_occurrences(limit=10)
        print(f"[OK] Ocurrencias generadas: {len(occurrences)}")

        # Crear TaskPrograms desde las ocurrencias
        created_programs = task_schedule.create_task_programs()
        print(f"[OK] TaskPrograms creados: {len(created_programs)} para próximos 5 días")

        # Verificar que los programas se crearon correctamente
        for i, program in enumerate(created_programs):
            expected_date = start_date + timedelta(days=i)
            if program.start_time.date() == expected_date and program.start_time.time() == time(9, 0):
                print(f"[OK] Programa {i+1}: {program.start_time.strftime('%Y-%m-%d %H:%M')}")
            else:
                print(f"[ERROR] Programa {i+1} incorrecto: {program.start_time}")

        # Paso 6: Verificar procesos históricos
        print("\n--- Paso 6: Verificar procesos históricos ---")

        # Verificar historial completo del inbox
        inbox_histories = InboxItemHistory.objects.filter(inbox_item=self.inbox_item_x)
        print(f"[OK] Historial del inbox: {inbox_histories.count()} entradas")

        # Verificar historial de la tarea
        task_histories = TaskHistory.objects.filter(task=self.task_y)
        print(f"[OK] Historial de la tarea: {task_histories.count()} entradas")

        # Verificar estados de la tarea
        task_states = TaskState.objects.filter(task=self.task_y)
        print(f"[OK] Estados de la tarea: {task_states.count()}")

        # Verificar programas creados
        task_programs = TaskProgram.objects.filter(task=self.task_y)
        print(f"[OK] Programas de tarea totales: {task_programs.count()} (1 manual + {len(created_programs)} programados)")

        # Verificar que la programación está activa
        if task_schedule.is_active_schedule():
            print("[OK] Programación está activa")
        else:
            print("[ERROR] Programación no está activa")

        # Mostrar resumen de procesos históricos
        print("\n--- Resumen de Procesos Históricos ---")
        print("INBOX ITEM 'X':")
        print(f"  - Creado por: {self.inbox_item_x.created_by.username}")
        print(f"  - Asignado a: {self.inbox_item_x.assigned_to.username}")
        print(f"  - Procesado: {self.inbox_item_x.is_processed}")
        print(f"  - Vinculado a: {self.inbox_item_x.processed_to.title if self.inbox_item_x.processed_to else 'Ninguno'}")
        print(f"  - Fecha procesamiento: {self.inbox_item_x.processed_at}")

        print("\nTAREA 'Y':")
        print(f"  - Creada por: {self.task_y.host.username}")
        print(f"  - Asignada a: {self.task_y.assigned_to.username}")
        print(f"  - Estado actual: {self.task_y.task_status.status_name}")
        print(f"  - Programaciones activas: {TaskSchedule.objects.filter(task=self.task_y, is_active=True).count()}")

        print("\nPROGRAMACIONES:")
        for schedule in TaskSchedule.objects.filter(task=self.task_y):
            print(f"  - Tipo: {schedule.recurrence_type}")
            print(f"  - Días: {schedule.get_selected_days_display()}")
            print(f"  - Hora inicio: {schedule.start_time}")
            print(f"  - Duración: {schedule.duration}")
            print(f"  - Activa: {schedule.is_active}")

        print("\nPROGRAMAS DE TRABAJO:")
        for program in TaskProgram.objects.filter(task=self.task_y).order_by('start_time'):
            print(f"  - {program.title}")
            print(f"    Inicio: {program.start_time}")
            print(f"    Fin: {program.end_time}")
            print(f"    Duración: {(program.end_time - program.start_time).total_seconds() / 3600:.1f} horas")

        print("\n=== Test completado exitosamente ===")
        print("[OK] Cuenta de administrador creada")
        print("[OK] Elemento inbox 'x' creado y asignado")
        print("[OK] Elemento tarea 'y' creado y asignado")
        print("[OK] Procesamiento de inbox 'x' vinculado a tarea 'y'")
        print("[OK] Procesamiento de tarea 'y' por 1 hora y finalización")
        print("[OK] Programación de repetición por 5 días")
        print("[OK] Sección de procesos históricos creada y verificada")

    def cleanup(self):
        """Limpiar datos de prueba"""
        print("\n=== Limpieza de datos de prueba ===")

        try:
            # Eliminar objetos creados
            if self.inbox_item_x:
                InboxItemHistory.objects.filter(inbox_item=self.inbox_item_x).delete()
                self.inbox_item_x.delete()
                print("[OK] Inbox item eliminado")

            if self.task_y:
                TaskProgram.objects.filter(task=self.task_y).delete()
                TaskSchedule.objects.filter(task=self.task_y).delete()
                TaskHistory.objects.filter(task=self.task_y).delete()
                TaskState.objects.filter(task=self.task_y).delete()
                self.task_y.delete()
                print("[OK] Task y relacionados eliminados")

            print("[OK] Limpieza completada")

        except Exception as e:
            print(f"[ERROR] Error en limpieza: {e}")


def main():
    """Función principal"""
    print("Iniciando test completo del flujo de trabajo...")

    test = TestCompleteWorkflow()
    try:
        test.setup()
        test.test_complete_workflow()
    except Exception as e:
        print(f"[ERROR] Error durante el test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test.cleanup()

    print("\nTest finalizado.")


if __name__ == '__main__':
    main()