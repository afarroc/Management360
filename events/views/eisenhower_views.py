# events/eisenhower_views.py
# ============================================================================
# VISTAS DE LA MATRIZ DE EISENHOWER PARA PRIORIZACIÓN
# ============================================================================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from ..models import Task, TaskStatus, TagCategory
from ..management.task_manager import TaskManager

# ============================================================================
# VISTA PRINCIPAL DE LA MATRIZ DE EISENHOWER
# ============================================================================

@login_required
def eisenhower_matrix(request):
    """
    Vista de la Matriz de Eisenhower para priorización visual
    """
    title = "Matriz de Eisenhower"

    # Obtener todas las tareas del usuario
    task_manager = TaskManager(request.user)
    tasks_data, _ = task_manager.get_all_tasks()

    # Definir los cuadrantes de la matriz
    eisenhower_quadrants = {
        'urgent_important': {
            'title': 'Urgente e Importante',
            'subtitle': '¡Hacer inmediatamente!',
            'color': '#dc3545',
            'bg_color': '#ffebee',
            'icon': 'bi-exclamation-triangle-fill',
            'tasks': []
        },
        'important_not_urgent': {
            'title': 'Importante pero No Urgente',
            'subtitle': 'Planificar para hacer',
            'color': '#ffc107',
            'bg_color': '#fff8e1',
            'icon': 'bi-calendar-check',
            'tasks': []
        },
        'urgent_not_important': {
            'title': 'Urgente pero No Importante',
            'subtitle': 'Delegar si es posible',
            'color': '#fd7e14',
            'bg_color': '#fff3e0',
            'icon': 'bi-people',
            'tasks': []
        },
        'not_urgent_important': {
            'title': 'No Urgente ni Importante',
            'subtitle': 'Eliminar o posponer',
            'color': '#6c757d',
            'bg_color': '#f8f9fa',
            'icon': 'bi-trash',
            'tasks': []
        }
    }

    # Categorizar las tareas según la matriz de Eisenhower
    for task_data in tasks_data:
        task = task_data['task']

        # Determinar si es urgente (por fecha de vencimiento o estado)
        is_urgent = (
            task.task_status.status_name in ['To Do', 'In Progress'] or
            task.important  # Tareas marcadas como importantes
        )

        # Determinar si es importante (por prioridad o etiquetas)
        is_important = (
            task.important or
            task.title.lower().startswith(('urgente', 'importante', 'prioridad', 'review', 'fix', 'bug'))
        )

        # Asignar a cuadrante
        if is_urgent and is_important:
            quadrant = 'urgent_important'
        elif is_important and not is_urgent:
            quadrant = 'important_not_urgent'
        elif is_urgent and not is_important:
            quadrant = 'urgent_not_important'
        else:
            quadrant = 'not_urgent_important'

        eisenhower_quadrants[quadrant]['tasks'].append({
            'task': task,
            'task_data': task_data,
            'quadrant': quadrant
        })

    # Obtener etiquetas disponibles para filtros
    tag_categories = TagCategory.objects.filter(is_system=True)

    context = {
        'title': title,
        'eisenhower_quadrants': eisenhower_quadrants,
        'tag_categories': tag_categories,
        'total_tasks': sum(len(quadrant['tasks']) for quadrant in eisenhower_quadrants.values()),
    }

    return render(request, 'events/eisenhower_matrix.html', context)


# ============================================================================
# API ENDPOINT PARA MOVER TAREAS ENTRE CUADRANTES
# ============================================================================

@login_required
def move_task_eisenhower(request, task_id, quadrant):
    """
    API endpoint para mover tareas entre cuadrantes de la matriz de Eisenhower
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        task = Task.objects.get(id=task_id)

        # Verificar permisos
        if task.host != request.user and request.user not in task.attendees.all():
            return JsonResponse({'success': False, 'error': 'No tienes permisos para modificar esta tarea'})

        # Determinar el nuevo estado basado en el cuadrante
        new_status_map = {
            'urgent_important': 'In Progress',  # Urgente e Importante -> En Progreso
            'important_not_urgent': 'To Do',    # Importante pero No Urgente -> Por Hacer
            'urgent_not_important': 'To Do',    # Urgente pero No Importante -> Por Hacer
            'not_urgent_important': 'To Do'     # No Urgente ni Importante -> Por Hacer
        }

        new_status_name = new_status_map.get(quadrant, 'To Do')
        new_status = TaskStatus.objects.get(status_name=new_status_name)

        # Actualizar el estado de la tarea
        old_status = task.task_status
        task.record_edit(
            editor=request.user,
            field_name='task_status',
            old_value=str(old_status),
            new_value=str(new_status)
        )

        # Actualizar el campo "importante" basado en el cuadrante
        is_important = quadrant in ['urgent_important', 'important_not_urgent']
        if task.important != is_important:
            task.important = is_important
            task.save()

        return JsonResponse({
            'success': True,
            'message': f'Tarea movida a: {new_status_name}',
            'new_quadrant': quadrant
        })

    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tarea no encontrada'})
    except TaskStatus.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Estado no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})