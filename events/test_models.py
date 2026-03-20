# events/tests/test_models.py
# EV-4 — Tests base: CRUD Project + Task + InboxItem
#
# Ejecutar:
#   python manage.py test events.tests.test_models
#   python manage.py test events.tests.test_models -v 2   # verbose

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from events.models import (
    Project, ProjectStatus, ProjectState, ProjectHistory,
    Task, TaskStatus, TaskState, TaskHistory,
    InboxItem, Event, Status,
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures compartidos
# ─────────────────────────────────────────────────────────────────────────────

class BaseTestCase(TestCase):
    """Crea usuario + statuses base que todos los tests comparten."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        cls.other_user = User.objects.create_user(
            username='otheruser', password='testpass123'
        )
        cls.project_status = ProjectStatus.objects.create(
            status_name='Created', icon='bi-circle', color='secondary'
        )
        cls.project_status_done = ProjectStatus.objects.create(
            status_name='Completed', icon='bi-check-circle', color='success'
        )
        cls.task_status = TaskStatus.objects.create(
            status_name='To Do', icon='bi-circle', color='secondary'
        )
        cls.task_status_done = TaskStatus.objects.create(
            status_name='Completed', icon='bi-check-circle', color='success'
        )
        cls.event_status = Status.objects.create(
            status_name='Active', icon='bi-play', color='primary'
        )


# ─────────────────────────────────────────────────────────────────────────────
# Project
# ─────────────────────────────────────────────────────────────────────────────

class ProjectModelTest(BaseTestCase):

    def _make_project(self, **kwargs):
        defaults = dict(
            title='Proyecto test',
            project_status=self.project_status,
            host=self.user,
            assigned_to=self.user,
        )
        defaults.update(kwargs)
        return Project.objects.create(**defaults)

    # CREATE
    def test_create_project_minimal(self):
        p = self._make_project()
        self.assertEqual(p.title, 'Proyecto test')
        self.assertEqual(p.host, self.user)
        self.assertFalse(p.done)
        self.assertEqual(p.ticket_price, 0)

    def test_project_str(self):
        p = self._make_project()
        self.assertIn('Proyecto test', str(p))

    # READ
    def test_filter_by_host(self):
        self._make_project(title='P1')
        self._make_project(title='P2', host=self.other_user, assigned_to=self.other_user)
        qs = Project.objects.filter(host=self.user)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().title, 'P1')

    # UPDATE
    def test_update_title(self):
        p = self._make_project()
        p.title = 'Proyecto actualizado'
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.title, 'Proyecto actualizado')

    # DELETE
    def test_delete_project(self):
        p = self._make_project()
        pk = p.pk
        p.delete()
        self.assertFalse(Project.objects.filter(pk=pk).exists())

    # change_status
    def test_change_status(self):
        p = self._make_project()
        # Crear estado inicial para que change_status pueda cerrarlo
        ProjectState.objects.create(project=p, status=self.project_status)
        p.change_status(self.project_status_done.id)
        p.refresh_from_db()
        self.assertEqual(p.project_status, self.project_status_done)

    def test_change_status_closes_previous_state(self):
        p = self._make_project()
        initial_state = ProjectState.objects.create(project=p, status=self.project_status)
        p.change_status(self.project_status_done.id)
        initial_state.refresh_from_db()
        self.assertIsNotNone(initial_state.end_time)

    # record_edit
    def test_record_edit_creates_history(self):
        p = self._make_project()
        p.record_edit(self.user, 'title', 'Viejo', 'Nuevo')
        self.assertTrue(
            ProjectHistory.objects.filter(project=p, field_name='title').exists()
        )

    # ProjectState auto-timestamps
    def test_project_state_sets_start_time_on_create(self):
        p = self._make_project()
        state = ProjectState.objects.create(project=p, status=self.project_status)
        self.assertIsNotNone(state.start_time)
        self.assertIsNone(state.end_time)

    def test_project_state_sets_end_time_on_save(self):
        p = self._make_project()
        state = ProjectState.objects.create(project=p, status=self.project_status)
        # Guardar de nuevo simula cierre
        state.save()
        state.refresh_from_db()
        self.assertIsNotNone(state.end_time)


# ─────────────────────────────────────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────────────────────────────────────

class TaskModelTest(BaseTestCase):

    def _make_project(self):
        return Project.objects.create(
            title='Proyecto para tareas',
            project_status=self.project_status,
            host=self.user,
            assigned_to=self.user,
        )

    def _make_task(self, project=None, **kwargs):
        defaults = dict(
            title='Tarea test',
            task_status=self.task_status,
            host=self.user,
            assigned_to=self.user,
            project=project,
        )
        defaults.update(kwargs)
        return Task.objects.create(**defaults)

    # CREATE
    def test_create_task_minimal(self):
        t = self._make_task()
        self.assertEqual(t.title, 'Tarea test')
        self.assertEqual(t.host, self.user)
        self.assertFalse(t.done)
        self.assertFalse(t.important)

    def test_create_task_with_project(self):
        p = self._make_project()
        t = self._make_task(project=p)
        self.assertEqual(t.project, p)

    def test_task_str(self):
        t = self._make_task()
        self.assertIn('Tarea test', str(t))

    # READ
    def test_filter_by_host(self):
        self._make_task(title='T1')
        self._make_task(title='T2', host=self.other_user, assigned_to=self.other_user)
        self.assertEqual(Task.objects.filter(host=self.user).count(), 1)

    def test_filter_important(self):
        self._make_task(important=True)
        self._make_task(important=False)
        self.assertEqual(Task.objects.filter(important=True).count(), 1)

    # UPDATE
    def test_update_task(self):
        t = self._make_task()
        t.done = True
        t.save()
        t.refresh_from_db()
        self.assertTrue(t.done)

    # DELETE
    def test_delete_task(self):
        t = self._make_task()
        pk = t.pk
        t.delete()
        self.assertFalse(Task.objects.filter(pk=pk).exists())

    # change_status
    def test_change_status(self):
        t = self._make_task()
        TaskState.objects.create(task=t, status=self.task_status)
        t.change_status(self.task_status_done.id, user=self.user)
        t.refresh_from_db()
        self.assertEqual(t.task_status, self.task_status_done)

    def test_change_status_creates_history_when_user_provided(self):
        t = self._make_task()
        TaskState.objects.create(task=t, status=self.task_status)
        t.change_status(self.task_status_done.id, user=self.user)
        self.assertTrue(
            TaskHistory.objects.filter(task=t, field_name='task_status').exists()
        )

    def test_change_status_no_history_without_user(self):
        t = self._make_task()
        TaskState.objects.create(task=t, status=self.task_status)
        t.change_status(self.task_status_done.id)
        self.assertFalse(
            TaskHistory.objects.filter(task=t).exists()
        )

    # record_edit
    def test_record_edit_creates_history(self):
        t = self._make_task()
        t.record_edit(self.user, 'title', 'Viejo', 'Nuevo')
        self.assertTrue(
            TaskHistory.objects.filter(task=t, field_name='title').exists()
        )

    # Cascada al eliminar project
    def test_task_deleted_on_project_delete(self):
        p = self._make_project()
        t = self._make_task(project=p)
        pk = t.pk
        p.delete()
        self.assertFalse(Task.objects.filter(pk=pk).exists())


# ─────────────────────────────────────────────────────────────────────────────
# InboxItem
# ─────────────────────────────────────────────────────────────────────────────

class InboxItemModelTest(BaseTestCase):

    def _make_item(self, **kwargs):
        defaults = dict(
            title='Item test',
            description='Descripción test',
            created_by=self.user,
        )
        defaults.update(kwargs)
        return InboxItem.objects.create(**defaults)

    # CREATE
    def test_create_inbox_item_minimal(self):
        item = self._make_item()
        self.assertEqual(item.title, 'Item test')
        self.assertEqual(item.created_by, self.user)
        self.assertFalse(item.is_processed)
        self.assertEqual(item.gtd_category, 'pendiente')
        self.assertEqual(item.priority, 'media')

    def test_inbox_item_str(self):
        item = self._make_item()
        self.assertIn('Item test', str(item))
        self.assertIn('pendiente', str(item))

    # READ
    def test_filter_by_created_by(self):
        self._make_item()
        self._make_item(created_by=self.other_user)
        self.assertEqual(InboxItem.objects.filter(created_by=self.user).count(), 1)

    def test_filter_unprocessed(self):
        self._make_item(is_processed=False)
        self._make_item(is_processed=True)
        self.assertEqual(InboxItem.objects.filter(is_processed=False).count(), 1)

    # UPDATE
    def test_mark_as_processed(self):
        item = self._make_item()
        item.is_processed = True
        item.processed_at = timezone.now()
        item.save()
        item.refresh_from_db()
        self.assertTrue(item.is_processed)
        self.assertIsNotNone(item.processed_at)

    def test_update_gtd_category(self):
        item = self._make_item()
        item.gtd_category = 'accionable'
        item.action_type = 'hacer'
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.gtd_category, 'accionable')
        self.assertEqual(item.action_type, 'hacer')

    # DELETE
    def test_delete_inbox_item(self):
        item = self._make_item()
        pk = item.pk
        item.delete()
        self.assertFalse(InboxItem.objects.filter(pk=pk).exists())

    # increment_views
    def test_increment_views(self):
        item = self._make_item()
        self.assertEqual(item.view_count, 0)
        item.increment_views()
        item.refresh_from_db()
        self.assertEqual(item.view_count, 1)

    def test_increment_views_accumulates(self):
        item = self._make_item()
        item.increment_views()
        item.increment_views()
        item.increment_views()
        item.refresh_from_db()
        self.assertEqual(item.view_count, 3)

    # get_classification_consensus — sin votos devuelve gtd_category del item
    def test_consensus_without_votes_returns_own_category(self):
        item = self._make_item(gtd_category='accionable')
        self.assertEqual(item.get_classification_consensus(), 'accionable')

    # assigned_to
    def test_assign_to_user(self):
        item = self._make_item()
        item.assigned_to = self.other_user
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.assigned_to, self.other_user)

    # Cascada al eliminar usuario creador
    def test_item_deleted_on_user_delete(self):
        temp_user = User.objects.create_user(username='temp', password='pass')
        item = self._make_item(created_by=temp_user)
        pk = item.pk
        temp_user.delete()
        self.assertFalse(InboxItem.objects.filter(pk=pk).exists())
