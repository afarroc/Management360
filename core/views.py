# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry

# Import models from other apps
from events.models import Event, Project, Task, Status, ProjectStatus, TaskStatus

@login_required
def home_view(request, days=None, days_ago=None):
    """
    Enhanced home view with comprehensive dashboard data and intelligent alerts.

    Args:
        request: HttpRequest object
        days: Optional number of days to look back for statistics
        days_ago: Optional number of days ago to start the range

    Returns:
        Rendered home template with comprehensive context data
    """

    # Default time range (last 30 days)
    if days is None:
        days = 30

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    if days_ago:
        # Custom range: from days_ago days ago to (days_ago - days) days ago
        start_date = end_date - timedelta(days=days_ago)
        end_date = start_date + timedelta(days=days)

    # Basic statistics
    total_events = Event.objects.count()
    total_projects = Project.objects.count()
    total_tasks = Task.objects.count()

    # Time-filtered statistics
    events_in_period = Event.objects.filter(created_at__range=(start_date, end_date)).count()
    projects_in_period = Project.objects.filter(created_at__range=(start_date, end_date)).count()
    tasks_in_period = Task.objects.filter(created_at__range=(start_date, end_date)).count()

    # Status-based counts
    try:
        completed_status = Status.objects.get(status_name='Completed')
        in_progress_status = Status.objects.get(status_name='In Progress')
        created_status = Status.objects.get(status_name='Created')

        completed_events = Event.objects.filter(event_status=completed_status).count()
        in_progress_events = Event.objects.filter(event_status=in_progress_status).count()
        created_events = Event.objects.filter(event_status=created_status).count()
    except Status.DoesNotExist:
        completed_events = in_progress_events = created_events = 0

    try:
        completed_project_status = ProjectStatus.objects.get(status_name='Completed')
        in_progress_project_status = ProjectStatus.objects.get(status_name='In Progress')

        completed_projects = Project.objects.filter(project_status=completed_project_status).count()
        active_projects = Project.objects.filter(project_status=in_progress_project_status).count()
    except ProjectStatus.DoesNotExist:
        completed_projects = active_projects = 0

    try:
        completed_task_status = TaskStatus.objects.get(status_name='Completed')
        in_progress_task_status = TaskStatus.objects.get(status_name='In Progress')
        todo_task_status = TaskStatus.objects.get(status_name='To Do')

        completed_tasks_count = Task.objects.filter(task_status=completed_task_status).count()
        in_progress_tasks = Task.objects.filter(task_status=in_progress_task_status).count()
        pending_tasks = Task.objects.filter(task_status=todo_task_status).count()
    except TaskStatus.DoesNotExist:
        completed_tasks_count = in_progress_tasks = pending_tasks = 0

    # Recent activities (last 10)
    recent_activities = []
    try:
        event_ct = ContentType.objects.get_for_model(Event)
        project_ct = ContentType.objects.get_for_model(Project)
        task_ct = ContentType.objects.get_for_model(Task)

        recent_logs = LogEntry.objects.filter(
            content_type__in=[event_ct, project_ct, task_ct]
        ).select_related('user', 'content_type').order_by('-action_time')[:10]

        for log in recent_logs:
            action_map = {
                1: 'Created',
                2: 'Updated',
                3: 'Deleted'
            }
            recent_activities.append({
                'content_type': log.content_type.model,
                'action': action_map.get(log.action_flag, 'Modified'),
                'user': log.user,
                'timestamp': log.action_time,
                'object_repr': log.object_repr,
                'get_badge_color': 'success' if log.action_flag == 1 else 'primary'
            })
    except:
        recent_activities = []

    # Upcoming events (next 5)
    upcoming_events = Event.objects.filter(
        created_at__gte=timezone.now()
    ).order_by('created_at')[:5]

    # Recent projects (last 5 updated)
    recent_projects_list = Project.objects.select_related(
        'project_status', 'host', 'assigned_to'
    ).order_by('-updated_at')[:5]

    # Recent tasks (last 5 updated)
    recent_tasks = Task.objects.select_related(
        'task_status', 'project', 'assigned_to'
    ).order_by('-updated_at')[:5]

    # User profile completion (simplified without custom UserProfile model)
    profile_completion = 50  # Default completion percentage

    # Generate intelligent alerts
    alerts = generate_home_alerts(request.user, {
        'total_events': total_events,
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'active_projects': active_projects,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'upcoming_events': upcoming_events.count(),
        'recent_activities': len(recent_activities)
    })

    # Event categories for filtering
    event_categories = Event.objects.values('event_category').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Project categories
    project_categories = []
    try:
        from events.models import Classification
        project_categories = Classification.objects.all()[:10]
    except:
        project_categories = []

    context = {
        'page_title': 'Management360 Dashboard',
        'days': days,
        'days_ago': days_ago,
        'start_date': start_date,
        'end_date': end_date,

        # Statistics
        'total_events': total_events,
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'events_in_period': events_in_period,
        'projects_in_period': projects_in_period,
        'tasks_in_period': tasks_in_period,

        # Status counts
        'completed_events': completed_events,
        'in_progress_events': in_progress_events,
        'created_events': created_events,
        'completed_projects': completed_projects,
        'active_projects': active_projects,
        'completed_tasks_count': completed_tasks_count,
        'in_progress_tasks': in_progress_tasks,
        'pending_tasks': pending_tasks,

        # Recent data
        'recent_activities': recent_activities,
        'upcoming_events': upcoming_events,
        'upcoming_events_count': upcoming_events.count(),
        'recent_projects_list': recent_projects_list,
        'recent_tasks': recent_tasks,

        # User data
        'profile_completion': profile_completion,

        # Categories
        'event_categories': event_categories,
        'project_categories': project_categories,

        # Intelligent alerts
        'alerts': alerts,

        # Time range info
        'time_range_text': f"Last {days} days" if not days_ago else f"{days} days from {days_ago} days ago"
    }

    return render(request, 'home/home.html', context)


def generate_home_alerts(user, stats):
    """
    Generate intelligent alerts for the home dashboard.

    Args:
        user: User object
        stats: Dictionary with dashboard statistics

    Returns:
        List of alert dictionaries
    """
    alerts = []

    # Welcome alert for new users
    if stats['total_events'] == 0 and stats['total_projects'] == 0:
        alerts.append({
            'type': 'info',
            'icon': 'bi-info-circle',
            'title': 'Welcome to Management360!',
            'message': 'Get started by creating your first event or project.',
            'action_url': '/events/events/create/',
            'action_text': 'Create Event'
        })

    # High activity alert
    if stats['recent_activities'] > 5:
        alerts.append({
            'type': 'success',
            'icon': 'bi-graph-up',
            'title': 'High Activity Detected',
            'message': f'You have {stats["recent_activities"]} recent activities. Keep up the great work!',
            'action_url': '/events/management/',
            'action_text': 'View Management'
        })

    # Upcoming events alert
    if stats['upcoming_events'] > 0:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-calendar-event',
            'title': 'Upcoming Events',
            'message': f'You have {stats["upcoming_events"]} upcoming event(s) scheduled.',
            'action_url': '/events/events/',
            'action_text': 'View Events'
        })

    # Task backlog alert
    if stats['pending_tasks'] > 10:
        alerts.append({
            'type': 'danger',
            'icon': 'bi-exclamation-triangle',
            'title': 'Task Backlog',
            'message': f'You have {stats["pending_tasks"]} pending tasks. Consider prioritizing them.',
            'action_url': '/events/tasks/',
            'action_text': 'Manage Tasks'
        })

    # Project completion alert
    if stats['active_projects'] > 0 and stats['pending_tasks'] == 0:
        alerts.append({
            'type': 'success',
            'icon': 'bi-trophy',
            'title': 'Great Progress!',
            'message': f'You have {stats["active_projects"]} active projects with no pending tasks.',
            'action_url': '/events/projects/',
            'action_text': 'View Projects'
        })

    # Low activity alert
    if stats['recent_activities'] == 0 and (stats['total_events'] > 0 or stats['total_projects'] > 0):
        alerts.append({
            'type': 'warning',
            'icon': 'bi-clock',
            'title': 'Low Recent Activity',
            'message': 'Consider updating your events or projects to keep them current.',
            'action_url': '/events/management/',
            'action_text': 'Update Items'
        })

    return alerts

def about_view(request):
    context = {
        'page_title': 'About Us'
    }
    return render(request, 'about/about.html', context)
    
def contact_view(request):
    context = {
        'page_title': 'Contact'
    }
    return render(request, 'contact/contact.html', context)

def faq_view(request):
    context = {
        'page_title': 'F.A.Q.'
    }
    return render(request, 'faq/faq.html', context)

def blank_view(request):
    context = {
        'page_title': 'Blank Page',
        'message': 'This is a blank page. You can add your own content here.'
    }
    return render(request, 'blank/blank.html', context)

from django.db.models import Q
from .models import Article
from events.models import Event, Project, Task

def search_view(request):
    query = request.GET.get('query', '').strip()
    results = {
        'articles': Article.objects.none(),
        'events': Event.objects.none(),
        'projects': Project.objects.none(),
        'tasks': Task.objects.none()
    }
    
    if query:
        # Búsqueda en Artículos
        results['articles'] = Article.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(excerpt__icontains=query)
        ).order_by('-publication_date')
        
        # Búsqueda en Eventos
        results['events'] = Event.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(venue__icontains=query) |
            Q(event_category__icontains=query)
        ).select_related('event_status').order_by('-created_at')
        
        # Búsqueda en Proyectos
        results['projects'] = Project.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).select_related('project_status').order_by('-created_at')
        
        # Búsqueda en Tareas
        results['tasks'] = Task.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).select_related('task_status').order_by('-created_at')
    
    total_results = sum(results[c].count() for c in results.keys())
    
    context = {
        'page_title': 'Search Results',
        'query': query,
        'results': results,
        'total_results': total_results,
        'has_results': total_results > 0
    }
    return render(request, 'search/search.html', context)


# Standard library imports
import os
import re
import ast
from pathlib import Path

# Django imports
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_GET
from django.shortcuts import render


@require_GET
def url_map_view(request):
    """
    View to generate a URL map structure for all apps in the project.

    Args:
        request: HttpRequest object with optional 'app_name' GET parameter

    Returns:
        JsonResponse with either:
        - List of all apps with their URLs (if no app_name provided)
        - URL structure for specified app
        - Error message if app doesn't exist
    """
    app_name = request.GET.get("app_name", "")

    if not app_name:
        # List all apps with their URL structures
        apps_data = get_all_apps_url_structure()
        return JsonResponse(apps_data, safe=False)

    # Get URL structure for specific app
    app_urls = get_app_url_structure(app_name)
    if app_urls is None:
        return JsonResponse(
            {"error": f"The app '{app_name}' does not exist or has no URLs configured."},
            status=400
        )

    return JsonResponse(app_urls, safe=False)


def get_all_apps_url_structure():
    """
    Get URL structure for all apps in the project.

    Returns:
        List of dictionaries with app information and URL structures
    """
    apps_data = []

    # Get all Django apps from INSTALLED_APPS
    from django.conf import settings
    installed_apps = getattr(settings, 'INSTALLED_APPS', [])

    # Filter local apps (exclude Django core and third-party apps)
    local_apps = []
    for app in installed_apps:
        if not app.startswith('django.') and '.' in app:
            app_name = app.split('.')[-2]  # Get app name from 'app.apps.AppConfig'
            local_apps.append(app_name)

    # Also check for apps in the project directory
    project_dir = Path(settings.BASE_DIR)
    for item in project_dir.iterdir():
        if item.is_dir() and not item.name.startswith('__') and item.name not in ['static', 'media', 'templates']:
            if item.name not in local_apps:
                local_apps.append(item.name)

    for app_name in sorted(local_apps):
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
    """
    Get URL structure for a specific app.

    Args:
        app_name: Name of the Django app

    Returns:
        Dictionary with app URL information or None if not found
    """
    urls_file = Path(settings.BASE_DIR) / app_name / 'urls.py'

    if not urls_file.exists():
        return None

    try:
        # Read and parse the urls.py file
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract urlpatterns
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
    """
    Parse Django urlpatterns from Python code.

    Args:
        content: String content of urls.py file
        app_name: Name of the Django app (optional)

    Returns:
        List of parsed URL patterns
    """
    urls = []

    try:
        # Use regex to find path() calls
        path_pattern = r'path\s*\(\s*[\'"](.*?)[\'"]\s*,?\s*([^,]+(?:,.*?)?)\)'
        matches = re.findall(path_pattern, content, re.DOTALL)

        for match in matches:
            url_pattern = match[0]
            view_info = match[1].strip()

            # Clean up the view info
            view_info = re.sub(r'\s+', ' ', view_info)

            # Build full URL pattern including app prefix
            if app_name:
                if url_pattern.startswith('/'):
                    full_pattern = f"/{app_name}{url_pattern}"
                else:
                    full_pattern = f"/{app_name}/{url_pattern}" if url_pattern else f"/{app_name}/"
            else:
                # Fallback for when app_name is not provided
                if url_pattern.startswith('/'):
                    full_pattern = url_pattern
                else:
                    full_pattern = f"/{url_pattern}" if url_pattern else "/"

            urls.append({
                "pattern": url_pattern,
                "view": view_info,
                "type": "path",
                "full_pattern": full_pattern
            })

        # Also look for re_path patterns
        repath_pattern = r're_path\s*\(\s*r?[\'"](.*?)[\'"]\s*,?\s*([^,]+(?:,.*?)?)\)'
        repath_matches = re.findall(repath_pattern, content, re.DOTALL)

        for match in repath_matches:
            url_pattern = match[0]
            view_info = match[1].strip()

            view_info = re.sub(r'\s+', ' ', view_info)

            # For re_path, build full pattern with app prefix
            if app_name:
                if url_pattern.startswith('/'):
                    full_pattern = f"/{app_name}{url_pattern}"
                else:
                    full_pattern = f"/{app_name}/{url_pattern}" if url_pattern else f"/{app_name}/"
            else:
                full_pattern = f"/{url_pattern}" if not url_pattern.startswith('/') else url_pattern

            urls.append({
                "pattern": url_pattern,
                "view": view_info,
                "type": "re_path",
                "full_pattern": full_pattern
            })

    except Exception as e:
        error_pattern = "/error"
        if app_name:
            error_pattern = f"/{app_name}/error"

        urls.append({
            "pattern": "error",
            "view": f"Error parsing: {str(e)}",
            "type": "error",
            "full_pattern": error_pattern
        })

    return urls


def url_map_html_view(request):
    """
    HTML view to display the URL map in a web interface.
    """
    import django
    django_version = django.get_version()

    app_name = request.GET.get("app_name", "")

    if app_name:
        # Show specific app URLs
        app_urls = get_app_url_structure(app_name)
        if app_urls:
            return render(request, 'core/url_map_detail.html', {
                'app_urls': app_urls,
                'app_name': app_name,
                'django_version': django_version
            })
        else:
            return render(request, 'core/url_map_detail.html', {
                'error': f"App '{app_name}' not found or has no URLs",
                'app_name': app_name,
                'django_version': django_version
            })

    # Show all apps
    apps_data = get_all_apps_url_structure()
    return render(request, 'core/url_map.html', {
        'apps_data': apps_data,
        'django_version': django_version
    })
