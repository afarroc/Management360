# events/tasks_views.py - VERSIÓN COMPLETA CORREGIDA Y MEJORADA
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
import logging
from .models import (
    TaskState, TaskStatus, Project, Task, 
    Event, ProjectStatus, Status
)

logger = logging.getLogger(__name__)

# ============================================================================
# VISTA PRINCIPAL DE TASKS
# ============================================================================

@login_required
def tasks(request, task_id=None, project_id=None):
    """
    Vista principal de tareas - maneja listado y detalle
    """
    title = 'Tasks'
    
    # URLs para navegación
    urls = [
        {'url': 'task_create', 'name': 'Task Create'},
        {'url': 'task_edit', 'name': 'Task Edit'},
    ]

    other_urls = [
        {'url': 'events', 'id': None, 'name': 'Events Panel'},
        {'url': 'projects', 'id': None, 'name': 'Projects Panel'},
        {'url': 'tasks', 'id': None, 'name': 'Tasks Panel'},
    ]
    
    instructions = [
        {'instruction': 'Fill carefully the metadata.', 'name': 'Form'},
    ]
    
    task_statuses = TaskStatus.objects.all().order_by('status_name')

    # ============================================================
    # VISTA DETALLADA DE UNA TAREA ESPECÍFICA
    # ============================================================
    if task_id:
        task = get_object_or_404(Task, id=task_id)

        # Generate alerts for specific task
        task_data = {'task': task}
        alerts = generate_task_alerts(task_data, request.user)

        return render(request, "tasks/task_detail.html", {
            'title': title,
            'task': task,
            'task_statuses': task_statuses,
            'alerts': alerts,
        })

    # ============================================================
    # VISTA DE LISTADO DE TAREAS
    # ============================================================
    else:
        if not project_id:
            tasks_list = Task.objects.filter(
                Q(host=request.user) | Q(assigned_to=request.user)
            ).select_related(
                'task_status', 
                'project', 
                'project__project_status',
                'event', 
                'event__event_status',
                'assigned_to',
                'host'
            ).prefetch_related(
                'taskstate_set'
            ).order_by('-created_at')
        else:
            tasks_list = Task.objects.filter(
                Q(host=request.user) | Q(assigned_to=request.user), 
                project_id=project_id
            ).select_related(
                'task_status', 
                'project', 
                'project__project_status',
                'event', 
                'event__event_status',
                'assigned_to',
                'host'
            ).prefetch_related(
                'taskstate_set'
            ).order_by('-created_at')

        # Convertir a formato tasks_data con estados activos y completados
        tasks_data = []
        for task in tasks_list:
            # Obtener el estado activo (In Progress) si existe
            active_state = task.taskstate_set.filter(
                end_time__isnull=True,
                status__status_name='In Progress'
            ).first()

            # Obtener el estado completado más reciente si existe
            completed_state_qs = task.taskstate_set.filter(
                status__status_name='Completed'
            ).order_by('-end_time')
            
            completed_state = completed_state_qs.first() if completed_state_qs.exists() else None
            
            task_data = {
                'task': task,
                'active_state': active_state,
                'completed_state': completed_state,
            }
            
            tasks_data.append(task_data)

        # Generate overview alerts
        alerts = generate_tasks_overview_alerts(tasks_data, request.user)

        # Add performance alerts
        performance_alerts = generate_task_performance_alerts(tasks_data, request.user)
        alerts.extend(performance_alerts)

        # Obtener otros estados de tarea para el dropdown
        other_task_statuses = TaskStatus.objects.exclude(
            status_name__in=['In Progress', 'Completed']
        )

        return render(request, "tasks/tasks.html", {
            'title': title,
            'tasks': tasks_list,
            'tasks_data': tasks_data,
            'alerts': alerts,
            'task_statuses': task_statuses,
            'other_task_statuses': other_task_statuses,
        })


# ============================================================================
# VISTA PANEL DE TAREAS (OPTIMIZADA)
# ============================================================================

@login_required
def task_panel(request, task_id=None):
    """
    Vista principal del panel de tareas - VERSIÓN COMPLETAMENTE OPTIMIZADA
    """
    title = "Task Panel"
    
    # Obtener estados del sistema
    statuses = get_statuses()
    
    # Obtener estados de tarea recientes (los últimos 10)
    tasks_states = TaskState.objects.select_related(
        'task', 
        'task__task_status',
        'task__project',
        'task__project__project_status',
        'task__event',
        'task__assigned_to'
    ).order_by('-start_time')[:10]
    
    # Estados disponibles para dropdown
    all_task_statuses = TaskStatus.objects.all()
    other_task_statuses = all_task_statuses.exclude(
        status_name__in=['In Progress', 'Completed']
    )
    
    # ============================================================
    # VISTA DETALLADA DE UNA TAREA ESPECÍFICA
    # ============================================================
    if task_id:
        return render_single_task_view(
            request, task_id, title, other_task_statuses, statuses
        )
    
    # ============================================================
    # VISTA GENERAL DEL PANEL DE TAREAS (TODAS LAS TAREAS)
    # ============================================================
    return render_task_panel_view(
        request, title, other_task_statuses, statuses, tasks_states
    )


def get_statuses():
    """
    Obtiene todos los estados del sistema con optimización
    """
    event_statuses = Status.objects.all()
    project_statuses = ProjectStatus.objects.all()
    task_statuses = TaskStatus.objects.all()
    
    return [event_statuses, project_statuses, task_statuses]


def get_tasks_for_user(user):
    """
    Obtiene todas las tareas para un usuario específico con optimización completa
    """
    tasks = Task.objects.filter(
        Q(host=user) | Q(assigned_to=user)
    ).select_related(
        'task_status', 
        'project', 
        'project__project_status',  # Estado del proyecto
        'event', 
        'event__event_status',      # Estado del evento
        'assigned_to',
        'host'
    ).prefetch_related(
        'taskstate_set'
    ).order_by('-created_at')
    
    tasks_data = []
    active_tasks = []
    completed_tasks = []
    blocked_tasks = []
    
    for task in tasks:
        # Obtener el estado activo (In Progress) si existe
        active_state = task.taskstate_set.filter(
            end_time__isnull=True,
            status__status_name='In Progress'
        ).first()

        # Obtener el estado completado más reciente si existe
        completed_state_qs = task.taskstate_set.filter(
            status__status_name='Completed'
        ).order_by('-end_time')
        
        completed_state = completed_state_qs.first() if completed_state_qs.exists() else None
        
        task_data = {
            'task': task,
            'active_state': active_state,
            'completed_state': completed_state,
        }
        
        tasks_data.append(task_data)
        
        # Clasificar tareas por estado
        if task.task_status.status_name == 'In Progress':
            active_tasks.append(task_data)
        elif task.task_status.status_name == 'Completed':
            completed_tasks.append(task_data)
        elif task.task_status.status_name == 'Blocked':
            blocked_tasks.append(task_data)
    
    # Calcular estadísticas de proyectos relacionados
    project_stats = {}
    for task_data in tasks_data:
        task = task_data['task']
        if task.project:
            project_id = task.project.id
            if project_id not in project_stats:
                project_stats[project_id] = {
                    'project': task.project,
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'in_progress_tasks': 0,
                    'blocked_tasks': 0,
                }
            
            project_stats[project_id]['total_tasks'] += 1
            if task.task_status.status_name == 'Completed':
                project_stats[project_id]['completed_tasks'] += 1
            elif task.task_status.status_name == 'In Progress':
                project_stats[project_id]['in_progress_tasks'] += 1
            elif task.task_status.status_name == 'Blocked':
                project_stats[project_id]['blocked_tasks'] += 1
    
    # Calcular porcentajes para cada proyecto
    for project_id, stats in project_stats.items():
        if stats['total_tasks'] > 0:
            stats['completion_rate'] = (stats['completed_tasks'] / stats['total_tasks']) * 100
            stats['progress_rate'] = (stats['in_progress_tasks'] / stats['total_tasks']) * 100
            stats['blocked_rate'] = (stats['blocked_tasks'] / stats['total_tasks']) * 100
        else:
            stats['completion_rate'] = 0
            stats['progress_rate'] = 0
            stats['blocked_rate'] = 0
    
    return tasks_data, active_tasks, completed_tasks, blocked_tasks, project_stats


def render_single_task_view(request, task_id, title, other_task_statuses, statuses):
    """
    Renderiza la vista detallada de una tarea específica con optimización
    """
    try:
        task = get_object_or_404(Task.objects.select_related(
            'task_status', 
            'project', 
            'project__project_status',  # Estado del proyecto
            'event', 
            'event__event_status',      # Estado del evento
            'assigned_to', 
            'host'
        ).prefetch_related('taskstate_set'), id=task_id)
        
        # Verificar permisos
        if task.host != request.user and task.assigned_to != request.user:
            messages.error(request, 'No tienes permiso para ver esta tarea.')
            return redirect('task_panel')
        
        # Obtener datos de la tarea
        active_state = task.taskstate_set.filter(
            end_time__isnull=True,
            status__status_name='In Progress'
        ).first()

        completed_state_qs = task.taskstate_set.filter(
            status__status_name='Completed'
        ).order_by('-end_time')
        
        completed_state = completed_state_qs.first() if completed_state_qs.exists() else None
        
        task_data = {
            'task': task,
            'active_state': active_state,
            'completed_state': completed_state,
        }
        
        # Obtener datos relacionados del proyecto
        project_data = None
        if task.project:
            # Obtener tareas relacionadas del mismo proyecto
            project_tasks = Task.objects.filter(
                project=task.project
            ).select_related(
                'task_status',
                'assigned_to'
            ).order_by('-created_at')[:10]
            
            # Calcular estadísticas del proyecto
            project_total_tasks = Task.objects.filter(project=task.project).count()
            project_completed_tasks = Task.objects.filter(
                project=task.project,
                task_status__status_name='Completed'
            ).count()
            project_in_progress_tasks = Task.objects.filter(
                project=task.project,
                task_status__status_name='In Progress'
            ).count()
            
            project_data = {
                'project': task.project,
                'active_state': None,
                'related_tasks': project_tasks,
                'total_tasks': project_total_tasks,
                'completed_tasks': project_completed_tasks,
                'in_progress_tasks': project_in_progress_tasks,
                'completion_rate': (project_completed_tasks / project_total_tasks * 100) if project_total_tasks > 0 else 0,
            }
        
        # Obtener datos relacionados del evento
        event_data = None
        if task.event:
            event_data = {
                'event': task.event,
                'active_state': None,
            }
        
        # Generar alertas
        alerts = generate_task_alerts(task_data, request.user)
        
        context = {
            'event_statuses': statuses[0],
            'project_statuses': statuses[1],
            'task_statuses': statuses[2],
            'title': f'{title} - {task.title}',
            'task_data': task_data,
            'project_data': project_data,
            'event_data': event_data,
            'alerts': alerts,
            'is_single_task_view': True,
            'other_task_statuses': other_task_statuses,
            'single_task': task,
        }
        
        return render(request, "tasks/task_panel.html", context)
        
    except Exception as e:
        logger.error(f"Error en vista detallada de tarea {task_id}: {str(e)}", exc_info=True)
        messages.error(request, f'Ha ocurrido un error al cargar la tarea: {e}')
        return redirect('task_panel')


def render_task_panel_view(request, title, other_task_statuses, statuses, tasks_states):
    """
    Renderiza la vista general del panel de tareas con optimización completa
    """
    try:
        # Obtener todas las tareas del usuario con estadísticas
        tasks_data, active_tasks, completed_tasks, blocked_tasks, project_stats = get_tasks_for_user(request.user)
        
        # Calcular estadísticas generales
        total_tasks = len(tasks_data)
        in_progress_count = len(active_tasks)
        completed_count = len(completed_tasks)
        pending_count = sum(1 for task_data in tasks_data 
                           if task_data['task'].task_status.status_name == 'To Do')
        blocked_count = len(blocked_tasks)
        
        # Calcular tiempos promedio
        total_duration_hours = 0
        completed_with_times = 0
        
        for task_data in completed_tasks:
            if task_data['completed_state'] and task_data['completed_state'].end_time:
                duration = task_data['completed_state'].end_time - task_data['completed_state'].start_time
                total_duration_hours += duration.total_seconds() / 3600
                completed_with_times += 1
        
        avg_completion_hours = total_duration_hours / completed_with_times if completed_with_times > 0 else 0
        
        # Get unique projects for filter dropdown
        projects = Project.objects.filter(
            Q(host=request.user) | Q(attendees=request.user)
        ).select_related(
            'project_status'
        ).distinct().order_by('title')
        
        # Generate comprehensive alerts
        alerts = generate_tasks_overview_alerts(tasks_data, request.user)
        
        # Add performance alerts
        performance_alerts = generate_task_performance_alerts(tasks_data, request.user)
        alerts.extend(performance_alerts)
        
        # Add project-related alerts
        for project_id, stats in project_stats.items():
            if stats['completion_rate'] > 90:
                alerts.append({
                    'type': 'success',
                    'icon': 'bi-trophy',
                    'title': f'¡Proyecto {stats["project"].title} casi listo!',
                    'message': f'{stats["completion_rate"]:.1f}% completado. ¿Listo para finalizar?',
                    'action_url': f'/events/projects/{project_id}/',
                    'action_text': 'Ver proyecto'
                })
            elif stats['blocked_rate'] > 30:
                alerts.append({
                    'type': 'warning',
                    'icon': 'bi-exclamation-triangle',
                    'title': f'Alta tasa de bloqueo en {stats["project"].title}',
                    'message': f'{stats["blocked_rate"]:.1f}% de las tareas están bloqueadas.',
                    'action_url': f'/events/projects/{project_id}/',
                    'action_text': 'Revisar proyecto'
                })
        
        context = {
            'title': f'{title} (User Tasks)',
            'event_statuses': statuses[0],
            'task_statuses': statuses[2],
            'project_statuses': statuses[1],
            'tasks_data': tasks_data,
            'active_tasks': active_tasks,
            'completed_tasks': completed_tasks,
            'blocked_tasks': blocked_tasks,
            'tasks_states': tasks_states,
            'project_stats': project_stats,
            'total_tasks': total_tasks,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'pending_count': pending_count,
            'blocked_count': blocked_count,
            'avg_completion_hours': avg_completion_hours,
            'projects': projects,
            'alerts': alerts,
            'other_task_statuses': other_task_statuses,
            'is_single_task_view': False,
        }
        
        return render(request, 'tasks/task_panel.html', context)
        
    except Exception as e:
        logger.error(f"Error en panel general de tareas: {str(e)}", exc_info=True)
        messages.error(request, f'Ha ocurrido un error al cargar el panel de tareas: {e}')
        
        # Contexto de fallback simple
        context = {
            'title': 'Task Panel',
            'tasks_data': [],
            'alerts': [],
            'is_single_task_view': False,
            'other_task_statuses': other_task_statuses,
        }
        return render(request, 'tasks/task_panel.html', context)


# ============================================================================
# FUNCIONES DE ALERTAS PARA TAREAS (PERMANECEN IGUAL)
# ============================================================================

def generate_task_alerts(task_data, user):
    """
    Generate contextual alerts for a specific task
    """
    alerts = []
    task = task_data['task']

    # Alert: Task overdue
    if task.updated_at and (timezone.now() - task.updated_at).days > 3:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-exclamation-triangle',
            'title': 'Tarea inactiva',
            'message': f'La tarea "{task.title}" no ha sido actualizada en {(timezone.now() - task.updated_at).days} días.',
            'action_url': f'/events/tasks/edit/{task.id}',
            'action_text': 'Actualizar tarea'
        })

    # Alert: High priority task
    if task.important and task.task_status.status_name != 'Completed':
        alerts.append({
            'type': 'danger',
            'icon': 'bi-star-fill',
            'title': '¡Prioridad alta!',
            'message': f'La tarea "{task.title}" es de alta prioridad y requiere atención inmediata.',
            'action_url': f'/events/tasks/edit/{task.id}',
            'action_text': 'Revisar prioridad'
        })

    # Alert: Task blocked
    if task.task_status.status_name == 'Blocked':
        alerts.append({
            'type': 'warning',
            'icon': 'bi-slash-circle',
            'title': 'Tarea bloqueada',
            'message': f'La tarea "{task.title}" está bloqueada. Revisa las dependencias.',
            'action_url': f'/events/tasks/edit/{task.id}',
            'action_text': 'Resolver bloqueo'
        })

    # Alert: Task in project with issues
    if task.project and task.project.project_status.status_name == 'Blocked':
        alerts.append({
            'type': 'danger',
            'icon': 'bi-exclamation-octagon',
            'title': 'Proyecto bloqueado',
            'message': f'El proyecto "{task.project.title}" está bloqueado, afectando esta tarea.',
            'action_url': f'/events/projects/{task.project.id}/',
            'action_text': 'Ver proyecto'
        })

    return alerts


def generate_tasks_overview_alerts(tasks_data, user):
    """
    Generate overview alerts for all tasks
    """
    alerts = []

    if not tasks_data:
        alerts.append({
            'type': 'info',
            'icon': 'bi-info-circle',
            'title': '¡Bienvenido!',
            'message': 'No tienes tareas activas. ¿Quieres crear una nueva?',
            'action_url': '/events/tasks/create/',
            'action_text': 'Crear tarea'
        })
        return alerts

    # Alert: Overall completion rate
    total_tasks = len(tasks_data)
    completed_tasks = sum(1 for task in tasks_data if task['task'].task_status.status_name == 'Completed')
    in_progress_tasks = sum(1 for task in tasks_data if task['task'].task_status.status_name == 'In Progress')
    pending_tasks = sum(1 for task in tasks_data if task['task'].task_status.status_name == 'To Do')

    if total_tasks > 0:
        completion_rate = (completed_tasks / total_tasks) * 100
        if completion_rate < 30:
            alerts.append({
                'type': 'danger',
                'icon': 'bi-graph-down',
                'title': 'Bajo progreso general',
                'message': f'Solo {completion_rate:.1f}% de las tareas completadas ({completed_tasks}/{total_tasks}).',
                'action_url': '/events/tasks/',
                'action_text': 'Ver todas las tareas'
            })
        elif completion_rate > 80:
            alerts.append({
                'type': 'success',
                'icon': 'bi-trophy',
                'title': '¡Excelente progreso!',
                'message': f'{completion_rate:.1f}% de las tareas completadas. ¡Sigue así!',
                'action_url': '/events/tasks/',
                'action_text': 'Ver estadísticas'
            })

    # Alert: Too many tasks in progress
    if in_progress_tasks > 5:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-exclamation-circle',
            'title': 'Demasiadas tareas activas',
            'message': f'Tienes {in_progress_tasks} tareas en progreso. Considera priorizar.',
            'action_url': '/events/tasks/',
            'action_text': 'Gestionar prioridades'
        })

    # Alert: High priority tasks pending
    high_priority_tasks = [task for task in tasks_data if task['task'].important and task['task'].task_status.status_name != 'Completed']
    if high_priority_tasks:
        alerts.append({
            'type': 'danger',
            'icon': 'bi-star-fill',
            'title': 'Tareas prioritarias pendientes',
            'message': f'{len(high_priority_tasks)} tarea(s) de alta prioridad requieren atención.',
            'action_url': '/events/tasks/',
            'action_text': 'Revisar prioridades'
        })

    # Alert: Blocked tasks
    blocked_tasks = [task for task in tasks_data if task['task'].task_status.status_name == 'Blocked']
    if blocked_tasks:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-slash-circle',
            'title': 'Tareas bloqueadas',
            'message': f'{len(blocked_tasks)} tarea(s) están bloqueadas y necesitan resolución.',
            'action_url': '/events/tasks/',
            'action_text': 'Resolver bloqueos'
        })

    # Alert: Recent activity
    recent_tasks = [task for task in tasks_data if task['task'].created_at > timezone.now() - timezone.timedelta(days=3)]
    if recent_tasks:
        alerts.append({
            'type': 'info',
            'icon': 'bi-calendar-plus',
            'title': 'Actividad reciente',
            'message': f'{len(recent_tasks)} tarea(s) creada(s) en los últimos 3 días.',
            'action_url': '/events/tasks/',
            'action_text': 'Ver tareas nuevas'
        })

    return alerts


def generate_task_performance_alerts(tasks_data, user):
    """
    Generate performance-based alerts for tasks
    """
    alerts = []

    if not tasks_data:
        return alerts

    # Calculate task completion velocity
    completed_tasks = [task for task in tasks_data if task['task'].task_status.status_name == 'Completed']
    if completed_tasks:
        recent_completed = [task for task in completed_tasks if task['task'].updated_at > timezone.now() - timezone.timedelta(days=7)]
        if recent_completed:
            alerts.append({
                'type': 'success',
                'icon': 'bi-speedometer2',
                'title': 'Buena velocidad de trabajo',
                'message': f'Has completado {len(recent_completed)} tarea(s) en la última semana.',
                'action_url': '/events/tasks/',
                'action_text': 'Ver progreso'
            })

    # Task distribution by project
    project_task_counts = {}
    for task_data in tasks_data:
        project_id = task_data['task'].project.id if task_data['task'].project else 'no_project'
        project_name = task_data['task'].project.title if task_data['task'].project else 'Sin proyecto'
        if project_id not in project_task_counts:
            project_task_counts[project_id] = {'name': project_name, 'count': 0}
        project_task_counts[project_id]['count'] += 1

    # Alert for projects with too many tasks
    for project_info in project_task_counts.values():
        if project_info['count'] > 15:
            alerts.append({
                'type': 'warning',
                'icon': 'bi-list-check',
                'title': 'Proyecto sobrecargado',
                'message': f'El proyecto "{project_info["name"]}" tiene {project_info["count"]} tareas. Considera dividir el trabajo.',
                'action_url': '/events/projects/',
                'action_text': 'Revisar proyecto'
            })

    return alerts