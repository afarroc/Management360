from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from datetime import date, time, datetime, timedelta
from unittest.mock import patch, MagicMock
from ..models import (
    Task, TaskSchedule, TaskStatus, Status, TaskProgram,
    InboxItem, InboxItemHistory, TaskState, TaskHistory
)


class TestInboxTaskWorkflow(TestCase):
    """
    Test completo del flujo de trabajo: Inbox -> Task -> Schedule -> History
    """

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        self.user_a = User.objects.create_user(
            username='user_a',
            email='user_a@example.com',
            password='userpass123'
        )

        # Crear estados necesarios
        self.task_status_todo = TaskStatus.objects.create(status_name='To Do', color='#6c757d')
        self.task_status_in_progress = TaskStatus.objects.create(status_name='In Progress', color='#007bff')
        self.task_status_completed = TaskStatus.objects.create(status_name='Completed', color='#28a745')
        self.event_status = Status.objects.create(status_name='Created', color='#6c757d')

        # Cliente para requests
        self.client = Client()

    def test_complete_inbox_task_workflow(self):
        """
        Test completo del flujo:
        1. Admin crea inbox item 'x' asignado a user_a
        2. Admin crea task 'y' asignada a user_a
        3. User_a procesa inbox 'x' vinculándolo a task 'y'
        4. User_a procesa task 'y' por una hora y la finaliza
        5. User_a programa task 'y' para repetir 5 días
        6. Verificar procesos históricos
        """
        print("=== Test: Flujo Completo Inbox -> Task -> Schedule ===")

        # Paso 1: Admin crea inbox item 'x' asignado a user_a
        print("\n--- Paso 1: Crear inbox item 'x' ---")
        inbox_item_x = InboxItem.objects.create(
            title='Inbox Item X',
            description='Descripción del item inbox x',
            created_by=self.admin_user,
            assigned_to=self.user_a,
            gtd_category='accionable',
            priority='media',
            action_type='hacer'
        )

        self.assertEqual(inbox_item_x.title, 'Inbox Item X')
        self.assertEqual(inbox_item_x.assigned_to, self.user_a)
        self.assertFalse(inbox_item_x.is_processed)
        print("[OK] Inbox item 'x' creado y asignado a user_a")

        # Paso 2: Admin crea task 'y' asignada a user_a
        print("\n--- Paso 2: Crear task 'y' ---")
        task_y = Task.objects.create(
            title='Task Y',
            description='Descripción de la tarea y',
            host=self.admin_user,
            assigned_to=self.user_a,
            task_status=self.task_status_todo,
            event=None,
            ticket_price=0.0
        )

        self.assertEqual(task_y.title, 'Task Y')
        self.assertEqual(task_y.assigned_to, self.user_a)
        self.assertEqual(task_y.task_status, self.task_status_todo)
        print("[OK] Task 'y' creada y asignada a user_a")

        # Paso 3: User_a procesa inbox 'x' vinculándolo a task 'y'
        print("\n--- Paso 3: Procesar inbox 'x' vinculándolo a task 'y' ---")

        # Login como user_a
        self.client.login(username='user_a', password='userpass123')

        # Procesar inbox item usando la vista process_inbox_item
        print(f"Procesando inbox item {inbox_item_x.id} con task {task_y.id}")
        print(f"User logged in: {self.client.session.get('_auth_user_id')}")

        response = self.client.post(
            reverse('process_inbox_item', kwargs={'item_id': inbox_item_x.id}),
            {
                'action': 'choose_existing_task',
                'selected_task_id': task_y.id
            }
        )

        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode() if response.content else 'No content'}")

        # Si hay error, mostrar mensajes de error
        if response.status_code != 302:
            print(f"Error response: {response.status_code}")
            if hasattr(response, 'context') and response.context and 'messages' in response.context:
                for message in response.context['messages']:
                    print(f"Message: {message}")

        # Verificar que la respuesta es exitosa (debería redirigir)
        self.assertEqual(response.status_code, 302)

        # Recargar objetos de la BD
        inbox_item_x.refresh_from_db()
        task_y.refresh_from_db()

        print(f"Inbox item processed: {inbox_item_x.is_processed}")
        print(f"Inbox item processed_to: {inbox_item_x.processed_to}")
        print(f"Inbox item processed_to_content_type: {inbox_item_x.processed_to_content_type}")
        print(f"Inbox item processed_to_object_id: {inbox_item_x.processed_to_object_id}")

        # Verificar que el inbox item está procesado y vinculado
        self.assertTrue(inbox_item_x.is_processed)
        self.assertEqual(inbox_item_x.processed_to, task_y)
        self.assertIsNotNone(inbox_item_x.processed_at)
        print("[OK] Inbox item 'x' procesado y vinculado a task 'y'")

        # Verificar historial del inbox
        inbox_history = InboxItemHistory.objects.filter(inbox_item=inbox_item_x)
        self.assertTrue(inbox_history.exists())
        self.assertEqual(inbox_history.first().action, 'linked_to_task')
        print("[OK] Historial del inbox registrado")

        # Paso 4: User_a procesa task 'y' por una hora y la finaliza
        print("\n--- Paso 4: Procesar task 'y' por una hora y finalizarla ---")

        # Cambiar estado a In Progress
        task_y.change_status(self.task_status_in_progress.id, self.user_a)
        task_y.refresh_from_db()
        self.assertEqual(task_y.task_status, self.task_status_in_progress)

        # Crear un TaskProgram para simular procesamiento por una hora
        start_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        task_program = TaskProgram.objects.create(
            title=f"{task_y.title} - Sesión de trabajo",
            start_time=start_time,
            end_time=end_time,
            host=self.user_a,
            task=task_y
        )

        self.assertIsNotNone(task_program)
        self.assertEqual(task_program.task, task_y)
        self.assertEqual(task_program.host, self.user_a)
        print("[OK] TaskProgram creado para simular 1 hora de trabajo")

        # Finalizar la tarea
        task_y.change_status(self.task_status_completed.id, self.user_a)
        task_y.refresh_from_db()
        self.assertEqual(task_y.task_status, self.task_status_completed)
        print("[OK] Task 'y' finalizada")

        # Verificar TaskState (historial de estados)
        task_states = TaskState.objects.filter(task=task_y).order_by('start_time')
        self.assertGreaterEqual(task_states.count(), 2)  # Al menos To Do -> In Progress -> Completed

        # Verificar TaskHistory
        task_history = TaskHistory.objects.filter(task=task_y)
        self.assertTrue(task_history.exists())
        print("[OK] Historial de estados de la tarea registrado")

        # Paso 5: User_a programa task 'y' para repetir 5 días
        print("\n--- Paso 5: Programar repetición por 5 días ---")

        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=5)

        task_schedule = TaskSchedule.objects.create(
            task=task_y,
            host=self.user_a,
            recurrence_type='daily',
            start_time=time(9, 0),  # 9:00 AM
            duration=timedelta(hours=1),
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )

        self.assertIsNotNone(task_schedule)
        self.assertEqual(task_schedule.task, task_y)
        self.assertEqual(task_schedule.recurrence_type, 'daily')
        self.assertEqual(task_schedule.start_time, time(9, 0))
        self.assertEqual(task_schedule.duration, timedelta(hours=1))
        print("[OK] TaskSchedule creado para repetición diaria por 5 días")

        # Generar ocurrencias
        occurrences = task_schedule.generate_occurrences(limit=10)
        self.assertEqual(len(occurrences), 6)  # 6 días (incluyendo start_date y end_date)

        # Crear TaskPrograms desde las ocurrencias
        created_programs = task_schedule.create_task_programs()
        self.assertEqual(len(created_programs), 5)  # Solo los programados, no el manual

        # Verificar que los programas se crearon correctamente
        for program in created_programs:
            self.assertEqual(program.task, task_y)
            self.assertEqual(program.host, self.user_a)
            self.assertEqual(program.start_time.time(), time(9, 0))
            self.assertEqual(program.end_time.time(), time(10, 0))

        print("[OK] 5 TaskPrograms creados para las próximas 5 días")

        # Paso 6: Verificar procesos históricos
        print("\n--- Paso 6: Verificar procesos históricos ---")

        # Verificar historial completo del inbox
        inbox_histories = InboxItemHistory.objects.filter(inbox_item=inbox_item_x)
        self.assertTrue(inbox_histories.exists())

        # Verificar historial de la tarea
        task_histories = TaskHistory.objects.filter(task=task_y)
        self.assertTrue(task_histories.exists())

        # Verificar estados de la tarea
        task_states = TaskState.objects.filter(task=task_y)
        self.assertGreaterEqual(task_states.count(), 2)

        # Verificar programas creados
        task_programs = TaskProgram.objects.filter(task=task_y)
        self.assertEqual(task_programs.count(), 6)  # 1 manual + 5 programados

        # Verificar que la programación está activa
        self.assertTrue(task_schedule.is_active_schedule())

        print("[OK] Todos los procesos históricos verificados correctamente")

        print("\n=== Test completado exitosamente ===")
        print("[OK] Inbox item creado y asignado")
        print("[OK] Task creada y asignada")
        print("[OK] Inbox procesado y vinculado a task")
        print("[OK] Task procesada por 1 hora y finalizada")
        print("[OK] Programación recurrente creada por 5 días")
        print("[OK] Procesos históricos completos verificados")

    def test_workflow_permissions(self):
        """
        Test que verifica los permisos en el flujo de trabajo
        """
        print("\n=== Test: Verificación de Permisos ===")

        # Crear otro usuario que no debería tener acceso
        other_user = User.objects.create_user(
            username='other_user',
            email='other@example.com',
            password='otherpass123'
        )

        # Crear inbox item asignado a user_a
        inbox_item = InboxItem.objects.create(
            title='Inbox Item Privado',
            created_by=self.admin_user,
            assigned_to=self.user_a,
            gtd_category='accionable'
        )

        # Crear task asignada a user_a
        task = Task.objects.create(
            title='Task Privada',
            host=self.admin_user,
            assigned_to=self.user_a,
            task_status=self.task_status_todo
        )

        # Intentar procesar como other_user (debería fallar)
        self.client.login(username='other_user', password='otherpass123')
        response = self.client.post(
            reverse('process_inbox_item', kwargs={'item_id': inbox_item.id}),
            {'action': 'choose_existing_task', 'selected_task_id': task.id}
        )

        # Debería redirigir o dar error (dependiendo de la implementación)
        self.assertIn(response.status_code, [302, 403, 404])

        # Verificar que el inbox item no fue procesado
        inbox_item.refresh_from_db()
        self.assertFalse(inbox_item.is_processed)

        print("[OK] Permisos verificados correctamente - usuario sin acceso no puede procesar")

    def test_workflow_data_integrity(self):
        """
        Test que verifica la integridad de datos durante el flujo
        """
        print("\n=== Test: Integridad de Datos ===")

        # Crear inbox item y task
        inbox_item = InboxItem.objects.create(
            title='Test Integrity',
            created_by=self.admin_user,
            assigned_to=self.user_a,
            gtd_category='accionable'
        )

        task = Task.objects.create(
            title='Task Integrity',
            host=self.admin_user,
            assigned_to=self.user_a,
            task_status=self.task_status_todo
        )

        # Contar objetos antes
        initial_inbox_count = InboxItem.objects.count()
        initial_task_count = Task.objects.count()
        initial_history_count = InboxItemHistory.objects.count()

        # Procesar workflow
        self.client.login(username='user_a', password='userpass123')
        self.client.post(
            reverse('process_inbox_item', kwargs={'item_id': inbox_item.id}),
            {'action': 'choose_existing_task', 'selected_task_id': task.id}
        )

        # Verificar que no se crearon/eliminar objetos inesperados
        self.assertEqual(InboxItem.objects.count(), initial_inbox_count)
        self.assertEqual(Task.objects.count(), initial_task_count)
        self.assertEqual(InboxItemHistory.objects.count(), initial_history_count + 1)

        # Verificar que el inbox item está correctamente vinculado
        inbox_item.refresh_from_db()
        self.assertTrue(inbox_item.is_processed)
        self.assertEqual(inbox_item.processed_to, task)

        print("[OK] Integridad de datos verificada correctamente")

    @patch('events.views.activate_bot')
    def test_bot_center_activation_mock(self, mock_activate_bot):
        """
        Test del Centro de Bots - usando mocks para evitar problemas de BD
        """
        print("\n=== Test: Centro de Bots (con mocks) ===")

        # Configurar el mock para simular respuesta exitosa
        mock_activate_bot.return_value = {
            'success': True,
            'message': 'Bot Bot de Proyectos activado exitosamente',
            'executed_tasks': [
                {'task_id': 'create_project', 'status': 'success', 'result': 'Proyecto creado'}
            ],
            'bot_name': 'Bot de Proyectos'
        }

        # Crear usuario admin con permisos
        admin_user = User.objects.create_superuser(
            username='admin_bot',
            email='admin_bot@example.com',
            password='adminbot123'
        )

        # Login como admin
        self.client.login(username='admin_bot', password='adminbot123')

        # Test 1: Activar Bot de Proyectos con tarea create_project
        print("\n--- Test 1: Activar Bot de Proyectos ---")
        response = self.client.post(
            reverse('activate_bot'),
            {
                'bot_id': 'project_bot',
                'tasks[]': ['create_project']
            }
        )

        # Verificar que se llamó a la función
        mock_activate_bot.assert_called_once()
        args, kwargs = mock_activate_bot.call_args
        self.assertEqual(args[0], admin_user)  # request.user

        print("[OK] Función activate_bot llamada correctamente")

        # Test 2: Verificar estructura de respuesta
        print("\n--- Test 2: Verificar respuesta ---")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['bot_name'], 'Bot de Proyectos')
        self.assertEqual(len(data['executed_tasks']), 1)

        print("[OK] Respuesta del bot estructurada correctamente")

        # Test 3: Verificar validaciones
        print("\n--- Test 3: Validaciones ---")

        # Reset mock
        mock_activate_bot.reset_mock()

        # Configurar mock para error
        mock_activate_bot.return_value = {
            'success': False,
            'error': 'Bot no válido'
        }

        response = self.client.post(
            reverse('activate_bot'),
            {
                'bot_id': 'invalid_bot',
                'tasks[]': ['some_task']
            }
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Bot no válido', data['error'])

        print("[OK] Validaciones funcionando correctamente")

        print("\n=== Test del Centro de Bots (con mocks) completado exitosamente ===")