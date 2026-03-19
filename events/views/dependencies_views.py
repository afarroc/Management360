# events/dependencies_views.py
# ============================================================================
# VISTAS DE DEPENDENCIAS ENTRE TAREAS
# ============================================================================

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404

from ..models import Task, TaskDependency

logger = logging.getLogger(__name__)


# ============================================================================
# VISTAS PRINCIPALES DE DEPENDENCIAS
# ============================================================================

@login_required
def task_dependencies(request, task_id=None):
    """
    Vista para gestionar dependencias entre tareas
    """
    # Debug logs para identificar el problema de URL
    logger.info(f"[task_dependencies] Request method: {request.method}")
    logger.info(f"[task_dependencies] Task ID parameter: {task_id}")
    logger.info(f"[task_dependencies] Request path: {request.path}")
    logger.info(f"[task_dependencies] Request GET parameters: {request.GET}")
    logger.info(f"[task_dependencies] Request POST parameters: {request.POST}")

    if task_id:
        # Ver dependencias de una tarea específica
        return _handle_specific_task_dependencies(request, task_id)
    else:
        # Vista general de todas las dependencias
        return _handle_all_dependencies(request)


def _handle_specific_task_dependencies(request, task_id):
    """
    Maneja la vista de dependencias para una tarea específica
    """
    logger.info(f"[task_dependencies] Processing specific task ID: {task_id}")
    
    try:
        task = Task.objects.get(id=task_id)
        
        # Verificar permisos
        if not (task.host == request.user or request.user in task.attendees.all()):
            logger.warning(f"[task_dependencies] Permission denied for task {task_id}")
            messages.error(request, 'No tienes permisos para ver las dependencias de esta tarea.')
            return redirect('tasks')

        # Obtener dependencias donde esta tarea es la dependiente
        dependencies = TaskDependency.objects.filter(task=task)
        # Obtener tareas que esta tarea bloquea
        blocking = TaskDependency.objects.filter(depends_on=task)

        logger.info(f"[task_dependencies] Found {dependencies.count()} dependencies and {blocking.count()} blocking tasks for task {task_id}")

        context = {
            'title': f'Dependencias de: {task.title}',
            'task': task,
            'dependencies': dependencies,
            'blocking': blocking,
            'available_tasks': Task.objects.filter(
                project=task.project
            ).exclude(id=task_id).order_by('title')
        }
        return render(request, 'events/task_dependencies.html', context)

    except Task.DoesNotExist:
        logger.error(f"[task_dependencies] Task {task_id} not found")
        messages.error(request, 'Tarea no encontrada.')
        return redirect('tasks')


def _handle_all_dependencies(request):
    """
    Maneja la vista general de todas las dependencias
    """
    logger.info("[task_dependencies] Processing general dependencies view (no task_id)")
    all_dependencies = TaskDependency.objects.all().order_by('-created_at')
    logger.info(f"[task_dependencies] Found {all_dependencies.count()} total dependencies")

    context = {
        'title': 'Gestión de Dependencias',
        'all_dependencies': all_dependencies,
    }
    return render(request, 'events/task_dependencies_list.html', context)


# ============================================================================
# VISTAS CRUD DE DEPENDENCIAS
# ============================================================================

@login_required
def create_task_dependency(request, task_id):
    """
    Vista para crear una nueva dependencia entre tareas
    """
    try:
        task = Task.objects.get(id=task_id)
        if not (task.host == request.user or request.user in task.attendees.all()):
            messages.error(request, 'No tienes permisos para gestionar dependencias de esta tarea.')
            return redirect('tasks')
    except Task.DoesNotExist:
        messages.error(request, 'Tarea no encontrada.')
        return redirect('tasks')

    if request.method == 'POST':
        return _process_create_dependency(request, task)

    # GET request - mostrar formulario
    return _render_create_dependency_form(request, task)


def _process_create_dependency(request, task):
    """
    Procesa la creación de una nueva dependencia
    """
    depends_on_id = request.POST.get('depends_on')
    dependency_type = request.POST.get('dependency_type')

    try:
        depends_on_task = Task.objects.get(id=depends_on_id)

        # Validar que no se cree una dependencia circular
        if task.id == depends_on_id:
            messages.error(request, 'Una tarea no puede depender de sí misma.')
            return redirect('task_dependencies_list', task_id=task.id)

        # Verificar si ya existe esta dependencia
        existing = TaskDependency.objects.filter(
            task=task,
            depends_on=depends_on_task
        ).exists()

        if existing:
            messages.error(request, 'Esta dependencia ya existe.')
            return redirect('task_dependencies_list', task_id=task.id)

        # Crear la dependencia
        TaskDependency.objects.create(
            task=task,
            depends_on=depends_on_task,
            dependency_type=dependency_type
        )

        messages.success(request, f'Dependencia creada: "{task.title}" depende de "{depends_on_task.title}"')
        return redirect('task_dependencies_list', task_id=task.id)

    except Task.DoesNotExist:
        messages.error(request, 'La tarea objetivo no existe.')
    except Exception as e:
        messages.error(request, f'Error al crear la dependencia: {e}')

    return redirect('create_task_dependency', task_id=task.id)


def _render_create_dependency_form(request, task):
    """
    Renderiza el formulario para crear una dependencia
    """
    # Obtener tareas disponibles para dependencias
    available_tasks = Task.objects.filter(
        project=task.project
    ).exclude(id=task.id).order_by('title')

    context = {
        'title': f'Crear Dependencia para: {task.title}',
        'task': task,
        'available_tasks': available_tasks,
        'dependency_types': TaskDependency._meta.get_field('dependency_type').choices,
    }

    return render(request, 'events/create_task_dependency.html', context)


@login_required
def delete_task_dependency(request, dependency_id):
    """
    Vista para eliminar una dependencia entre tareas
    """
    try:
        dependency = TaskDependency.objects.get(id=dependency_id)
        task_id = dependency.task.id

        # Verificar permisos
        if not (dependency.task.host == request.user or request.user in dependency.task.attendees.all()):
            messages.error(request, 'No tienes permisos para eliminar esta dependencia.')
            return redirect('tasks')

        if request.method == 'POST':
            return _process_delete_dependency(request, dependency, task_id)

        # GET request - mostrar confirmación
        context = {
            'title': 'Eliminar Dependencia',
            'dependency': dependency,
        }
        return render(request, 'events/delete_task_dependency.html', context)

    except TaskDependency.DoesNotExist:
        messages.error(request, 'Dependencia no encontrada.')
        return redirect('tasks')


def _process_delete_dependency(request, dependency, task_id):
    """
    Procesa la eliminación de una dependencia
    """
    task_title = dependency.task.title
    depends_on_title = dependency.depends_on.title

    dependency.delete()

    messages.success(request, f'Dependencia eliminada: "{task_title}" ya no depende de "{depends_on_title}"')
    return redirect('task_dependencies_list', task_id=task_id)


# ============================================================================
# VISTA DEL GRÁFICO DE DEPENDENCIAS
# ============================================================================

@login_required
def task_dependency_graph(request, task_id):
    """
    Vista para mostrar el gráfico de dependencias de una tarea
    """
    try:
        task = Task.objects.get(id=task_id)
        if not (task.host == request.user or request.user in task.attendees.all()):
            messages.error(request, 'No tienes permisos para ver el gráfico de dependencias.')
            return redirect('tasks')
    except Task.DoesNotExist:
        messages.error(request, 'Tarea no encontrada.')
        return redirect('tasks')

    # Obtener todas las dependencias relacionadas
    all_dependencies = _get_all_dependencies(task)

    # Crear estructura para el gráfico
    nodes, edges = _build_graph_structure(task, all_dependencies)

    context = {
        'title': f'Gráfico de Dependencias: {task.title}',
        'task': task,
        'nodes': nodes,
        'edges': edges,
    }

    return render(request, 'events/task_dependency_graph.html', context)


def _get_all_dependencies(task, visited=None):
    """
    Obtener todas las dependencias recursivamente
    """
    if visited is None:
        visited = set()

    if task.id in visited:
        return []

    visited.add(task.id)
    dependencies = []

    # Tareas que dependen de esta tarea (tareas bloqueadas)
    blocking = TaskDependency.objects.filter(depends_on=task)
    for dep in blocking:
        dependencies.append({
            'task': dep.task,
            'type': 'blocking',
            'dependency_type': dep.dependency_type
        })
        # Recursivamente obtener dependencias de las tareas bloqueadas
        dependencies.extend(_get_all_dependencies(dep.task, visited))

    # Tareas de las que esta tarea depende
    depending_on = TaskDependency.objects.filter(task=task)
    for dep in depending_on:
        dependencies.append({
            'task': dep.depends_on,
            'type': 'depends_on',
            'dependency_type': dep.dependency_type
        })
        # Recursivamente obtener dependencias de las tareas que son dependencias
        dependencies.extend(_get_all_dependencies(dep.depends_on, visited))

    return dependencies


def _build_graph_structure(main_task, all_dependencies):
    """
    Construye la estructura de nodos y aristas para el gráfico
    """
    nodes = []
    edges = []
    processed_tasks = set()

    def add_task_to_graph(task_obj):
        if task_obj.id in processed_tasks:
            return

        processed_tasks.add(task_obj.id)
        nodes.append({
            'id': task_obj.id,
            'label': task_obj.title,
            'status': task_obj.task_status.status_name,
            'color': task_obj.task_status.color,
            'important': task_obj.important
        })

    # Añadir la tarea principal
    add_task_to_graph(main_task)

    # Añadir todas las tareas relacionadas
    for dep in all_dependencies:
        add_task_to_graph(dep['task'])

        # Crear arista
        if dep['type'] == 'blocking':
            # Esta tarea bloquea a dep['task']
            edges.append({
                'from': main_task.id,
                'to': dep['task'].id,
                'label': dep['dependency_type'].replace('_', ' ').title(),
                'type': 'blocking'
            })
        else:
            # Esta tarea depende de dep['task']
            edges.append({
                'from': dep['task'].id,
                'to': main_task.id,
                'label': dep['dependency_type'].replace('_', ' ').title(),
                'type': 'depends_on'
            })

    return nodes, edges