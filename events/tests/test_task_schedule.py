from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from datetime import date, time, datetime, timedelta
from ..models import Task, TaskSchedule, TaskStatus, Status, TaskProgram


class TestTaskSchedule(TestCase):
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

        # Crear tarea de prueba
        self.task = Task.objects.create(
            title='Tarea de prueba para schedule',
            description='Descripción de prueba',
            host=self.user,
            assigned_to=self.user,
            task_status=self.task_status,
            ticket_price=0.0
        )

        # Fechas de prueba
        self.start_date = date.today() + timedelta(days=1)
        self.end_date = self.start_date + timedelta(days=30)

    def test_create_task_schedule_daily(self):
        """Test crear una programación diaria"""
        print("=== Test: Crear programación diaria ===")

        schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='daily',
            start_time=time(9, 0),  # 9:00 AM
            duration=timedelta(hours=1),
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True
        )

        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.recurrence_type, 'daily')
        self.assertEqual(schedule.start_time, time(9, 0))
        self.assertEqual(schedule.duration, timedelta(hours=1))

        print("Test pasado: Programación diaria creada correctamente")

    def test_create_task_schedule_weekly(self):
        """Test crear una programación semanal"""
        print("\n=== Test: Crear programación semanal ===")

        schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='weekly',
            monday=True,
            wednesday=True,
            friday=True,
            start_time=time(14, 30),  # 2:30 PM
            duration=timedelta(hours=2),
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True
        )

        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.recurrence_type, 'weekly')
        self.assertTrue(schedule.monday)
        self.assertTrue(schedule.wednesday)
        self.assertTrue(schedule.friday)
        self.assertFalse(schedule.tuesday)  # No debería estar seleccionado

        print("Test pasado: Programación semanal creada correctamente")

    def test_generate_occurrences_daily(self):
        """Test generar ocurrencias para programación diaria"""
        print("\n=== Test: Generar ocurrencias diarias ===")

        schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='daily',
            start_time=time(10, 0),
            duration=timedelta(hours=1),
            start_date=self.start_date,
            end_date=self.start_date + timedelta(days=5),  # 6 días total
            is_active=True
        )

        occurrences = schedule.generate_occurrences(limit=10)

        # Debería generar 6 ocurrencias (día 0 a 5)
        self.assertEqual(len(occurrences), 6)

        # Verificar que todas las ocurrencias tienen la hora correcta
        for occurrence in occurrences:
            self.assertEqual(occurrence['start_time'].time(), time(10, 0))
            self.assertEqual(occurrence['end_time'].time(), time(11, 0))  # 1 hora después

        print(f"Test pasado: {len(occurrences)} ocurrencias diarias generadas")

    def test_generate_occurrences_weekly(self):
        """Test generar ocurrencias para programación semanal"""
        print("\n=== Test: Generar ocurrencias semanales ===")

        schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='weekly',
            monday=True,
            wednesday=True,
            start_time=time(15, 0),
            duration=timedelta(hours=1, minutes=30),
            start_date=self.start_date,
            end_date=self.start_date + timedelta(days=14),  # 2 semanas
            is_active=True
        )

        occurrences = schedule.generate_occurrences(limit=10)

        # Debería generar 4 ocurrencias (2 lunes + 2 miércoles)
        self.assertEqual(len(occurrences), 4)

        # Verificar que todas son lunes o miércoles
        for occurrence in occurrences:
            weekday = occurrence['date'].weekday()  # 0=lunes, 2=miércoles
            self.assertIn(weekday, [0, 2])

        print(f"Test pasado: {len(occurrences)} ocurrencias semanales generadas")

    def test_create_task_programs_from_schedule(self):
        """Test crear TaskPrograms desde una programación"""
        print("\n=== Test: Crear TaskPrograms desde programación ===")

        schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='daily',
            start_time=time(8, 0),
            duration=timedelta(hours=1),
            start_date=self.start_date,
            end_date=self.start_date + timedelta(days=2),  # 3 días
            is_active=True
        )

        # Crear programas desde las ocurrencias
        created_programs = schedule.create_task_programs()

        # Debería crear 3 programas
        self.assertEqual(len(created_programs), 3)

        # Verificar que los programas se crearon correctamente
        for program in created_programs:
            self.assertEqual(program.task, self.task)
            self.assertEqual(program.host, self.user)
            self.assertEqual(program.start_time.time(), time(8, 0))
            self.assertEqual(program.end_time.time(), time(9, 0))

        # Verificar que están en la base de datos
        total_programs = TaskProgram.objects.filter(task=self.task).count()
        self.assertEqual(total_programs, 3)

        print(f"Test pasado: {len(created_programs)} TaskPrograms creados")

    def test_schedule_is_active(self):
        """Test verificar si una programación está activa"""
        print("\n=== Test: Verificar si programación está activa ===")

        # Programación activa
        active_schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='daily',
            start_time=time(9, 0),
            duration=timedelta(hours=1),
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True
        )

        self.assertTrue(active_schedule.is_active_schedule())

        # Programación inactiva
        inactive_schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='daily',
            start_time=time(9, 0),
            duration=timedelta(hours=1),
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=False
        )

        self.assertFalse(inactive_schedule.is_active_schedule())

        # Programación expirada
        expired_schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='daily',
            start_time=time(9, 0),
            duration=timedelta(hours=1),
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=1),  # Ya expiró
            is_active=True
        )

        self.assertFalse(expired_schedule.is_active_schedule())

        print("Test pasado: Estados de actividad verificados correctamente")

    def test_get_next_occurrence(self):
        """Test obtener la próxima ocurrencia"""
        print("\n=== Test: Obtener próxima ocurrencia ===")

        schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='daily',
            start_time=time(12, 0),
            duration=timedelta(hours=1),
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True
        )

        next_occurrence = schedule.get_next_occurrence()

        self.assertIsNotNone(next_occurrence)
        self.assertEqual(next_occurrence['date'], self.start_date)
        self.assertEqual(next_occurrence['start_time'].time(), time(12, 0))
        self.assertEqual(next_occurrence['end_time'].time(), time(13, 0))

        print("Test pasado: Próxima ocurrencia obtenida correctamente")

    def test_get_selected_days_display(self):
        """Test obtener representación de días seleccionados"""
        print("\n=== Test: Representación de días seleccionados ===")

        # Sin días seleccionados
        schedule_no_days = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='weekly',
            start_time=time(9, 0),
            duration=timedelta(hours=1),
            start_date=self.start_date,
            is_active=True
        )

        self.assertEqual(schedule_no_days.get_selected_days_display(), "Ningún día seleccionado")

        # Con días seleccionados
        schedule_with_days = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='weekly',
            monday=True,
            wednesday=True,
            friday=True,
            start_time=time(9, 0),
            duration=timedelta(hours=1),
            start_date=self.start_date,
            is_active=True
        )

        display = schedule_with_days.get_selected_days_display()
        self.assertIn("Lun", display)
        self.assertIn("Mié", display)
        self.assertIn("Vie", display)

        print("Test pasado: Representación de días correcta")

    def test_schedule_str_representation(self):
        """Test representación string de la programación"""
        print("\n=== Test: Representación string ===")

        schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='weekly',
            start_time=time(16, 45),
            duration=timedelta(hours=1),
            start_date=self.start_date,
            is_active=True
        )

        str_repr = str(schedule)
        self.assertIn(self.task.title, str_repr)
        self.assertIn("Semanal", str_repr)
        self.assertIn("16:45", str_repr)

        print("Test pasado: Representación string correcta")


class TestTaskScheduleViews(TestCase):
    """Tests para las vistas de creación y edición de programaciones"""

    def setUp(self):
        """Configurar datos de prueba para vistas"""
        from django.test import override_settings

        # Usar configuración de test más simple
        self.client = Client()

        # Crear usuarios
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='testpass123'
        )
        # Asignar perfil de admin
        try:
            from core.models import UserProfile
            UserProfile.objects.create(user=self.admin_user, role='SU')
        except:
            # Si no existe el modelo UserProfile, crear atributo directamente
            self.admin_user.profile = type('Profile', (), {'role': 'SU'})()

        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        # Crear estados necesarios
        self.task_status = TaskStatus.objects.create(status_name='To Do')
        self.event_status = Status.objects.create(status_name='Created')

        # Crear tarea para el usuario
        self.task = Task.objects.create(
            title='Tarea para testing vistas',
            description='Descripción de prueba',
            host=self.user,
            assigned_to=self.user,
            task_status=self.task_status,
            ticket_price=0.0
        )

        # Crear tarea para otro usuario
        self.other_task = Task.objects.create(
            title='Tarea de otro usuario',
            description='Descripción de prueba',
            host=self.other_user,
            assigned_to=self.other_user,
            task_status=self.task_status,
            ticket_price=0.0
        )

        # Fechas de prueba
        self.start_date = date.today() + timedelta(days=1)
        self.end_date = self.start_date + timedelta(days=30)

        # Crear una programación existente para tests de edición
        self.existing_schedule = TaskSchedule.objects.create(
            task=self.task,
            host=self.user,
            recurrence_type='weekly',
            monday=True,
            wednesday=True,
            friday=True,
            start_time=time(9, 0),
            duration=timedelta(hours=1),
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True
        )

    def test_create_task_schedule_view_get(self):
        """Test vista GET de creación de programación"""
        print("\n=== Test Vista: GET Crear Programación ===")

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_task_schedule'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/create_task_schedule.html')
        self.assertContains(response, 'Crear Programación Recurrente')

        print("Test pasado: Vista GET de creación funciona correctamente")

    def test_create_task_schedule_view_post_success(self):
        """Test vista POST exitosa de creación de programación"""
        print("\n=== Test Vista: POST Crear Programación (Éxito) ===")

        self.client.login(username='testuser', password='testpass123')

        # Datos válidos para el formulario
        data = {
            'task': self.task.id,
            'recurrence_type': 'weekly',
            'monday': True,
            'wednesday': True,
            'start_time': '10:30',
            'duration_hours': '1.5',
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'is_active': True
        }

        response = self.client.post(reverse('create_task_schedule'), data)

        # Debería redirigir al detalle de la programación creada
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/events/tasks/schedules/'))

        # Verificar que se creó la programación
        schedule = TaskSchedule.objects.filter(task=self.task, host=self.user).latest('created_at')
        self.assertEqual(schedule.recurrence_type, 'weekly')
        self.assertEqual(schedule.start_time, time(10, 30))
        self.assertEqual(schedule.duration, timedelta(hours=1.5))
        self.assertTrue(schedule.monday)
        self.assertTrue(schedule.wednesday)
        self.assertFalse(schedule.tuesday)  # No seleccionado

        print("Test pasado: Programación creada exitosamente via POST")

    def test_create_task_schedule_view_post_validation_error(self):
        """Test vista POST con errores de validación"""
        print("\n=== Test Vista: POST Crear Programación (Error Validación) ===")

        self.client.login(username='testuser', password='testpass123')

        # Datos inválidos (fecha fin anterior a fecha inicio)
        data = {
            'task': self.task.id,
            'recurrence_type': 'weekly',
            'start_time': '10:30',
            'duration_hours': '1.0',
            'start_date': self.end_date.strftime('%Y-%m-%d'),  # Fecha futura
            'end_date': self.start_date.strftime('%Y-%m-%d'),  # Fecha anterior
            'is_active': True
        }

        response = self.client.post(reverse('create_task_schedule'), data)

        # Debería volver al formulario con errores
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/create_task_schedule.html')
        self.assertContains(response, 'La fecha de fin debe ser posterior a la fecha de inicio')

        # Verificar que no se creó ninguna programación
        schedules_count = TaskSchedule.objects.filter(task=self.task).count()
        self.assertEqual(schedules_count, 1)  # Solo la existente del setUp

        print("Test pasado: Validación de fechas funciona correctamente")

    def test_create_task_schedule_view_post_weekly_no_days(self):
        """Test vista POST semanal sin días seleccionados"""
        print("\n=== Test Vista: POST Crear Programación Semanal Sin Días ===")

        self.client.login(username='testuser', password='testpass123')

        # Datos inválidos (recurrencia semanal sin días)
        data = {
            'task': self.task.id,
            'recurrence_type': 'weekly',
            'start_time': '10:30',
            'duration_hours': '1.0',
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'is_active': True
            # Ningún día seleccionado
        }

        response = self.client.post(reverse('create_task_schedule'), data)

        # Debería volver al formulario con errores
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/create_task_schedule.html')
        self.assertContains(response, 'Debes seleccionar al menos un día de la semana')

        print("Test pasado: Validación de días semanales funciona correctamente")

    def test_create_task_schedule_view_unauthenticated(self):
        """Test vista de creación sin autenticación"""
        print("\n=== Test Vista: Crear Programación Sin Autenticación ===")

        response = self.client.get(reverse('create_task_schedule'))

        # Debería redirigir al login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

        print("Test pasado: Redirección correcta para usuario no autenticado")

    def test_edit_task_schedule_view_get(self):
        """Test vista GET de edición de programación"""
        print("\n=== Test Vista: GET Editar Programación ===")

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('edit_task_schedule', kwargs={'schedule_id': self.existing_schedule.id}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/edit_task_schedule.html')
        self.assertContains(response, 'Editar Programación')

        print("Test pasado: Vista GET de edición funciona correctamente")

    def test_edit_task_schedule_view_post_success(self):
        """Test vista POST exitosa de edición de programación"""
        print("\n=== Test Vista: POST Editar Programación (Éxito) ===")

        self.client.login(username='testuser', password='testpass123')

        # Datos actualizados
        data = {
            'task': self.task.id,
            'recurrence_type': 'daily',  # Cambiar a diaria
            'start_time': '14:00',  # Cambiar hora
            'duration_hours': '2.0',  # Cambiar duración
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'is_active': False  # Desactivar
        }

        response = self.client.post(reverse('edit_task_schedule', kwargs={'schedule_id': self.existing_schedule.id}), data)

        # Debería redirigir al detalle
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/events/tasks/schedules/'))

        # Verificar cambios
        self.existing_schedule.refresh_from_db()
        self.assertEqual(self.existing_schedule.recurrence_type, 'daily')
        self.assertEqual(self.existing_schedule.start_time, time(14, 0))
        self.assertEqual(self.existing_schedule.duration, timedelta(hours=2))
        self.assertFalse(self.existing_schedule.is_active)

        print("Test pasado: Programación editada exitosamente")

    def test_edit_task_schedule_view_permission_denied(self):
        """Test vista de edición con usuario incorrecto"""
        print("\n=== Test Vista: Editar Programación Sin Permisos ===")

        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(reverse('edit_task_schedule', kwargs={'schedule_id': self.existing_schedule.id}))

        # Debería ser 404 o redirección (dependiendo de la implementación)
        self.assertIn(response.status_code, [404, 302])

        print("Test pasado: Acceso denegado correctamente para usuario sin permisos")

    def test_edit_task_schedule_view_not_found(self):
        """Test vista de edición con ID inexistente"""
        print("\n=== Test Vista: Editar Programación Inexistente ===")

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('edit_task_schedule', kwargs={'schedule_id': 99999}))

        self.assertEqual(response.status_code, 404)

        print("Test pasado: Error 404 correcto para programación inexistente")

    def test_task_schedule_detail_view(self):
        """Test vista de detalle de programación"""
        print("\n=== Test Vista: Detalle de Programación ===")

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_schedule_detail', kwargs={'schedule_id': self.existing_schedule.id}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/task_schedule_detail.html')
        self.assertContains(response, self.task.title)
        self.assertContains(response, 'Programación:')

        print("Test pasado: Vista de detalle funciona correctamente")

    def test_task_schedules_list_view(self):
        """Test vista de lista de programaciones del usuario"""
        print("\n=== Test Vista: Lista de Programaciones ===")

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_schedules'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/task_schedules.html')
        self.assertContains(response, 'Programaciones Recurrentes')

        print("Test pasado: Vista de lista funciona correctamente")

    def test_task_schedule_form_validation(self):
        """Test validación del formulario TaskScheduleForm"""
        print("\n=== Test Formulario: Validación TaskScheduleForm ===")

        from ..forms import TaskScheduleForm

        # Test formulario válido
        form_data = {
            'task': self.task.id,
            'recurrence_type': 'weekly',
            'monday': True,
            'wednesday': True,
            'start_time': '10:30',
            'duration_hours': '1.5',
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'is_active': True
        }

        form = TaskScheduleForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid(), f"Formulario debería ser válido. Errores: {form.errors}")

        # Test validación de fechas (fin antes de inicio)
        invalid_form_data = form_data.copy()
        invalid_form_data['end_date'] = (self.start_date - timedelta(days=1)).strftime('%Y-%m-%d')

        invalid_form = TaskScheduleForm(data=invalid_form_data, user=self.user)
        self.assertFalse(invalid_form.is_valid())
        self.assertIn('La fecha de fin debe ser posterior a la fecha de inicio.', str(invalid_form.errors))

        # Test validación semanal sin días
        weekly_no_days_data = form_data.copy()
        weekly_no_days_data['monday'] = False
        weekly_no_days_data['wednesday'] = False

        weekly_form = TaskScheduleForm(data=weekly_no_days_data, user=self.user)
        self.assertFalse(weekly_form.is_valid())
        self.assertIn('Debes seleccionar al menos un día de la semana', str(weekly_form.errors))

        print("Test pasado: Validación del formulario funciona correctamente")

    def test_task_schedule_form_save(self):
        """Test guardar formulario TaskScheduleForm"""
        print("\n=== Test Formulario: Guardar TaskScheduleForm ===")

        from ..forms import TaskScheduleForm

        form_data = {
            'task': self.task.id,
            'recurrence_type': 'daily',
            'start_time': '08:00',
            'duration_hours': '2.0',
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'is_active': True
        }

        form = TaskScheduleForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

        # Guardar el formulario
        schedule = form.save()
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.task, self.task)
        self.assertEqual(schedule.host, self.user)
        self.assertEqual(schedule.recurrence_type, 'daily')
        self.assertEqual(schedule.start_time, time(8, 0))
        self.assertEqual(schedule.duration, timedelta(hours=2))

        print("Test pasado: Guardado del formulario funciona correctamente")

    def test_schedule_admin_dashboard_permission(self):
        """Test permisos del panel administrativo"""
        print("\n=== Test Panel Admin: Permisos ===")

        # Usuario normal no debería acceder
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('schedule_admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirección por falta de permisos

        # Usuario admin debería acceder
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.get(reverse('schedule_admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel de Administración')

        print("Test pasado: Permisos del panel administrativo funcionan correctamente")