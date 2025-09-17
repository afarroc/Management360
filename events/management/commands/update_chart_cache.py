"""
Management command to update chart cache in the background.
Run this periodically to keep chart data fresh.
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from events.models import Project, Task, Event


class Command(BaseCommand):
    help = 'Update chart data cache for improved performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of data to cache (default: 30)'
        )

    def handle(self, *args, **options):
        days = options['days']
        self.stdout.write(f'Updating chart cache for last {days} days...')

        try:
            # Calculate start date
            start_date = timezone.now() - timezone.timedelta(days=days)

            # Update project chart data
            self.update_project_chart_data(start_date)

            # Update task chart data
            self.update_task_chart_data(start_date)

            # Update event chart data
            self.update_event_chart_data(start_date)

            # Update combined statistics
            self.update_combined_stats()

            self.stdout.write(
                self.style.SUCCESS('Successfully updated chart cache')
            )

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error updating chart cache: {e}')
            )

    def update_project_chart_data(self, start_date):
        """Update project chart data cache"""
        chart_queryset = Project.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            project_count=Count('id')
        ).order_by('date')

        projects_data = [item['project_count'] for item in chart_queryset]
        project_dates = [
            item['date'].strftime('%Y-%m-%dT%H:%M:%S.000Z')
            for item in chart_queryset
        ]

        cache.set('projects_chart_data', {
            'projects_data': projects_data,
            'project_dates': project_dates,
        }, 3600)  # Cache for 1 hour

    def update_task_chart_data(self, start_date):
        """Update task chart data cache"""
        chart_queryset = Task.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            task_count=Count('id')
        ).order_by('date')

        tasks_data = [item['task_count'] for item in chart_queryset]
        task_dates = [
            item['date'].strftime('%Y-%m-%dT%H:%M:%S.000Z')
            for item in chart_queryset
        ]

        cache.set('tasks_chart_data', {
            'tasks_data': tasks_data,
            'task_dates': task_dates,
        }, 3600)

    def update_event_chart_data(self, start_date):
        """Update event chart data cache"""
        chart_queryset = Event.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            event_count=Count('id')
        ).order_by('date')

        events_data = [item['event_count'] for item in chart_queryset]
        event_dates = [
            item['date'].strftime('%Y-%m-%dT%H:%M:%S.000Z')
            for item in chart_queryset
        ]

        cache.set('events_chart_data', {
            'events_data': events_data,
            'event_dates': event_dates,
        }, 3600)

    def update_combined_stats(self):
        """Update combined statistics cache"""
        stats = {
            'total_projects': Project.objects.count(),
            'total_tasks': Task.objects.count(),
            'total_events': Event.objects.count(),
            'active_projects': Project.objects.filter(
                project_status__status_name='In Progress'
            ).count(),
            'completed_projects': Project.objects.filter(
                project_status__status_name='Completed'
            ).count(),
            'updated_at': timezone.now().isoformat()
        }

        cache.set('combined_stats', stats, 1800)  # Cache for 30 minutes