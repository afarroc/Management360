# events/views.py - ARCHIVO PRINCIPAL CON TODAS LAS FUNCIONES

# ============================================================================
# IMPORTACIONES ESTÁNDAR
# ============================================================================

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, time, date
from decimal import Decimal
from difflib import SequenceMatcher

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model

User = get_user_model()
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction, models
from django.db.models import Q, Sum, Count, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate
from django.http import Http404, HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .my_utils import statuses_get
from .utils.chart_utils import get_optimized_chart_data
from .utils.status_utils import update_status
from .utils.schedule_utils import log_schedule_changes
# ============================================================================
# IMPORTACIONES LOCALES - MODELOS
# ============================================================================

from .models import (
    Event, Project, Task, Status,
    ProjectStatus, TaskStatus, EventState, TaskState,
    EventAttendee, TaskDependency,
    Classification, TagCategory, Tag,
    ProjectTemplate, TemplateTask,
    InboxItem, InboxItemClassification, InboxItemAuthorization, InboxItemHistory,
    TaskSchedule, TaskProgram,
    Reminder,
    GTDProcessingSettings
)

# ============================================================================
# IMPORTACIONES LOCALES - FORMULARIOS
# ============================================================================

from .forms import (
    CreateNewEvent, CreateNewProject, CreateNewTask,
    EventStatusForm, TaskStatusForm, ProjectStatusForm,
    EditClassificationForm,
    ProjectTemplateForm, TemplateTaskForm, TemplateTaskFormSet
)

# ============================================================================
# IMPORTACIONES LOCALES - GESTIÓN Y UTILIDADES
# ============================================================================

from .management.event_manager import EventManager
from .management.project_manager import ProjectManager
from .management.task_manager import TaskManager
from .management.utils import add_credits_to_user

# ============================================================================
# IMPORTACIÓN DE VISTAS ESPECIALIZADAS
# ============================================================================

# Importar vistas de eventos
from .events_views import *

# Importar vistas de proyectos
from .projects_views import *

# Importar vistas de tareas
from .tasks_views import *

# Importar vistas GTD (Getting Things Done)
from .gtd_views import *
# ============================================================================
# EXPORTACIÓN PARA FÁCIL ACCESO
# ============================================================================

# Todas las funciones estarán disponibles desde views.*

def index(request):
    """Vista principal del dashboard."""
    # Tu código existente para index...
    pass

def dashboard(request):
    """Dashboard principal."""
    # Tu código existente para dashboard...
    pass

# Tasks

@login_required
def task_create(request, project_id=None):
    title="Create New Task"
    
    if request.method == 'GET':
        try:
            initial_status_name = 'To Do'
            initial_task_status = get_object_or_404(TaskStatus, status_name=initial_status_name)
        except Exception as e:
            messages.error(request, f"Error al obtener estado de tarea: {e}")
            return redirect('task_panel')
        initial_ticket_price = 0.07
        if project_id:
            # Aquí debes asignar el formulario con el proyecto seleccionado
            form = CreateNewTask(initial={
                'project': project_id,
                'task_status': initial_task_status,
                'assigned_to': request.user,
                'ticket_price': initial_ticket_price,

                })
        else:
            # Aquí puedes asignar el formulario sin ningún valor inicial

            form = CreateNewTask(initial={
                'project': project_id,
                'task_status':initial_task_status,
                'assigned_to': request.user,
                'ticket_price': initial_ticket_price,

                })

    else:
        print('POST data:', request.POST)
        form = CreateNewTask(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.host = request.user
            task.event = form.cleaned_data['event']

            # Si el campo de evento está vacío, crea un nuevo objeto Evento
            if not task.event:
                status = get_object_or_404(Status, status_name='Created')
                try:
                    with transaction.atomic():
                        
                        new_event = Event.objects.create(
                            title =form.cleaned_data['title'],
                            event_status=status,
                            host = request.user,
                            assigned_to = request.user,
                            
                            )
                        task.event = new_event
                        task.save()
                        form.save_m2m()
                        messages.success(request, 'Tarea creada exitosamente!')
                        return redirect('task_panel')
                    
                except IntegrityError as e:
                    messages.error(request, f'Hubo un problema al guardar la tarea o crear el evento: {e}')
            else:
                try:
                    with transaction.atomic():
                        task.save()
                        form.save_m2m()
                        messages.success(request, 'Tarea creado exitosamente!')
                        return redirect('task_panel')
                except IntegrityError:
                    messages.error(request, 'Hubo un problema al guardar la Tarea.')




    return render(request, 'tasks/task_create.html', {
        'form': form,
        'title':title,
        })

def task_edit(request, task_id=None):
    try:
        if task_id is not None:
            # Estamos editando una tarea existente
            try:
                task = get_object_or_404(Task, pk=task_id)
            except Http404:
                messages.error(request, 'La Tarea con el ID "{}" no existe.'.format(task_id))
                return redirect('home')

            if request.method == 'POST':
                form = CreateNewTask(request.POST, instance=task)
                if form.is_valid():
                    # Asigna el usuario autenticado como el editor
                    task.editor = request.user
                    print('guardando via post si es valido')

                    # Guardar el proyecto con el editor actual (usuario que realiza la solicitud)
                    for field in form.changed_data:
                        old_value = getattr(task, field)
                        new_value = form.cleaned_data.get(field)
                        task.record_edit(
                            editor=request.user,
                            field_name=field,
                            old_value=str(old_value),
                            new_value=str(new_value)
                        )
                    form.save()

                    messages.success(request, 'Tarea guardada con éxito.')
                    return redirect('task_panel')  # Redirige a la página de lista de edición
                else:
                    messages.error(request, 'Hubo un error al guardar la tarea. Por favor, revisa el formulario.')
            else:
                form = CreateNewTask(instance=task)
            return render(request, 'tasks/task_edit.html', {'form': form})
        else:
            # Estamos manejando una solicitud GET sin argumentos
            # Verificar el rol del usuario
            if hasattr(request.user, 'profile') and hasattr(request.user.cv, 'role') and request.user.cv.role == 'SU':
                # Si el usuario es un 'SU', puede ver todos los proyectos
                tasks = Task.objects.all().order_by('-created_at')
            else:
                # Si no, solo puede ver los tareas que le están asignados o a los que asiste
                tasks = Task.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-created_at')
            return render(request, 'tasks/task_panel.html', {'tasks': tasks})
    except Exception as e:
        messages.error(request, 'Ha ocurrido un error: {}'.format(e))
        return redirect('home')

def task_delete(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=task_id)
        if not (hasattr(request.user, 'profile') and hasattr(request.user.cv, 'role') and request.user.cv.role == 'SU'):
            messages.error(request, 'No tienes permiso para eliminar esta tarea.')
            return redirect(reverse('tasks'))
        task.delete()
        messages.success(request, 'La tarea ha sido eliminado exitosamente.')
    else:
        messages.error(request, 'Método no permitido.')
    return redirect(reverse('tasks'))

# Task panel

def change_task_status(request, task_id):
    try:
        if request.method != 'POST':
            return HttpResponse("Método no permitido", status=405)
        task = get_object_or_404(Task, pk=task_id)
        new_status_id = request.POST.get('new_status_id')
        new_status = get_object_or_404(TaskStatus, pk=new_status_id)
        if request.user is None:
            messages.error(request, "User is none: Usuario no autenticado")
            return redirect('home')
        if task.host is not None and (task.host == request.user or request.user in task.attendees.all()):
            old_status = task.task_status
            task.record_edit(
                editor=request.user,
                field_name='task_status',
                old_value=str(old_status),
                new_value=str(new_status)
            )
        else:
            return HttpResponse("No tienes permiso para editar este task", status=403)
    except Exception as e:
        print(f"Error: {str(e)}")
        return HttpResponse(f"Error: {str(e)}", status=500)
    messages.success(request, 'task status edited successfully!')

    return redirect('task_panel')

def task_export(request):
    """Export tasks data"""
    # Simple CSV export for now
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tasks_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Description', 'Status', 'Project', 'Assigned To', 'Created At'])

    tasks = Task.objects.all().select_related('task_status', 'project', 'assigned_to')
    for task in tasks:
        writer.writerow([
            task.id,
            task.title,
            task.description or '',
            task.task_status.status_name if task.task_status else '',
            task.project.title if task.project else '',
            task.assigned_to.username if task.assigned_to else '',
            task.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response

def task_bulk_action(request):
    """Handle bulk actions for tasks"""
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_tasks = request.POST.getlist('selected_items')

        if not selected_tasks:
            messages.error(request, 'No tasks selected.')
            return redirect('task_panel')

        tasks = Task.objects.filter(id__in=selected_tasks)

        if action == 'delete':
            count = tasks.count()
            tasks.delete()
            messages.success(request, f'Successfully deleted {count} task(s).')
        elif action == 'activate':
            count = tasks.update(task_status=TaskStatus.objects.get(status_name='In Progress'))
            messages.success(request, f'Successfully activated {count} task(s).')
        elif action == 'complete':
            count = tasks.update(task_status=TaskStatus.objects.get(status_name='Completed'))
            messages.success(request, f'Successfully completed {count} task(s).')

    return redirect('task_panel')

@login_required
def task_change_status_ajax(request):
    """AJAX endpoint to change task status (with project/event cascade updates)"""
    logger.debug(f"task_change_status_ajax: Método de solicitud = {request.method}")
    logger.debug(f"task_change_status_ajax: Usuario autenticado = {request.user.username} (ID: {request.user.id})")
    
    if request.method == 'POST':
        try:
            # Log todos los parámetros POST recibidos
            logger.debug(f"task_change_status_ajax: Parámetros POST recibidos = {dict(request.POST)}")
            
            task_id = request.POST.get('task_id')
            new_status_name = request.POST.get('new_status_name')
            action = request.POST.get('action')
            
            logger.debug(f"task_change_status_ajax: Parámetros iniciales - task_id='{task_id}', new_status_name='{new_status_name}', action='{action}'")
            
            if not task_id:
                logger.error("task_change_status_ajax: No se proporcionó task_id en la solicitud")
                return JsonResponse({'success': False, 'error': 'Task ID is required'})
            
            # Determinar el nuevo estado basado en los parámetros
            if not new_status_name and action:
                logger.debug(f"task_change_status_ajax: Determinando estado basado en action='{action}'")
                if action == 'activate':
                    new_status_name = 'In Progress'
                elif action == 'deactivate':
                    new_status_name = 'To Do'
                else:
                    logger.error(f"task_change_status_ajax: Acción desconocida '{action}'")
                    return JsonResponse({'success': False, 'error': f'Acción desconocida: {action}'})
            
            if not new_status_name:
                logger.error("task_change_status_ajax: No se pudo determinar el nuevo estado")
                return JsonResponse({'success': False, 'error': 'No se pudo determinar el nuevo estado'})
            
            logger.debug(f"task_change_status_ajax: Estado final determinado = '{new_status_name}'")
            
            # Obtener la tarea
            logger.debug(f"task_change_status_ajax: Buscando tarea con ID={task_id}")
            task = get_object_or_404(Task, id=task_id)
            logger.debug(f"task_change_status_ajax: Tarea encontrada - ID: {task.id}, Título: '{task.title}', Estado actual: '{task.task_status.status_name}'")
            logger.debug(f"task_change_status_ajax: Proyecto asociado: {task.project}, Evento asociado: {task.event}")

            # Check permissions
            logger.debug(f"task_change_status_ajax: Verificando permisos - Host: {task.host}, Usuario actual: {request.user}")
            if task.host != request.user and request.user not in task.attendees.all():
                logger.warning(f"task_change_status_ajax: Permiso denegado para usuario {request.user.username}")
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            logger.debug("task_change_status_ajax: Permisos validados correctamente")

            # Obtener el nuevo estado
            logger.debug(f"task_change_status_ajax: Buscando estado '{new_status_name}'")
            new_status = get_object_or_404(TaskStatus, status_name=new_status_name)
            logger.debug(f"task_change_status_ajax: Nuevo estado encontrado - ID: {new_status.id}, Nombre: '{new_status.status_name}'")

            # Record the change
            old_status = task.task_status
            logger.info(f"task_change_status_ajax: Cambiando estado de tarea {task.id} de '{old_status}' a '{new_status}'")
            
            # Guardar el cambio en el historial
            task.record_edit(
                editor=request.user,
                field_name='task_status',
                old_value=str(old_status),
                new_value=str(new_status)
            )
            logger.debug("task_change_status_ajax: Cambio registrado en el historial")

            # Actualizar el estado en la tarea
            task.task_status = new_status
            task.save()
            logger.debug(f"task_change_status_ajax: Tarea actualizada en base de datos")

            # ============================================================
            # ACTUALIZACIÓN CASCADA DE PROYECTOS Y EVENTOS ASOCIADOS
            # ============================================================
            
            # 1. Actualizar el evento asociado a la tarea
            if task.event:
                logger.debug(f"task_change_status_ajax: Actualizando evento asociado - ID: {task.event.id}")
                try:
                    new_event_status = Status.objects.get(status_name=new_status_name)
                    update_status(task.event, 'event_status', new_event_status, request.user)
                    logger.info(f"task_change_status_ajax: Evento {task.event.id} actualizado a '{new_status_name}'")
                except Status.DoesNotExist:
                    logger.warning(f"task_change_status_ajax: Estado '{new_status_name}' no existe para eventos")
                except Exception as e:
                    logger.error(f"task_change_status_ajax: Error actualizando evento: {e}")

            # 2. Verificar y actualizar el proyecto asociado
            if task.project:
                logger.debug(f"task_change_status_ajax: Verificando proyecto asociado - ID: {task.project.id}")
                
                # Contar tareas en progreso en el proyecto
                tasks_in_progress = Task.objects.filter(
                    project_id=task.project.id, 
                    task_status__status_name='In Progress'
                ).exclude(id=task.id)  # Excluir la tarea actual
                
                logger.debug(f"task_change_status_ajax: Tareas en progreso en el proyecto (excluyendo actual): {tasks_in_progress.count()}")
                
                # Si la tarea se marca como "Completed" y NO hay otras tareas en progreso
                if new_status_name == 'Completed' and not tasks_in_progress.exists():
                    logger.debug(f"task_change_status_ajax: Última tarea completada, actualizando proyecto a 'Completed'")
                    try:
                        # Actualizar estado del proyecto
                        new_project_status = ProjectStatus.objects.get(status_name='Completed')
                        update_status(task.project, 'project_status', new_project_status, request.user)
                        logger.info(f"task_change_status_ajax: Proyecto {task.project.id} actualizado a 'Completed'")
                        
                        # Actualizar evento del proyecto
                        if task.project.event:
                            new_event_status = Status.objects.get(status_name='Completed')
                            update_status(task.project.event, 'event_status', new_event_status, request.user)
                            logger.info(f"task_change_status_ajax: Evento del proyecto {task.project.event.id} actualizado a 'Completed'")
                    except Exception as e:
                        logger.error(f"task_change_status_ajax: Error actualizando proyecto: {e}")
                
                # Si la tarea se marca como "In Progress" (activando)
                elif new_status_name == 'In Progress':
                    logger.debug(f"task_change_status_ajax: Tarea activada, verificando estado del proyecto")
                    try:
                        # Si el proyecto no está en "In Progress", actualizarlo
                        if task.project.project_status.status_name != 'In Progress':
                            new_project_status = ProjectStatus.objects.get(status_name='In Progress')
                            update_status(task.project, 'project_status', new_project_status, request.user)
                            logger.info(f"task_change_status_ajax: Proyecto {task.project.id} activado a 'In Progress'")
                            
                            # Actualizar evento del proyecto
                            if task.project.event:
                                new_event_status = Status.objects.get(status_name='In Progress')
                                update_status(task.project.event, 'event_status', new_event_status, request.user)
                                logger.info(f"task_change_status_ajax: Evento del proyecto {task.project.event.id} activado a 'In Progress'")
                    except Exception as e:
                        logger.error(f"task_change_status_ajax: Error activando proyecto: {e}")
                
                # Si la tarea se marca como "To Do" (desactivando)
                elif new_status_name == 'To Do':
                    logger.debug(f"task_change_status_ajax: Tarea desactivada, verificando si es la última tarea activa")
                    # Contar tareas en progreso incluyendo la actual (que ahora está en "To Do")
                    all_tasks_in_progress = Task.objects.filter(
                        project_id=task.project.id, 
                        task_status__status_name='In Progress'
                    )
                    
                    if not all_tasks_in_progress.exists():
                        logger.debug(f"task_change_status_ajax: No hay tareas en progreso, actualizando proyecto a 'To Do'")
                        try:
                            new_project_status = ProjectStatus.objects.get(status_name='To Do')
                            update_status(task.project, 'project_status', new_project_status, request.user)
                            logger.info(f"task_change_status_ajax: Proyecto {task.project.id} actualizado a 'To Do'")
                            
                            if task.project.event:
                                new_event_status = Status.objects.get(status_name='To Do')
                                update_status(task.project.event, 'event_status', new_event_status, request.user)
                                logger.info(f"task_change_status_ajax: Evento del proyecto {task.project.event.id} actualizado a 'To Do'")
                        except Exception as e:
                            logger.error(f"task_change_status_ajax: Error desactivando proyecto: {e}")

            # ============================================================
            # MANEJO DE CRÉDITOS (similar a task_activate)
            # ============================================================
            if new_status_name == "Completed":
                logger.debug(f"task_change_status_ajax: Tarea completada, calculando créditos")
                try:
                    # Obtener el estado de tarea "In Progress" completado
                    task_state = TaskState.objects.filter(
                        task=task,
                        status__status_name='In Progress'
                    ).latest('start_time')
                    
                    if task_state.end_time:
                        elapsed_time = (task_state.end_time - task_state.start_time).total_seconds()
                        elapsed_minutes = Decimal(elapsed_time) / Decimal(60)
                        total_cost = elapsed_minutes * task.ticket_price
                        
                        logger.debug(f"task_change_status_ajax: Tiempo transcurrido: {elapsed_time}s = {elapsed_minutes} min")
                        logger.debug(f"task_change_status_ajax: Costo total: {total_cost} (ticket_price: {task.ticket_price})")
                        
                        if total_cost > 0:
                            success, message = add_credits_to_user(request.user, total_cost)
                            if success:
                                logger.info(f"task_change_status_ajax: Créditos añadidos: {total_cost}, Mensaje: {message}")
                            else:
                                logger.error(f"task_change_status_ajax: Error añadiendo créditos: {message}")
                except TaskState.DoesNotExist:
                    logger.warning(f"task_change_status_ajax: No se encontró estado 'In Progress' para calcular créditos")
                except Exception as e:
                    logger.error(f"task_change_status_ajax: Error calculando créditos: {e}")

            logger.info(f"task_change_status_ajax: Estado de tarea {task.id} actualizado exitosamente por {request.user.username}")
            return JsonResponse({
                'success': True, 
                'message': f'Task status updated to {new_status_name}',
                'task_id': task_id,
                'old_status': str(old_status),
                'new_status': str(new_status),
                'project_updated': task.project is not None,
                'event_updated': task.event is not None
            })

        except Exception as e:
            logger.exception(f"task_change_status_ajax: Error inesperado - {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e),
                'task_id': task_id if 'task_id' in locals() else None,
                'new_status_name': new_status_name if 'new_status_name' in locals() else None
            })

    logger.warning(f"task_change_status_ajax: Método {request.method} no permitido")
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def task_activate(request, task_id=None):
    switch = 'In Progress'
    title = 'Task Activate'
    
    if task_id:
        task = get_object_or_404(Task, pk=task_id)
        event = task.event
        project = task.project
        project_event = project.event
        amount = 0
        
        if task.task_status.status_name == switch:
            switch = 'Completed'
            amount += 1           

        try:
            new_task_status = TaskStatus.objects.get(status_name=switch)
            update_status(task, 'task_status', new_task_status, request.user)
            messages.success(request, f'La tarea ha sido cambiada a estado {switch} exitosamente.')

            new_event_status = Status.objects.get(status_name=switch)
            update_status(event, 'event_status', new_event_status, request.user)
            messages.success(request, f'El evento de la tarea ha sido cambiado a estado {switch} exitosamente.')

            tasks_in_progress = Task.objects.filter(project_id=project.id, task_status__status_name='In Progress')

            if switch == 'Completed' and tasks_in_progress.exists():
                messages.success(request, f'There are tasks in progress: {tasks_in_progress}')
            else:
                new_project_status = ProjectStatus.objects.get(status_name=switch)
                update_status(project, 'project_status', new_project_status, request.user)
                messages.success(request, f'El proyecto ha sido cambiado a estado {switch} exitosamente.')
                
                update_status(project_event, 'event_status', new_event_status, request.user)
                messages.success(request, f'El evento del proyecto ha sido cambiado a estado {switch} exitosamente.')

            if task.task_status.status_name == "Completed":
                task_state = TaskState.objects.filter(
                    task=task,
                    status__status_name='In Progress'
                ).latest('start_time')
                
                if task_state.end_time:
                    elapsed_time = (task_state.end_time - task_state.start_time).total_seconds()
            else:
                elapsed_time = 0

            elapsed_minutes = Decimal(elapsed_time) / Decimal(60)
            total_cost = elapsed_minutes * task.ticket_price
            print(total_cost)
            amount += total_cost
            
            if amount > 0:
                success, message = add_credits_to_user(request.user, amount)
                if success:
                    messages.success(request, f"Commission:")
                    messages.success(request, message)
                    messages.success(request, f"Total Credits: {request.user.creditaccount.balance}")
                else:
                    return render(request, 'credits/add_credits.html', {'error': message})
        
        except TaskStatus.DoesNotExist:
            messages.error(request, 'El estado "En Curso" no existe en la base de datos.')
        except TaskState.DoesNotExist:
            messages.error(request, 'No se encontró un estado "En Curso" para la tarea.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al intentar activar la tarea: {e}')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    
    else:
        tasks = Task.objects.all().order_by('-updated_at')
        try:
            return render(request, "tasks/task_activate.html",{
                'title': f'{title} (No ID)',
                'tasks': tasks,
            })
        except Exception as e:
            messages.error(request, f'Ha ocurrido un error: {e}')
            return redirect('task_panel')


# Otros
def panel(request):
    events = Event.objects.all().order_by('-created_at')
    #events = events.filter(event_status_id = 2)
    return render(request, 'panel/panel.html', {'events': events})    

from django.core.exceptions import PermissionDenied
from django import forms


# Estatuses

def status(request):
    title='Status Panel'
    urls=[
        {'url':'status_create','name':'Create Status'},
        {'url':'status_edit','name':'Edit Status'},        
    ]

    form_urls = [
        {'url': 'status_create', 'form_id' : 1 ,'name': 'Create Event Status'},
        {'url': 'status_create', 'form_id' : 2 , 'name': 'Create Project Status'},
        {'url': 'status_create', 'form_id' : 3 , 'name': 'Create Task Status'},
        {'url': 'status_edit', 'form_id' : 1 ,'name': 'Edit Event Status'},
        {'url': 'status_edit', 'form_id' : 2 , 'name': 'Edit Project Status'},
        {'url': 'status_edit', 'form_id' : 3 , 'name': 'Edit Task Status'},
        ]

    return render(request, 'configuration/status.html', {
        'form_urls':form_urls,
        'title' : title,
        'urls' : urls,
        })

def status_edit(request, model_id=None, status_id=None):
    # Titulo de la Pagina
    title="Status Edit"
    urls = [
        {'url': 'status', 'name': 'Status Panel'},

    ]
    try:
        # Si se proporcina id del Modelo
        if model_id:
            
            if model_id ==1:
                model=Status
                FormClass = EventStatusForm
                title=f'Event {title}'
            elif model_id ==2:
                model=ProjectStatus
                FormClass = ProjectStatusForm
                title=f'Project {title}'
            elif model_id ==3:
                FormClass = TaskStatusForm
                model=TaskStatus
                title=f'Task {title}'
            else:
                raise ValueError(f'Invalid model_id: {model_id}')
            
            print(model_id, FormClass, model)      
            # Si se proporcina id del Estado
            if status_id:
                print('estatus id', status_id)
                # Obtén la tipificación o muestra un error 404 si no se encuentra
                status = get_object_or_404(model, id=status_id)
                print(status)
                if request.method == 'POST':
                    # Si el formulario se envía, rellena el formulario con los datos enviados
                    form = FormClass(request.POST, instance=status)

                    if form.is_valid():
                        # Si el formulario es válido, guárdalo y redirige al usuario a la lista de Status
                        form.save()

                        messages.success(request, 'El evento ha sido editado exitosamente.')
                        return redirect('status_edit', model_id=model_id)
                else:
                    # Si el formulario no se envía, rellena el formulario con los datos actuales de la tipificación
                    form = FormClass(instance=status)
                    return render(request, 'configuration/status_edit.html', {
                        'title' : title,
                        'form' : form,

                        })

            else:
                instructions = [
                    {'instruction': 'Select the Status you want to edit.', 'name': 'Select status to edit'},
                    ]
 
                statuses = model.objects.all()
                return render(request, 'configuration/status_list.html', {
                    'title' : title,
                    'statuses':statuses,
                    'urls':urls,
                    'instructions':instructions,
                    'model_id':model_id,
                    })
                                    
        else:

            form_urls = [
                {'url': 'status_edit', 'form_id' : 1 ,'name': 'Edit Event Status'},
                {'url': 'status_edit', 'form_id' : 2 , 'name': 'Edit Project Status'},
                {'url': 'status_edit', 'form_id' : 3 , 'name': 'Edit Task Status'},

            ]
            return render(request, 'configuration/status_edit.html', {
                'title' : title,
                'form_urls' : form_urls,
                'urls' : urls,
                })
            
    except ValueError as e:
            messages.error(request, str(e))
            return redirect('home')  
        
def status_create(request, model_id=None):  
    title = 'Status Create'
    urls = [
        {'url': 'status', 'name': 'Status Panel'},
        ]
    form_urls = [
        {'url': 'status_create', 'form_id' : 1 ,'name': 'Create Event Status'},
        {'url': 'status_create', 'form_id' : 2 , 'name': 'Create Project Status'},
        {'url': 'status_create', 'form_id' : 3 , 'name': 'Create Task Status'},

    ]
    instructions = [
        {'instruction': 'Fill carefully the metadata.', 'name': 'Form'},
    ]

    if model_id is None:
        
        if request.method == 'GET':       
            return render(request, 'configuration/status_create.html', {
                'title':title,
                'urls':urls,
                'form_urls':form_urls,
                })
    else:
        form_urls_copy = [form for form in form_urls if form['form_id'] != model_id]
        print(form_urls_copy)
        # Aquí es donde seleccionas el modelo basado en model_id
        if model_id == 1:
            FormClass = EventStatusForm
            model=Status
            title = 'Event Status Create'
        elif model_id == 2: 
            FormClass = ProjectStatusForm
            model=ProjectStatus
            title = 'Project Status Create'
        elif model_id == 3:  
            title = 'Task Status Create'
            FormClass = TaskStatusForm
            model=TaskStatus
        else:
            raise ValueError(f'Invalid model_id: {model_id}')

        if request.method == 'POST':
            statuses = model.objects.all()
            form = FormClass(request.POST)
            if form.is_valid():
                
                messages.success(request, 'El evento ha sido creado exitosamente.')
                form.save()
                return render(request, 'configuration/status_list.html', {
                    'model_id':model_id,
                    'title':title,
                    'urls':urls,
                    'form_urls':form_urls_copy,
                    'instructions':instructions,
                    'statuses': statuses,
                    })
        else:
            form = FormClass()

        return render(request, 'configuration/status_create.html', {
            'title':title,
            'form': form,
            'urls':urls,
            'instructions':instructions,
            'form_urls':form_urls_copy,
            })

def status_delete(request, model_id, status_id):
    try:
        if model_id:
            if status_id:
                if model_id ==1:
                    model=Status
                elif model_id==2:
                    model=ProjectStatus
                elif model_id==3:
                    model=TaskStatus
                else:
                    raise ValueError(f'Invalid model_id: {model_id}')
  
            status = get_object_or_404(model, id=status_id)
            print(status)
            if request.method == 'POST':
                print(request.POST)
                status.delete()
                messages.success(request, 'El evento ha sido eliminado exitosamente.')
                return redirect('status_edit', model_id=model_id)
            
            return render(request, 'configuration/confirm_delete.html', {
                'object': status,
                'model_id':model_id
                })
        else:
            print('Nothing yet')
            
    except ValueError as e:
            messages.error(request, str(e))
            return redirect('home')  
                
# Classifications

def create_Classification(request):
    if request.method == 'POST':
        form = EditClassificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('classification_list')
    else:
        form = EditClassificationForm()
    return render(request, 'configuration/create_classification.html', {'form': form})

def edit_Classification(request, Classification_id):
    # Obtén la tipificación o muestra un error 404 si no se encuentra
    classification = get_object_or_404(Classification, id=Classification_id)

    if request.method == 'POST':
        # Si el formulario se envía, rellena el formulario con los datos enviados
        form = EditClassificationForm(request.POST, instance=classification)
        if form.is_valid():
            # Si el formulario es válido, guárdalo y redirige al usuario a la lista de Classificationes
            form.save()
            return redirect('classification_list')
    else:
        # Si el formulario no se envía, rellena el formulario con los datos actuales de la tipificación
        form = EditClassificationForm(instance=classification)

    # Renderiza la plantilla con el formulario
    return render(request, 'configuration/edit_classification.html', {'form': form})

def delete_Classification(request, Classification_id):
    Classification = get_object_or_404(Classification, id=Classification_id)
    if request.method == 'POST':
        Classification.delete()
        return redirect('Classification_list')
    return render(request, 'configuration/confirm_delete.html', {'object': Classification})

def Classification_list(request):
    classifications = Classification.objects.all()
    for classification in classifications:
        print(classification)
    return render(request, 'configuration/classification_list.html', {'classifications': classifications})

# GTR

def management_index(request):
    """
    Vista índice para la gestión de eventos, proyectos y tareas.
    Muestra estadísticas y enlaces a las diferentes secciones de gestión.
    """
    # Obtener conteos
    event_count = Event.objects.count()
    project_count = Project.objects.count()
    task_count = Task.objects.count()

    # Obtener actividad reciente (últimas 10 modificaciones)
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.admin.models import LogEntry

    event_ct = ContentType.objects.get_for_model(Event)
    project_ct = ContentType.objects.get_for_model(Project)
    task_ct = ContentType.objects.get_for_model(Task)

    recent_activities = LogEntry.objects.filter(
        content_type__in=[event_ct, project_ct, task_ct]
    ).select_related('user', 'content_type').order_by('-action_time')[:10]

    # Preparar actividades para el template
    activities = []
    for activity in recent_activities:
        action_map = {
            1: 'Añadido',
            2: 'Modificado',
            3: 'Eliminado'
        }
        activities.append({
            'content_type': activity.content_type,
            'action': action_map.get(activity.action_flag, 'Desconocido'),
            'user': activity.user,
            'timestamp': activity.action_time,
            'object_repr': activity.object_repr
        })

    context = {
        'event_count': event_count,
        'project_count': project_count,
        'task_count': task_count,
        'recent_activities': activities,
    }

    return render(request, 'management/index.html', context)

# Añade esta función a tu vista 
def update_event(request):
    if request.method == 'POST':
        # Obtén el ID del evento y si está seleccionado o no
        evento_id = request.POST.get('evento')
        selected = request.POST.get('selected') == 'true'

        # Encuentra el evento en la base de datos
        evento = Event.objects.get(id=evento_id)

        # Actualiza el estado del evento
        evento.estado = 'Completed' if selected else 'No Completed'
        evento.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})

@login_required
def planning_task(request):
    """
    Vista mejorada para mostrar el horario de tareas programadas con seguridad y funcionalidad avanzada
    """
    # Verificar permisos - solo usuarios autenticados pueden ver su horario
    user = request.user

    # Obtener parámetros de filtro
    start_date_param = request.GET.get('start_date')
    days_param = request.GET.get('days', 7)

    try:
        days_param = int(days_param)
        if days_param < 1 or days_param > 31:
            days_param = 7  # Valor por defecto si está fuera de rango
    except (ValueError, TypeError):
        days_param = 7

    # Determinar fecha de inicio
    if start_date_param:
        try:
            start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
        except ValueError:
            start_date = timezone.now().date()
    else:
        start_date = timezone.now().date()

    end_date = start_date + timedelta(days=days_param)

    # Obtener tareas programadas del usuario dentro del rango de fechas
    task_programs = TaskProgram.objects.filter(
        host=user,
        start_time__date__range=(start_date, end_date)
    ).select_related('task', 'task__task_status', 'task__project').order_by('start_time')

    # Crear una matriz para el horario
    days = [(start_date + timedelta(days=i)) for i in range(days_param)]
    schedule = {day: {hour: [] for hour in range(24)} for day in days}

    # Estadísticas del horario
    total_programs = task_programs.count()
    total_hours = 0
    programs_by_day = {day: 0 for day in days}

    # Llenar la matriz con las tareas programadas
    for program in task_programs:
        day = program.start_time.date()
        hour = program.start_time.hour

        if day in schedule and hour in schedule[day]:
            schedule[day][hour].append(program)
            programs_by_day[day] += 1

            # Calcular duración si hay end_time
            if program.end_time:
                duration = (program.end_time - program.start_time).total_seconds() / 3600
                total_hours += duration

    # Determinar horas activas (con al menos una tarea programada)
    active_hours = set()
    for day_schedule in schedule.values():
        for hour, programs in day_schedule.items():
            if programs:
                active_hours.add(hour)

    hours = sorted(list(active_hours)) if active_hours else range(9, 18)  # 9 AM - 6 PM por defecto

    # Preparar navegación de fechas
    prev_start = start_date - timedelta(days=days_param)
    next_start = start_date + timedelta(days=days_param)

    context = {
        'title': f'Horario de Tareas - {start_date.strftime("%d/%m/%Y")} a {(end_date - timedelta(days=1)).strftime("%d/%m/%Y")}',
        'schedule': schedule,
        'days': days,
        'hours': hours,
        'start_date': start_date,
        'end_date': end_date,
        'days_param': days_param,
        'prev_start': prev_start,
        'next_start': next_start,

        # Estadísticas
        'total_programs': total_programs,
        'total_hours': round(total_hours, 1),
        'programs_by_day': programs_by_day,

        # URLs de navegación
        'urls': {
            'today': f'/events/planning_task/?start_date={timezone.now().date()}&days={days_param}',
            'this_week': f'/events/planning_task/?start_date={timezone.now().date() - timedelta(days=timezone.now().weekday())}&days=7',
            'next_week': f'/events/planning_task/?start_date={start_date + timedelta(days=7)}&days={days_param}',
        }
    }

    return render(request, 'program/program.html', context)

@login_required
def task_programs_calendar(request):
    """
    Vista de calendario semanal para programas de tareas creados
    """
    from datetime import datetime, timedelta
    from collections import defaultdict

    # Obtener parámetros de filtro
    start_date_param = request.GET.get('start_date')
    weeks_param = request.GET.get('weeks', 1)

    try:
        weeks_param = int(weeks_param)
        if weeks_param < 1 or weeks_param > 4:
            weeks_param = 1  # Valor por defecto si está fuera de rango
    except (ValueError, TypeError):
        weeks_param = 1

    # Determinar fecha de inicio (lunes de la semana actual)
    if start_date_param:
        try:
            start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
        except ValueError:
            start_date = timezone.now().date()
    else:
        start_date = timezone.now().date()

    # Ajustar al lunes de la semana
    start_date = start_date - timedelta(days=start_date.weekday())

    end_date = start_date + timedelta(days=weeks_param * 7 - 1)

    # Obtener programas de tareas del usuario en el rango de fechas
    task_programs = TaskProgram.objects.filter(
        host=request.user,
        start_time__date__range=(start_date, end_date)
    ).select_related('task', 'task__task_status').order_by('start_time')

    # Crear estructura de calendario
    calendar_data = {}
    current_date = start_date

    while current_date <= end_date:
        calendar_data[current_date] = {
            'date': current_date,
            'weekday': current_date.strftime('%A'),
            'weekday_short': current_date.strftime('%a'),
            'programs': []
        }
        current_date += timedelta(days=1)

    # Llenar el calendario con programas
    for program in task_programs:
        program_date = program.start_time.date()
        if program_date in calendar_data:
            calendar_data[program_date]['programs'].append({
                'program': program,
                'start_time': program.start_time,
                'end_time': program.end_time,
                'duration': program.end_time - program.start_time if program.end_time else None,
                'task_title': program.task.title,
                'task_status': program.task.task_status.status_name,
                'task_status_color': program.task.task_status.color
            })

    # Estadísticas
    total_programs = task_programs.count()
    total_hours = sum(
        (p.end_time - p.start_time).total_seconds() / 3600
        for p in task_programs if p.end_time
    )

    # Navegación
    prev_week = start_date - timedelta(days=7)
    next_week = start_date + timedelta(days=7 * weeks_param)

    context = {
        'title': f'Calendario de Programas - Semana del {start_date.strftime("%d/%m/%Y")}',
        'calendar_data': calendar_data,
        'start_date': start_date,
        'end_date': end_date,
        'weeks_param': weeks_param,
        'prev_week': prev_week,
        'next_week': next_week,
        'total_programs': total_programs,
        'total_hours': round(total_hours, 1),
        'urls': {
            'today': f'/events/task_programs_calendar/?start_date={timezone.now().date() - timedelta(days=timezone.now().weekday())}&weeks={weeks_param}',
            'this_week': f'/events/task_programs_calendar/?start_date={timezone.now().date() - timedelta(days=timezone.now().weekday())}&weeks={weeks_param}',
            'next_week': f'/events/task_programs_calendar/?start_date={next_week}&weeks={weeks_param}',
        }
    }

    return render(request, 'events/task_programs_calendar.html', context)

@login_required
def add_credits(request):
    if request.method == 'POST':
        amount = request.POST['amount']
        success, message = add_credits_to_user(request.user, amount)
        
        if success:
            messages.success(request, message)
            return redirect('home')
        else:
            return render(request, 'credits/add_credits.html', {'error': message})

    return render(request, 'credits/add_credits.html')

def project_tasks_status_check(request, project_id):
    task_active_status = TaskStatus.objects.filter(status_name='In Progress').first()
    task_finished_status = TaskStatus.objects.filter(status_name='Completed').first()
    project_active_status = ProjectStatus.objects.filter(status_name='In Progress').first()
    project_finished_status = ProjectStatus.objects.filter(status_name='Completed').first()

    if not task_active_status or not task_finished_status or not project_active_status or not project_finished_status:
        return render(request, 'projects/projects_check.html', {
            'error': 'Statuses not found'
        })

    project = get_object_or_404(Project, id=project_id)
    project_tasks = Task.objects.filter(project_id=project.id)
    active_tasks = project_tasks.filter(task_status=task_active_status)

    if active_tasks.exists():
        # Preguntar al usuario si desea forzar el cierre de las tareas activas
        if request.method == 'POST' and 'force_close' in request.POST:
            # Forzar el cierre de todas las tareas activas
            for task in active_tasks:
                old_status = task.task_status
                task.record_edit(
                    editor=request.user,
                    field_name='task_status',
                    old_value=str(old_status),
                    new_value=str(task_finished_status)
                )
                # Ejecutar event.record_edit para el evento de cada tarea
                if hasattr(task, 'event'):
                    print('have event')
                    event = task.event
                    event_old_status = event.event_status  # Suponiendo que 'status' es el campo relevante en el evento
                    event.record_edit(
                        editor=request.user,
                        field_name='event_status',
                        old_value=str(event_old_status),
                        new_value=str(task_finished_status)  # O el estado que corresponda para el evento
                    )
                else:
                    print('doesnt have event')

            # Actualizar el estado del proyecto a Completed
            old_status = project.project_status
            project.record_edit(
                editor=request.user,
                field_name='project_status',
                old_value=str(old_status),
                new_value=str(project_finished_status)
            )
        else:
            # Renderizar una plantilla que pregunte al usuario si desea forzar el cierre
            return render(request, 'projects/confirm_force_close.html', {
                'project': project,
                'active_tasks': active_tasks
            })

    return render(request, 'projects/projects_check.html', {
        'project_tasks': project_tasks
    })

def test_board(request, id=None):
    page_title = 'Test Board'
    event_statuses, project_statuses, task_statuses = statuses_get()
    user = get_object_or_404(User, pk=request.user.id)
    messages.success(request, f'{page_title}: Este mensaje se cerrará en 60 segundos')
    
    # Obtener el estado 'In Progress'
    in_progress_status = get_object_or_404(TaskStatus, status_name='In Progress')
    
    # Obtener las tareas en curso y calcular duraciones
    task_states = TaskState.objects.filter(status=in_progress_status).annotate(
        duration_seconds=ExpressionWrapper(
            F('end_time') - F('start_time'),
            output_field=DurationField()
        )
    ).order_by('-start_time')

    task_states_with_duration = [
        {
            'task_state': task_state,
            'duration_seconds': (duration_seconds := round(task_state.duration_seconds.total_seconds())) if task_state.duration_seconds else None,
            'duration_minutes': round(duration_seconds / 60, 1) if task_state.duration_seconds else None,
            'duration_hours': round(duration_seconds / 3600, 4) if task_state.duration_seconds else None,
            'start_date': task_state.start_time.date(),
            'start_time': task_state.start_time.strftime('%H:%M'),
            'end_time': task_state.end_time.strftime('%H:%M') if task_state.end_time else None,
        }
        for task_state in task_states
    ]

    # Datos para el gráfico de barras por tarea (sin cambios)
    task_counts = task_states.values('task__title').annotate(count=Count('id')).order_by('-count')[:15]
    bar_chart_data = {
        'categories': [item['task__title'] for item in task_counts],
        'counts': [item['count'] for item in task_counts],
    }
    
    # Calcular el rango de fechas de los ultimos dias
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=7)
    
    # Filtrar tareas en curso por el último mes
    task_states_last_month = task_states.filter(start_time__date__gte=start_date)
    
    # Datos para el gráfico de líneas a lo largo del tiempo
    date_counts = task_states_last_month.values('start_time__date').annotate(count=Count('id')).order_by('start_time__date')
    line_chart_data = {
        'dates': [item['start_time__date'].strftime('%Y-%m-%d') for item in date_counts],
        'counts_over_time': [item['count'] for item in date_counts],
    }
    
    # Crear instancias de los managers 
    project_manager = ProjectManager(user)
    task_manager = TaskManager(user)
    event_manager = EventManager(user)
    
    # Obtener proyectos, tareas y eventos
    projects, _ = project_manager.get_all_projects()
    tasks, _ = task_manager.get_all_tasks()
    events, _ = event_manager.get_all_events()

    # Recuento de proyectos, tareas y eventos creados por día
    def count_created_per_day(data, key_name):
        print(key_name)
        counts = defaultdict(int)
        for item in data:
            print(item )
            created_date = getattr(item[key_name], 'created_at', None).date()
            
            if created_date:
                counts[created_date] += 1
        return counts

    # Filtrar proyectos, tareas y eventos por el último mes
    def filter_data_last_month(data, key_name):
        filtered_data = [item for item in data if getattr(item[key_name], 'created_at', None).date() >= start_date]
        return count_created_per_day(filtered_data, key_name)
    
    projects_created_per_day = filter_data_last_month(projects, 'project')
    tasks_created_per_day = filter_data_last_month(tasks, 'task')
    events_created_per_day = filter_data_last_month(events, 'event')

    # Encontrar el rango de fechas dentro del último mes
    date_range = [start_date + datetime.timedelta(days=x) for x in range((today - start_date).days + 1)]

    def fill_data_for_dates(date_range, counts):
        return [counts.get(date, 0) for date in date_range]

    combined_chart_data = {
        'dates': [date.strftime('%Y-%m-%d') for date in date_range],
        'projects': fill_data_for_dates(date_range, projects_created_per_day),
        'tasks': fill_data_for_dates(date_range, tasks_created_per_day),
        'events': fill_data_for_dates(date_range, events_created_per_day),
    }

    # Calcular la duración total en horas por tarea
    task_durations = defaultdict(float)
    for task_state in task_states:
        task_name = task_state.task.title
        if task_state.duration_seconds:
            task_durations[task_name] += (task_state.duration_seconds.total_seconds() / 3600)

        
    duration_chart_data = {
        'task_names': list(task_durations.keys()),
        'durations': [round(duration, 2) for duration in task_durations.values()],
    }

    context = {
        'page_title': page_title,
        'event_statuses': event_statuses,
        'task_statuses': task_statuses,
        'task_states_with_duration': task_states_with_duration,
        'bar_chart_data': bar_chart_data,
        'line_chart_data': line_chart_data,
        'combined_chart_data': combined_chart_data,
        'duration_chart_data': duration_chart_data,  # Añadir los datos del gráfico de duración
    }
    
    return render(request, 'tests/test.html', context)





@login_required
def kanban_board_unified(request):
    """
    Vista Kanban unificada que integra las mejores características de ambas vistas
    """
    title = "Panel Kanban Unificado"

    # Obtener todas las tareas del usuario
    task_manager = TaskManager(request.user)
    tasks_data, _ = task_manager.get_all_tasks()

    # Obtener proyectos del usuario
    project_manager = ProjectManager(request.user)
    projects_data, _ = project_manager.get_all_projects()

    # Obtener eventos del usuario
    event_manager = EventManager(request.user)
    events_data, _ = event_manager.get_all_events()

    # Organizar tareas por estado para el kanban principal
    kanban_columns = {
        'To Do': {
            'title': 'Por Hacer',
            'color': '#6c757d',
            'tasks': []
        },
        'In Progress': {
            'title': 'En Progreso',
            'color': '#007bff',
            'tasks': []
        },
        'Completed': {
            'title': 'Completado',
            'color': '#28a745',
            'tasks': []
        },
        'In Review': {
            'title': 'En Revisión',
            'color': '#fd7e14',
            'tasks': []
        }
    }

    # Categorizar las tareas
    for task_data in tasks_data:
        task = task_data['task']
        status_name = task.task_status.status_name

        if status_name in kanban_columns:
            kanban_columns[status_name]['tasks'].append(task_data)

    # Secciones adicionales organizadas (versión mejorada)
    organized_sections = {
        'recent_projects': {
            'title': 'Proyectos Recientes',
            'icon': 'bi-folder',
            'color': 'primary',
            'items': projects_data[:5],  # Últimos 5 proyectos
            'view_all_url': 'projects'
        },
        'active_events': {
            'title': 'Eventos Activos',
            'icon': 'bi-calendar-event',
            'color': 'success',
            'items': [e for e in events_data if e['event'].event_status.status_name == 'In Progress'][:5],
            'view_all_url': 'events'
        },
        'gtd_tools': {
            'title': 'Herramientas GTD',
            'icon': 'bi-lightbulb',
            'color': 'warning',
            'items': [
                {'name': 'Bandeja de Entrada', 'url': 'inbox', 'icon': 'bi-inbox', 'description': 'Capturar tareas rápidamente'},
                {'name': 'Matriz Eisenhower', 'url': 'eisenhower_matrix', 'icon': 'bi-grid-3x3', 'description': 'Priorizar tareas'},
                {'name': 'Dependencias', 'url': 'task_dependencies_list', 'icon': 'bi-link', 'description': 'Gestionar dependencias'},
                {'name': 'Plantillas', 'url': 'project_templates', 'icon': 'bi-file-earmark-plus', 'description': 'Crear desde plantillas'},
            ],
            'view_all_url': None
        },
        'quick_config': {
            'title': 'Configuración Rápida',
            'icon': 'bi-gear',
            'color': 'info',
            'items': [
                {'name': 'Crear Tarea', 'url': 'task_create', 'icon': 'bi-plus-circle', 'description': 'Nueva tarea rápida'},
                {'name': 'Crear Proyecto', 'url': 'project_create', 'icon': 'bi-folder-plus', 'description': 'Nuevo proyecto'},
                {'name': 'Crear Evento', 'url': 'event_create', 'icon': 'bi-calendar-plus', 'description': 'Nuevo evento'},
                {'name': 'Recordatorios', 'url': 'reminders_dashboard', 'icon': 'bi-bell', 'description': 'Gestionar recordatorios'},
            ],
            'view_all_url': 'status'
        }
    }

    # Obtener etiquetas disponibles para filtros
    from .models import TagCategory, Tag
    tag_categories = TagCategory.objects.filter(is_system=True)

    # Calcular estadísticas generales mejoradas
    total_tasks = len(tasks_data)
    in_progress_count = sum(1 for task_data in tasks_data if task_data['task'].task_status.status_name == 'In Progress')
    completed_count = sum(1 for task_data in tasks_data if task_data['task'].task_status.status_name == 'Completed')
    pending_count = sum(1 for task_data in tasks_data if task_data['task'].task_status.status_name == 'To Do')

    # Estadísticas de proyectos
    total_projects = len(projects_data)
    active_projects = [p for p in projects_data if p['project'].project_status.status_name == 'In Progress']

    # Estadísticas de eventos
    total_events = len(events_data)
    active_events = [e for e in events_data if e['event'].event_status.status_name == 'In Progress']

    # Items del inbox GTD para mostrar en el panel
    from .models import InboxItem
    inbox_items = InboxItem.objects.filter(created_by=request.user, is_processed=False)[:5]

    # Obtener proyectos para el modal de creación rápida (de la primera vista)
    from .models import Project
    projects = Project.objects.filter(
        Q(host=request.user) | Q(attendees=request.user)
    ).distinct().order_by('title')

    context = {
        'title': title,
        'kanban_columns': kanban_columns,
        'organized_sections': organized_sections,
        'tag_categories': tag_categories,

        # Estadísticas
        'total_tasks': total_tasks,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_events': total_events,
        'active_events': active_events,

        # Datos adicionales de ambas vistas
        'inbox_items': inbox_items,
        'projects': projects,  # Para el modal de creación rápida
        'recent_activities': [],  # Podría implementarse más tarde
    }

    return render(request, 'events/kanban_enhanced.html', context)

@login_required
def kanban_project(request, project_id):
    """
    Vista Kanban específica para un proyecto
    """
    title = "Kanban del Proyecto"

    try:
        project = Project.objects.get(id=project_id)
        if not (project.host == request.user or request.user in project.attendees.all()):
            messages.error(request, 'No tienes permisos para ver este proyecto.')
            return redirect('projects')
    except Project.DoesNotExist:
        messages.error(request, 'El proyecto no existe.')
        return redirect('projects')

    # Obtener tareas del proyecto específico
    tasks = Task.objects.filter(project=project).select_related(
        'task_status', 'assigned_to', 'host'
    )

    # Organizar tareas por estado
    kanban_columns = {
        'To Do': {
            'title': 'Por Hacer',
            'color': '#6c757d',
            'tasks': []
        },
        'In Progress': {
            'title': 'En Progreso',
            'color': '#007bff',
            'tasks': []
        },
        'In Review': {
            'title': 'En Revisión',
            'color': '#fd7e14',
            'tasks': []
        },
        'Completed': {
            'title': 'Completado',
            'color': '#28a745',
            'tasks': []
        }
    }

    # Categorizar las tareas
    for task in tasks:
        status_name = task.task_status.status_name
        if status_name in kanban_columns:
            # Obtener etiquetas de la tarea
            task_tags = task.tags.all()  # Las tareas pueden tener etiquetas a través del modelo Tag

            task_data = {
                'task': task,
                'tags': task_tags
            }
            kanban_columns[status_name]['tasks'].append(task_data)

    # Obtener etiquetas disponibles para filtros
    from .models import TagCategory
    tag_categories = TagCategory.objects.filter(is_system=True)

    context = {
        'title': title,
        'project': project,
        'kanban_columns': kanban_columns,
        'tag_categories': tag_categories,
    }

    return render(request, 'events/kanban_enhanced.html', context)

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
    from .models import TagCategory, Tag
    tag_categories = TagCategory.objects.filter(is_system=True)

    context = {
        'title': title,
        'eisenhower_quadrants': eisenhower_quadrants,
        'tag_categories': tag_categories,
        'total_tasks': sum(len(quadrant['tasks']) for quadrant in eisenhower_quadrants.values()),
    }

    return render(request, 'events/eisenhower_matrix.html', context)

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


@login_required
def project_templates(request):
    """
    Vista para mostrar todas las plantillas de proyectos disponibles
    """
    from .models import ProjectTemplate

    # Obtener filtros
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')

    # Base queryset
    templates = ProjectTemplate.objects.all()

    # Aplicar filtros
    if category_filter:
        templates = templates.filter(category=category_filter)

    if search_query:
        templates = templates.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Obtener categorías únicas para el filtro
    categories = ProjectTemplate.objects.values_list('category', flat=True).distinct()

    # Separar plantillas públicas y privadas
    public_templates = templates.filter(is_public=True)
    user_templates = templates.filter(created_by=request.user)

    context = {
        'title': 'Plantillas de Proyectos',
        'public_templates': public_templates,
        'user_templates': user_templates,
        'categories': categories,
        'category_filter': category_filter,
        'search_query': search_query,
    }

    return render(request, 'events/project_templates.html', context)


@login_required
def create_project_template(request):
    """
    Vista para crear una nueva plantilla de proyecto
    """
    from .models import ProjectTemplate, TemplateTask

    if request.method == 'POST':
        template_form = ProjectTemplateForm(request.POST)
        task_formset = TemplateTaskFormSet(request.POST)

        if template_form.is_valid() and task_formset.is_valid():
            try:
                with transaction.atomic():
                    # Crear la plantilla
                    template = template_form.save(commit=False)
                    template.created_by = request.user
                    template.save()

                    # Crear las tareas de plantilla
                    tasks = task_formset.save(commit=False)
                    for i, task in enumerate(tasks):
                        task.template = template
                        task.order = i + 1
                        task.save()

                    # Guardar las relaciones many-to-many
                    task_formset.save_m2m()

                    messages.success(request, f'Plantilla "{template.name}" creada exitosamente')
                    return redirect('project_template_detail', template_id=template.id)

            except Exception as e:
                messages.error(request, f'Error al crear la plantilla: {e}')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        template_form = ProjectTemplateForm()
        task_formset = TemplateTaskFormSet()

    context = {
        'title': 'Crear Plantilla de Proyecto',
        'template_form': template_form,
        'task_formset': task_formset,
    }

    return render(request, 'events/create_project_template.html', context)


@login_required
def project_template_detail(request, template_id):
    """
    Vista para mostrar los detalles de una plantilla de proyecto
    """
    from .models import ProjectTemplate

    try:
        template = ProjectTemplate.objects.get(id=template_id)

        # Verificar permisos
        if not template.is_public and template.created_by != request.user:
            messages.error(request, 'No tienes permisos para ver esta plantilla.')
            return redirect('project_templates')

        context = {
            'title': f'Plantilla: {template.name}',
            'template': template,
            'can_edit': template.created_by == request.user,
            'can_use': True,  # Cualquier usuario puede usar plantillas públicas
        }

        return render(request, 'events/project_template_detail.html', context)

    except ProjectTemplate.DoesNotExist:
        messages.error(request, 'Plantilla no encontrada.')
        return redirect('project_templates')


@login_required
def edit_project_template(request, template_id):
    """
    Vista para editar una plantilla de proyecto existente
    """
    from .models import ProjectTemplate, TemplateTask

    try:
        template = ProjectTemplate.objects.get(id=template_id)

        # Verificar permisos
        if template.created_by != request.user:
            messages.error(request, 'No tienes permisos para editar esta plantilla.')
            return redirect('project_templates')

        if request.method == 'POST':
            template_form = ProjectTemplateForm(request.POST, instance=template)
            task_formset = TemplateTaskFormSet(request.POST, instance=template)

            if template_form.is_valid() and task_formset.is_valid():
                try:
                    with transaction.atomic():
                        template_form.save()

                        # Eliminar tareas existentes y crear nuevas
                        TemplateTask.objects.filter(template=template).delete()

                        tasks = task_formset.save(commit=False)
                        for i, task in enumerate(tasks):
                            task.template = template
                            task.order = i + 1
                            task.save()

                        task_formset.save_m2m()

                        messages.success(request, f'Plantilla "{template.name}" actualizada exitosamente')
                        return redirect('project_template_detail', template_id=template.id)

                except Exception as e:
                    messages.error(request, f'Error al actualizar la plantilla: {e}')
            else:
                messages.error(request, 'Por favor, corrige los errores en el formulario.')
        else:
            template_form = ProjectTemplateForm(instance=template)
            task_formset = TemplateTaskFormSet(instance=template)

        context = {
            'title': f'Editar Plantilla: {template.name}',
            'template': template,
            'template_form': template_form,
            'task_formset': task_formset,
        }

        return render(request, 'events/edit_project_template.html', context)

    except ProjectTemplate.DoesNotExist:
        messages.error(request, 'Plantilla no encontrada.')
        return redirect('project_templates')


@login_required
def delete_project_template(request, template_id):
    """
    Vista para eliminar una plantilla de proyecto
    """
    from .models import ProjectTemplate

    try:
        template = ProjectTemplate.objects.get(id=template_id)

        # Verificar permisos
        if template.created_by != request.user:
            messages.error(request, 'No tienes permisos para eliminar esta plantilla.')
            return redirect('project_templates')

        if request.method == 'POST':
            template_name = template.name
            template.delete()

            messages.success(request, f'Plantilla "{template_name}" eliminada exitosamente')
            return redirect('project_templates')

        context = {
            'title': 'Eliminar Plantilla',
            'template': template,
        }

        return render(request, 'events/delete_project_template.html', context)

    except ProjectTemplate.DoesNotExist:
        messages.error(request, 'Plantilla no encontrada.')
        return redirect('project_templates')


@login_required
def use_project_template(request, template_id):
    """
    Vista para usar una plantilla para crear un nuevo proyecto
    """
    from .models import ProjectTemplate, Project, Task, TaskStatus
    from .forms import CreateNewProject

    try:
        template = ProjectTemplate.objects.get(id=template_id)

        # Verificar permisos
        if not template.is_public and template.created_by != request.user:
            messages.error(request, 'No tienes permisos para usar esta plantilla.')
            return redirect('project_templates')

        if request.method == 'POST':
            project_form = CreateNewProject(request.POST)

            if project_form.is_valid():
                try:
                    with transaction.atomic():
                        # Crear el proyecto
                        project = project_form.save(commit=False)
                        project.host = request.user
                        project.event = project_form.cleaned_data['event']

                        # Si no hay evento, crear uno
                        if not project.event:
                            status = Status.objects.get(status_name='Created')
                            new_event = Event.objects.create(
                                title=project_form.cleaned_data['title'],
                                event_status=status,
                                host=request.user,
                                assigned_to=request.user,
                            )
                            project.event = new_event

                        project.save()
                        project_form.save_m2m()

                        # Crear tareas basadas en la plantilla usando TaskManager
                        template_tasks = template.templatetask_set.all().order_by('order')

                        # Crear TaskManager para el usuario
                        task_manager = TaskManager(request.user)

                        for template_task in template_tasks:
                            # Usar TaskManager para crear tareas con procedimientos correctos
                            task_manager.create_task(
                                title=template_task.title,
                                description=template_task.description,
                                important=False,
                                project=project,
                                event=project.event,  # Asignar el evento del proyecto
                                task_status=None,  # Usará 'To Do' por defecto
                                assigned_to=request.user,
                                ticket_price=0.07
                            )

                        messages.success(request,
                            f'Proyecto "{project.title}" creado exitosamente usando la plantilla "{template.name}"')
                        return redirect('projects', project_id=project.id)

                except Exception as e:
                    messages.error(request, f'Error al crear el proyecto: {e}')
            else:
                messages.error(request, 'Por favor, corrige los errores en el formulario.')
        else:
            # Pre-llenar el formulario con datos de la plantilla
            initial_data = {
                'title': f"{template.name} - {timezone.now().strftime('%Y-%m-%d')}",
                'description': template.description,
            }
            project_form = CreateNewProject(initial=initial_data)

        context = {
            'title': f'Usar Plantilla: {template.name}',
            'template': template,
            'project_form': project_form,
            'task_count': template.templatetask_set.count(),
        }

        return render(request, 'events/use_project_template.html', context)

    except ProjectTemplate.DoesNotExist:
        messages.error(request, 'Plantilla no encontrada.')
        return redirect('project_templates')


@login_required
def task_dependencies(request, task_id=None):
    """
    Vista para gestionar dependencias entre tareas
    """
    from .models import TaskDependency

    # Debug logs para identificar el problema de URL
    logger = logging.getLogger(__name__)
    logger.info(f"[task_dependencies] Request method: {request.method}")
    logger.info(f"[task_dependencies] Task ID parameter: {task_id}")
    logger.info(f"[task_dependencies] Request path: {request.path}")
    logger.info(f"[task_dependencies] Request GET parameters: {request.GET}")
    logger.info(f"[task_dependencies] Request POST parameters: {request.POST}")

    if task_id:
        # Ver dependencias de una tarea específica
        logger.info(f"[task_dependencies] Processing specific task ID: {task_id}")
        try:
            task = Task.objects.get(id=task_id)
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
    else:
        # Vista general de todas las dependencias
        logger.info("[task_dependencies] Processing general dependencies view (no task_id)")
        all_dependencies = TaskDependency.objects.all().order_by('-created_at')
        logger.info(f"[task_dependencies] Found {all_dependencies.count()} total dependencies")

        context = {
            'title': 'Gestión de Dependencias',
            'all_dependencies': all_dependencies,
        }
        return render(request, 'events/task_dependencies_list.html', context)


@login_required
def create_task_dependency(request, task_id):
    """
    Vista para crear una nueva dependencia entre tareas
    """
    from .models import TaskDependency

    try:
        task = Task.objects.get(id=task_id)
        if not (task.host == request.user or request.user in task.attendees.all()):
            messages.error(request, 'No tienes permisos para gestionar dependencias de esta tarea.')
            return redirect('tasks')
    except Task.DoesNotExist:
        messages.error(request, 'Tarea no encontrada.')
        return redirect('tasks')

    if request.method == 'POST':
        depends_on_id = request.POST.get('depends_on')
        dependency_type = request.POST.get('dependency_type')

        try:
            depends_on_task = Task.objects.get(id=depends_on_id)

            # Validar que no se cree una dependencia circular
            if task_id == depends_on_id:
                messages.error(request, 'Una tarea no puede depender de sí misma.')
                return redirect('task_dependencies_list', task_id=task_id)

            # Verificar si ya existe esta dependencia
            existing = TaskDependency.objects.filter(
                task=task,
                depends_on=depends_on_task
            ).exists()

            if existing:
                messages.error(request, 'Esta dependencia ya existe.')
                return redirect('task_dependencies_list', task_id=task_id)

            # Crear la dependencia
            TaskDependency.objects.create(
                task=task,
                depends_on=depends_on_task,
                dependency_type=dependency_type
            )

            messages.success(request, f'Dependencia creada: "{task.title}" depende de "{depends_on_task.title}"')
            return redirect('task_dependencies_list', task_id=task_id)

        except Task.DoesNotExist:
            messages.error(request, 'La tarea objetivo no existe.')
        except Exception as e:
            messages.error(request, f'Error al crear la dependencia: {e}')

    # Obtener tareas disponibles para dependencias
    available_tasks = Task.objects.filter(
        project=task.project
    ).exclude(id=task_id).order_by('title')

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
    from .models import TaskDependency

    try:
        dependency = TaskDependency.objects.get(id=dependency_id)
        task_id = dependency.task.id

        if not (dependency.task.host == request.user or request.user in dependency.task.attendees.all()):
            messages.error(request, 'No tienes permisos para eliminar esta dependencia.')
            return redirect('tasks')

        if request.method == 'POST':
            task_title = dependency.task.title
            depends_on_title = dependency.depends_on.title

            dependency.delete()

            messages.success(request, f'Dependencia eliminada: "{task_title}" ya no depende de "{depends_on_title}"')
            return redirect('task_dependencies_list', task_id=task_id)

        context = {
            'title': 'Eliminar Dependencia',
            'dependency': dependency,
        }
        return render(request, 'events/delete_task_dependency.html', context)

    except TaskDependency.DoesNotExist:
        messages.error(request, 'Dependencia no encontrada.')
        return redirect('tasks')


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

    # Obtener todas las dependencias relacionadas (hacia adelante y hacia atrás)
    from .models import TaskDependency

    def get_all_dependencies(task, visited=None):
        """Obtener todas las dependencias recursivamente"""
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
            dependencies.extend(get_all_dependencies(dep.task, visited))

        # Tareas de las que esta tarea depende
        depending_on = TaskDependency.objects.filter(task=task)
        for dep in depending_on:
            dependencies.append({
                'task': dep.depends_on,
                'type': 'depends_on',
                'dependency_type': dep.dependency_type
            })
            # Recursivamente obtener dependencias de las tareas que son dependencias
            dependencies.extend(get_all_dependencies(dep.depends_on, visited))

        return dependencies

    all_dependencies = get_all_dependencies(task)

    # Crear estructura para el gráfico
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
    add_task_to_graph(task)

    # Añadir todas las tareas relacionadas
    for dep in all_dependencies:
        add_task_to_graph(dep['task'])

        # Crear arista
        if dep['type'] == 'blocking':
            # Esta tarea bloquea a dep['task']
            edges.append({
                'from': task.id,
                'to': dep['task'].id,
                'label': dep['dependency_type'].replace('_', ' ').title(),
                'type': 'blocking'
            })
        else:
            # Esta tarea depende de dep['task']
            edges.append({
                'from': dep['task'].id,
                'to': task.id,
                'label': dep['dependency_type'].replace('_', ' ').title(),
                'type': 'depends_on'
            })

    context = {
        'title': f'Gráfico de Dependencias: {task.title}',
        'task': task,
        'nodes': nodes,
        'edges': edges,
    }

    return render(request, 'events/task_dependency_graph.html', context)


@login_required
def reminders_dashboard(request):
    """
    Vista principal del dashboard de recordatorios
    """
    # Obtener recordatorios del usuario
    user_reminders = Reminder.objects.filter(created_by=request.user)

    # Separar por estado
    pending_reminders = user_reminders.filter(is_sent=False, remind_at__gte=timezone.now())
    sent_reminders = user_reminders.filter(is_sent=True)
    overdue_reminders = user_reminders.filter(is_sent=False, remind_at__lt=timezone.now())

    # Obtener recordatorios para hoy
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
    today_end = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))

    today_reminders = user_reminders.filter(
        remind_at__range=(today_start, today_end),
        is_sent=False
    )

    # Estadísticas
    total_reminders = user_reminders.count()
    pending_count = pending_reminders.count()
    sent_count = sent_reminders.count()
    overdue_count = overdue_reminders.count()

    context = {
        'title': 'Dashboard de Recordatorios',
        'user_reminders': user_reminders,
        'pending_reminders': pending_reminders,
        'sent_reminders': sent_reminders,
        'overdue_reminders': overdue_reminders,
        'today_reminders': today_reminders,
        'total_reminders': total_reminders,
        'pending_count': pending_count,
        'sent_count': sent_count,
        'overdue_count': overdue_count,
    }

    return render(request, 'events/reminders_dashboard.html', context)

@login_required
def create_reminder(request):
    """
    Vista para crear un nuevo recordatorio
    """
    from .forms import ReminderForm

    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.created_by = request.user
            reminder.save()

            messages.success(request, f'Recordatorio "{reminder.title}" creado exitosamente')
            return redirect('reminders_dashboard')


    else:
        form = ReminderForm()

    context = {
        'title': 'Crear Recordatorio',
        'form': form,
    }

    return render(request, 'events/create_reminder.html', context)


@login_required
def check_new_emails_api(request):
    """
    API endpoint para verificar y procesar correos nuevos manualmente
    """
    from .utils import check_root_access

    # Verificar permisos usando la misma lógica que el dashboard root
    if not check_root_access(request.user):
        return JsonResponse({'success': False, 'error': 'No tienes permisos para acceder a esta funcionalidad'})

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        from django.core.management import call_command
        from io import StringIO

        # Capturar la salida del comando
        output = StringIO()
        call_command('process_cx_emails', stdout=output, max_emails=20)

        # Analizar la salida para extraer información
        output_str = output.getvalue()
        processed_count = 0

        # Buscar el número de emails procesados en la salida
        import re
        match = re.search(r'Processed (\d+) CX emails successfully', output_str)
        if match:
            processed_count = int(match.group(1))

        return JsonResponse({
            'success': True,
            'processed_count': processed_count,
            'message': f'Se procesaron {processed_count} emails CX exitosamente',
            'details': output_str
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def activate_bot(request):
    """
    Vista para activar bots que simulan tareas usando credenciales de usuarios reales
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    # Verificar permisos - solo administradores pueden activar bots
    if not (request.user.is_superuser or
            (hasattr(request.user, 'cv') and hasattr(request.user.cv, 'role') and
             request.user.cv.role in ['SU', 'ADMIN', 'GTD_ANALYST'])):
        return JsonResponse({'success': False, 'error': 'No tienes permisos para activar bots'})

    try:
        bot_id = request.POST.get('bot_id')
        selected_tasks = request.POST.getlist('tasks[]')

        if not bot_id:
            return JsonResponse({'success': False, 'error': 'Bot requerido'})

        if not selected_tasks:
            return JsonResponse({'success': False, 'error': 'Debes seleccionar al menos una tarea'})

        # Definir configuración de bots
        bot_configs = {
            'project_bot': {
                'name': 'Bot de Proyectos',
                'tasks': {
                    'create_project': 'create_project_simulation',
                    'manage_tasks': 'manage_tasks_simulation',
                    'generate_reports': 'generate_reports_simulation',
                    'simulate_inbox': 'simulate_inbox_simulation'
                }
            },
            'teacher_bot': {
                'name': 'Bot Profesor',
                'tasks': {
                    'create_course': 'create_course_simulation',
                    'create_lesson': 'create_lesson_simulation',
                    'create_content': 'create_content_simulation',
                    'manage_students': 'manage_students_simulation'
                }
            },
            'client_bot': {
                'name': 'Bot Cliente',
                'tasks': {
                    'simulate_inbox': 'simulate_client_inbox',
                    'send_emails': 'simulate_email_sending',
                    'create_tickets': 'create_support_tickets',
                    'simulate_calls': 'simulate_phone_calls'
                }
            }
        }

        if bot_id not in bot_configs:
            return JsonResponse({'success': False, 'error': 'Bot no válido'})

        bot_config = bot_configs[bot_id]
        executed_tasks = []

        # Ejecutar cada tarea seleccionada
        for task_id in selected_tasks:
            if task_id in bot_config['tasks']:
                task_function_name = bot_config['tasks'][task_id]
                try:
                    # Ejecutar la función de simulación correspondiente
                    result = globals()[task_function_name](request.user)
                    executed_tasks.append({
                        'task_id': task_id,
                        'status': 'success',
                        'result': result
                    })
                except Exception as e:
                    executed_tasks.append({
                        'task_id': task_id,
                        'status': 'error',
                        'error': str(e)
                    })

        # Registrar la activación del bot
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Bot {bot_config['name']} activado por {request.user.username}. Tareas ejecutadas: {len(executed_tasks)}")

        return JsonResponse({
            'success': True,
            'message': f'Bot {bot_config["name"]} activado exitosamente',
            'executed_tasks': executed_tasks,
            'bot_name': bot_config['name']
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def process_cx_emails_api(request):
    """
    API endpoint para procesar emails CX manualmente (similar a check_new_emails pero más específico)
    """
    from .utils import check_root_access

    # Verificar permisos usando la misma lógica que el dashboard root
    if not check_root_access(request.user):
        return JsonResponse({'success': False, 'error': 'No tienes permisos para acceder a esta funcionalidad'})

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        from django.core.management import call_command
        from io import StringIO

        # Ejecutar el comando de procesamiento CX
        output = StringIO()
        call_command('process_cx_emails', stdout=output, max_emails=50, dry_run=False)

        # Analizar la salida
        output_str = output.getvalue()
        processed_count = 0

        # Extraer información de la salida
        import re
        match = re.search(r'Processed (\d+) CX emails successfully', output_str)
        if match:
            processed_count = int(match.group(1))

        return JsonResponse({
            'success': True,
            'processed_count': processed_count,
            'message': f'Procesamiento CX completado: {processed_count} emails procesados',
            'details': output_str
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
        
        
# ============================================================================
# TASK SCHEDULING SYSTEM (Programaciones recurrentes de tareas)
# ============================================================================

@login_required
def task_schedules(request):
    """
    Vista para listar todas las programaciones recurrentes del usuario
    """
    from .models import TaskSchedule

    # Obtener programaciones del usuario
    user_schedules = TaskSchedule.objects.filter(
        host=request.user
    ).select_related('task').order_by('-created_at')

    # Estadísticas
    total_schedules = user_schedules.count()
    active_schedules = user_schedules.filter(is_active=True).count()
    inactive_schedules = total_schedules - active_schedules

    # Próximas ocurrencias para cada programación
    schedules_with_next = []
    for schedule in user_schedules:
        next_occurrence = schedule.get_next_occurrence()
        schedules_with_next.append({
            'schedule': schedule,
            'next_occurrence': next_occurrence
        })

    context = {
        'title': 'Programaciones Recurrentes',
        'schedules': schedules_with_next,
        'total_schedules': total_schedules,
        'active_schedules': active_schedules,
        'inactive_schedules': inactive_schedules,
    }

    return render(request, 'events/task_schedules.html', context)


@login_required
def create_task_schedule(request):
    """
    Vista para crear una nueva programación recurrente
    """
    from .forms import TaskScheduleForm
    from .models import TaskSchedule

    if request.method == 'POST':
        form = TaskScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            schedule = form.save()
            messages.success(request, f'Programación creada exitosamente para "{schedule.task.title}"')
            return redirect('task_schedule_detail', schedule_id=schedule.id)
    else:
        form = TaskScheduleForm(user=request.user)

    context = {
        'title': 'Crear Programación Recurrente',
        'form': form,
    }

    return render(request, 'events/create_task_schedule.html', context)


@login_required
def task_schedule_detail(request, schedule_id):
    """
    Vista detallada de una programación recurrente
    """
    from .models import TaskSchedule

    try:
        schedule = TaskSchedule.objects.select_related('task').get(
            id=schedule_id,
            host=request.user
        )
    except TaskSchedule.DoesNotExist:
        messages.error(request, 'Programación no encontrada.')
        return redirect('task_schedules')

    # Generar próximas ocurrencias
    next_occurrences = schedule.generate_occurrences(limit=10)

    # Obtener programas creados por esta programación
    created_programs = TaskProgram.objects.filter(
        task=schedule.task,
        host=request.user,
        start_time__gte=schedule.start_date
    ).order_by('start_time')[:10]

    context = {
        'title': f'Programación: {schedule.task.title}',
        'schedule': schedule,
        'next_occurrences': next_occurrences,
        'created_programs': created_programs,
    }

    return render(request, 'events/task_schedule_detail.html', context)


from django.views.generic import UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

@login_required
def edit_task_schedule(request, schedule_id):
    """
    Vista mejorada para editar una programación recurrente con funcionalidades avanzadas
    """
    from .forms import TaskScheduleForm
    from .models import TaskSchedule, TaskProgram

    try:
        schedule = TaskSchedule.objects.select_related('task').get(id=schedule_id, host=request.user)
    except TaskSchedule.DoesNotExist:
        messages.error(request, 'Programación no encontrada.')
        return redirect('task_schedules')

    if request.method == 'POST':
        form = TaskScheduleForm(request.POST, instance=schedule, user=request.user)
        if form.is_valid():
            # Store original values for logging
            field_mapping = {'duration_hours': 'duration'}
            original_values = {}
            for field in form.changed_data:
                model_field = field_mapping.get(field, field)
                original_values[model_field] = getattr(schedule, model_field)

            # Guardar cambios
            schedule = form.save()

            # Log de cambios para auditoría
            _log_schedule_changes(schedule, form.changed_data, original_values)

            messages.success(
                request,
                f'Programación "{schedule.task.title}" actualizada exitosamente. '
                f'Se generarán {len(schedule.generate_occurrences(limit=5))} próximas ocurrencias.'
            )
            return redirect('task_schedule_detail', schedule_id=schedule.id)
        else:
            # Mejor manejo de errores
            for field, errors in form.errors.items():
                if field != '__all__':
                    messages.error(request, f'{form.fields[field].label}: {errors[0]}')
    else:
        form = TaskScheduleForm(instance=schedule, user=request.user)

    # Próximas ocurrencias para preview
    next_occurrences = schedule.generate_occurrences(limit=10)

    # Estadísticas de la programación
    created_programs_count = TaskProgram.objects.filter(
        task=schedule.task,
        host=request.user,
        start_time__gte=schedule.start_date
    ).count()

    # Programas creados recientemente
    recent_programs = TaskProgram.objects.filter(
        task=schedule.task,
        host=request.user,
        start_time__gte=schedule.start_date
    ).select_related('task__task_status').order_by('-start_time')[:5]

    context = {
        'title': f'Editar Programación: {schedule.task.title}',
        'form': form,
        'schedule': schedule,
        'next_occurrences': next_occurrences,
        'created_programs_count': created_programs_count,
        'recent_programs': recent_programs,
        'can_preview': True,
        'preview_url': reverse('task_schedule_preview', kwargs={'schedule_id': schedule.id}),
    }

    return render(request, 'events/edit_task_schedule_enhanced.html', context)
    

class TaskScheduleEditView(LoginRequiredMixin, UpdateView):
    """
    Vista mejorada basada en clases para editar programaciones recurrentes de tareas.
    Incluye funcionalidades avanzadas como preview, validación mejorada y mejor UX.
    """
    model = TaskSchedule
    form_class = None  # Se define dinámicamente
    template_name = 'events/edit_task_schedule_enhanced.html'
    context_object_name = 'schedule'

    def get_queryset(self):
        """Filtrar solo las programaciones del usuario actual"""
        return TaskSchedule.objects.filter(host=self.request.user)

    def get_form_class(self):
        """Obtener la clase del formulario dinámicamente"""
        from .forms import TaskScheduleForm
        return TaskScheduleForm

    def get_form_kwargs(self):
        """Pasar el usuario al formulario"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Añadir datos adicionales al contexto"""
        context = super().get_context_data(**kwargs)
        schedule = self.object

        # Próximas ocurrencias para preview
        next_occurrences = schedule.generate_occurrences(limit=10)

        # Estadísticas de la programación
        created_programs_count = TaskProgram.objects.filter(
            task=schedule.task,
            host=self.request.user,
            start_time__gte=schedule.start_date
        ).count()

        # Programaciones creadas recientemente
        recent_programs = TaskProgram.objects.filter(
            task=schedule.task,
            host=self.request.user,
            start_time__gte=schedule.start_date
        ).order_by('-start_time')[:5]

        context.update({
            'title': f'Editar Programación: {schedule.task.title}',
            'next_occurrences': next_occurrences,
            'created_programs_count': created_programs_count,
            'recent_programs': recent_programs,
            'can_preview': True,
            'preview_url': reverse_lazy('task_schedule_preview', kwargs={'schedule_id': schedule.id}),
        })

        return context

    def form_valid(self, form):
        """Procesar formulario válido con funcionalidades adicionales"""
        # Store original values for logging
        field_mapping = {'duration_hours': 'duration'}
        original_values = {}
        for field in form.changed_data:
            model_field = field_mapping.get(field, field)
            original_values[model_field] = getattr(form.instance, model_field)

        # Guardar cambios
        schedule = form.save()

        # Generar preview si se solicita
        if self.request.POST.get('action') == 'preview':
            # Redirigir a preview en lugar de guardar
            return redirect('task_schedule_preview', schedule_id=schedule.id)

        # Log de cambios para auditoría
        self._log_schedule_changes(schedule, form.changed_data, original_values)

        messages.success(
            self.request,
            f'Programación "{schedule.task.title}" actualizada exitosamente. '
            f'Se generarán {len(schedule.generate_occurrences(limit=5))} próximas ocurrencias.'
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        """Manejar formulario inválido con mejor feedback"""
        # Añadir contexto adicional para errores
        for field, errors in form.errors.items():
            if field != '__all__':
                messages.error(self.request, f'{form.fields[field].label}: {errors[0]}')

        return super().form_invalid(form)

    def get_success_url(self):
        """URL de éxito después de guardar"""
        return reverse_lazy('task_schedule_detail', kwargs={'schedule_id': self.object.id})

    def _log_schedule_changes(self, schedule, changed_fields, original_values=None):
        """Registrar cambios para auditoría"""
        if changed_fields:
            changes = []
            # Mapping for form fields that don't directly match model fields
            field_mapping = {
                'duration_hours': 'duration'
            }

            if original_values is None:
                original_values = {}

            for field in changed_fields:
                # Map form field to model field if necessary
                model_field = field_mapping.get(field, field)

                try:
                    old_value = original_values.get(model_field, 'N/A')
                    new_value = getattr(schedule, model_field)
                    changes.append(f"{field}: {old_value} → {new_value}")
                except AttributeError as e:
                    # Skip fields that don't exist on the model
                    print(f"Warning: Could not log change for field {field} (mapped to {model_field}): {e}")
                    continue

            # Aquí se podría guardar en un log de auditoría
            print(f"[AUDIT] Schedule {schedule.id} changed: {', '.join(changes)}")


@login_required
def task_schedule_preview(request, schedule_id):
    """
    Vista para previsualizar cambios en una programación antes de guardarlos
    """
    from .models import TaskSchedule

    try:
        schedule = TaskSchedule.objects.get(id=schedule_id, host=request.user)
    except TaskSchedule.DoesNotExist:
        messages.error(request, 'Programación no encontrada.')
        return redirect('task_schedules')

    # Simular cambios basados en POST data
    if request.method == 'POST':
        from .forms import TaskScheduleForm
        form = TaskScheduleForm(request.POST, instance=schedule, user=request.user)

        if form.is_valid():
            # Crear preview sin guardar
            preview_schedule = TaskSchedule(
                task=form.cleaned_data['task'],
                recurrence_type=form.cleaned_data['recurrence_type'],
                monday=form.cleaned_data.get('monday', False),
                tuesday=form.cleaned_data.get('tuesday', False),
                wednesday=form.cleaned_data.get('wednesday', False),
                thursday=form.cleaned_data.get('thursday', False),
                friday=form.cleaned_data.get('friday', False),
                saturday=form.cleaned_data.get('saturday', False),
                sunday=form.cleaned_data.get('sunday', False),
                start_time=form.cleaned_data['start_time'],
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data.get('end_date'),
                is_active=form.cleaned_data.get('is_active', True),
                host=request.user
            )

            # Calcular duración
            duration_hours = form.cleaned_data.get('duration_hours', 1.0)
            preview_schedule.duration = timedelta(hours=float(duration_hours))

            # Generar preview de ocurrencias
            preview_occurrences = preview_schedule.generate_occurrences(limit=15)

            context = {
                'title': f'Preview: {preview_schedule.task.title}',
                'original_schedule': schedule,
                'preview_schedule': preview_schedule,
                'preview_occurrences': preview_occurrences,
                'form_data': request.POST,
                'changes_detected': True,
            }

            return render(request, 'events/task_schedule_preview.html', context)
        else:
            messages.error(request, 'Datos inválidos para preview.')
            return redirect('edit_task_schedule', schedule_id=schedule_id)

    # GET request - mostrar preview actual
    current_occurrences = schedule.generate_occurrences(limit=10)

    context = {
        'title': f'Preview Actual: {schedule.task.title}',
        'original_schedule': schedule,
        'preview_schedule': schedule,
        'preview_occurrences': current_occurrences,
        'changes_detected': False,
    }

    return render(request, 'events/task_schedule_preview.html', context)


@login_required
def delete_task_schedule(request, schedule_id):
    """
    Vista para eliminar una programación recurrente
    """
    from .models import TaskSchedule

    try:
        schedule = TaskSchedule.objects.get(id=schedule_id, host=request.user)
    except TaskSchedule.DoesNotExist:
        messages.error(request, 'Programación no encontrada.')
        return redirect('task_schedules')

    if request.method == 'POST':
        task_title = schedule.task.title
        schedule.delete()
        messages.success(request, f'Programación eliminada: "{task_title}"')
        return redirect('task_schedules')

    context = {
        'title': 'Eliminar Programación',
        'schedule': schedule,
    }

    return render(request, 'events/delete_task_schedule.html', context)


@login_required
def generate_schedule_occurrences(request, schedule_id):
    """
    Vista para generar ocurrencias manualmente para una programación
    """
    from .models import TaskSchedule

    try:
        schedule = TaskSchedule.objects.get(id=schedule_id, host=request.user)
    except TaskSchedule.DoesNotExist:
        messages.error(request, 'Programación no encontrada.')
        return redirect('task_schedules')

    if request.method == 'POST':
        # Generar ocurrencias
        created_programs = schedule.create_task_programs()

        if created_programs:
            messages.success(request, f'Se generaron {len(created_programs)} nuevas programaciones')
        else:
            messages.info(request, 'No se generaron nuevas programaciones (ya existen o no hay fechas futuras)')

        return redirect('task_schedule_detail', schedule_id=schedule.id)

    # GET request - mostrar confirmación
    next_occurrences = schedule.generate_occurrences(limit=5)

    context = {
        'title': f'Generar Ocurrencias: {schedule.task.title}',
        'schedule': schedule,
        'next_occurrences': next_occurrences,
    }

    return render(request, 'events/generate_schedule_occurrences.html', context)



@login_required
def user_schedules_panel(request):
    """
    Panel para administrar los horarios y programaciones de todos los usuarios
    """
    # Verificar permisos de administrador
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder al panel de administración de horarios.')
        return redirect('task_schedules')

    # Filtros
    user_filter = request.GET.get('user', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')

    # Obtener todos los usuarios que tienen programaciones o programas
    users_with_schedules = User.objects.filter(
        models.Q(hosted_schedules__isnull=False) |
        models.Q(hosted_programs__isnull=False)
    ).distinct().order_by('username')

    # Aplicar filtros
    if user_filter != 'all':
        users_with_schedules = users_with_schedules.filter(id=user_filter)

    if search_query:
        users_with_schedules = users_with_schedules.filter(
            models.Q(username__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )

    # Preparar datos por usuario
    users_data = []
    for user in users_with_schedules:
        # Programaciones recurrentes del usuario
        user_schedules = TaskSchedule.objects.filter(host=user).select_related('task')

        # Aplicar filtro de estado
        if status_filter == 'active':
            user_schedules = user_schedules.filter(is_active=True)
        elif status_filter == 'inactive':
            user_schedules = user_schedules.filter(is_active=False)

        # Programas específicos del usuario
        user_programs = TaskProgram.objects.filter(host=user).select_related('task').order_by('-start_time')[:10]

        # Próximas ocurrencias para las programaciones
        schedules_with_next = []
        for schedule in user_schedules:
            next_occurrence = schedule.get_next_occurrence()
            schedules_with_next.append({
                'schedule': schedule,
                'next_occurrence': next_occurrence
            })

        # Estadísticas del usuario
        user_stats = {
            'total_schedules': user_schedules.count(),
            'active_schedules': user_schedules.filter(is_active=True).count(),
            'inactive_schedules': user_schedules.filter(is_active=False).count(),
            'total_programs': TaskProgram.objects.filter(host=user).count(),
            'weekly_schedules': user_schedules.filter(recurrence_type='weekly').count(),
            'daily_schedules': user_schedules.filter(recurrence_type='daily').count(),
            'custom_schedules': user_schedules.filter(recurrence_type='custom').count(),
        }

        users_data.append({
            'user': user,
            'schedules': schedules_with_next,
            'programs': user_programs,
            'stats': user_stats,
        })

    # Estadísticas generales
    total_stats = {
        'total_users': users_with_schedules.count(),
        'total_schedules': TaskSchedule.objects.count(),
        'active_schedules': TaskSchedule.objects.filter(is_active=True).count(),
        'total_programs': TaskProgram.objects.count(),
        'today_schedules': TaskSchedule.objects.filter(created_at__date=timezone.now().date()).count(),
        'this_week_schedules': TaskSchedule.objects.filter(created_at__gte=timezone.now() - timedelta(days=7)).count(),
    }

    context = {
        'title': 'Panel de Horarios y Programaciones',
        'users_data': users_data,
        'total_stats': total_stats,
        'user_filter': user_filter,
        'status_filter': status_filter,
        'search_query': search_query,
    }

    return render(request, 'events/user_schedules_panel.html', context)


@login_required
def schedule_admin_dashboard(request):
    """
    Panel de administración de programaciones recurrentes - Vista principal para gestionar schedules de todos los usuarios
    """
    from .models import TaskSchedule

    # Verificar permisos de administrador
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder al panel de administración de programaciones.')
        return redirect('task_schedules')

    # Filtros
    status_filter = request.GET.get('status', 'all')
    user_filter = request.GET.get('user', 'all')
    recurrence_filter = request.GET.get('recurrence', 'all')
    search_query = request.GET.get('search', '')

    # Base queryset
    schedules = TaskSchedule.objects.select_related(
        'task', 'host'
    ).prefetch_related(
        'task__task_status'
    ).order_by('-created_at')

    # Aplicar filtros
    if status_filter == 'active':
        schedules = schedules.filter(is_active=True)
    elif status_filter == 'inactive':
        schedules = schedules.filter(is_active=False)

    if user_filter != 'all':
        schedules = schedules.filter(host=user_filter)

    if recurrence_filter != 'all':
        schedules = schedules.filter(recurrence_type=recurrence_filter)

    if search_query:
        schedules = schedules.filter(
            models.Q(task__title__icontains=search_query) |
            models.Q(host__username__icontains=search_query) |
            models.Q(task__description__icontains=search_query)
        )

    # Estadísticas generales
    stats = {
        'total': TaskSchedule.objects.count(),
        'active': TaskSchedule.objects.filter(is_active=True).count(),
        'inactive': TaskSchedule.objects.filter(is_active=False).count(),
        'weekly': TaskSchedule.objects.filter(recurrence_type='weekly').count(),
        'daily': TaskSchedule.objects.filter(recurrence_type='daily').count(),
        'custom': TaskSchedule.objects.filter(recurrence_type='custom').count(),
        'today': TaskSchedule.objects.filter(created_at__date=timezone.now().date()).count(),
        'this_week': TaskSchedule.objects.filter(created_at__gte=timezone.now() - timedelta(days=7)).count(),
    }

    # Programaciones recientes
    recent_schedules = schedules[:10]

    # Próximas ocurrencias para las programaciones recientes
    schedules_with_next = []
    for schedule in recent_schedules:
        next_occurrence = schedule.get_next_occurrence()
        schedules_with_next.append({
            'schedule': schedule,
            'next_occurrence': next_occurrence
        })

    # Usuarios activos con programaciones
    active_users = User.objects.filter(
        models.Q(hosted_schedules__isnull=False)
    ).distinct().annotate(
        schedule_count=models.Count('hosted_schedules')
    ).order_by('-schedule_count')[:20]

    context = {
        'title': 'Administración de Programaciones Recurrentes',
        'schedules': schedules_with_next,
        'all_schedules': schedules,  # Para paginación si es necesario
        'stats': stats,
        'active_users': active_users,
        'status_filter': status_filter,
        'user_filter': user_filter,
        'recurrence_filter': recurrence_filter,
        'search_query': search_query,
    }

    return render(request, 'events/schedule_admin_dashboard.html', context)


@login_required
def schedule_admin_bulk_action(request):
    """
    Vista para acciones masivas en programaciones recurrentes
    """
    # Verificar permisos de administrador
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para realizar acciones masivas.')
        return redirect('schedule_admin_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        selected_schedules = request.POST.getlist('selected_schedules')

        if not selected_schedules:
            messages.error(request, 'No se seleccionaron programaciones.')
            return redirect('schedule_admin_dashboard')

        schedules = TaskSchedule.objects.filter(id__in=selected_schedules)

        if action == 'activate':
            count = schedules.update(is_active=True)
            messages.success(request, f'Se activaron {count} programaciones exitosamente.')

        elif action == 'deactivate':
            count = schedules.update(is_active=False)
            messages.success(request, f'Se desactivaron {count} programaciones exitosamente.')

        elif action == 'delete':
            if not request.user.is_superuser:
                messages.error(request, 'No tienes permiso para eliminar programaciones.')
                return redirect('schedule_admin_dashboard')

            count = schedules.count()
            schedules.delete()
            messages.success(request, f'Se eliminaron {count} programaciones exitosamente.')

        elif action == 'generate_occurrences':
            total_created = 0
            for schedule in schedules:
                created_programs = schedule.create_task_programs()
                total_created += len(created_programs)
            messages.success(request, f'Se generaron {total_created} nuevas programaciones.')

        else:
            messages.error(request, 'Acción no válida.')

    return redirect('schedule_admin_dashboard')




@login_required
def create_reminder(request):
    """
    Vista para crear un nuevo recordatorio
    """
    from .forms import ReminderForm

    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.created_by = request.user
            reminder.save()

            messages.success(request, f'Recordatorio "{reminder.title}" creado exitosamente')
            return redirect('reminders_dashboard')


    else:
        form = ReminderForm()

    context = {
        'title': 'Crear Recordatorio',
        'form': form,
    }

    return render(request, 'events/create_reminder.html', context)


@login_required
def unified_dashboard(request):
    """
    Dashboard unificado que integra todas las herramientas de productividad
    """
    from django.db.models import Q, Count
    from datetime import datetime, timedelta

    # Obtener datos del usuario
    user = request.user

    # Estadísticas generales
    today = timezone.now().date()
    this_week = today - timedelta(days=7)

    # Tareas del usuario
    user_tasks = Task.objects.filter(
        Q(host=user) | Q(assigned_to=user)
    ).select_related('task_status', 'project', 'event')

    # Proyectos del usuario
    user_projects = Project.objects.filter(
        Q(host=user) | Q(assigned_to=user) | Q(attendees=user)
    ).distinct().select_related('project_status', 'event')

    # Eventos del usuario
    user_events = Event.objects.filter(
        Q(host=user) | Q(assigned_to=user) | Q(attendees=user)
    ).distinct().select_related('event_status')

    # Estadísticas de tareas
    task_stats = {
        'total': user_tasks.count(),
        'completed': user_tasks.filter(task_status__status_name='Completed').count(),
        'in_progress': user_tasks.filter(task_status__status_name='In Progress').count(),
        'pending': user_tasks.filter(task_status__status_name='To Do').count(),
        'overdue': user_tasks.filter(
            Q(updated_at__lt=timezone.now() - timedelta(days=3)) &
            ~Q(task_status__status_name='Completed')
        ).count()
    }

    # Estadísticas de proyectos
    project_stats = {
        'total': user_projects.count(),
        'completed': user_projects.filter(project_status__status_name='Completed').count(),
        'in_progress': user_projects.filter(project_status__status_name='In Progress').count(),
        'pending': user_projects.filter(project_status__status_name='Created').count(),
    }

    # Estadísticas de eventos
    event_stats = {
        'total': user_events.count(),
        'completed': user_events.filter(event_status__status_name='Completed').count(),
        'in_progress': user_events.filter(event_status__status_name='In Progress').count(),
        'upcoming': user_events.filter(
            Q(updated_at__gte=this_week) &
            ~Q(event_status__status_name='Completed')
        ).count()
    }

    # Actividad reciente (últimos 7 días)
    recent_tasks = user_tasks.filter(updated_at__gte=this_week)[:5]
    recent_projects = user_projects.filter(updated_at__gte=this_week)[:5]
    recent_events = user_events.filter(updated_at__gte=this_week)[:5]

    # Items del inbox GTD
    inbox_items = InboxItem.objects.filter(created_by=user, is_processed=False)[:5]

    # Recordatorios próximos
    upcoming_reminders = Reminder.objects.filter(
        created_by=user,
        is_sent=False,
        remind_at__gte=timezone.now(),
        remind_at__lte=timezone.now() + timedelta(days=7)
    ).order_by('remind_at')[:5]

    # Tareas prioritarias (importantes y urgentes)
    priority_tasks = user_tasks.filter(
        Q(important=True) &
        Q(task_status__status_name__in=['To Do', 'In Progress'])
    ).order_by('-important', '-updated_at')[:5]

    # Proyectos activos
    active_projects = user_projects.filter(
        project_status__status_name__in=['In Progress', 'Created']
    ).order_by('-updated_at')[:5]

    # URLs de acceso rápido
    quick_access = {
        'kanban': {'url': 'kanban_board', 'title': 'Kanban Board', 'icon': 'bi-kanban', 'color': 'primary'},
        'eisenhower': {'url': 'eisenhower_matrix', 'title': 'Eisenhower Matrix', 'icon': 'bi-grid-3x3', 'color': 'warning'},
        'inbox': {'url': 'inbox', 'title': 'GTD Inbox', 'icon': 'bi-inbox', 'color': 'info'},
        'templates': {'url': 'project_templates', 'title': 'Project Templates', 'icon': 'bi-file-earmark-plus', 'color': 'success'},
        'reminders': {'url': 'reminders_dashboard', 'title': 'Reminders', 'icon': 'bi-bell', 'color': 'danger'},
        'dependencies': {'url': 'task_dependencies_list', 'title': 'Task Dependencies', 'icon': 'bi-link', 'color': 'secondary'},
    }

    # Agregar panel administrativo de programaciones si el usuario es admin
    if request.user.is_superuser:
        quick_access['schedule_admin'] = {
            'url': 'schedule_admin_dashboard',
            'title': 'Admin Programaciones',
            'icon': 'bi-calendar-check',
            'color': 'dark'
        }

    context = {
        'title': 'Dashboard Unificado de Productividad',

        # Estadísticas
        'task_stats': task_stats,
        'project_stats': project_stats,
        'event_stats': event_stats,

        # Datos recientes
        'recent_tasks': recent_tasks,
        'recent_projects': recent_projects,
        'recent_events': recent_events,

        # Herramientas específicas
        'inbox_items': inbox_items,
        'upcoming_reminders': upcoming_reminders,
        'priority_tasks': priority_tasks,
        'active_projects': active_projects,

        # URLs de acceso rápido
        'quick_access': quick_access,
    }

    return render(request, 'events/unified_dashboard.html', context)


@login_required
def edit_reminder(request, reminder_id):
    """
    Vista para editar un recordatorio existente
    """
    from .forms import ReminderForm

    try:
        reminder = Reminder.objects.get(id=reminder_id, created_by=request.user)
    except Reminder.DoesNotExist:
        messages.error(request, 'Recordatorio no encontrado.')
        return redirect('reminders_dashboard')

    if request.method == 'POST':
        form = ReminderForm(request.POST, instance=reminder)
        if form.is_valid():
            form.save()
            messages.success(request, f'Recordatorio "{reminder.title}" actualizado exitosamente')
            return redirect('reminders_dashboard')
    else:
        form = ReminderForm(instance=reminder)

    context = {
        'title': 'Editar Recordatorio',
        'form': form,
        'reminder': reminder,
    }

    return render(request, 'events/edit_reminder.html', context)


@login_required
def delete_reminder(request, reminder_id):
    """
    Vista para eliminar un recordatorio
    """
    try:
        reminder = Reminder.objects.get(id=reminder_id, created_by=request.user)
    except Reminder.DoesNotExist:
        messages.error(request, 'Recordatorio no encontrado.')
        return redirect('reminders_dashboard')

    if request.method == 'POST':
        reminder_title = reminder.title
        reminder.delete()
        messages.success(request, f'Recordatorio "{reminder_title}" eliminado exitosamente')
        return redirect('reminders_dashboard')

    context = {
        'title': 'Eliminar Recordatorio',
        'reminder': reminder,
    }

    return render(request, 'events/delete_reminder.html', context)


@login_required
def mark_reminder_sent(request, reminder_id):
    """
    API endpoint para marcar un recordatorio como enviado
    """
    if request.method == 'POST':
        try:
            reminder = Reminder.objects.get(id=reminder_id, created_by=request.user)
            reminder.is_sent = True
            reminder.save()

            return JsonResponse({
                'success': True,
                'message': 'Recordatorio marcado como enviado'
            })
        except Reminder.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Recordatorio no encontrado'
            })

    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })


@login_required
def bulk_reminder_action(request):
    """
    Vista para acciones masivas en recordatorios
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_reminders = request.POST.getlist('selected_reminders')

        if not selected_reminders:
            messages.error(request, 'No se seleccionaron recordatorios.')
            return redirect('reminders_dashboard')

        reminders = Reminder.objects.filter(id__in=selected_reminders, created_by=request.user)

        if action == 'mark_sent':
            count = reminders.update(is_sent=True)
            messages.success(request, f'Se marcaron {count} recordatorio(s) como enviados.')

        elif action == 'delete':
            count = reminders.count()
            reminders.delete()
            messages.success(request, f'Se eliminaron {count} recordatorio(s).')

        elif action == 'duplicate':
            for reminder in reminders:
                Reminder.objects.create(
                    title=f"{reminder.title} (Copia)",
                    description=reminder.description,
                    remind_at=reminder.remind_at,
                    task=reminder.task,
                    project=reminder.project,
                    event=reminder.event,
                    created_by=request.user,
                    reminder_type=reminder.reminder_type
                )
            messages.success(request, f'Se duplicaron {count} recordatorio(s).')

# Funciones helper movidas a módulos separados:
# - check_root_access -> events.utils.dashboard_utils
# - get_responsive_grid_classes -> events.utils.dashboard_utils
# - _get_user_info, _get_profile_info, _get_player_info -> events.services.dashboard_service


@login_required
def root(request):
    """
    Vista raíz refactorizada con servicios modulares y mejor mantenibilidad
    """
    from .services.dashboard_service import RootDashboardService
    from .utils import check_root_access, get_responsive_grid_classes, log_dashboard_access

    # Verificar acceso usando utilidad centralizada
    if not check_root_access(request.user):
        messages.error(request, 'No tienes permisos suficientes para acceder al panel root.')
        return redirect('dashboard')

    # Registrar acceso para auditoría
    log_dashboard_access(request.user, 'root_dashboard_access')

    try:
        # Usar el servicio refactorizado para obtener todos los datos
        dashboard = RootDashboardService(request.user, request)
        context = dashboard.get_dashboard_data()

        # Definir bots disponibles con sus tareas predefinidas
        available_bots = [
            {
                'id': 'project_bot',
                'name': 'Bot de Proyectos',
                'description': 'Simula gestión completa de proyectos',
                'icon': 'bi-folder-plus',
                'color': 'primary',
                'tasks': [
                    {'id': 'create_project', 'name': 'Crear Proyecto', 'description': 'Crea un nuevo proyecto con estructura completa'},
                    {'id': 'manage_tasks', 'name': 'Gestionar Tareas', 'description': 'Asigna y administra tareas del proyecto'},
                    {'id': 'generate_reports', 'name': 'Generar Reportes', 'description': 'Crea reportes de progreso del proyecto'},
                    {'id': 'simulate_inbox', 'name': 'Simular Inbox', 'description': 'Crea items de inbox relacionados con el proyecto'}
                ]
            },
            {
                'id': 'teacher_bot',
                'name': 'Bot Profesor',
                'description': 'Simula creación y gestión de cursos educativos',
                'icon': 'bi-mortarboard',
                'color': 'success',
                'tasks': [
                    {'id': 'create_course', 'name': 'Crear Curso', 'description': 'Crea un nuevo curso con estructura básica'},
                    {'id': 'create_lesson', 'name': 'Crear Lección', 'description': 'Añade lecciones al curso'},
                    {'id': 'create_content', 'name': 'Crear Contenido', 'description': 'Genera secciones de contenido educativo'},
                    {'id': 'manage_students', 'name': 'Gestionar Estudiantes', 'description': 'Simula gestión de estudiantes inscritos'}
                ]
            },
            {
                'id': 'client_bot',
                'name': 'Bot Cliente',
                'description': 'Simula interacciones y consultas de clientes',
                'icon': 'bi-person-gear',
                'color': 'info',
                'tasks': [
                    {'id': 'simulate_inbox', 'name': 'Simular Inbox', 'description': 'Crea consultas y tickets de soporte'},
                    {'id': 'send_emails', 'name': 'Enviar Emails', 'description': 'Simula envío de correos electrónicos'},
                    {'id': 'create_tickets', 'name': 'Crear Tickets', 'description': 'Genera tickets de soporte técnico'},
                    {'id': 'simulate_calls', 'name': 'Simular Llamadas', 'description': 'Crea registros de llamadas telefónicas'}
                ]
            }
        ]

        # Añadir elementos finales del contexto
        import json
        context.update({
            'title': 'Root Dashboard',
            'page_title': 'Root Dashboard',
            'css_classes': get_responsive_grid_classes(),
            'available_bots': available_bots,
            'available_bots_json': json.dumps(available_bots),
        })

        return render(request, 'events/root.html', context)

    except Exception as e:
        # Manejo de errores mejorado
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in root dashboard for user {request.user.username}: {str(e)}", exc_info=True)
        messages.error(request, 'Error al cargar el dashboard. Contacte al administrador.')
        return redirect('dashboard')


@login_required
def root_bulk_actions(request):
    """
    Vista para manejar acciones masivas desde el panel root
    """
    from .utils.dashboard_utils import check_root_access

    if not check_root_access(request.user):
        return JsonResponse({'success': False, 'error': 'No tienes permisos suficientes'})

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    action = request.POST.get('action')
    selected_items = request.POST.getlist('selected_items[]')

    # Validación básica de entrada
    if not action:
        return JsonResponse({'success': False, 'error': 'Acción requerida'})

    if not selected_items:
        return JsonResponse({'success': False, 'error': 'No se seleccionaron items'})

    # Limitar número máximo de items por acción para prevenir abuso
    if len(selected_items) > 50:
        return JsonResponse({'success': False, 'error': 'Demasiados items seleccionados (máximo 50)'})

    # Logging para auditoría
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"User {request.user.username} performing bulk action '{action}' on {len(selected_items)} items")

    try:
        items = InboxItem.objects.filter(id__in=selected_items)

        if action == 'mark_processed':
            count = 0
            for item in items:
                if not item.is_processed:
                    item.is_processed = True
                    item.processed_at = timezone.now()
                    item.save()
                    count += 1

                    # Registrar en historial
                    InboxItemHistory.objects.create(
                        inbox_item=item,
                        user=request.user,
                        action='bulk_mark_processed',
                        new_values={'processed_at': item.processed_at.isoformat()}
                    )

            return JsonResponse({
                'success': True,
                'message': f'Se marcaron {count} item(s) como procesados',
                'count': count
            })

        elif action == 'mark_unprocessed':
            count = 0
            for item in items:
                if item.is_processed:
                    item.is_processed = False
                    item.processed_at = None
                    item.save()
                    count += 1

                    # Registrar en historial
                    InboxItemHistory.objects.create(
                        inbox_item=item,
                        user=request.user,
                        action='bulk_mark_unprocessed',
                        old_values={'processed_at': item.processed_at.isoformat() if item.processed_at else None}
                    )

            return JsonResponse({
                'success': True,
                'message': f'Se marcaron {count} item(s) como no procesados',
                'count': count
            })

        elif action == 'change_priority':
            new_priority = request.POST.get('new_priority')
            if not new_priority or new_priority not in ['alta', 'media', 'baja']:
                return JsonResponse({'success': False, 'error': 'Prioridad inválida'})

            count = items.update(priority=new_priority)

            # Registrar en historial para cada item
            for item in items:
                InboxItemHistory.objects.create(
                    inbox_item=item,
                    user=request.user,
                    action='bulk_change_priority',
                    old_values={'priority': item.priority},
                    new_values={'priority': new_priority}
                )

            return JsonResponse({
                'success': True,
                'message': f'Se cambió la prioridad de {count} item(s) a {new_priority}',
                'count': count
            })

        elif action == 'assign_to_user':
            user_id = request.POST.get('user_id')
            if not user_id:
                return JsonResponse({'success': False, 'error': 'ID de usuario requerido'})

            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Usuario no encontrado'})

            count = items.update(assigned_to=target_user)

            # Registrar en historial para cada item
            for item in items:
                InboxItemHistory.objects.create(
                    inbox_item=item,
                    user=request.user,
                    action='bulk_assign_user',
                    old_values={'assigned_to': item.assigned_to.username if item.assigned_to else None},
                    new_values={'assigned_to': target_user.username}
                )

            return JsonResponse({
                'success': True,
                'message': f'Se asignaron {count} item(s) al usuario {target_user.username}',
                'count': count
            })

        elif action == 'change_category':
            new_category = request.POST.get('new_category')
            if not new_category:
                return JsonResponse({'success': False, 'error': 'Categoría requerida'})

            count = items.update(gtd_category=new_category)

            # Registrar en historial para cada item
            for item in items:
                InboxItemHistory.objects.create(
                    inbox_item=item,
                    user=request.user,
                    action='bulk_change_category',
                    old_values={'gtd_category': item.gtd_category},
                    new_values={'gtd_category': new_category}
                )

            return JsonResponse({
                'success': True,
                'message': f'Se cambió la categoría de {count} item(s) a {new_category}',
                'count': count
            })

        elif action == 'delegate':
            delegate_user_id = request.POST.get('delegate_user_id')
            if not delegate_user_id:
                return JsonResponse({'success': False, 'error': 'Usuario destino requerido'})

            try:
                delegate_user = User.objects.get(id=delegate_user_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Usuario destino no encontrado'})

            # Verificar que el usuario destino esté activo
            if not delegate_user.is_active:
                return JsonResponse({'success': False, 'error': 'El usuario destino no está activo'})

            # Verificar permisos para delegar cada item
            # Permitir delegación si es superusuario o tiene rol admin
            user_can_delegate = (request.user.is_superuser or
                                (hasattr(request.user, 'cv') and
                                 hasattr(request.user.cv, 'role') and
                                 request.user.cv.role in ['SU', 'ADMIN', 'GTD_ANALYST']))

            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"DEBUG DELEGATION: User {request.user.username}, is_superuser: {request.user.is_superuser}")
            logger.info(f"DEBUG DELEGATION: has_cv: {hasattr(request.user, 'cv')}")
            if hasattr(request.user, 'cv'):
                logger.info(f"DEBUG DELEGATION: User role: {getattr(request.user.cv, 'role', 'NO_ROLE')}")
            logger.info(f"DEBUG DELEGATION: user_can_delegate: {user_can_delegate}")

            for item in items:
                # Solo permitir delegar si el usuario es el creador del item o puede delegar
                can_delegate_item = item.created_by == request.user or user_can_delegate
                logger.info(f"DEBUG DELEGATION: Item '{item.title}', created_by: {item.created_by.username}, can_delegate_item: {can_delegate_item}")

                if not can_delegate_item:
                    return JsonResponse({
                        'success': False,
                        'error': f'No tienes permisos para delegar el item "{item.title}". Usuario: {request.user.username}, is_superuser: {request.user.is_superuser}, Rol detectado: {getattr(request.user.cv, "role", "SIN_ROL")}'
                    })

            count = 0
            for item in items:
                old_assigned = item.assigned_to
                item.assigned_to = delegate_user
                item.save(update_fields=['assigned_to'])
                count += 1

                # Registrar en historial
                InboxItemHistory.objects.create(
                    inbox_item=item,
                    user=request.user,
                    action='bulk_delegated',
                    old_values={'assigned_to': old_assigned.username if old_assigned else None},
                    new_values={
                        'assigned_to': delegate_user.username,
                        'delegation_method': 'bulk_action',
                        'delegated_by': request.user.username
                    }
                )

            return JsonResponse({
                'success': True,
                'message': f'Se delegaron {count} item(s) al usuario {delegate_user.username}',
                'count': count,
                'delegate_user': delegate_user.username
            })

        elif action == 'delete':
            count = items.count()
            items.delete()

            return JsonResponse({
                'success': True,
                'message': f'Se eliminaron {count} item(s)',
                'count': count
            })

        else:
            return JsonResponse({'success': False, 'error': 'Acción no válida'})

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })



