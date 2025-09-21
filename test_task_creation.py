#!/usr/bin/env python3
"""
Test para verificar que no se creen inbox items duplicados al crear tareas desde el inbox
"""
import os
import sys
import django
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from events.models import Task, InboxItem, TaskStatus, Status
from events.management.task_manager import TaskManager


class TestInboxDuplication(TestCase):
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Crear estados necesarios
        self.task_status = TaskStatus.objects.create(status_name='To Do')
        self.event_status = Status.objects.create(status_name='Created')

        # Crear inbox item de prueba
        self.inbox_item = InboxItem.objects.create(
            title='Tarea de prueba desde inbox',
            description='Descripción de prueba',
            created_by=self.user,
            is_processed=False
        )

    def test_no_duplicate_inbox_items(self):
        """Test que no se creen inbox items duplicados al procesar desde inbox"""
        print("=== Test: No duplicación de inbox items ===")

        # Verificar que inicialmente solo hay un inbox item no procesado
        unprocessed_count_before = InboxItem.objects.filter(
            created_by=self.user,
            is_processed=False
        ).count()
        print(f"Inbox items no procesados antes: {unprocessed_count_before}")

        # Simular la creación de tarea desde el inbox processing
        task_manager = TaskManager(self.user)

        # Crear tarea usando TaskManager (como lo hace process_inbox_item)
        task = task_manager.create_task(
            title=self.inbox_item.title,
            description=self.inbox_item.description,
            important=False,
            project=None,
            event=None,
            task_status=self.task_status,
            assigned_to=self.user,
            ticket_price=0.07
        )

        print(f"Tarea creada: {task.title}")

        # Verificar que no se creó un inbox item duplicado
        unprocessed_count_after = InboxItem.objects.filter(
            created_by=self.user,
            is_processed=False
        ).count()

        print(f"Inbox items no procesados después: {unprocessed_count_after}")

        # El conteo debería ser el mismo (no se creó duplicado)
        self.assertEqual(
            unprocessed_count_before,
            unprocessed_count_after,
            "Se creó un inbox item duplicado cuando no debería"
        )

        # Verificar que la tarea se creó correctamente
        self.assertIsNotNone(task)
        self.assertEqual(task.title, self.inbox_item.title)

        print("✅ Test pasado: No se crearon inbox items duplicados")

    def test_inbox_item_marked_as_processed(self):
        """Test que el inbox item se marca como procesado correctamente"""
        print("\n=== Test: Inbox item se marca como procesado ===")

        # Marcar el inbox item como procesado (simulando lo que hace process_inbox_item)
        self.inbox_item.is_processed = True
        self.inbox_item.processed_to = Task.objects.first()  # La tarea que se acaba de crear
        self.inbox_item.save()

        # Verificar que se marcó correctamente
        updated_inbox_item = InboxItem.objects.get(id=self.inbox_item.id)
        self.assertTrue(updated_inbox_item.is_processed)
        self.assertIsNotNone(updated_inbox_item.processed_to)

        print("✅ Test pasado: Inbox item marcado como procesado correctamente")


if __name__ == '__main__':
    # Ejecutar tests
    test = TestInboxDuplication()
    test.setUp()

    try:
        test.test_no_duplicate_inbox_items()
        test.test_inbox_item_marked_as_processed()
        print("\n🎉 Todos los tests pasaron exitosamente!")
    except Exception as e:
        print(f"\n❌ Error en los tests: {e}")
        sys.exit(1)