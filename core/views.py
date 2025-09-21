# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from django.core.cache import cache
from django.conf import settings
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
import time
import logging
import psutil
from functools import wraps

# Configure logging for performance metrics
logger = logging.getLogger('performance')

def performance_monitor(func):
    """
    Decorator to monitor function performance.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time
        logger.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")

        return result
    return wrapper

# Import models from other apps
from events.models import Event, Project, Task, Status, ProjectStatus, TaskStatus


def validate_time_parameters(days, days_ago):
    """
    Validate and sanitize time-related parameters for dashboard.

    Args:
        days: Number of days to look back
        days_ago: Number of days ago to start the range

    Returns:
        tuple: (validated_days, validated_days_ago, start_date, end_date)
    """
    try:
        days = int(days) if days is not None else 30
        if days <= 0 or days > 365:
            days = 30  # Fallback to safe default
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
            pass  # Use default range if invalid

    return days, days_ago, start_date, end_date


def get_cached_basic_stats(start_date, end_date, days, days_ago):
    """
    Get cached basic statistics for events, projects, and tasks.

    Args:
        start_date: Start of the time range
        end_date: End of the time range
        days: Number of days parameter
        days_ago: Days ago parameter

    Returns:
        dict: Dictionary with total counts and period counts
    """
    cache_key = f'home_stats_{days}_{days_ago or 0}'
    cached_stats = cache.get(cache_key)

    if cached_stats:
        return cached_stats

    # Calculate fresh statistics
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

    # Cache for 5 minutes
    cache.set(cache_key, stats, 300)
    return stats


def get_cached_status_counts():
    """
    Get cached status counts for all models.

    Returns:
        dict: Dictionary with all status counts
    """
    cache_key = 'home_status_counts'
    cached_counts = cache.get(cache_key)

    if cached_counts:
        return cached_counts

    try:
        # Get all status objects in one query
        status_objects = {s.status_name: s for s in Status.objects.filter(
            status_name__in=['Completed', 'In Progress', 'Created']
        )}
        project_status_objects = {s.status_name: s for s in ProjectStatus.objects.filter(
            status_name__in=['Completed', 'In Progress']
        )}
        task_status_objects = {s.status_name: s for s in TaskStatus.objects.filter(
            status_name__in=['Completed', 'In Progress', 'To Do']
        )}

        # Event status counts
        event_status_stats = Event.objects.aggregate(
            completed_events=Count('id', filter=Q(event_status=status_objects.get('Completed'))),
            in_progress_events=Count('id', filter=Q(event_status=status_objects.get('In Progress'))),
            created_events=Count('id', filter=Q(event_status=status_objects.get('Created')))
        )

        # Project status counts
        project_status_stats = Project.objects.aggregate(
            completed_projects=Count('id', filter=Q(project_status=project_status_objects.get('Completed'))),
            active_projects=Count('id', filter=Q(project_status=project_status_objects.get('In Progress')))
        )

        # Task status counts
        task_status_stats = Task.objects.aggregate(
            completed_tasks_count=Count('id', filter=Q(task_status=task_status_objects.get('Completed'))),
            in_progress_tasks=Count('id', filter=Q(task_status=task_status_objects.get('In Progress'))),
            pending_tasks=Count('id', filter=Q(task_status=task_status_objects.get('To Do')))
        )

        counts = {
            'completed_events': event_status_stats['completed_events'] or 0,
            'in_progress_events': event_status_stats['in_progress_events'] or 0,
            'created_events': event_status_stats['created_events'] or 0,
            'completed_projects': project_status_stats['completed_projects'] or 0,
            'active_projects': project_status_stats['active_projects'] or 0,
            'completed_tasks_count': task_status_stats['completed_tasks_count'] or 0,
            'in_progress_tasks': task_status_stats['in_progress_tasks'] or 0,
            'pending_tasks': task_status_stats['pending_tasks'] or 0
        }

        # Cache for 10 minutes
        cache.set(cache_key, counts, 600)
        return counts

    except (Status.DoesNotExist, KeyError, AttributeError):
        return {
            'completed_events': 0, 'in_progress_events': 0, 'created_events': 0,
            'completed_projects': 0, 'active_projects': 0,
            'completed_tasks_count': 0, 'in_progress_tasks': 0, 'pending_tasks': 0
        }


def get_recent_activities():
    """
    Get recent activities from LogEntry with optimized queries.

    Returns:
        list: List of recent activity dictionaries
    """
    recent_activities = []
    try:
        # Cache ContentType lookups
        content_types = ContentType.objects.get_for_models(Event, Project, Task)
        event_ct = content_types[Event]
        project_ct = content_types[Project]
        task_ct = content_types[Task]

        recent_logs = LogEntry.objects.filter(
            content_type__in=[event_ct, project_ct, task_ct]
        ).select_related('user', 'content_type').order_by('-action_time')[:10]

        # Pre-compute action map for efficiency
        action_map = {1: 'Created', 2: 'Updated', 3: 'Deleted'}

        for log in recent_logs:
            recent_activities.append({
                'content_type': log.content_type.model,
                'action': action_map.get(log.action_flag, 'Modified'),
                'user': log.user,
                'timestamp': log.action_time,
                'object_repr': log.object_repr,
                'get_badge_color': 'success' if log.action_flag == 1 else 'primary'
            })
    except Exception:
        recent_activities = []

    return recent_activities


def get_recent_items():
    """
    Get recent projects, tasks, and upcoming events with optimized queries.

    Returns:
        dict: Dictionary with recent items
    """
    # Upcoming events
    upcoming_events = Event.objects.filter(
        created_at__gte=timezone.now()
    ).select_related('event_status').order_by('created_at')[:5]

    # Recent projects
    recent_projects_list = Project.objects.select_related(
        'project_status', 'host', 'assigned_to'
    ).prefetch_related('assigned_to__groups').order_by('-updated_at')[:5]

    # Recent tasks
    recent_tasks = Task.objects.select_related(
        'task_status', 'project', 'assigned_to'
    ).prefetch_related('assigned_to__groups', 'project__project_status').order_by('-updated_at')[:5]

    return {
        'upcoming_events': upcoming_events,
        'recent_projects_list': recent_projects_list,
        'recent_tasks': recent_tasks
    }


def get_cached_categories():
    """
    Get cached categories for events and projects.

    Returns:
        dict: Dictionary with event and project categories
    """
    # Event categories
    cache_key_event_categories = 'home_event_categories'
    event_categories = cache.get(cache_key_event_categories)

    if not event_categories:
        event_categories = list(Event.objects.values('event_category').annotate(
            count=Count('id')
        ).order_by('-count')[:10])
        cache.set(cache_key_event_categories, event_categories, 900)  # 15 minutes

    # Project categories
    cache_key_project_categories = 'home_project_categories'
    project_categories = cache.get(cache_key_project_categories)

    if project_categories is None:
        try:
            from events.models import Classification
            project_categories = list(Classification.objects.all()[:10])
            cache.set(cache_key_project_categories, project_categories, 1800)  # 30 minutes
        except:
            project_categories = []

    return {
        'event_categories': event_categories,
        'project_categories': project_categories
    }


@require_GET
@login_required
def load_more_activities(request):
    """
    AJAX endpoint to load more recent activities.

    Query parameters:
        offset: Number of activities to skip (default: 10)
        limit: Number of activities to load (default: 10, max: 50)
    """
    try:
        offset = int(request.GET.get('offset', 10))
        limit = min(int(request.GET.get('limit', 10)), 50)  # Max 50 items

        # Get ContentTypes
        content_types = ContentType.objects.get_for_models(Event, Project, Task)
        event_ct = content_types[Event]
        project_ct = content_types[Project]
        task_ct = content_types[Task]

        activities = LogEntry.objects.filter(
            content_type__in=[event_ct, project_ct, task_ct]
        ).select_related('user', 'content_type').order_by('-action_time')[offset:offset + limit]

        action_map = {1: 'Created', 2: 'Updated', 3: 'Deleted'}
        activities_data = []

        for log in activities:
            activities_data.append({
                'content_type': log.content_type.model,
                'action': action_map.get(log.action_flag, 'Modified'),
                'user': log.user.username if log.user else 'System',
                'timestamp': log.action_time.isoformat(),
                'object_repr': log.object_repr,
                'badge_color': 'success' if log.action_flag == 1 else 'primary'
            })

        return JsonResponse({
            'success': True,
            'activities': activities_data,
            'has_more': len(activities_data) == limit
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
@login_required
def load_more_recent_items(request, item_type):
    """
    AJAX endpoint to load more recent items (projects, tasks, or events).

    Args:
        item_type: Type of items to load ('projects', 'tasks', 'events')
    """
    try:
        offset = int(request.GET.get('offset', 5))
        limit = min(int(request.GET.get('limit', 5)), 20)  # Max 20 items

        if item_type == 'projects':
            items = Project.objects.select_related(
                'project_status', 'host', 'assigned_to'
            ).order_by('-updated_at')[offset:offset + limit]

            items_data = [{
                'id': item.id,
                'title': item.title,
                'status': item.project_status.status_name if item.project_status else 'Unknown',
                'host': item.host.username if item.host else 'Unassigned',
                'assigned_to': item.assigned_to.username if item.assigned_to else 'Unassigned',
                'updated_at': item.updated_at.isoformat()
            } for item in items]

        elif item_type == 'tasks':
            items = Task.objects.select_related(
                'task_status', 'project', 'assigned_to'
            ).order_by('-updated_at')[offset:offset + limit]

            items_data = [{
                'id': item.id,
                'title': item.title,
                'status': item.task_status.status_name if item.task_status else 'Unknown',
                'project': item.project.title if item.project else 'No Project',
                'assigned_to': item.assigned_to.username if item.assigned_to else 'Unassigned',
                'updated_at': item.updated_at.isoformat()
            } for item in items]

        elif item_type == 'events':
            items = Event.objects.select_related(
                'event_status'
            ).filter(created_at__gte=timezone.now()).order_by('created_at')[offset:offset + limit]

            items_data = [{
                'id': item.id,
                'title': item.title,
                'status': item.event_status.status_name if item.event_status else 'Unknown',
                'created_at': item.created_at.isoformat(),
                'venue': item.venue or 'TBD'
            } for item in items]

        else:
            return JsonResponse({
                'success': False,
                'error': f'Invalid item type: {item_type}'
            }, status=400)

        return JsonResponse({
            'success': True,
            'items': items_data,
            'has_more': len(items_data) == limit,
            'item_type': item_type
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
@login_required
def load_more_categories(request, category_type):
    """
    AJAX endpoint to load more categories.

    Args:
        category_type: Type of categories ('events' or 'projects')
    """
    try:
        offset = int(request.GET.get('offset', 10))
        limit = min(int(request.GET.get('limit', 10)), 50)  # Max 50 items

        if category_type == 'events':
            categories = Event.objects.values('event_category').annotate(
                count=Count('id')
            ).order_by('-count')[offset:offset + limit]

            categories_data = [{
                'name': cat['event_category'] or 'Uncategorized',
                'count': cat['count']
            } for cat in categories]

        elif category_type == 'projects':
            try:
                from events.models import Classification
                categories = Classification.objects.all()[offset:offset + limit]

                categories_data = [{
                    'id': cat.id,
                    'name': cat.name,
                    'description': cat.description or ''
                } for cat in categories]
            except:
                categories_data = []

        else:
            return JsonResponse({
                'success': False,
                'error': f'Invalid category type: {category_type}'
            }, status=400)

        return JsonResponse({
            'success': True,
            'categories': categories_data,
            'has_more': len(categories_data) == limit,
            'category_type': category_type
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
@login_required
@csrf_exempt
def refresh_dashboard_data(request):
    """
    AJAX endpoint to refresh specific dashboard data without full page reload.
    """
    try:
        data_type = request.POST.get('data_type', 'all')

        response_data = {}

        if data_type in ['all', 'stats']:
            # Refresh basic stats (bypass cache for fresh data)
            days = int(request.POST.get('days', 30))
            days_ago = request.POST.get('days_ago')

            _, _, start_date, end_date = validate_time_parameters(days, days_ago)
            basic_stats = get_cached_basic_stats(start_date, end_date, days, days_ago)

            response_data['stats'] = basic_stats

        if data_type in ['all', 'status_counts']:
            # Refresh status counts
            status_counts = get_cached_status_counts()
            response_data['status_counts'] = status_counts

        if data_type in ['all', 'activities']:
            # Refresh recent activities
            activities = get_recent_activities()
            response_data['activities'] = activities

        return JsonResponse({
            'success': True,
            'data': response_data,
            'refreshed_at': timezone.now().isoformat()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
@login_required
def get_performance_metrics(request):
    """
    AJAX endpoint to get performance metrics for monitoring.
    """
    try:
        # System metrics
        system_metrics = get_system_metrics()

        # Cache metrics
        cache_metrics = get_cache_metrics()

        # Database connection info
        from django.db import connection
        db_queries_count = len(connection.queries)

        # Dashboard-specific metrics
        dashboard_metrics = {
            'total_cache_keys': len(cache._cache) if hasattr(cache, '_cache') else 0,
            'db_queries_this_request': db_queries_count,
            'python_version': f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
            'django_version': __import__('django').get_version()
        }

        return JsonResponse({
            'success': True,
            'metrics': {
                'system': system_metrics,
                'cache': cache_metrics,
                'dashboard': dashboard_metrics,
                'timestamp': timezone.now().isoformat()
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
@login_required
def get_dashboard_stats(request):
    """
    AJAX endpoint to get real-time dashboard statistics.
    """
    try:
        # Get current time parameters
        days = int(request.GET.get('days', 30))
        days_ago = request.GET.get('days_ago')

        # Validate and get time range
        _, _, start_date, end_date = validate_time_parameters(days, days_ago)

        # Get fresh statistics (bypass cache for real-time data)
        basic_stats = get_cached_basic_stats(start_date, end_date, days, days_ago)
        status_counts = get_cached_status_counts()

        # Calculate some derived metrics
        total_items = (basic_stats['total_events'] + basic_stats['total_projects'] +
                      basic_stats['total_tasks'])

        completion_rate = 0
        if total_items > 0:
            completed_items = (status_counts['completed_events'] +
                             status_counts['completed_projects'] +
                             status_counts['completed_tasks_count'])
            completion_rate = (completed_items / total_items) * 100

        return JsonResponse({
            'success': True,
            'stats': {
                'basic': basic_stats,
                'status': status_counts,
                'derived': {
                    'total_items': total_items,
                    'completion_rate': round(completion_rate, 2),
                    'active_rate': round(((status_counts['active_projects'] +
                                          status_counts['in_progress_events'] +
                                          status_counts['in_progress_tasks']) / max(total_items, 1)) * 100, 2)
                }
            },
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@performance_monitor
def home_view(request, days=None, days_ago=None):
    """
    Enhanced home view with comprehensive dashboard data and intelligent alerts.
    Optimized with caching and modular functions for better performance.

    Args:
        request: HttpRequest object
        days: Optional number of days to look back for statistics
        days_ago: Optional number of days ago to start the range

    Returns:
        Rendered home template with comprehensive context data
    """
    # Validate parameters and get time range
    days, days_ago, start_date, end_date = validate_time_parameters(days, days_ago)

    # Get cached basic statistics
    basic_stats = get_cached_basic_stats(start_date, end_date, days, days_ago)

    # Get cached status counts
    status_counts = get_cached_status_counts()

    # Get recent activities
    recent_activities = get_recent_activities()

    # Get recent items (projects, tasks, events)
    recent_items = get_recent_items()

    # Get cached categories
    categories = get_cached_categories()

    # User profile completion (simplified without custom UserProfile model)
    profile_completion = 50  # Default completion percentage

    # Generate intelligent alerts
    alerts = generate_home_alerts(request.user, {
        'total_events': basic_stats['total_events'],
        'total_projects': basic_stats['total_projects'],
        'total_tasks': basic_stats['total_tasks'],
        'active_projects': status_counts['active_projects'],
        'pending_tasks': status_counts['pending_tasks'],
        'in_progress_tasks': status_counts['in_progress_tasks'],
        'upcoming_events': recent_items['upcoming_events'].count(),
        'recent_activities': len(recent_activities)
    })

    context = {
        'page_title': 'Management360 Dashboard',
        'days': days,
        'days_ago': days_ago,
        'start_date': start_date,
        'end_date': end_date,

        # Statistics
        'total_events': basic_stats['total_events'],
        'total_projects': basic_stats['total_projects'],
        'total_tasks': basic_stats['total_tasks'],
        'events_in_period': basic_stats['events_in_period'],
        'projects_in_period': basic_stats['projects_in_period'],
        'tasks_in_period': basic_stats['tasks_in_period'],

        # Status counts
        'completed_events': status_counts['completed_events'],
        'in_progress_events': status_counts['in_progress_events'],
        'created_events': status_counts['created_events'],
        'completed_projects': status_counts['completed_projects'],
        'active_projects': status_counts['active_projects'],
        'completed_tasks_count': status_counts['completed_tasks_count'],
        'in_progress_tasks': status_counts['in_progress_tasks'],
        'pending_tasks': status_counts['pending_tasks'],

        # Recent data
        'recent_activities': recent_activities,
        'upcoming_events': recent_items['upcoming_events'],
        'upcoming_events_count': recent_items['upcoming_events'].count(),
        'recent_projects_list': recent_items['recent_projects_list'],
        'recent_tasks': recent_items['recent_tasks'],

        # User data
        'profile_completion': profile_completion,

        # Categories
        'event_categories': categories['event_categories'],
        'project_categories': categories['project_categories'],

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


def gtd_guide_view(request):
    """
    Vista para mostrar la guía completa de procesamiento de inbox GTD
    """
    context = {
        'page_title': 'Guía de Procesamiento GTD',
        'title': 'Guía Completa: Procesamiento de Inbox GTD',
        'subtitle': 'Aprende a usar eficientemente el sistema de procesamiento de items del inbox'
    }
    return render(request, 'docs/gtd_guide.html', context)

def blank_view(request):
    context = {
        'page_title': 'Blank Page',
        'message': 'This is a blank page. You can add your own content here.'
    }
    return render(request, 'blank/blank.html', context)

from django.db.models import Q
from .models import Article

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

def get_system_metrics():
    """
    Get system performance metrics.
    """
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_mb': psutil.virtual_memory().used / 1024 / 1024,
            'memory_available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'timestamp': timezone.now().isoformat()
        }
    except:
        return {
            'cpu_percent': 0,
            'memory_percent': 0,
            'memory_used_mb': 0,
            'memory_available_mb': 0,
            'disk_usage_percent': 0,
            'timestamp': timezone.now().isoformat()
        }

def get_cache_metrics():
    """
    Get cache performance metrics.
    """
    try:
        # Get cache stats if using Redis or similar
        cache_stats = {
            'cache_hits': getattr(cache, '_cache_hits', 0),
            'cache_misses': getattr(cache, '_cache_misses', 0),
            'cache_hit_rate': 0
        }

        total_requests = cache_stats['cache_hits'] + cache_stats['cache_misses']
        if total_requests > 0:
            cache_stats['cache_hit_rate'] = (cache_stats['cache_hits'] / total_requests) * 100

        return cache_stats
    except:
        return {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_hit_rate': 0
        }


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
