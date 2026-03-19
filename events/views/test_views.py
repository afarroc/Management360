# events/test_views.py
# ============================================================================
# VISTAS DE PRUEBA Y DEMOSTRACIÓN
# ============================================================================

from collections import defaultdict
import datetime
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import F, Count, ExpressionWrapper, DurationField
from django.shortcuts import render, get_object_or_404

from ..models import TaskState, TaskStatus
from ..my_utils import statuses_get
from ..management.project_manager import ProjectManager
from ..management.task_manager import TaskManager
from ..management.event_manager import EventManager


# ============================================================================
# VISTA DE TABLERO DE PRUEBAS
# ============================================================================

@login_required
def test_board(request, id=None):
    """
    Vista de pruebas que muestra estadísticas y gráficos de tareas en progreso
    """
    page_title = 'Test Board'
    
    # Obtener estados del sistema
    event_statuses, project_statuses, task_statuses = statuses_get()
    
    # Obtener usuario actual
    user = get_object_or_404(User, pk=request.user.id)
    
    # Mensaje de prueba con auto-cierre (simulado con JavaScript en el template)
    messages.success(request, f'{page_title}: Este mensaje se cerrará en 60 segundos')
    
    # Obtener datos de tareas en progreso
    task_states_data = _get_task_states_data()
    
    # Obtener datos de creación de proyectos, tareas y eventos
    creation_data = _get_creation_data(user)
    
    context = {
        'page_title': page_title,
        'event_statuses': event_statuses,
        'task_statuses': task_statuses,
        'task_states_with_duration': task_states_data['task_states_with_duration'],
        'bar_chart_data': task_states_data['bar_chart_data'],
        'line_chart_data': task_states_data['line_chart_data'],
        'combined_chart_data': creation_data['combined_chart_data'],
        'duration_chart_data': task_states_data['duration_chart_data'],
    }
    
    return render(request, 'tests/test.html', context)


# ============================================================================
# FUNCIONES AUXILIARES PARA DATOS DE TAREAS
# ============================================================================

def _get_task_states_data():
    """
    Obtiene datos de estados de tareas para gráficos
    """
    # Obtener el estado 'In Progress'
    in_progress_status = get_object_or_404(TaskStatus, status_name='In Progress')
    
    # Obtener las tareas en curso y calcular duraciones
    task_states = TaskState.objects.filter(status=in_progress_status).annotate(
        duration_seconds=ExpressionWrapper(
            F('end_time') - F('start_time'),
            output_field=DurationField()
        )
    ).order_by('-start_time')

    # Formatear estados de tareas con duraciones calculadas
    task_states_with_duration = _format_task_states_with_duration(task_states)

    # Datos para gráfico de barras por tarea
    bar_chart_data = _get_bar_chart_data(task_states)
    
    # Datos para gráfico de líneas (evolución temporal)
    line_chart_data = _get_line_chart_data(task_states)
    
    # Datos para gráfico de duración por tarea
    duration_chart_data = _get_duration_chart_data(task_states)

    return {
        'task_states_with_duration': task_states_with_duration,
        'bar_chart_data': bar_chart_data,
        'line_chart_data': line_chart_data,
        'duration_chart_data': duration_chart_data,
    }


def _format_task_states_with_duration(task_states):
    """
    Formatea los estados de tareas con duraciones calculadas
    """
    task_states_with_duration = []
    
    for task_state in task_states:
        duration_seconds = None
        if task_state.duration_seconds:
            duration_seconds = round(task_state.duration_seconds.total_seconds())
            
        task_states_with_duration.append({
            'task_state': task_state,
            'duration_seconds': duration_seconds,
            'duration_minutes': round(duration_seconds / 60, 1) if duration_seconds else None,
            'duration_hours': round(duration_seconds / 3600, 4) if duration_seconds else None,
            'start_date': task_state.start_time.date(),
            'start_time': task_state.start_time.strftime('%H:%M'),
            'end_time': task_state.end_time.strftime('%H:%M') if task_state.end_time else None,
        })
    
    return task_states_with_duration


def _get_bar_chart_data(task_states):
    """
    Genera datos para gráfico de barras (conteo por tarea)
    """
    task_counts = task_states.values('task__title').annotate(
        count=Count('id')
    ).order_by('-count')[:15]
    
    return {
        'categories': [item['task__title'] for item in task_counts],
        'counts': [item['count'] for item in task_counts],
    }


def _get_line_chart_data(task_states):
    """
    Genera datos para gráfico de líneas (evolución temporal)
    """
    # Calcular el rango de fechas de los últimos 7 días
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=7)
    
    # Filtrar tareas en curso por los últimos 7 días
    task_states_last_month = task_states.filter(start_time__date__gte=start_date)
    
    # Agrupar por fecha
    date_counts = task_states_last_month.values('start_time__date').annotate(
        count=Count('id')
    ).order_by('start_time__date')
    
    return {
        'dates': [item['start_time__date'].strftime('%Y-%m-%d') for item in date_counts],
        'counts_over_time': [item['count'] for item in date_counts],
    }


def _get_duration_chart_data(task_states):
    """
    Genera datos para gráfico de duración por tarea
    """
    task_durations = defaultdict(float)
    
    for task_state in task_states:
        task_name = task_state.task.title
        if task_state.duration_seconds:
            task_durations[task_name] += (task_state.duration_seconds.total_seconds() / 3600)

    return {
        'task_names': list(task_durations.keys()),
        'durations': [round(duration, 2) for duration in task_durations.values()],
    }


# ============================================================================
# FUNCIONES AUXILIARES PARA DATOS DE CREACIÓN
# ============================================================================

def _get_creation_data(user):
    """
    Obtiene datos de creación de proyectos, tareas y eventos
    """
    # Crear instancias de los managers
    project_manager = ProjectManager(user)
    task_manager = TaskManager(user)
    event_manager = EventManager(user)
    
    # Obtener proyectos, tareas y eventos
    projects, _ = project_manager.get_all_projects()
    tasks, _ = task_manager.get_all_tasks()
    events, _ = event_manager.get_all_events()

    # Calcular rango de fechas (últimos 7 días)
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=7)

    # Contar items creados por día
    projects_created_per_day = _filter_and_count_by_date(projects, 'project', start_date)
    tasks_created_per_day = _filter_and_count_by_date(tasks, 'task', start_date)
    events_created_per_day = _filter_and_count_by_date(events, 'event', start_date)

    # Generar datos combinados para gráfico
    combined_chart_data = _generate_combined_chart_data(
        start_date, today,
        projects_created_per_day,
        tasks_created_per_day,
        events_created_per_day
    )

    return {
        'combined_chart_data': combined_chart_data,
    }


def _filter_and_count_by_date(data, key_name, start_date):
    """
    Filtra datos por fecha y cuenta ocurrencias por día
    """
    filtered_data = [
        item for item in data 
        if getattr(item[key_name], 'created_at', None) and 
        getattr(item[key_name], 'created_at').date() >= start_date
    ]
    return _count_created_per_day(filtered_data, key_name)


def _count_created_per_day(data, key_name):
    """
    Cuenta elementos creados por día
    """
    counts = defaultdict(int)
    for item in data:
        created_date = getattr(item[key_name], 'created_at', None).date()
        if created_date:
            counts[created_date] += 1
    return counts


def _generate_combined_chart_data(start_date, today, projects_counts, tasks_counts, events_counts):
    """
    Genera datos combinados para gráfico de líneas múltiples
    """
    # Crear rango de fechas
    delta = today - start_date
    date_range = [start_date + datetime.timedelta(days=x) for x in range(delta.days + 1)]

    def fill_data_for_dates(date_range, counts):
        return [counts.get(date, 0) for date in date_range]

    return {
        'dates': [date.strftime('%Y-%m-%d') for date in date_range],
        'projects': fill_data_for_dates(date_range, projects_counts),
        'tasks': fill_data_for_dates(date_range, tasks_counts),
        'events': fill_data_for_dates(date_range, events_counts),
    }