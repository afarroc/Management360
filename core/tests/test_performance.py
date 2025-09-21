"""
Performance tests for the optimized home_view.

This module contains tests to validate the performance improvements
made to the home dashboard.
"""

import time
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
from django.test.utils import override_settings

from events.models import Event, Project, Task, Status, ProjectStatus, TaskStatus
from events.management.task_manager import TaskManager


class HomeViewPerformanceTest(TestCase):
    """Test performance optimizations for home_view."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test data
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Create statuses
        self.completed_status = Status.objects.create(
            status_name='Completed',
            color='success'
        )
        self.in_progress_status = Status.objects.create(
            status_name='In Progress',
            color='primary'
        )
        self.created_status = Status.objects.create(
            status_name='Created',
            color='info'
        )

        # Create project statuses
        self.project_completed = ProjectStatus.objects.create(
            status_name='Completed',
            color='success'
        )
        self.project_in_progress = ProjectStatus.objects.create(
            status_name='In Progress',
            color='primary'
        )

        # Create task statuses
        self.task_completed = TaskStatus.objects.create(
            status_name='Completed',
            color='success'
        )
        self.task_in_progress = TaskStatus.objects.create(
            status_name='In Progress',
            color='primary'
        )
        self.task_todo = TaskStatus.objects.create(
            status_name='To Do',
            color='secondary'
        )

        # Create test data
        for i in range(50):
            event = Event.objects.create(
                title=f'Test Event {i}',
                description=f'Description {i}',
                event_status=self.in_progress_status if i % 2 == 0 else self.completed_status
            )

            project = Project.objects.create(
                title=f'Test Project {i}',
                description=f'Project description {i}',
                project_status=self.project_in_progress if i % 3 != 0 else self.project_completed,
                host=self.user
            )

            # Usar TaskManager para crear tareas con procedimientos correctos
            task_manager = TaskManager(self.user)
            task_manager.create_task(
                title=f'Test Task {i}',
                description=f'Task description {i}',
                important=False,
                project=project,
                event=event,
                task_status=self.task_todo if i % 4 == 0 else self.task_in_progress,
                assigned_to=self.user,
                ticket_price=0.07
            )

    def test_home_view_response_time(self):
        """Test that home view responds within acceptable time."""
        # Clear cache to test fresh load
        cache.clear()

        start_time = time.time()
        response = self.client.get('/')
        end_time = time.time()

        response_time = end_time - start_time

        # Assert response is successful
        self.assertEqual(response.status_code, 200)

        # Assert response time is reasonable (should be under 2 seconds for optimized view)
        self.assertLess(response_time, 2.0, f"Response time too slow: {response_time} seconds")

        print(f"Home view response time: {response_time:.4f} seconds")

    def test_database_query_count(self):
        """Test that database query count is optimized."""
        # Clear cache
        cache.clear()

        # Reset query count
        connection.queries_log.clear()

        # Make request
        response = self.client.get('/')

        # Count database queries
        query_count = len(connection.queries)

        # Assert query count is reasonable (should be under 20 for optimized view)
        self.assertLess(query_count, 20, f"Too many database queries: {query_count}")

        print(f"Database queries executed: {query_count}")

        # Print query details for analysis
        for i, query in enumerate(connection.queries[-10:]):  # Show last 10 queries
            print(f"Query {i+1}: {query['sql'][:100]}...")

    def test_cache_effectiveness(self):
        """Test that caching reduces response time."""
        # Clear cache
        cache.clear()

        # First request (cache miss)
        start_time = time.time()
        response1 = self.client.get('/')
        first_request_time = time.time() - start_time

        # Second request (cache hit)
        start_time = time.time()
        response2 = self.client.get('/')
        second_request_time = time.time() - start_time

        # Assert both responses are successful
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        # Assert second request is faster (at least 30% improvement)
        improvement_ratio = first_request_time / second_request_time
        self.assertGreater(improvement_ratio, 1.3,
                          f"Cache not effective enough. Ratio: {improvement_ratio}")

        print(f"First request: {first_request_time:.4f}s")
        print(f"Second request: {second_request_time:.4f}s")
        print(f"Performance improvement: {improvement_ratio:.2f}x")

    def test_lazy_loading_endpoints(self):
        """Test lazy loading AJAX endpoints."""
        # Test activities endpoint
        response = self.client.get('/api/activities/more/?offset=0&limit=5')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('activities', data)

        # Test items endpoint
        response = self.client.get('/api/items/projects/more/?offset=0&limit=5')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('items', data)

    def test_performance_metrics_endpoint(self):
        """Test performance metrics endpoint."""
        response = self.client.get('/api/metrics/performance/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('metrics', data)
        self.assertIn('system', data['metrics'])
        self.assertIn('cache', data['metrics'])

    def test_dashboard_stats_endpoint(self):
        """Test dashboard stats endpoint."""
        response = self.client.get('/api/metrics/dashboard/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('stats', data)
        self.assertIn('derived', data['stats'])

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    def test_cache_keys_creation(self):
        """Test that appropriate cache keys are created."""
        # Clear cache
        cache.clear()

        # Make request
        self.client.get('/')

        # Check that expected cache keys exist
        expected_keys = [
            'home_event_categories',
            'home_project_categories'
        ]

        for key in expected_keys:
            self.assertIsNotNone(cache.get(key), f"Cache key '{key}' not found")

    def tearDown(self):
        """Clean up test data."""
        # Clear cache
        cache.clear()

        # Clean up test data
        Event.objects.all().delete()
        Project.objects.all().delete()
        Task.objects.all().delete()
        Status.objects.all().delete()
        ProjectStatus.objects.all().delete()
        TaskStatus.objects.all().delete()


if __name__ == '__main__':
    import unittest
    unittest.main()