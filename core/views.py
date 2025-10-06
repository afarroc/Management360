# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q, Sum, Avg
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

# Import models from other apps
from events.models import Event, Project, Task
from events.setup_views import SetupView

# Local imports
from .models import Article
from .utils import (
    performance_monitor,
    validate_time_parameters,
    get_cached_basic_stats,
    get_cached_status_counts,
    get_recent_activities,
    get_recent_items,
    get_cached_categories,
    generate_home_alerts,
    get_system_metrics,
    get_cache_metrics,
    get_all_apps_url_structure,
    get_app_url_structure,
    parse_urlpatterns
)


# =============================================================================
# VISTAS DEL DASHBOARD
# =============================================================================

@login_required
@performance_monitor
def home_view(request, days=None, days_ago=None):
    """
    Vista principal mejorada con datos completos del dashboard y alertas inteligentes.
    Optimizada con caché y funciones modulares para mejor rendimiento.

    Args:
        request: Objeto HttpRequest
        days: Número opcional de días para revisar estadísticas
        days_ago: Número opcional de días atrás para iniciar el rango

    Returns:
        Template renderizado con contexto completo del dashboard
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


# =============================================================================
# PÁGINAS ESTÁTICAS
# =============================================================================

def about_view(request):
    """Vista de la página 'Acerca de'"""
    context = {
        'page_title': 'Acerca de Nosotros'
    }
    return render(request, 'about/about.html', context)

def contact_view(request):
    """Vista de la página de contacto"""
    context = {
        'page_title': 'Contacto'
    }
    return render(request, 'contact/contact.html', context)

def faq_view(request):
    """Vista de la página de preguntas frecuentes"""
    context = {
        'page_title': 'P.F.'
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
    """Vista de página en blanco para desarrollo"""
    context = {
        'page_title': 'Página en Blanco',
        'message': 'Esta es una página en blanco. Puedes agregar tu propio contenido aquí.'
    }
    return render(request, 'blank/blank.html', context)


# =============================================================================
# ENDPOINTS AJAX
# =============================================================================

# Endpoints AJAX para carga lazy del dashboard
@require_GET
@login_required
def load_more_activities(request):
    """
    Endpoint AJAX para cargar más actividades recientes.

    Parámetros de consulta:
        offset: Número de actividades a saltar (por defecto: 10)
        limit: Número de actividades a cargar (por defecto: 10, máximo: 50)
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
    Endpoint AJAX para cargar más elementos recientes (proyectos, tareas o eventos).

    Args:
        item_type: Tipo de elementos a cargar ('projects', 'tasks', 'events')
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
    Endpoint AJAX para cargar más categorías.

    Args:
        category_type: Tipo de categorías ('events' o 'projects')
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
    Endpoint AJAX para refrescar datos específicos del dashboard sin recarga completa de página.
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
    Endpoint AJAX para obtener métricas de rendimiento para monitoreo.
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
    Endpoint AJAX para obtener estadísticas del dashboard en tiempo real.
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


# =============================================================================
# VISTAS DE UTILIDAD
# =============================================================================

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


# Mapeo de URLs y utilidades de desarrollo
@require_GET
def url_map_view(request):
    """
    Vista para generar estructura de mapa de URLs para todas las apps del proyecto.

    Args:
        request: Objeto HttpRequest con parámetro GET opcional 'app_name'

    Returns:
        JsonResponse con:
        - Lista de todas las apps con sus URLs (si no se proporciona app_name)
        - Estructura de URLs para la app especificada
        - Mensaje de error si la app no existe
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


def url_map_html_view(request):
    """
    Vista HTML para mostrar el mapa de URLs en una interfaz web.
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
