from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction
from ..models import Task, InboxItem, TaskStatus, Status
from ..management.task_manager import TaskManager


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

        print("Test pasado: No se crearon inbox items duplicados")

    def test_inbox_item_marked_as_processed(self):
        """Test que el inbox item se puede marcar como procesado correctamente"""
        print("\n=== Test: Inbox item se puede marcar como procesado ===")

        # Marcar el inbox item como procesado (simulando lo que hace process_inbox_item)
        self.inbox_item.is_processed = True
        self.inbox_item.save()

        # Verificar que se marcó correctamente
        updated_inbox_item = InboxItem.objects.get(id=self.inbox_item.id)
        self.assertTrue(updated_inbox_item.is_processed)

        print("Test pasado: Inbox item marcado como procesado correctamente")

    def test_inbox_item_linked_to_task_and_event(self):
        """Test que el inbox item se vincula correctamente a la tarea y al evento generado"""
        print("\n=== Test: Inbox item vinculado a tarea y evento ===")

        # Crear tarea desde el inbox usando TaskManager
        task_manager = TaskManager(self.user)
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

        # Verificar que la tarea se creó correctamente
        self.assertIsNotNone(task)
        self.assertEqual(task.title, self.inbox_item.title)

        # Verificar que la tarea tiene un evento asociado
        self.assertIsNotNone(task.event)
        print(f"Evento creado: {task.event.title}")
        print(f"Estado del evento: {task.event.event_status.status_name}")

        # Verificar que se puede acceder al evento a través de la tarea
        self.assertEqual(task.event.title, task.title)  # El evento tiene el mismo título que la tarea
        self.assertEqual(task.event.host, self.user)
        self.assertEqual(task.event.assigned_to, self.user)

        # Marcar el inbox item como procesado y vinculado a la tarea
        self.inbox_item.is_processed = True
        self.inbox_item.processed_to = task
        self.inbox_item.save()

        # Verificar que el inbox item está correctamente vinculado
        updated_inbox_item = InboxItem.objects.get(id=self.inbox_item.id)
        self.assertTrue(updated_inbox_item.is_processed)
        self.assertEqual(updated_inbox_item.processed_to, task)

        # Verificar que se puede acceder al evento a través del inbox item
        # inbox_item -> task -> event
        linked_task = updated_inbox_item.processed_to
        linked_event = linked_task.event

        self.assertIsNotNone(linked_event)
        self.assertEqual(linked_event.title, task.title)
        self.assertEqual(linked_event.host, self.user)

        print("Test pasado: Inbox item correctamente vinculado a tarea y evento")
        print(f"  - Inbox Item: {updated_inbox_item.title}")
        print(f"  - Tarea vinculada: {linked_task.title}")
        print(f"  - Evento vinculado: {linked_event.title}")