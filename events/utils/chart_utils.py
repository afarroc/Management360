"""
Utilidades para generación de datos de gráficos
Centraliza funciones de estadísticas y visualización
"""

from collections import defaultdict
from datetime import timedelta
from django.db.models import Count, F, ExpressionWrapper, DurationField
from django.core.exceptions import ObjectDoesNotExist
from ..models import TaskState, TaskStatus
from .time_utils import get_date_range
import logging

logger = logging.getLogger(__name__)


def get_task_states_with_duration(start_date=None, end_date=None):
    """
    Obtiene estados de tareas con duración calculada
    
    Args:
        start_date (date, optional): Fecha de inicio
        end_date (date, optional): Fecha de fin
        
    Returns:
        list: Estados de tareas con duraciones calculadas
    """
    try:
        in_progress_status = TaskStatus.objects.get(status_name="En Curso")
    except ObjectDoesNotExist:
        logger.warning("Status 'En Curso' not found, trying 'In Progress'")
        try:
            in_progress_status = TaskStatus.objects.get(status_name="In Progress")
        except ObjectDoesNotExist:
            logger.error("No 'In Progress' or 'En Curso' status found")
            return []
    
    # Construir consulta con duración
    queryset = TaskState.objects.filter(status=in_progress_status).annotate(
        duration_seconds=ExpressionWrapper(
            F('end_time') - F('start_time'),
            output_field=DurationField()
        )
    )
    
    if start_date:
        queryset = queryset.filter(start_time__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(start_time__date__lte=end_date)
    
    queryset = queryset.order_by('-start_time')
    
    result = []
    for task_state in queryset:
        duration_seconds = None
        duration_minutes = None
        duration_hours = None
        
        if task_state.duration_seconds:
            duration_seconds = round(task_state.duration_seconds.total_seconds())
            duration_minutes = round(duration_seconds / 60, 1)
            duration_hours = round(duration_seconds / 3600, 4)
        
        result.append({
            'task_state': task_state,
            'duration_seconds': duration_seconds,
            'duration_minutes': duration_minutes,
            'duration_hours': duration_hours,
            'start_date': task_state.start_time.date(),
            'start_time': task_state.start_time.strftime('%H:%M'),
            'end_time': task_state.end_time.strftime('%H:%M') if task_state.end_time else None,
        })
    
    logger.debug(f"Retrieved {len(result)} task states with duration")
    return result


def get_bar_chart_data(task_states):
    """
    Genera datos para gráfico de barras (frecuencia de tareas)
    
    Args:
        task_states (list): Estados de tareas con duración
        
    Returns:
        dict: Datos formateados para gráfico de barras
    """
    task_count_dict = defaultdict(int)
    
    for task_state in task_states:
        task_title = task_state['task_state'].task.title
        task_count_dict[task_title] += 1
    
    sorted_tasks = sorted(task_count_dict.items(), key=lambda x: x[1], reverse=True)[:15]
    categories, counts = zip(*sorted_tasks) if sorted_tasks else ([], [])
    
    return {
        'categories': list(categories),
        'counts': list(counts),
        'total': sum(counts)
    }


def get_line_chart_data(task_states):
    """
    Genera datos para gráfico de líneas (tendencias temporales)
    
    Args:
        task_states (list): Estados de tareas con duración
        
    Returns:
        dict: Datos formateados para gráfico de líneas
    """
    task_ids = [ts['task_state'].id for ts in task_states]
    
    date_task_counts = (
        TaskState.objects.filter(id__in=task_ids)
        .values('start_time__date', 'task')
        .annotate(task_count=Count('task', distinct=True))
        .order_by('start_time__date')
    )
    
    date_count_dict = defaultdict(int)
    for entry in date_task_counts:
        start_date = entry['start_time__date']
        task_count = entry['task_count']
        date_count_dict[start_date] += task_count
    
    sorted_dates = sorted(date_count_dict.items())
    dates, counts = zip(*sorted_dates) if sorted_dates else ([], [])
    
    return {
        'dates': [date.strftime('%Y-%m-%d') for date in dates],
        'counts_over_time': list(counts),
    }


def filter_data_last_month(data, key_name, start_date):
    """
    Filtra datos del último mes
    
    Args:
        data (list): Lista de objetos
        key_name (str): Nombre de la clave que contiene el objeto
        start_date (date): Fecha de inicio
        
    Returns:
        dict: Conteos por día
    """
    filtered_data = []
    for item in data:
        obj = item.get(key_name)
        if obj and hasattr(obj, 'created_at') and obj.created_at:
            if obj.created_at.date() >= start_date:
                filtered_data.append(obj)
    
    return count_created_per_day(filtered_data)


def count_created_per_day(data):
    """
    Cuenta objetos creados por día
    
    Args:
        data (list): Lista de objetos con campo created_at
        
    Returns:
        dict: Mapeo fecha -> conteo
    """
    counts = defaultdict(int)
    for item in data:
        if item and hasattr(item, 'created_at') and item.created_at:
            created_date = item.created_at.date()
            counts[created_date] += 1
    return counts


def fill_data_for_dates(date_range, counts):
    """
    Completa datos para un rango de fechas
    
    Args:
        date_range (list): Lista de fechas
        counts (dict): Mapeo fecha -> conteo
        
    Returns:
        list: Conteos en orden de date_range
    """
    return [counts.get(date, 0) for date in date_range]


def get_combined_chart_data(user, start_date, end_date):
    """
    Genera datos combinados de proyectos, tareas y eventos
    
    Args:
        user (User): Usuario
        start_date (date): Fecha de inicio
        end_date (date): Fecha de fin
        
    Returns:
        dict: Datos combinados para gráficos
    """
    from .managers import get_managers_for_user
    
    managers = get_managers_for_user(user)
    project_manager = managers['project_manager']
    task_manager = managers['task_manager']
    event_manager = managers['event_manager']
    
    projects, _ = project_manager.get_all_projects()
    tasks, _ = task_manager.get_all_tasks()
    events, _ = event_manager.get_all_events()
    
    projects_created = filter_data_last_month(projects, 'project', start_date)
    tasks_created = filter_data_last_month(tasks, 'task', start_date)
    events_created = filter_data_last_month(events, 'event', start_date)
    
    date_range = [start_date + timedelta(days=x) 
                  for x in range((end_date - start_date).days + 1)]
    
    return {
        'dates': [date.strftime('%Y-%m-%d') for date in date_range],
        'projects': fill_data_for_dates(date_range, projects_created),
        'tasks': fill_data_for_dates(date_range, tasks_created),
        'events': fill_data_for_dates(date_range, events_created),
    }


def get_duration_chart_data(task_states):
    """
    Genera datos de duración por tarea
    
    Args:
        task_states (list): Estados de tareas con duración
        
    Returns:
        dict: Datos de duración por tarea
    """
    task_durations = defaultdict(float)
    
    for task_state in task_states:
        task_name = task_state['task_state'].task.title
        if task_state['duration_seconds']:
            task_durations[task_name] += (task_state['duration_seconds'] / 3600)
    
    # Ordenar por duración descendente
    sorted_tasks = sorted(task_durations.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'task_names': [task[0] for task in sorted_tasks],
        'durations': [round(task[1], 2) for task in sorted_tasks],
        'total_hours': round(sum(task_durations.values()), 2)
    }
    
def get_optimized_chart_data():
    """
    Optimized function to get chart data with minimal database queries
    """
    from django.core.cache import cache

    cache_key = 'projects_chart_data'
    cached_data = cache.get(cache_key)

    if cached_data:
        return cached_data['data'], cached_data['json']

    try:
        # Single optimized query for all chart data
        chart_queryset = Project.objects.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            project_count=Count('id')
        ).order_by('date')

        # Get data for the last 30 days only
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_chart_data = chart_queryset.filter(date__gte=thirty_days_ago)

        projects_data = [item['project_count'] for item in recent_chart_data] if recent_chart_data else []
        project_dates = [item['date'].strftime('%Y-%m-%d') for item in recent_chart_data] if recent_chart_data else []

        # Similar optimization for events and tasks
        events_chart = Event.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(date=TruncDate('created_at')).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        tasks_chart = Task.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(date=TruncDate('created_at')).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        events_data = [item['count'] for item in events_chart] if events_chart else []
        tasks_data = [item['count'] for item in tasks_chart] if tasks_chart else []
        event_dates = [item['date'].strftime('%Y-%m-%d') for item in events_chart] if events_chart else []
        task_dates = [item['date'].strftime('%Y-%m-%d') for item in tasks_chart] if tasks_chart else []

        # Ensure all arrays have the same length for chart compatibility
        max_length = max(len(projects_data), len(events_data), len(tasks_data))
        if max_length == 0:
            # No data available, create default structure
            default_dates = [(timezone.now() - timezone.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
            chart_data = {
                'events_data': [0] * 7,
                'projects_data': [0] * 7,
                'tasks_data': [0] * 7,
                'event_dates': default_dates,
                'project_dates': default_dates,
                'task_dates': default_dates,
            }
        else:
            # Pad shorter arrays with zeros to match the longest
            projects_data.extend([0] * (max_length - len(projects_data)))
            events_data.extend([0] * (max_length - len(events_data)))
            tasks_data.extend([0] * (max_length - len(tasks_data)))

            # Use project_dates as the primary date array since it's most likely to have data
            primary_dates = project_dates if project_dates else (event_dates if event_dates else task_dates)

            chart_data = {
                'events_data': events_data,
                'projects_data': projects_data,
                'tasks_data': tasks_data,
                'event_dates': primary_dates,
                'project_dates': primary_dates,
                'task_dates': primary_dates,
            }

        # Convert to JSON string for safe template rendering
        import json
        chart_data_json = json.dumps(chart_data)

        # Cache both the data and JSON
        cache.set(cache_key, {'data': chart_data, 'json': chart_data_json}, 600)
        return chart_data, chart_data_json

    except Exception as e:
        # Return safe default data structure in case of any errors
        default_dates = [(timezone.now() - timezone.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        default_data = {
            'events_data': [0] * 7,
            'projects_data': [0] * 7,
            'tasks_data': [0] * 7,
            'event_dates': default_dates,
            'project_dates': default_dates,
            'task_dates': default_dates,
        }
        import json
        return default_data, json.dumps(default_data)
