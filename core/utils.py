from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from django.core.cache import cache
from django.conf import settings
from pathlib import Path
import re

from events.models import Event, Project, Task, Status, ProjectStatus, TaskStatus


def validate_time_parameters(days, days_ago):
    """Validate time parameters for dashboard."""
    try:
        days = int(days) if days is not None else 30
        if days <= 0 or days > 365:
            days = 30
    except (ValueError, TypeError):
        days = 30
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    if days_ago:
        try:
            days_ago = int(days_ago)
            if days_ago > 0:
                start_date = end_date - timedelta(days=days_ago)
                end_date = start_date + timedelta(days=days)
        except (ValueError, TypeError):
            pass
    
    return days, days_ago, start_date, end_date


def get_cached_basic_stats(start_date, end_date, days, days_ago):
    """Get cached basic statistics."""
    cache_key = f'home_stats_{days}_{days_ago or 0}'
    cached_stats = cache.get(cache_key)
    
    if cached_stats:
        return cached_stats
    
    basic_stats = Event.objects.aggregate(
        total_events=Count('id'),
        events_in_period=Count('id', filter=Q(created_at__range=(start_date, end_date)))
    )
    
    project_stats = Project.objects.aggregate(
        total_projects=Count('id'),
        projects_in_period=Count('id', filter=Q(created_at__range=(start_date, end_date)))
    )
    
    task_stats = Task.objects.aggregate(
        total_tasks=Count('id'),
        tasks_in_period=Count('id', filter=Q(created_at__range=(start_date, end_date)))
    )
    
    stats = {
        'total_events': basic_stats['total_events'],
        'events_in_period': basic_stats['events_in_period'],
        'total_projects': project_stats['total_projects'],
        'projects_in_period': project_stats['projects_in_period'],
        'total_tasks': task_stats['total_tasks'],
        'tasks_in_period': task_stats['tasks_in_period']
    }
    
    cache.set(cache_key, stats, 300)  # 5 minutes
    return stats


def get_cached_status_counts():
    """Get cached status counts."""
    cache_key = 'home_status_counts'
    cached_counts = cache.get(cache_key)
    
    if cached_counts:
        return cached_counts
    
    try:
        # Get status objects
        status_objs = {s.status_name: s for s in Status.objects.filter(
            status_name__in=['Completed', 'In Progress', 'Created']
        )}
        project_status_objs = {s.status_name: s for s in ProjectStatus.objects.filter(
            status_name__in=['Completed', 'In Progress']
        )}
        task_status_objs = {s.status_name: s for s in TaskStatus.objects.filter(
            status_name__in=['Completed', 'In Progress', 'To Do']
        )}
        
        # Get counts
        event_counts = Event.objects.aggregate(
            completed_events=Count('id', filter=Q(event_status=status_objs.get('Completed'))),
            in_progress_events=Count('id', filter=Q(event_status=status_objs.get('In Progress'))),
            created_events=Count('id', filter=Q(event_status=status_objs.get('Created')))
        )
        
        project_counts = Project.objects.aggregate(
            completed_projects=Count('id', filter=Q(project_status=project_status_objs.get('Completed'))),
            active_projects=Count('id', filter=Q(project_status=project_status_objs.get('In Progress')))
        )
        
        task_counts = Task.objects.aggregate(
            completed_tasks_count=Count('id', filter=Q(task_status=task_status_objs.get('Completed'))),
            in_progress_tasks=Count('id', filter=Q(task_status=task_status_objs.get('In Progress'))),
            pending_tasks=Count('id', filter=Q(task_status=task_status_objs.get('To Do')))
        )
        
        counts = {
            'completed_events': event_counts['completed_events'] or 0,
            'in_progress_events': event_counts['in_progress_events'] or 0,
            'created_events': event_counts['created_events'] or 0,
            'completed_projects': project_counts['completed_projects'] or 0,
            'active_projects': project_counts['active_projects'] or 0,
            'completed_tasks_count': task_counts['completed_tasks_count'] or 0,
            'in_progress_tasks': task_counts['in_progress_tasks'] or 0,
            'pending_tasks': task_counts['pending_tasks'] or 0
        }
        
        cache.set(cache_key, counts, 600)  # 10 minutes
        return counts
        
    except Exception:
        return {
            'completed_events': 0, 'in_progress_events': 0, 'created_events': 0,
            'completed_projects': 0, 'active_projects': 0,
            'completed_tasks_count': 0, 'in_progress_tasks': 0, 'pending_tasks': 0
        }


def get_recent_activities():
    """Get recent activities."""
    try:
        content_types = ContentType.objects.get_for_models(Event, Project, Task)
        recent_logs = LogEntry.objects.filter(
            content_type__in=content_types.values()
        ).select_related('user', 'content_type').order_by('-action_time')[:10]
        
        action_map = {1: 'Created', 2: 'Updated', 3: 'Deleted'}
        
        return [{
            'content_type': log.content_type.model,
            'action': action_map.get(log.action_flag, 'Modified'),
            'user': log.user,
            'timestamp': log.action_time,
            'object_repr': log.object_repr,
            'get_badge_color': 'success' if log.action_flag == 1 else 'primary'
        } for log in recent_logs]
    except Exception:
        return []


def get_recent_items():
    """Get recent items."""
    upcoming_events = Event.objects.filter(
        created_at__gte=timezone.now()
    ).select_related('event_status').order_by('created_at')[:5]
    
    recent_projects_list = Project.objects.select_related(
        'project_status', 'host', 'assigned_to'
    ).order_by('-updated_at')[:5]
    
    recent_tasks = Task.objects.select_related(
        'task_status', 'project', 'assigned_to'
    ).order_by('-updated_at')[:5]
    
    return {
        'upcoming_events': upcoming_events,
        'recent_projects_list': recent_projects_list,
        'recent_tasks': recent_tasks
    }


def get_cached_categories():
    """Get cached categories."""
    # Event categories
    event_cache_key = 'home_event_categories'
    event_categories = cache.get(event_cache_key)
    
    if not event_categories:
        event_categories = list(Event.objects.values('event_category').annotate(
            count=Count('id')
        ).order_by('-count')[:10])
        cache.set(event_cache_key, event_categories, 900)
    
    # Project categories
    project_cache_key = 'home_project_categories'
    project_categories = cache.get(project_cache_key)
    
    if project_categories is None:
        try:
            from events.models import Classification
            project_categories = list(Classification.objects.all()[:10])
            cache.set(project_cache_key, project_categories, 1800)
        except:
            project_categories = []
    
    return {
        'event_categories': event_categories,
        'project_categories': project_categories
    }


def generate_home_alerts(user, stats):
    """Generate intelligent alerts for dashboard."""
    alerts = []
    
    # Welcome alert
    if stats['total_events'] == 0 and stats['total_projects'] == 0:
        alerts.append({
            'type': 'info',
            'icon': 'bi-info-circle',
            'title': 'Welcome!',
            'message': 'Create your first event or project.',
            'action_url': '/events/events/create/',
            'action_text': 'Create Event'
        })
    
    # High activity
    if stats['recent_activities'] > 5:
        alerts.append({
            'type': 'success',
            'icon': 'bi-graph-up',
            'title': 'High Activity',
            'message': f'You have {stats["recent_activities"]} recent activities.',
            'action_url': '/events/management/',
            'action_text': 'View Management'
        })
    
    # Upcoming events
    if stats['upcoming_events'] > 0:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-calendar-event',
            'title': 'Upcoming Events',
            'message': f'You have {stats["upcoming_events"]} event(s) scheduled.',
            'action_url': '/events/events/',
            'action_text': 'View Events'
        })
    
    # Task backlog
    if stats['pending_tasks'] > 10:
        alerts.append({
            'type': 'danger',
            'icon': 'bi-exclamation-triangle',
            'title': 'Task Backlog',
            'message': f'You have {stats["pending_tasks"]} pending tasks.',
            'action_url': '/events/tasks/',
            'action_text': 'Manage Tasks'
        })
    
    # Low activity
    if stats['recent_activities'] == 0 and (stats['total_events'] > 0 or stats['total_projects'] > 0):
        alerts.append({
            'type': 'warning',
            'icon': 'bi-clock',
            'title': 'Low Recent Activity',
            'message': 'Consider updating your events or projects.',
            'action_url': '/events/management/',
            'action_text': 'Update Items'
        })
    
    return alerts


def get_all_apps_url_structure():
    """Get URL structure for all apps."""
    apps_data = []
    
    for app_name in _get_local_apps():
        app_urls = get_app_url_structure(app_name)
        if app_urls:
            apps_data.append({
                "name": app_name,
                "type": "app",
                "url_count": len(app_urls.get('urls', [])),
                "urls": app_urls
            })
    
    return apps_data


def get_app_url_structure(app_name):
    """Get URL structure for specific app."""
    urls_file = Path(settings.BASE_DIR) / app_name / 'urls.py'
    
    if not urls_file.exists():
        return None
    
    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        urlpatterns = parse_urlpatterns(content, app_name)
        
        return {
            "app_name": app_name,
            "urls_file": str(urls_file.relative_to(settings.BASE_DIR)),
            "urls": urlpatterns
        }
    except Exception as e:
        return {
            "app_name": app_name,
            "error": f"Error parsing URLs: {str(e)}",
            "urls": []
        }


def parse_urlpatterns(content, app_name=None):
    """Parse Django urlpatterns from Python code."""
    urls = []
    
    # Find path() calls
    path_pattern = r'path\s*\(\s*[\'"](.*?)[\'"]\s*,?\s*([^,]+(?:,.*?)?)\)'
    for match in re.findall(path_pattern, content, re.DOTALL):
        url_pattern = match[0]
        view_info = match[1].strip()
        view_info = re.sub(r'\s+', ' ', view_info)
        
        full_pattern = _build_full_pattern(url_pattern, app_name)
        
        urls.append({
            "pattern": url_pattern,
            "view": view_info,
            "type": "path",
            "full_pattern": full_pattern
        })
    
    # Find re_path() calls
    repath_pattern = r're_path\s*\(\s*r?[\'"](.*?)[\'"]\s*,?\s*([^,]+(?:,.*?)?)\)'
    for match in re.findall(repath_pattern, content, re.DOTALL):
        url_pattern = match[0]
        view_info = match[1].strip()
        view_info = re.sub(r'\s+', ' ', view_info)
        
        full_pattern = _build_full_pattern(url_pattern, app_name)
        
        urls.append({
            "pattern": url_pattern,
            "view": view_info,
            "type": "re_path",
            "full_pattern": full_pattern
        })
    
    return urls


def _build_full_pattern(url_pattern, app_name):
    """Build full URL pattern with app prefix."""
    if not app_name:
        return f"/{url_pattern}" if not url_pattern.startswith('/') else url_pattern
    
    if url_pattern.startswith('/'):
        return f"/{app_name}{url_pattern}"
    return f"/{app_name}/{url_pattern}" if url_pattern else f"/{app_name}/"


def _get_local_apps():
    """Get list of local Django apps."""
    from django.conf import settings
    
    local_apps = set()
    
    # From INSTALLED_APPS
    for app in settings.INSTALLED_APPS:
        if not app.startswith('django.') and '.' in app:
            app_name = app.split('.')[-2]
            local_apps.add(app_name)
    
    # From project directory
    project_dir = Path(settings.BASE_DIR)
    for item in project_dir.iterdir():
        if item.is_dir() and not item.name.startswith('__'):
            if item.name not in ['static', 'media', 'templates', '__pycache__']:
                local_apps.add(item.name)
    
    return sorted(local_apps)