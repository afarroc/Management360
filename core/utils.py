# -*- coding: utf-8 -*-
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from django.core.cache import cache
from django.conf import settings
import time
import logging
import psutil
from functools import wraps
from events.models import Event, Project, Task, Status, ProjectStatus, TaskStatus
import os
import re
import ast
from pathlib import Path

# Configurar logging para métricas de rendimiento
logger = logging.getLogger('performance')

def performance_monitor(func):
    """
    Decorador para monitorear el rendimiento de funciones.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time
        logger.info(f"Función {func.__name__} ejecutada en {execution_time:.4f} segundos")

        return result
    return wrapper

def validate_time_parameters(days, days_ago):
    """
    Validar y sanitizar parámetros temporales para el dashboard.

    Args:
        days: Número de días para revisar
        days_ago: Número de días atrás para iniciar el rango

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
    Obtener estadísticas básicas en caché para eventos, proyectos y tareas.

    Args:
        start_date: Inicio del rango temporal
        end_date: Fin del rango temporal
        days: Parámetro de número de días
        days_ago: Parámetro de días atrás

    Returns:
        dict: Diccionario con conteos totales y por período
    """
    cache_key = f'home_stats_{days}_{days_ago or 0}'
    cached_stats = cache.get(cache_key)

    if cached_stats:
        return cached_stats

    # Calcular estadísticas frescas
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

    # Cache por 5 minutos
    cache.set(cache_key, stats, 300)
    return stats

def get_cached_status_counts():
    """
    Obtener conteos de estados en caché para todos los modelos.

    Returns:
        dict: Diccionario con todos los conteos de estados
    """
    cache_key = 'home_status_counts'
    cached_counts = cache.get(cache_key)

    if cached_counts:
        return cached_counts

    try:
        # Obtener todos los objetos de estado en una consulta
        status_objects = {s.status_name: s for s in Status.objects.filter(
            status_name__in=['Completed', 'In Progress', 'Created']
        )}
        project_status_objects = {s.status_name: s for s in ProjectStatus.objects.filter(
            status_name__in=['Completed', 'In Progress']
        )}
        task_status_objects = {s.status_name: s for s in TaskStatus.objects.filter(
            status_name__in=['Completed', 'In Progress', 'To Do']
        )}

        # Conteos de estados de eventos
        event_status_stats = Event.objects.aggregate(
            completed_events=Count('id', filter=Q(event_status=status_objects.get('Completed'))),
            in_progress_events=Count('id', filter=Q(event_status=status_objects.get('In Progress'))),
            created_events=Count('id', filter=Q(event_status=status_objects.get('Created')))
        )

        # Conteos de estados de proyectos
        project_status_stats = Project.objects.aggregate(
            completed_projects=Count('id', filter=Q(project_status=project_status_objects.get('Completed'))),
            active_projects=Count('id', filter=Q(project_status=project_status_objects.get('In Progress')))
        )

        # Conteos de estados de tareas
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

        # Cache por 10 minutos
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
    Obtener actividades recientes desde LogEntry con consultas optimizadas.

    Returns:
        list: Lista de diccionarios de actividades recientes
    """
    recent_activities = []
    try:
        # Cache de búsquedas ContentType
        content_types = ContentType.objects.get_for_models(Event, Project, Task)
        event_ct = content_types[Event]
        project_ct = content_types[Project]
        task_ct = content_types[Task]

        recent_logs = LogEntry.objects.filter(
            content_type__in=[event_ct, project_ct, task_ct]
        ).select_related('user', 'content_type').order_by('-action_time')[:10]

        # Pre-computar mapa de acciones para eficiencia
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
    Obtener proyectos recientes, tareas y eventos próximos con consultas optimizadas.

    Returns:
        dict: Diccionario con elementos recientes
    """
    # Eventos próximos
    upcoming_events = Event.objects.filter(
        created_at__gte=timezone.now()
    ).select_related('event_status').order_by('created_at')[:5]

    # Proyectos recientes
    recent_projects_list = Project.objects.select_related(
        'project_status', 'host', 'assigned_to'
    ).prefetch_related('assigned_to__groups').order_by('-updated_at')[:5]

    # Tareas recientes
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
    Obtener categorías en caché para eventos y proyectos.

    Returns:
        dict: Diccionario con categorías de eventos y proyectos
    """
    # Categorías de eventos
    cache_key_event_categories = 'home_event_categories'
    event_categories = cache.get(cache_key_event_categories)

    if not event_categories:
        event_categories = list(Event.objects.values('event_category').annotate(
            count=Count('id')
        ).order_by('-count')[:10])
        cache.set(cache_key_event_categories, event_categories, 900)  # 15 minutos

    # Categorías de proyectos
    cache_key_project_categories = 'home_project_categories'
    project_categories = cache.get(cache_key_project_categories)

    if project_categories is None:
        try:
            from events.models import Classification
            project_categories = list(Classification.objects.all()[:10])
            cache.set(cache_key_project_categories, project_categories, 1800)  # 30 minutos
        except:
            project_categories = []

    return {
        'event_categories': event_categories,
        'project_categories': project_categories
    }

def generate_home_alerts(user, stats):
    """
    Generar alertas inteligentes para el dashboard principal.

    Args:
        user: Objeto User
        stats: Diccionario con estadísticas del dashboard

    Returns:
        Lista de diccionarios de alertas
    """
    alerts = []

    # Alerta de bienvenida para usuarios nuevos
    if stats['total_events'] == 0 and stats['total_projects'] == 0:
        alerts.append({
            'type': 'info',
            'icon': 'bi-info-circle',
            'title': '¡Bienvenido a Management360!',
            'message': 'Comienza creando tu primer evento o proyecto.',
            'action_url': '/events/events/create/',
            'action_text': 'Crear Evento'
        })

    # Alerta de alta actividad
    if stats['recent_activities'] > 5:
        alerts.append({
            'type': 'success',
            'icon': 'bi-graph-up',
            'title': 'Alta Actividad Detectada',
            'message': f'Tienes {stats["recent_activities"]} actividades recientes. ¡Sigue con el buen trabajo!',
            'action_url': '/events/management/',
            'action_text': 'Ver Gestión'
        })

    # Alerta de eventos próximos
    if stats['upcoming_events'] > 0:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-calendar-event',
            'title': 'Eventos Próximos',
            'message': f'Tienes {stats["upcoming_events"]} evento(s) programado(s).',
            'action_url': '/events/events/',
            'action_text': 'Ver Eventos'
        })

    # Alerta de backlog de tareas
    if stats['pending_tasks'] > 10:
        alerts.append({
            'type': 'danger',
            'icon': 'bi-exclamation-triangle',
            'title': 'Backlog de Tareas',
            'message': f'Tienes {stats["pending_tasks"]} tareas pendientes. Considera priorizarlas.',
            'action_url': '/events/tasks/',
            'action_text': 'Gestionar Tareas'
        })

    # Alerta de progreso en proyectos
    if stats['active_projects'] > 0 and stats['pending_tasks'] == 0:
        alerts.append({
            'type': 'success',
            'icon': 'bi-trophy',
            'title': '¡Gran Progreso!',
            'message': f'Tienes {stats["active_projects"]} proyectos activos sin tareas pendientes.',
            'action_url': '/events/projects/',
            'action_text': 'Ver Proyectos'
        })

    # Alerta de baja actividad reciente
    if stats['recent_activities'] == 0 and (stats['total_events'] > 0 or stats['total_projects'] > 0):
        alerts.append({
            'type': 'warning',
            'icon': 'bi-clock',
            'title': 'Baja Actividad Reciente',
            'message': 'Considera actualizar tus eventos o proyectos para mantenerlos al día.',
            'action_url': '/events/management/',
            'action_text': 'Actualizar Elementos'
        })

    return alerts

def get_system_metrics():
    """
    Obtener métricas de rendimiento del sistema.
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
    Obtener métricas de rendimiento de caché.
    """
    try:
        # Obtener estadísticas de caché si se usa Redis o similar
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

def get_all_apps_url_structure():
    """
    Obtener estructura de URLs para todas las apps del proyecto.

    Returns:
        Lista de diccionarios con información de apps y estructuras de URLs
    """
    apps_data = []

    # Obtener todas las apps de Django desde INSTALLED_APPS
    from django.conf import settings
    installed_apps = getattr(settings, 'INSTALLED_APPS', [])

    # Filtrar apps locales (excluir core de Django y apps de terceros)
    local_apps = []
    for app in installed_apps:
        if not app.startswith('django.') and '.' in app:
            app_name = app.split('.')[-2]  # Obtener nombre de app desde 'app.apps.AppConfig'
            local_apps.append(app_name)

    # También verificar apps en el directorio del proyecto
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
    Obtener estructura de URLs para una app específica.

    Args:
        app_name: Nombre de la app de Django

    Returns:
        Diccionario con información de URLs de la app o None si no se encuentra
    """
    urls_file = Path(settings.BASE_DIR) / app_name / 'urls.py'

    if not urls_file.exists():
        return None

    try:
        # Leer y parsear el archivo urls.py
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extraer urlpatterns
        urlpatterns = parse_urlpatterns(content, app_name)

        return {
            "app_name": app_name,
            "urls_file": str(urls_file.relative_to(settings.BASE_DIR)),
            "urls": urlpatterns
        }

    except Exception as e:
        return {
            "app_name": app_name,
            "error": f"Error parseando URLs: {str(e)}",
            "urls": []
        }

def parse_urlpatterns(content, app_name=None):
    """
    Parsear urlpatterns de Django desde código Python.

    Args:
        content: Contenido string del archivo urls.py
        app_name: Nombre de la app de Django (opcional)

    Returns:
        Lista de patrones de URL parseados
    """
    urls = []

    try:
        # Usar regex para encontrar llamadas path()
        path_pattern = r'path\s*\(\s*[\'"](.*?)[\'"]\s*,?\s*([^,]+(?:,.*?)?)\)'
        matches = re.findall(path_pattern, content, re.DOTALL)

        for match in matches:
            url_pattern = match[0]
            view_info = match[1].strip()

            # Limpiar la información de la vista
            view_info = re.sub(r'\s+', ' ', view_info)

            # Construir patrón de URL completo incluyendo prefijo de app
            if app_name:
                if url_pattern.startswith('/'):
                    full_pattern = f"/{app_name}{url_pattern}"
                else:
                    full_pattern = f"/{app_name}/{url_pattern}" if url_pattern else f"/{app_name}/"
            else:
                # Fallback cuando no se proporciona app_name
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

        # También buscar patrones re_path
        repath_pattern = r're_path\s*\(\s*r?[\'"](.*?)[\'"]\s*,?\s*([^,]+(?:,.*?)?)\)'
        repath_matches = re.findall(repath_pattern, content, re.DOTALL)

        for match in repath_matches:
            url_pattern = match[0]
            view_info = match[1].strip()

            view_info = re.sub(r'\s+', ' ', view_info)

            # Para re_path, construir patrón completo con prefijo de app
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
            "view": f"Error parseando: {str(e)}",
            "type": "error",
            "full_pattern": error_pattern
        })

    return urls
