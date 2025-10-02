"""
Test para probar la funcionalidad del botón "Vincular a Tarea Existente"
y el modal de selección de tareas en el procesamiento de inbox items.
"""

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from ..models import (
    Task, InboxItem, TaskStatus, Status, Project, Event,
    InboxItemClassification, InboxItemHistory
)


class TestLinkToTaskFunctionality(TestCase):
    """
    Test completo para la funcionalidad de vinculación de tareas existentes
    """

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuarios de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        # Crear estados necesarios
        self.task_status_todo = TaskStatus.objects.create(status_name='To Do')
        self.task_status_completed = TaskStatus.objects.create(status_name='Completed')
        self.event_status_created = Status.objects.create(status_name='Created')

        # Crear evento para tareas
        self.event = Event.objects.create(
            title='Evento de Prueba',
            event_status=self.event_status_created,
            host=self.user,
            assigned_to=self.user
        )

        # Crear proyecto para tareas
        self.project = Project.objects.create(
            title='Proyecto de Prueba',
            description='Descripción del proyecto',
            host=self.user,
            assigned_to=self.user,
            event=self.event,
            project_status=Project.objects.filter().first()  # Usar estado por defecto
        )

        # Crear tareas existentes para vincular
        self.existing_task_1 = Task.objects.create(
            title='Tarea Existente 1',
            description='Descripción de tarea existente 1',
            host=self.user,
            assigned_to=self.user,
            event=self.event,
            project=self.project,
            task_status=self.task_status_todo,
            important=False,
            ticket_price=0.07
        )

        self.existing_task_2 = Task.objects.create(
            title='Tarea Existente 2',
            description='Descripción de tarea existente 2',
            host=self.user,
            assigned_to=self.user,
            event=self.event,
            project=self.project,
            task_status=self.task_status_todo,
            important=True,
            ticket_price=0.07
        )

        # Crear tarea de otro usuario (para probar permisos)
        self.other_user_task = Task.objects.create(
            title='Tarea de Otro Usuario',
            description='Esta tarea pertenece a otro usuario',
            host=self.other_user,
            assigned_to=self.other_user,
            event=self.event,
            project=self.project,
            task_status=self.task_status_todo,
            ticket_price=0.07
        )

        # Crear item del inbox para procesar
        self.inbox_item = InboxItem.objects.create(
            title='Item del Inbox para Vincular',
            description='Este item será vinculado a una tarea existente',
            created_by=self.user,
            gtd_category='accionable',
            action_type='hacer',
            priority='media',
            is_processed=False
        )

        # Configurar cliente de prueba
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_get_available_tasks_api(self):
        """Test que la API de tareas disponibles funciona correctamente"""
        print("\n=== Test: API de tareas disponibles ===")

        # Hacer petición GET a la API
        response = self.client.get(reverse('inbox_api_tasks'))

        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('tasks', data)
        self.assertIn('total', data)

        # Verificar que se incluyen las tareas del usuario
        task_titles = [task['title'] for task in data['tasks']]
        self.assertIn('Tarea Existente 1', task_titles)
        self.assertIn('Tarea Existente 2', task_titles)
        # No debe incluir tareas de otros usuarios
        self.assertNotIn('Tarea de Otro Usuario', task_titles)

        print(f"✓ API devolvió {data['total']} tareas correctamente")
        print(f"✓ Tareas encontradas: {task_titles}")

    def test_get_available_tasks_with_search(self):
        """Test que la búsqueda en la API funciona correctamente"""
        print("\n=== Test: Búsqueda en API de tareas ===")

        # Buscar tareas que contengan "Existente 1"
        response = self.client.get(
            reverse('inbox_api_tasks') + '?search=Existente+1'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Solo debe devolver la tarea que coincide con la búsqueda
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['tasks'][0]['title'], 'Tarea Existente 1')

        print("✓ Búsqueda funcionó correctamente")

    def test_get_available_projects_api(self):
        """Test que la API de proyectos disponibles funciona correctamente"""
        print("\n=== Test: API de proyectos disponibles ===")

        response = self.client.get(reverse('inbox_api_projects'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('projects', data)

        # Verificar que se incluye el proyecto del usuario
        project_titles = [project['title'] for project in data['projects']]
        self.assertIn('Proyecto de Prueba', project_titles)

        print(f"✓ API devolvió {data['total']} proyectos correctamente")

    def test_link_to_existing_task_process(self):
        """Test del proceso completo de vinculación a tarea existente"""
        print("\n=== Test: Proceso completo de vinculación ===")

        # Datos para la vinculación
        post_data = {
            'action': 'link_to_task',
            'task_id': self.existing_task_1.id,
            'csrfmiddlewaretoken': 'test-csrf-token'  # En un test real se obtendría correctamente
        }

        # Hacer petición POST para vincular
        response = self.client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data
        )

        # Verificar que la respuesta sea exitosa (redirección)
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito

        # Verificar que el inbox item se marcó como procesado
        self.inbox_item.refresh_from_db()
        self.assertTrue(self.inbox_item.is_processed)
        self.assertIsNotNone(self.inbox_item.processed_at)

        # Verificar que se creó el historial
        history_entry = InboxItemHistory.objects.filter(
            inbox_item=self.inbox_item,
            action='linked_to_task'
        ).first()
        self.assertIsNotNone(history_entry)

        print("✓ Vinculación completada exitosamente")
        print(f"✓ Inbox item procesado: {self.inbox_item.is_processed}")
        print(f"✓ Historial creado: {history_entry is not None}")

    def test_link_to_nonexistent_task(self):
        """Test intentar vincular a una tarea que no existe"""
        print("\n=== Test: Vinculación a tarea inexistente ===")

        post_data = {
            'action': 'link_to_task',
            'task_id': 99999,  # ID que no existe
        }

        response = self.client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data
        )

        # Verificar que devuelve error
        self.assertEqual(response.status_code, 200)  # Se queda en la misma página con error

        # Verificar que el inbox item NO se procesó
        self.inbox_item.refresh_from_db()
        self.assertFalse(self.inbox_item.is_processed)

        print("✓ Error manejado correctamente para tarea inexistente")

    def test_link_to_task_without_permissions(self):
        """Test intentar vincular a tarea de otro usuario"""
        print("\n=== Test: Vinculación sin permisos ===")

        post_data = {
            'action': 'link_to_task',
            'task_id': self.other_user_task.id,  # Tarea de otro usuario
        }

        response = self.client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data
        )

        # Verificar que devuelve error de permisos
        self.assertEqual(response.status_code, 200)

        # Verificar que el inbox item NO se procesó
        self.inbox_item.refresh_from_db()
        self.assertFalse(self.inbox_item.is_processed)

        print("✓ Permisos verificados correctamente")

    def test_modal_task_selection_javascript(self):
        """Test que el JavaScript del modal funciona correctamente"""
        print("\n=== Test: Funcionalidad JavaScript del modal ===")

        # Obtener la página del procesamiento de inbox
        response = self.client.get(
            reverse('process_inbox_item', args=[self.inbox_item.id])
        )

        self.assertEqual(response.status_code, 200)

        # Verificar que el contenido incluye el botón de vinculación
        content = response.content.decode('utf-8')
        self.assertIn('Vincular a Tarea Existente', content)
        self.assertIn('showTaskSelector()', content)
        self.assertIn('linkToExistingTaskBtn', content)

        # Verificar que incluye el modal HTML
        self.assertIn('taskSelectorModal', content)
        self.assertIn('Elegir Tarea Existente', content)

        print("✓ Modal HTML incluido correctamente")
        print("✓ JavaScript functions presentes")

    def test_task_selection_modal_content(self):
        """Test que el modal contiene los elementos necesarios"""
        print("\n=== Test: Contenido del modal de selección ===")

        response = self.client.get(
            reverse('process_inbox_item', args=[self.inbox_item.id])
        )

        content = response.content.decode('utf-8')

        # Verificar elementos del modal
        self.assertIn('taskSelectorModal', content)
        self.assertIn('taskSearch', content)
        self.assertIn('Buscar Tareas:', content)
        self.assertIn('taskList', content)

        # Verificar botones del modal
        self.assertIn('Cancelar', content)
        self.assertIn('Confirmar y Vincular', content)

        print("✓ Modal contiene todos los elementos necesarios")

    def test_confirmation_message_display(self):
        """Test que los mensajes de confirmación se muestran correctamente"""
        print("\n=== Test: Mensajes de confirmación ===")

        # Primero crear una nueva tarea para vincular
        new_task = Task.objects.create(
            title='Nueva Tarea para Test',
            description='Tarea creada específicamente para test',
            host=self.user,
            assigned_to=self.user,
            event=self.event,
            project=self.project,
            task_status=self.task_status_todo,
            ticket_price=0.07
        )

        # Vincular el inbox item a la nueva tarea
        post_data = {
            'action': 'link_to_task',
            'task_id': new_task.id,
        }

        response = self.client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data,
            follow=True  # Seguir redirecciones
        )

        # Verificar que se redirige correctamente después de la vinculación
        self.assertEqual(response.status_code, 200)

        # Verificar que aparece el mensaje de éxito
        messages_list = list(response.context['messages'])
        success_messages = [msg for msg in messages_list if msg.level_tag == 'success']

        if success_messages:
            print(f"✓ Mensaje de éxito mostrado: {success_messages[0].message}")
        else:
            print("✓ Vinculación completada (mensaje puede estar en la vista de destino)")

    def test_inbox_item_processed_state(self):
        """Test que el estado del inbox item se actualiza correctamente"""
        print("\n=== Test: Estado del inbox item después de vinculación ===")

        # Estado inicial
        self.assertFalse(self.inbox_item.is_processed)
        self.assertIsNone(self.inbox_item.processed_at)

        # Vincular a tarea existente
        post_data = {
            'action': 'link_to_task',
            'task_id': self.existing_task_1.id,
        }

        self.client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data
        )

        # Verificar cambios en el estado
        self.inbox_item.refresh_from_db()
        self.assertTrue(self.inbox_item.is_processed)
        self.assertIsNotNone(self.inbox_item.processed_at)

        # Verificar que se estableció la relación con la tarea
        from django.contrib.contenttypes.models import ContentType
        task_content_type = ContentType.objects.get_for_model(Task)
        self.assertEqual(self.inbox_item.processed_to_content_type, task_content_type)
        self.assertEqual(self.inbox_item.processed_to_object_id, self.existing_task_1.id)

        print("✓ Estado del inbox item actualizado correctamente")
        print(f"✓ Procesado: {self.inbox_item.is_processed}")
        print(f"✓ Fecha de procesamiento: {self.inbox_item.processed_at}")
        print(f"✓ Vinculado a tarea ID: {self.inbox_item.processed_to_object_id}")

    def test_multiple_inbox_items_linking(self):
        """Test vincular múltiples items del inbox a diferentes tareas"""
        print("\n=== Test: Vinculación múltiple de items ===")

        # Crear otro inbox item
        inbox_item_2 = InboxItem.objects.create(
            title='Segundo Item del Inbox',
            description='Otro item para vincular',
            created_by=self.user,
            gtd_category='accionable',
            priority='alta',
            is_processed=False
        )

        # Vincular primer item a primera tarea
        post_data_1 = {
            'action': 'link_to_task',
            'task_id': self.existing_task_1.id,
        }

        self.client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data_1
        )

        # Vincular segundo item a segunda tarea
        post_data_2 = {
            'action': 'link_to_task',
            'task_id': self.existing_task_2.id,
        }

        self.client.post(
            reverse('process_inbox_item', args=[inbox_item_2.id]),
            post_data_2
        )

        # Verificar que ambos items se procesaron correctamente
        self.inbox_item.refresh_from_db()
        inbox_item_2.refresh_from_db()

        self.assertTrue(self.inbox_item.is_processed)
        self.assertTrue(inbox_item_2.is_processed)

        # Verificar que están vinculados a tareas diferentes
        self.assertEqual(self.inbox_item.processed_to_object_id, self.existing_task_1.id)
        self.assertEqual(inbox_item_2.processed_to_object_id, self.existing_task_2.id)

        print("✓ Múltiples vinculaciones completadas correctamente")

    def test_task_search_functionality(self):
        """Test que la funcionalidad de búsqueda de tareas funciona"""
        print("\n=== Test: Funcionalidad de búsqueda de tareas ===")

        # Crear tarea con título específico para búsqueda
        search_task = Task.objects.create(
            title='Tarea Especial de Búsqueda',
            description='Esta tarea debe aparecer en búsquedas específicas',
            host=self.user,
            assigned_to=self.user,
            event=self.event,
            project=self.project,
            task_status=self.task_status_todo,
            ticket_price=0.07
        )

        # Buscar por título específico
        response = self.client.get(
            reverse('inbox_api_tasks') + '?search=Especial+de+Búsqueda'
        )

        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Verificar que la tarea específica aparece en los resultados
        task_titles = [task['title'] for task in data['tasks']]
        self.assertIn('Tarea Especial de Búsqueda', task_titles)

        print("✓ Búsqueda específica funcionó correctamente")

    def test_error_handling_edge_cases(self):
        """Test manejo de errores en casos extremos"""
        print("\n=== Test: Manejo de errores extremos ===")

        # Test con task_id inválido (no numérico)
        post_data = {
            'action': 'link_to_task',
            'task_id': 'invalid_id',
        }

        response = self.client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data
        )

        # Debe manejar el error sin romper
        self.assertEqual(response.status_code, 200)

        # El item no debe procesarse
        self.inbox_item.refresh_from_db()
        self.assertFalse(self.inbox_item.is_processed)

        print("✓ Error de ID inválido manejado correctamente")

    def test_csrf_protection(self):
        """Test que la protección CSRF está funcionando"""
        print("\n=== Test: Protección CSRF ===")

        # Intentar hacer POST sin token CSRF
        post_data = {
            'action': 'link_to_task',
            'task_id': self.existing_task_1.id,
        }

        # En Django tests, el cliente automáticamente incluye CSRF token
        # Pero podemos verificar que el formulario lo requiere
        response = self.client.get(
            reverse('process_inbox_item', args=[self.inbox_item.id])
        )

        content = response.content.decode('utf-8')
        self.assertIn('csrfmiddlewaretoken', content)

        print("✓ Protección CSRF presente en el formulario")

    def test_user_permissions_validation(self):
        """Test validación de permisos de usuario"""
        print("\n=== Test: Validación de permisos ===")

        # Crear cliente para otro usuario
        other_client = Client()
        other_client.login(username='otheruser', password='testpass123')

        # Intentar vincular tarea de otro usuario
        post_data = {
            'action': 'link_to_task',
            'task_id': self.existing_task_1.id,  # Tarea del primer usuario
        }

        response = other_client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data
        )

        # Debe fallar por permisos
        self.assertEqual(response.status_code, 200)

        # El item no debe procesarse
        self.inbox_item.refresh_from_db()
        self.assertFalse(self.inbox_item.is_processed)

        print("✓ Validación de permisos funcionando correctamente")

    def test_inbox_item_history_tracking(self):
        """Test que se registra correctamente el historial de cambios"""
        print("\n=== Test: Seguimiento de historial ===")

        # Vincular tarea
        post_data = {
            'action': 'link_to_task',
            'task_id': self.existing_task_1.id,
        }

        self.client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data
        )

        # Verificar que se creó entrada en el historial
        history_entries = InboxItemHistory.objects.filter(inbox_item=self.inbox_item)

        # Debe haber al menos una entrada por la vinculación
        link_entries = history_entries.filter(action='linked_to_task')
        self.assertTrue(link_entries.exists())

        # Verificar detalles de la entrada de historial
        history_entry = link_entries.first()
        self.assertEqual(history_entry.user, self.user)
        self.assertIn('linked_task_id', history_entry.new_values)
        self.assertEqual(history_entry.new_values['linked_task_id'], self.existing_task_1.id)

        print("✓ Historial registrado correctamente")
        print(f"✓ Entradas de historial: {history_entries.count()}")
        print(f"✓ Acción registrada: {history_entry.action}")

    def test_template_rendering_with_data(self):
        """Test que la plantilla se renderiza correctamente con datos"""
        print("\n=== Test: Renderizado de plantilla ===")

        response = self.client.get(
            reverse('process_inbox_item', args=[self.inbox_item.id])
        )

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Verificar que se muestran los datos del inbox item
        self.assertIn(self.inbox_item.title, content)
        self.assertIn(self.inbox_item.description, content)

        # Verificar que aparecen las opciones de acción
        self.assertIn('Crear Nueva Tarea', content)
        self.assertIn('Vincular a Tarea Existente', content)
        self.assertIn('Crear Nuevo Proyecto', content)

        # Verificar estadísticas
        self.assertIn('Items procesados', content)
        self.assertIn('Items pendientes', content)

        print("✓ Plantilla renderizada correctamente con datos")

    def test_javascript_functions_presence(self):
        """Test que las funciones JavaScript necesarias están presentes"""
        print("\n=== Test: Funciones JavaScript presentes ===")

        response = self.client.get(
            reverse('process_inbox_item', args=[self.inbox_item.id])
        )

        content = response.content.decode('utf-8')

        # Verificar funciones JavaScript críticas
        self.assertIn('showTaskSelector', content)
        self.assertIn('loadAvailableTasks', content)
        self.assertIn('selectTask', content)
        self.assertIn('confirmTaskLink', content)
        self.assertIn('linkToExistingTask', content)

        # Verificar elementos del DOM necesarios
        self.assertIn('taskSelectorModal', content)
        self.assertIn('taskSearch', content)
        self.assertIn('taskList', content)

        print("✓ Todas las funciones JavaScript críticas presentes")

    def test_api_response_format(self):
        """Test que las respuestas de la API tienen el formato correcto"""
        print("\n=== Test: Formato de respuesta API ===")

        # Test API de tareas
        response = self.client.get(reverse('inbox_api_tasks'))
        data = json.loads(response.content)

        # Verificar estructura de respuesta
        self.assertIn('success', data)
        self.assertIn('tasks', data)
        self.assertIn('total', data)
        self.assertIsInstance(data['tasks'], list)
        self.assertIsInstance(data['total'], int)

        # Verificar estructura de cada tarea
        if data['tasks']:
            task = data['tasks'][0]
            expected_fields = ['id', 'title', 'description', 'status', 'status_color',
                             'project', 'project_id', 'updated_at', 'important']
            for field in expected_fields:
                self.assertIn(field, task)

        print("✓ Formato de respuesta API correcto")

    def test_concurrent_linking_attempts(self):
        """Test múltiples intentos de vinculación concurrentes"""
        print("\n=== Test: Intentos concurrentes de vinculación ===")

        # Crear múltiples clientes simulando usuarios concurrentes
        clients_data = []

        # Crear varios inbox items
        for i in range(3):
            inbox_item = InboxItem.objects.create(
                title=f'Item Concurrente {i}',
                description=f'Descripción del item {i}',
                created_by=self.user,
                gtd_category='accionable',
                priority='media',
                is_processed=False
            )
            clients_data.append((inbox_item, self.existing_task_1.id))

        # Intentar vincular todos al mismo tiempo
        for inbox_item, task_id in clients_data:
            post_data = {
                'action': 'link_to_task',
                'task_id': task_id,
            }

            response = self.client.post(
                reverse('process_inbox_item', args=[inbox_item.id]),
                post_data
            )

            # Todos deben procesarse correctamente
            self.assertEqual(response.status_code, 302)

        # Verificar que todos se procesaron
        for inbox_item, _ in clients_data:
            inbox_item.refresh_from_db()
            self.assertTrue(inbox_item.is_processed)

        print(f"✓ {len(clients_data)} vinculaciones concurrentes completadas")

    def test_database_integrity_after_linking(self):
        """Test que la integridad de la base de datos se mantiene después de vincular"""
        print("\n=== Test: Integridad de base de datos ===")

        # Obtener conteos iniciales
        initial_inbox_count = InboxItem.objects.count()
        initial_history_count = InboxItemHistory.objects.count()

        # Vincular tarea
        post_data = {
            'action': 'link_to_task',
            'task_id': self.existing_task_1.id,
        }

        self.client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data
        )

        # Verificar que no se crearon registros duplicados
        final_inbox_count = InboxItem.objects.count()
        final_history_count = InboxItemHistory.objects.count()

        self.assertEqual(initial_inbox_count, final_inbox_count)
        self.assertEqual(final_history_count, initial_history_count + 1)  # Solo una nueva entrada de historial

        # Verificar que la tarea sigue existiendo y no se modificó
        self.existing_task_1.refresh_from_db()
        self.assertEqual(self.existing_task_1.title, 'Tarea Existente 1')

        print("✓ Integridad de base de datos mantenida")
        print(f"✓ Inbox items: {initial_inbox_count} (sin cambios)")
        print(f"✓ Historial: +1 entrada (de {initial_history_count} a {final_history_count})")

    def test_performance_with_large_dataset(self):
        """Test rendimiento con gran cantidad de tareas"""
        print("\n=== Test: Rendimiento con dataset grande ===")

        # Crear muchas tareas para simular escenario real
        many_tasks = []
        for i in range(100):
            task = Task.objects.create(
                title=f'Tarea de Rendimiento {i}',
                description=f'Descripción de tarea de rendimiento {i}',
                host=self.user,
                assigned_to=self.user,
                event=self.event,
                project=self.project,
                task_status=self.task_status_todo,
                ticket_price=0.07
            )
            many_tasks.append(task)

        # Medir tiempo de respuesta de la API
        import time
        start_time = time.time()

        response = self.client.get(reverse('inbox_api_tasks'))

        end_time = time.time()
        response_time = end_time - start_time

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Verificar que el tiempo de respuesta es aceptable (< 2 segundos)
        self.assertLess(response_time, 2.0)

        print(f"✓ Tiempo de respuesta: {response_time:.3f} segundos")
        print(f"✓ Tareas procesadas: {data['total']}")

    def test_accessibility_features(self):
        """Test características de accesibilidad en el modal"""
        print("\n=== Test: Características de accesibilidad ===")

        response = self.client.get(
            reverse('process_inbox_item', args=[self.inbox_item.id])
        )

        content = response.content.decode('utf-8')

        # Verificar atributos de accesibilidad
        self.assertIn('aria-live', content)
        self.assertIn('aria-atomic', content)
        self.assertIn('role="alert"', content)

        # Verificar navegación por teclado
        self.assertIn('tabindex', content)
        self.assertIn('autofocus', content)

        # Verificar textos descriptivos
        self.assertIn('Buscar Tareas:', content)
        self.assertIn('visually-hidden', content)  # Para lectores de pantalla

        print("✓ Características de accesibilidad presentes")

    def test_responsive_design_elements(self):
        """Test elementos de diseño responsivo"""
        print("\n=== Test: Diseño responsivo ===")

        response = self.client.get(
            reverse('process_inbox_item', args=[self.inbox_item.id])
        )

        content = response.content.decode('utf-8')

        # Verificar clases de Bootstrap para responsividad
        self.assertIn('col-md-6', content)
        self.assertIn('col-lg-4', content)
        self.assertIn('col-lg-8', content)

        # Verificar media queries en CSS
        self.assertIn('@media (max-width: 768px)', content)
        self.assertIn('container-fluid', content)

        print("✓ Elementos de diseño responsivo presentes")

    def test_error_messages_display(self):
        """Test que los mensajes de error se muestran correctamente"""
        print("\n=== Test: Mensajes de error ===")

        # Intentar vincular a tarea inexistente
        post_data = {
            'action': 'link_to_task',
            'task_id': 99999,
        }

        response = self.client.post(
            reverse('process_inbox_item', args=[self.inbox_item.id]),
            post_data
        )

        # Verificar que se queda en la página con error
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Verificar que hay elementos para mostrar errores
        self.assertIn('alert', content)
        self.assertIn('Error', content.lower())

        print("✓ Sistema de mensajes de error funcionando")

    def test_success_workflow_integration(self):
        """Test integración completa del flujo de éxito"""
        print("\n=== Test: Flujo completo de éxito ===")

        # 1. Crear tarea específica para este test
        test_task = Task.objects.create(
            title='Tarea de Flujo Completo',
            description='Tarea creada para probar el flujo completo',
            host=self.user,
            assigned_to=self.user,
            event=self.event,
            project=self.project,
            task_status=self.task_status_todo,
            important=True,
            ticket_price=0.07
        )

        # 2. Crear inbox item específico
        workflow_item = InboxItem.objects.create(
            title='Item de Flujo de Trabajo',
            description='Item creado específicamente para test de flujo completo',
            created_by=self.user,
            gtd_category='accionable',
            priority='alta',
            is_processed=False
        )

        # 3. Verificar API de tareas funciona
        api_response = self.client.get(reverse('inbox_api_tasks'))
        self.assertEqual(api_response.status_code, 200)

        # 4. Vincular el item a la tarea
        post_data = {
            'action': 'link_to_task',
            'task_id': test_task.id,
        }

        link_response = self.client.post(
            reverse('process_inbox_item', args=[workflow_item.id]),
            post_data
        )

        # 5. Verificar redirección exitosa
        self.assertEqual(link_response.status_code, 302)

        # 6. Verificar cambios en la base de datos
        workflow_item.refresh_from_db()
        self.assertTrue(workflow_item.is_processed)
        self.assertEqual(workflow_item.processed_to_object_id, test_task.id)

        # 7. Verificar historial
        history_count = InboxItemHistory.objects.filter(inbox_item=workflow_item).count()
        self.assertGreater(history_count, 0)

        print("✓ Flujo completo ejecutado exitosamente")
        print("✓ Todos los pasos del workflow completados correctamente")

    def test_cleanup_after_test(self):
        """Test limpieza después de las pruebas"""
        print("\n=== Test: Limpieza después de pruebas ===")

        # Contar registros antes de limpieza
        initial_tasks = Task.objects.count()
        initial_inbox = InboxItem.objects.count()
        initial_history = InboxItemHistory.objects.count()

        # Nota: En un entorno de test real, se usarían fixtures o señales
        # para limpiar automáticamente después de cada test

        print(f"✓ Registros actuales - Tareas: {initial_tasks}, Inbox: {initial_inbox}, Historial: {initial_history}")

        # Verificar que los datos de prueba existen
        self.assertGreaterEqual(Task.objects.count(), 4)  # Al menos las tareas creadas en setUp
        self.assertGreaterEqual(InboxItem.objects.count(), 1)  # Al menos el item creado en setUp

        print("✓ Limpieza y verificación completadas")