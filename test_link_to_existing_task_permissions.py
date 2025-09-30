#!/usr/bin/env python3
"""
Prueba para verificar el manejo de permisos en la opción 'Vincular a Tarea Existente'
cuando el inbox es asignado (creado por otro usuario)
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from events.models import Task, InboxItem, TaskStatus, Status, Project, Event
from events.management.task_manager import TaskManager


class TestLinkToExistingTaskPermissions(TestCase):
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuarios
        self.user1 = User.objects.create_user(  # Creador del inbox
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(  # Asignado al inbox
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.user3 = User.objects.create_user(  # Dueño de la tarea
            username='user3',
            email='user3@example.com',
            password='pass123'
        )

        # Crear estados necesarios
        self.task_status = TaskStatus.objects.create(status_name='To Do')
        self.event_status = Status.objects.create(status_name='Created')

        # Crear tarea existente propiedad de user3
        self.existing_task = Task.objects.create(
            title='Tarea existente de user3',
            description='Esta tarea pertenece a user3',
            host=self.user3,
            assigned_to=self.user3,
            task_status=self.task_status,
            ticket_price=0.07
        )

        # Crear inbox item creado por user1 y asignado a user2
        self.inbox_item = InboxItem.objects.create(
            title='Inbox item asignado',
            description='Este inbox fue creado por user1 pero asignado a user2',
            created_by=self.user1,
            assigned_to=self.user2,
            is_processed=False,
            gtd_category='accionable',
            priority='media'
        )

        # Configurar cliente para simular requests
        self.client = Client()

    def test_link_to_task_without_permissions(self):
        """Test que user2 no puede vincular inbox asignado a tarea de user3 sin permisos"""
        print("=== Test: Vincular a tarea existente sin permisos ===")

        # Login como user2 (el asignado al inbox)
        self.client.login(username='user2', password='pass123')

        # Intentar vincular el inbox item a la tarea existente de user3
        url = reverse('process_inbox_item', kwargs={'item_id': self.inbox_item.id})
        response = self.client.post(url, {
            'action': 'link_to_task',
            'task_id': self.existing_task.id
        })

        # Verificar que se redirige de vuelta al formulario (debido al error)
        self.assertEqual(response.status_code, 302)
        self.assertIn('process_inbox_item', response.url)
        self.assertIn(str(self.inbox_item.id), response.url)

        # Verificar que se mostró el mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('No tienes permisos para vincular a esta tarea' in str(msg) for msg in messages))

        # Verificar que el inbox item NO se marcó como procesado
        self.inbox_item.refresh_from_db()
        self.assertFalse(self.inbox_item.is_processed)

        print("✅ Test pasado: Se mostró error de permisos correctamente")

    def test_link_to_task_with_permissions(self):
        """Test que user2 puede vincular inbox asignado a tarea donde tiene permisos"""
        print("\n=== Test: Vincular a tarea existente con permisos ===")

        # Crear una tarea donde user2 tenga permisos (es attendee)
        task_with_permissions = Task.objects.create(
            title='Tarea donde user2 es attendee',
            description='Esta tarea permite que user2 la vincule',
            host=self.user3,
            assigned_to=self.user3,
            task_status=self.task_status,
            ticket_price=0.07
        )
        # Agregar user2 como attendee
        task_with_permissions.attendees.add(self.user2)

        # Login como user2
        self.client.login(username='user2', password='pass123')

        # Intentar vincular el inbox item a la tarea donde tiene permisos
        url = reverse('process_inbox_item', kwargs={'item_id': self.inbox_item.id})
        response = self.client.post(url, {
            'action': 'link_to_task',
            'task_id': task_with_permissions.id
        })

        # Verificar que se redirige a la tarea (éxito)
        self.assertEqual(response.status_code, 302)
        self.assertIn('tasks', response.url)
        self.assertIn(str(task_with_permissions.id), response.url)

        # Verificar que el inbox item se marcó como procesado
        self.inbox_item.refresh_from_db()
        self.assertTrue(self.inbox_item.is_processed)
        self.assertEqual(self.inbox_item.processed_to_object_id, task_with_permissions.id)

        print("✅ Test pasado: Vinculación exitosa con permisos")

    def test_link_to_task_as_host(self):
        """Test que el host de la tarea puede vincular cualquier inbox"""
        print("\n=== Test: Host de tarea puede vincular inbox ===")

        # Login como user3 (host de la tarea)
        self.client.login(username='user3', password='pass123')

        # Intentar vincular el inbox item a su propia tarea
        url = reverse('process_inbox_item', kwargs={'item_id': self.inbox_item.id})
        response = self.client.post(url, {
            'action': 'link_to_task',
            'task_id': self.existing_task.id
        })

        # Verificar que se redirige a la tarea (éxito)
        self.assertEqual(response.status_code, 302)
        self.assertIn('tasks', response.url)
        self.assertIn(str(self.existing_task.id), response.url)

        # Verificar que el inbox item se marcó como procesado
        self.inbox_item.refresh_from_db()
        self.assertTrue(self.inbox_item.is_processed)
        self.assertEqual(self.inbox_item.processed_to_object_id, self.existing_task.id)

        print("✅ Test pasado: Host puede vincular exitosamente")

    def test_inbox_creator_can_link_to_own_task(self):
        """Test que el creador del inbox puede vincular a su propia tarea"""
        print("\n=== Test: Creador del inbox puede vincular a su tarea ===")

        # Crear una tarea propiedad de user1 (creador del inbox)
        task_user1 = Task.objects.create(
            title='Tarea de user1',
            description='Esta tarea pertenece al creador del inbox',
            host=self.user1,
            assigned_to=self.user1,
            task_status=self.task_status,
            ticket_price=0.07
        )

        # Login como user1 (creador del inbox)
        self.client.login(username='user1', password='pass123')

        # Intentar vincular el inbox item a su propia tarea
        url = reverse('process_inbox_item', kwargs={'item_id': self.inbox_item.id})
        response = self.client.post(url, {
            'action': 'link_to_task',
            'task_id': task_user1.id
        })

        # Verificar que se redirige a la tarea (éxito)
        self.assertEqual(response.status_code, 302)
        self.assertIn('tasks', response.url)
        self.assertIn(str(task_user1.id), response.url)

        # Verificar que el inbox item se marcó como procesado
        self.inbox_item.refresh_from_db()
        self.assertTrue(self.inbox_item.is_processed)
        self.assertEqual(self.inbox_item.processed_to_object_id, task_user1.id)

        print("✅ Test pasado: Creador del inbox puede vincular a su tarea")


if __name__ == '__main__':
    # Ejecutar tests
    import unittest

    # Configurar Django para tests
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])

    if failures == 0:
        print("\n🎉 Todos los tests pasaron exitosamente!")
    else:
        print(f"\n❌ {failures} test(s) fallaron")
        sys.exit(1)