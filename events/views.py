# Standard Library Imports
from datetime import datetime, timedelta, time
from decimal import Decimal
import csv
from collections import defaultdict

# Django Imports
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum, Count, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate
from django.http import Http404, HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from difflib import SequenceMatcher
import re

# Local Imports
from .management.utils import (
    add_credits_to_user,
)
from .management.event_manager import EventManager
from .management.project_manager import ProjectManager
from .management.task_manager import TaskManager
from .models import (
    Classification, Event, EventAttendee, ProjectStatus,
    TaskStatus, Project, Status, Task, EventState, TaskState,
    TaskSchedule, TaskProgram, ProjectTemplate, TemplateTask, InboxItem, Reminder,
    TagCategory, Tag, TaskDependency, InboxItemClassification,
    InboxItemAuthorization, InboxItemHistory
)
from .forms import (
    CreateNewEvent, CreateNewProject, CreateNewTask, EditClassificationForm,
    EventStatusForm, TaskStatusForm, ProjectStatusForm,
    ProjectTemplateForm, TemplateTaskForm, TemplateTaskFormSet
)

def event_assign(request, event_id=None):
    """
    Vista para asignar proyectos y tareas a un evento específico.
    Si no se proporciona un event_id, se muestra una lista de eventos disponibles.
    """
    title = "Event Assign"
    
    try:
        # Obtener los estados utilizando la función statuses_get
        event_statuses, project_statuses, task_statuses = statuses_get()

        if event_id:
            # Obtener el evento específico utilizando EventManager
            event_manager = EventManager(request.user)
            event_data = event_manager.get_event_by_id(event_id)
            
            if not event_data:
                messages.error(request, 'El evento no existe.')
                return redirect('index')

            # Obtener los proyectos y tareas disponibles utilizando ProjectManager y TaskManager
            project_manager = ProjectManager(request.user)
            task_manager = TaskManager(request.user)
            
            available_projects = project_manager.user_projects.exclude(id__in=[project.id for project in event_data['projects']])
            available_tasks = task_manager.user_tasks.exclude(id__in=[task.id for task in event_data['tasks']])

            if request.method == 'POST':
                assign_task_id = request.POST.get('assign_task_id')
                assign_project_id = request.POST.get('assign_project_id')

                if assign_task_id:
                    # Asignar tarea al evento
                    task_to_assign = get_object_or_404(Task, id=assign_task_id)
                    task_to_assign.event_id = event_id
                    task_to_assign.save()
                    messages.success(request, f'La tarea {task_to_assign.id} ha sido asignada al evento {event_id} exitosamente.')
                    return redirect('event_assign', event_id=event_id)

                elif assign_project_id:
                    # Asignar proyecto al evento
                    project_to_assign = get_object_or_404(Project, id=assign_project_id)
                    project_to_assign.event_id = event_id
                    project_to_assign.save()
                    messages.success(request, f'El proyecto {project_to_assign.id} ha sido asignado al evento {event_id} exitosamente.')
                    return redirect('event_assign', event_id=event_id)

                else:
                    messages.error(request, 'No se proporcionó un id de tarea o proyecto válido.')
                    return redirect('event_assign', event_id=event_id)

            else:
                # Renderizar la plantilla con los datos necesarios
                return render(request, "events/event_assign.html", {
                    'title': f'{title} (GET With Id)',
                    'event': event_data,
                    'available_projects': available_projects,
                    'available_tasks': available_tasks,
                    'event_statuses': event_statuses,
                    'project_statuses': project_statuses,
                    'task_statuses': task_statuses,
                })

        else:
            # Si no se proporciona event_id, mostrar todos los eventos disponibles
            event_manager = EventManager(request.user)
            events, _ = event_manager.get_all_events()
            return render(request, "events/event_assign.html", {
                'title': f'{title} (No ID)',
                'events': events,
            })
    except Exception as e:
        # Manejo de errores
        messages.error(request, f'Ha ocurrido un error: {e}')
        return redirect('index')

def statuses_get():
    event_statuses = Status.objects.all().order_by('status_name')
    project_statuses = ProjectStatus.objects.all().order_by('status_name')
    task_statuses = TaskStatus.objects.all().order_by('status_name')
    return event_statuses, project_statuses, task_statuses

def calculate_percentage_increase(queryset, days):
    # Obtiene la fecha y hora actuales
    end_date = timezone.now()
    # Calcula la fecha de inicio del período reciente
    start_date = end_date - timedelta(days=days)
    
    # Define el período anterior, equivalente en duración
    previous_end_date = start_date
    previous_start_date = previous_end_date - timedelta(days=days)
    
    # Filtra los objetos creados en los últimos 'days' días
    recent_objects = queryset.filter(created_at__range=(start_date, end_date))
    # Filtra los objetos creados en el mismo rango de días anterior
    previous_objects = queryset.filter(created_at__range=(previous_start_date, previous_end_date))
    
    # Calcula el número total de objetos en cada período
    count_recent_objects = recent_objects.count()
    count_previous_objects = previous_objects.count()
    
    # Calcula el porcentaje de incremento
    if count_previous_objects > 0:
        percentage_increase = ((count_recent_objects - count_previous_objects) / count_previous_objects) * 100
    else:
        # Si no hay objetos en el período anterior, se asume un incremento del 100%
        percentage_increase = 100 if count_recent_objects > 0 else 0

    return {
        'percentage_increase': percentage_increase,
        'count_recent_objects': count_recent_objects,
        'count_previous_objects': count_previous_objects,
        'start_date': start_date,
        'end_date': end_date,
        'previous_start_date': previous_start_date,
        'previous_end_date': previous_end_date,
    }

# Projects - Optimized Version
def projects(request, project_id=None):
    """
    Optimized projects view with database query improvements and caching
    """
    from django.core.cache import cache
    from django.db.models import Prefetch

    # Cache key for this view
    cache_key = f'projects_view_{request.user.id}_{project_id or "all"}'
    cached_data = cache.get(cache_key)

    if cached_data and not request.method == 'POST':
        return cached_data

    title = "Projects"
    urls = [
        {'url': 'project_create', 'name': 'Project Create'},
        {'url': 'project_edit', 'name': 'Project Edit'},
    ]
    other_urls = [
        {'url': 'events', 'id': None, 'name': 'Events Panel'},
        {'url': 'projects', 'id': None, 'name': 'Projects Panel'},
        {'url': 'tasks', 'id': None, 'name': 'Tasks Panel'},
    ]
    instructions = [
        {'instruction': 'Fill carefully the metadata.', 'name': 'Form'},
    ]

    # Optimized: Single query with select_related for related objects
    project_statuses = ProjectStatus.objects.all().order_by('status_name')

    # Optimized: Use select_related and prefetch_related to avoid N+1 queries
    projects_queryset = Project.objects.select_related(
        'host', 'assigned_to', 'project_status', 'event'
    ).prefetch_related(
        'attendees',
        Prefetch('task_set', queryset=Task.objects.select_related('task_status'))
    ).order_by('-updated_at')

    # Get statistics in a single optimized query
    projects_stats = projects_queryset.aggregate(
        total_projects=Count('id'),
        total_ticket_price=Sum('ticket_price'),
        increase=Count('id', filter=Q(created_at__gte=timezone.now() - timezone.timedelta(days=1)))
    )

    # Optimized chart data generation - single query per model
    chart_data, chart_data_json = _get_optimized_chart_data()

    if project_id:
        # Single optimized query for specific project
        try:
            project = projects_queryset.get(id=project_id)
            context = {
                'project': project,
                'total_ticket_price': projects_stats['total_ticket_price'],
                'instructions': instructions,
                'urls': urls,
            }
            response = render(request, "projects/project_detail.html", context)
        except Project.DoesNotExist:
            raise Http404("Project not found")
    else:
        # Optimized: Use pagination for large datasets
        from django.core.paginator import Paginator
        paginator = Paginator(projects_queryset, 20)  # 20 projects per page
        page_number = request.GET.get('page')
        projects_page = paginator.get_page(page_number)

        # Get status counts for distribution
        status_counts = {}
        for status in project_statuses:
            status_counts[status.id] = projects_queryset.filter(project_status=status).count()
            status.projects_count = status_counts[status.id]

        context = {
            'total_ticket_price': projects_stats['total_ticket_price'],
            'other_urls': other_urls,
            'urls': urls,
            'instructions': instructions,
            'increase': projects_stats['increase'],
            'projects': projects_page,
            'total_projects': projects_stats['total_projects'],
            'in_progress_count': projects_queryset.filter(project_status__status_name='In Progress').count(),
            'completed_count': projects_queryset.filter(project_status__status_name='Completed').count(),
            'project_statuses': project_statuses,
            'title': title,
            'chart_data': chart_data,  # Pass chart_data as a single object
            'chart_data_json': chart_data_json,  # Pass JSON string for template
        }
        response = render(request, "projects/projects.html", context)

    # Cache the response for 5 minutes
    cache.set(cache_key, response, 300)
    return response


def _get_optimized_chart_data():
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

def project_create(request):
    urls=[
        {'url':'project_create','name':'Project Create'},
        {'url':'project_edit','name':'Project Edit'},   
    ]
    other_urls = [
        {'url': 'events', 'id' : None ,'name': 'Events Panel'},
        {'url': 'projects', 'id' : None , 'name': 'Projects Panel'},
        {'url': 'tasks', 'id' : None , 'name': 'Tasks Panel'},
        ]
    instructions = [
        {'instruction': 'Fill carefully the metadata. XD', 'name': 'Form'},
    ]
    tittle="Create New Project"
    if request.method == 'GET':
        form = CreateNewProject()
    else:
        form = CreateNewProject(request.POST)

        if form.is_valid():
            project = form.save(commit=False)
            project.host = request.user
            project.event = form.cleaned_data['event']

            # Si el campo de evento está vacío, crea un nuevo objeto Evento
            if not project.event:
                status = get_object_or_404(Status,status_name='Created')
                try:
                    with transaction.atomic():
                        
                        new_event = Event.objects.create(
                            title =form.cleaned_data['title'],
                            event_status=status,
                            host = request.user,
                            assigned_to = request.user,
                            
                            )
                        project.event = new_event
                        project.save()
                        form.save_m2m()
                        messages.success(request, 'Proyecto creado exitosamente!')
                        return redirect('project_panel')
                except IntegrityError as e:
                    messages.error(request, f'Hubo un problema al guardar el proyecto o crear el evento: {e}')
            else:
                try:
                    with transaction.atomic():
                        project.save()
                        form.save_m2m()
                        messages.success(request, 'Proyecto creado exitosamente!')
                        return redirect('project_panel')
                except IntegrityError:
                    messages.error(request, 'Hubo un problema al guardar el proyecto.')

        else:
            messages.error(request, 'Por favor, corrige los errores.')

    return render(request, 'projects/project_create.html', {
        'instructions':instructions,
        'form': form,
        'title':tittle,
        'urls':urls,
        'other_urls':other_urls,
        })

def project_detail(request, id):
    """
    Vista detallada de un proyecto individual con estadísticas completas
    """
    from django.db.models import Q, Count

    project = get_object_or_404(Project, id=id)

    # Verificar permisos
    if not (project.host == request.user or request.user in project.attendees.all()):
        messages.error(request, 'No tienes permisos para ver este proyecto.')
        return redirect('projects')

    # Obtener tareas del proyecto con información detallada
    tasks = Task.objects.filter(project_id=id).select_related(
        'task_status', 'assigned_to', 'host'
    ).order_by('created_at')

    # Calcular estadísticas del proyecto
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(task_status__status_name='Completed').count()
    in_progress_tasks = tasks.filter(task_status__status_name='In Progress').count()
    pending_tasks = tasks.filter(task_status__status_name='To Do').count()

    # Calcular progreso
    progress_percentage = 0
    if total_tasks > 0:
        progress_percentage = (completed_tasks / total_tasks) * 100

    # Tareas por estado para gráficos
    tasks_by_status = tasks.values('task_status__status_name').annotate(
        count=Count('id')
    ).order_by('task_status__status_name')

    # Tareas importantes
    important_tasks = tasks.filter(important=True).exclude(
        task_status__status_name='Completed'
    )

    # Actividad reciente (últimas 5 tareas actualizadas)
    recent_tasks = tasks.order_by('-updated_at')[:5]

    # Estadísticas de tiempo (si hay campo de tiempo estimado)
    estimated_time_total = 0
    actual_time_total = 0

    # Preparar datos para gráficos
    status_data = []
    status_colors = []
    for status_item in tasks_by_status:
        status_data.append(status_item['count'])
        # Obtener color del estado (si existe)
        try:
            status_obj = TaskStatus.objects.get(status_name=status_item['task_status__status_name'])
            status_colors.append(status_obj.color)
        except:
            status_colors.append('#6c757d')  # Color por defecto

    context = {
        'project': project,
        'tasks': tasks,

        # Estadísticas
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'pending_tasks': pending_tasks,
        'progress_percentage': progress_percentage,
        'important_tasks_count': important_tasks.count(),

        # Datos para gráficos
        'tasks_by_status': tasks_by_status,
        'status_data': status_data,
        'status_colors': status_colors,

        # Actividad
        'recent_tasks': recent_tasks,
        'important_tasks': important_tasks,

        # Tiempos
        'estimated_time_total': estimated_time_total,
        'actual_time_total': actual_time_total,
    }

    return render(request, 'projects/project_detail.html', context)

def project_delete(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_id)

        # Verificar permisos - solo el host o attendees pueden eliminar
        if not (project.host == request.user or request.user in project.attendees.all()):
            messages.error(request, 'No tienes permiso para eliminar este proyecto.')
            return redirect(reverse('project_panel'))

        project.delete()
        messages.success(request, 'El proyecto ha sido eliminado exitosamente.')
    else:
        messages.error(request, 'Método no permitido.')
    return redirect(reverse('project_panel'))

@login_required
def project_export(request):
    """
    Vista para exportar proyectos a CSV o Excel
    """
    if request.method == 'POST':
        selected_projects = request.POST.getlist('selected_projects')
        if selected_projects:
            projects = Project.objects.filter(id__in=selected_projects)
        else:
            projects = Project.objects.all()
    else:
        projects = Project.objects.all()

    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="projects_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Description', 'Status', 'Event', 'Host', 'Created At', 'Updated At'])

    for project in projects:
        writer.writerow([
            project.id,
            project.title,
            project.description or '',
            project.project_status.status_name,
            project.event.title if project.event else 'None',
            project.host.username,
            project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            project.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response

@login_required
def project_bulk_action(request):
    """
    Vista para acciones masivas en proyectos
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_projects = request.POST.getlist('selected_projects')

        if not selected_projects:
            messages.error(request, 'No se seleccionaron proyectos.')
            return redirect('project_panel')

        projects = Project.objects.filter(id__in=selected_projects)

        if action == 'delete':
            if not (hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'SU'):
                messages.error(request, 'No tienes permiso para eliminar proyectos.')
                return redirect('project_panel')

            count = projects.count()
            projects.delete()
            messages.success(request, f'Se eliminaron {count} proyecto(s) exitosamente.')

        elif action == 'activate':
            active_status = ProjectStatus.objects.get(status_name='In Progress')
            count = projects.update(project_status=active_status)
            messages.success(request, f'Se activaron {count} proyecto(s) exitosamente.')

        elif action == 'complete':
            completed_status = ProjectStatus.objects.get(status_name='Completed')
            count = projects.update(project_status=completed_status)
            messages.success(request, f'Se completaron {count} proyecto(s) exitosamente.')

        else:
            messages.error(request, 'Acción no válida.')

    return redirect('project_panel')

def change_project_status(request, project_id):
    print("Inicio de vista change_project_status")
    try:
        if request.method != 'POST':
            print("solicitud GET")
            return HttpResponse("Método no permitido", status=405)
        print("solicitud Post:", request.POST)
        project = get_object_or_404(Project, pk=project_id)
        print("ID a cambiar:", str(project.id))
        new_status_id = request.POST.get('new_status_id')
        new_status = get_object_or_404(ProjectStatus, pk=new_status_id)
        print("new_status_id", str(new_status))
        if request.user is None:
            print("User is none: Usuario no autenticado")
            messages.error(request, "User is none: Usuario no autenticado")
            return redirect('index')
        if project.host is not None and (project.host == request.user or request.user in project.attendees.all()):
            old_status = project.project_status
            print("old_status:", old_status)
            project.record_edit(
                editor=request.user,
                field_name='project_status',
                old_value=str(old_status),
                new_value=str(new_status)
            )
        else:
            return HttpResponse("No tienes permiso para editar este projecto", status=403)
    except Exception as e:
        print(f"Error: {str(e)}")
        return HttpResponse(f"Error: {str(e)}", status=500)
    messages.success(request, 'Project status edited successfully!')

    return redirect('project_panel')

def project_edit(request, project_id=None):
    try:
        if project_id is not None:
            title="Project Edit"

            # Estamos editando un proyecto existente
            try:
                project = get_object_or_404(Project, pk=project_id)
            except Http404:
                messages.error(request, 'El proyecto con el ID "{}" no existe.'.format(project_id))
                return redirect('index')

            # Verificar permisos - solo el host o attendees pueden editar
            if not (project.host == request.user or request.user in project.attendees.all()):
                messages.error(request, 'No tienes permisos para editar este proyecto.')
                return redirect('projects')

            if request.method == 'POST':
                form = CreateNewProject(request.POST, instance=project)
                if form.is_valid():
                    # Asigna el usuario autenticado como el editor
                    project.editor = request.user
                    print('guardando via post si es valido')

                    # Guardar el proyecto con el editor actual (usuario que realiza la solicitud)
                    for field in form.changed_data:
                        old_value = getattr(project, field)
                        new_value = form.cleaned_data.get(field)
                        project.record_edit(
                            editor=request.user,
                            field_name=field,
                            old_value=str(old_value),
                            new_value=str(new_value)
                        )
                    form.save()

                    messages.success(request, 'Proyecto guardado con éxito.')
                    return redirect('projects')  # Redirige a la página de lista de edición
                else:
                    messages.error(request, 'Hubo un error al guardar el proyecto. Por favor, revisa el formulario.')
            else:
                form = CreateNewProject(instance=project)
            return render(request, 'projects/project_edit.html', {
                'form': form,
                'title':title,
                })
        else:
            title="Projects list"

            # Estamos manejando una solicitud GET sin argumentos
            # Verificar el rol del usuario
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'SU':
                # Si el usuario es un 'SU', puede ver todos los proyectos
                projects = Project.objects.all().order_by('-updated_at')
            else:
                # Si no, solo puede ver los proyectos que le están asignados o a los que asiste
                projects = Project.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
            return render(request, 'projects/project_list.html', {
                'projects': projects,
                'title':title,
                })
    except Exception as e:
        messages.error(request, 'Ha ocurrido un error: {}'.format(e))
        return redirect('index')

def generate_project_alerts(project_data, user):
    """
    Generate contextual alerts for a specific project
    """
    alerts = []
    project = project_data['project']
    tasks = project_data.get('tasks', [])

    # Alert: Project overdue
    if project.updated_at and (timezone.now() - project.updated_at).days > 7:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-exclamation-triangle',
            'title': 'Proyecto inactivo',
            'message': f'El proyecto "{project.title}" no ha sido actualizado en {(timezone.now() - project.updated_at).days} días.',
            'action_url': f'/events/projects/edit/{project.id}',
            'action_text': 'Actualizar proyecto'
        })

    # Alert: Tasks completion status
    completed_tasks = sum(1 for task in tasks if task.task_status.status_name == 'Completed')
    total_tasks = len(tasks)
    if total_tasks > 0:
        completion_rate = (completed_tasks / total_tasks) * 100
        if completion_rate < 30:
            alerts.append({
                'type': 'danger',
                'icon': 'bi-graph-down',
                'title': 'Bajo progreso',
                'message': f'Solo {completion_rate:.1f}% de las tareas completadas ({completed_tasks}/{total_tasks}).',
                'action_url': f'/events/tasks/?project_id={project.id}',
                'action_text': 'Ver tareas'
            })
        elif completion_rate > 90 and project.project_status.status_name != 'Completed':
            alerts.append({
                'type': 'success',
                'icon': 'bi-check-circle',
                'title': '¡Casi listo!',
                'message': f'{completion_rate:.1f}% de las tareas completadas. ¿Listo para finalizar?',
                'action_url': f'/events/projects/edit/{project.id}',
                'action_text': 'Marcar como completado'
            })

    # Alert: Multiple assignees
    if project.attendees.count() > 3:
        alerts.append({
            'type': 'info',
            'icon': 'bi-people',
            'title': 'Proyecto colaborativo',
            'message': f'{project.attendees.count()} personas trabajando en este proyecto.',
            'action_url': f'/events/projects/detail/{project.id}',
            'action_text': 'Ver detalles'
        })

    # Alert: High priority tasks
    high_priority_tasks = [task for task in tasks if task.important and task.task_status.status_name != 'Completed']
    if high_priority_tasks:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-star-fill',
            'title': 'Tareas prioritarias',
            'message': f'{len(high_priority_tasks)} tarea(s) de alta prioridad pendiente(s).',
            'action_url': f'/events/tasks/?project_id={project.id}',
            'action_text': 'Revisar prioridades'
        })

    return alerts

def generate_projects_overview_alerts(projects, user):
    """
    Generate overview alerts for all projects
    """
    alerts = []

    if not projects:
        alerts.append({
            'type': 'info',
            'icon': 'bi-info-circle',
            'title': '¡Bienvenido!',
            'message': 'No tienes proyectos activos. ¿Quieres crear uno nuevo?',
            'action_url': '/events/projects/create/',
            'action_text': 'Crear proyecto'
        })
        return alerts

    # Alert: Overall completion rate
    total_tasks = sum(p['count_tasks'] for p in projects)
    completed_tasks = 0
    for p in projects:
        project_tasks = p.get('tasks', [])
        completed_tasks += sum(1 for task in project_tasks if task.task_status.status_name == 'Completed')

    if total_tasks > 0:
        overall_completion = (completed_tasks / total_tasks) * 100
        if overall_completion < 50:
            alerts.append({
                'type': 'warning',
                'icon': 'bi-bar-chart',
                'title': 'Progreso general bajo',
                'message': f'Solo {overall_completion:.1f}% de todas las tareas completadas.',
                'action_url': '/events/projects/',
                'action_text': 'Ver todos los proyectos'
            })

    # Alert: Projects without recent activity
    inactive_projects = []
    for p in projects:
        if p['project'].updated_at and (timezone.now() - p['project'].updated_at).days > 14:
            inactive_projects.append(p['project'])

    if inactive_projects:
        alerts.append({
            'type': 'danger',
            'icon': 'bi-clock',
            'title': 'Proyectos inactivos',
            'message': f'{len(inactive_projects)} proyecto(s) sin actividad reciente.',
            'action_url': '/events/projects/',
            'action_text': 'Revisar proyectos'
        })

    # Alert: High number of in-progress projects
    in_progress_projects = sum(1 for p in projects if p['project'].project_status.status_name == 'In Progress')
    if in_progress_projects > 5:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-exclamation-circle',
            'title': 'Demasiados proyectos activos',
            'message': f'Tienes {in_progress_projects} proyectos en progreso. Considera priorizar.',
            'action_url': '/events/projects/',
            'action_text': 'Gestionar prioridades'
        })

    # Alert: Projects nearing completion
    nearly_complete = []
    for p in projects:
        if p['count_tasks'] > 0:
            project_tasks = p.get('tasks', [])
            completed = sum(1 for task in project_tasks if task.task_status.status_name == 'Completed')
            if completed / p['count_tasks'] > 0.8 and p['project'].project_status.status_name != 'Completed':
                nearly_complete.append(p['project'])

    if nearly_complete:
        alerts.append({
            'type': 'success',
            'icon': 'bi-trophy',
            'title': '¡Proyectos casi listos!',
            'message': f'{len(nearly_complete)} proyecto(s) están cerca de completarse.',
            'action_url': '/events/projects/',
            'action_text': 'Finalizar proyectos'
        })

    return alerts

def generate_performance_alerts(projects, user):
    """
    Generate performance-based alerts for projects
    """
    alerts = []

    # Calculate performance metrics
    total_projects = len(projects)
    if total_projects == 0:
        return alerts

    # Completion rate analysis
    completion_rates = []
    for p in projects:
        if p['count_tasks'] > 0:
            project_tasks = p.get('tasks', [])
            completed = sum(1 for task in project_tasks if task.task_status.status_name == 'Completed')
            rate = (completed / p['count_tasks']) * 100
            completion_rates.append(rate)

    if completion_rates:
        avg_completion = sum(completion_rates) / len(completion_rates)

        if avg_completion < 25:
            alerts.append({
                'type': 'danger',
                'icon': 'bi-graph-down',
                'title': 'Rendimiento bajo',
                'message': f'El promedio de completación de proyectos es solo {avg_completion:.1f}%.',
                'action_url': '/events/projects/',
                'action_text': 'Mejorar rendimiento'
            })
        elif avg_completion > 75:
            alerts.append({
                'type': 'success',
                'icon': 'bi-graph-up',
                'title': '¡Excelente rendimiento!',
                'message': f'Promedio de completación del {avg_completion:.1f}%. ¡Sigue así!',
                'action_url': '/events/projects/',
                'action_text': 'Ver estadísticas'
            })

    # Task distribution analysis
    total_tasks = sum(p['count_tasks'] for p in projects)
    if total_tasks > 0:
        avg_tasks_per_project = total_tasks / total_projects

        if avg_tasks_per_project > 10:
            alerts.append({
                'type': 'warning',
                'icon': 'bi-list-check',
                'title': 'Proyectos complejos',
                'message': f'Promedio de {avg_tasks_per_project:.1f} tareas por proyecto. Considera dividir en proyectos más pequeños.',
                'action_url': '/events/projects/create/',
                'action_text': 'Crear subproyectos'
            })

    # Time-based analysis
    recent_projects = [p for p in projects if p['project'].created_at > timezone.now() - timezone.timedelta(days=7)]
    if recent_projects:
        alerts.append({
            'type': 'info',
            'icon': 'bi-calendar-plus',
            'title': 'Actividad reciente',
            'message': f'{len(recent_projects)} proyecto(s) creado(s) en la última semana.',
            'action_url': '/events/projects/',
            'action_text': 'Ver proyectos nuevos'
        })

    return alerts

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

    # Alert: Task nearing deadline (if due date exists)
    # This would require adding a due_date field to Task model
    # For now, we'll skip this alert

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
        # Calculate average completion time (this would require tracking start/end times)
        # For now, we'll use a simple heuristic
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

def get_project_alerts_ajax(request):
    """
    AJAX endpoint to get project alerts
    """
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            project_manager = ProjectManager(request.user)
            projects, _ = project_manager.get_all_projects()

            alerts = generate_projects_overview_alerts(projects, request.user)
            performance_alerts = generate_performance_alerts(projects, request.user)
            alerts.extend(performance_alerts)

            return JsonResponse({
                'success': True,
                'alerts': alerts,
                'count': len(alerts)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    })

def project_panel(request, project_id=None):
    # Title of the page
    title = "Project Panel"

    # Retrieve projects and statuses
    project_manager = ProjectManager(request.user)
    statuses = statuses_get()

    try:

        if project_id:
            # If a specific project_id is provided, handle it here
            project_data = project_manager.get_project_data(project_id)

            if project_data:
                # Generate alerts for specific project
                alerts = generate_project_alerts(project_data, request.user)

                context = {
                    'title': title,
                    'project_data': project_data,
                    'event_statuses': statuses[0],
                    'project_statuses': statuses[1],
                    'task_statuses': statuses[2],
                    'alerts': alerts,
                }
                return render(request, 'projects/project_panel.html', context)
            else:
                messages.error(request, f'Project with id {project_id} not found')
                return redirect('index')
        else:
            projects, active_projects = project_manager.get_all_projects()

            # Calculate statistics
            total_projects = len(projects)
            in_progress_count = sum(1 for p in projects if p['project'].project_status.status_name == 'In Progress')
            completed_count = sum(1 for p in projects if p['project'].project_status.status_name == 'Completed')
            total_tasks = sum(p['count_tasks'] for p in projects)

            # Generate comprehensive alerts for all projects
            alerts = generate_projects_overview_alerts(projects, request.user)

            # If no specific project_id is provided
            if request.method == 'POST':
                # Handle POST request logic here
                pass
            else:
                # Create context for the template for GET requests
                title = "Projects Panel"
                context = {
                    'title': title,
                    'event_statuses': statuses[0],
                    'project_statuses': statuses[1],
                    'task_statuses': statuses[2],
                    'projects': projects,
                    'active_projects': active_projects,
                    'total_projects': total_projects,
                    'in_progress_count': in_progress_count,
                    'completed_count': completed_count,
                    'total_tasks': total_tasks,
                    'alerts': alerts,
                }
                return render(request, 'projects/project_panel.html', context)

    except Exception as e:
        messages.error(request, f'An error occurred: ({e})')
        return redirect('index')

def project_activate(request, project_id=None):
    title='Project Activate'
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        try:
            active_status = ProjectStatus.objects.get(status_name='In Progress')
            project.project_status = active_status
            project.save()
            messages.success(request, 'El proyecto ha sido activado exitosamente.')
        except ProjectStatus.DoesNotExist:
            messages.error(request, 'El estado "Activo" no existe en la base de datos.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al intentar activar el proyecto: {e}')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
        projects = Project.objects.all().order_by('-updated_at')
        # Crea una lista para almacenar los proyectos y sus recuentos de tareas
        projects_with_task_count = []
        for project in projects:
            # Cuenta las tareas para el proyecto actual
            count_tasks = Task.objects.filter(project_id=project.id).count()
            # Almacena el proyecto y su recuento de tareas en la lista
            projects_with_task_count.append((project, count_tasks))
        try:
            return render(request, "projects/project_activate.html",{
                'title':f'{title} (No iD)',
                'projects_with_task_count':projects_with_task_count,
            })
        except Exception as e:
            messages.error(request, 'Ha ocurrido un error: {}'.format(e))
            return redirect('project_panel')
        
# Tasks
     
def tasks(request, task_id=None, project_id=None):
    title='Tasks'
    urls=[
        {'url':'task_create','name':'Task Create'},
        {'url':'task_edit','name':'Task Edit'},
    ]

    other_urls = [
        {'url': 'events', 'id' : None ,'name': 'Events Panel'},
        {'url': 'projects', 'id' : None , 'name': 'Projects Panel'},
        {'url': 'tasks', 'id' : None , 'name': 'Tasks Panel'},
        ]
    instructions = [
        {'instruction': 'Fill carefully the metadata.', 'name': 'Form'},
    ]
    task_statuses = TaskStatus.objects.all().order_by('status_name')

    if task_id:
        task= get_object_or_404(Task, id=task_id)

        # Generate alerts for specific task
        task_data = {'task': task}
        alerts = generate_task_alerts(task_data, request.user)

        return render(request, "tasks/task_detail.html",{

            'title':title,
            'task':task,
            'task_statuses':task_statuses,
            'alerts': alerts,

        })

    else:

        if not project_id:
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(project_id=project_id)

        # Convert to tasks_data format for alert generation
        tasks_data = [{'task': task} for task in tasks]

        # Generate overview alerts
        alerts = generate_tasks_overview_alerts(tasks_data, request.user)

        # Add performance alerts
        performance_alerts = generate_task_performance_alerts(tasks_data, request.user)
        alerts.extend(performance_alerts)

        return render(request, "tasks/tasks.html",{
            'title':title,
            'tasks':tasks,
            'alerts': alerts,
        })
            
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
                return redirect('index')

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
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'SU':
                # Si el usuario es un 'SU', puede ver todos los proyectos
                tasks = Task.objects.all().order_by('-created_at')
            else:
                # Si no, solo puede ver los tareas que le están asignados o a los que asiste
                tasks = Task.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-created_at')
            return render(request, 'tasks/task_panel.html', {'tasks': tasks})
    except Exception as e:
        messages.error(request, 'Ha ocurrido un error: {}'.format(e))
        return redirect('index')

def task_delete(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=task_id)
        if not (hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'SU'):
            messages.error(request, 'No tienes permiso para eliminar esta tarea.')
            return redirect(reverse('tasks'))
        task.delete()
        messages.success(request, 'La tarea ha sido eliminado exitosamente.')
    else:
        messages.error(request, 'Método no permitido.')
    return redirect(reverse('tasks'))

def task_panel(request, task_id=None):
    title = "Task Panel"
    statuses = statuses_get()
    tasks_states = TaskState.objects.all().order_by('-start_time')[:10]
    task_manager = TaskManager(request.user)
    project_manager = ProjectManager(request.user)
    event_manager = EventManager(request.user)

    if task_id:
        task_data = task_manager.get_task_data(task_id)
        try:
            if not task_data:
                messages.error(request, 'La tarea no existe. Verifica el ID de la tarea.')
                return redirect('task_panel')
            task = task_data['task']
            project_data = project_manager.get_project_data(task.project.id) if task.project else None
            event_data = event_manager.get_event_data(task.event) if task.event else None

            if not project_data:
                messages.error(request, 'El proyecto no existe. Verifica el ID del proyecto.')
                return redirect('project_panel')

            if not event_data:
                messages.error(request, 'El evento no existe. Verifica el ID del evento.')
                return redirect('events')

            # Generate alerts for specific task
            alerts = generate_task_alerts(task_data, request.user)

            context={
                'event_statuses': statuses[0],
                'project_statuses': statuses[1],
                'task_statuses': statuses[2],
                'title': title+' (ID)',
                'task_data': task_data,
                'project_data': project_data,
                'event_data': event_data,
                'alerts': alerts,
            }
            for key, value in task_data.items():
                print(f"{key}: {value}")
            return render(request, "tasks/task_panel.html", context)
        except Exception as e:
            messages.error(request, 'Ha ocurrido un error: {}'.format(e))
            print(e)
            return redirect('task_panel')
    else:
        tasks_data, active_tasks = task_manager.get_all_tasks()

        # Calculate statistics for the template
        total_tasks = len(tasks_data)
        in_progress_count = sum(1 for task in tasks_data if task['task'].task_status.status_name == 'In Progress')
        completed_count = sum(1 for task in tasks_data if task['task'].task_status.status_name == 'Completed')
        pending_count = sum(1 for task in tasks_data if task['task'].task_status.status_name == 'To Do')

        # Get unique projects for filter dropdown
        projects = Project.objects.filter(
            Q(host=request.user) | Q(attendees=request.user)
        ).distinct().order_by('title')

        # Generate comprehensive alerts for all tasks
        alerts = generate_tasks_overview_alerts(tasks_data, request.user)

        # Add performance alerts
        performance_alerts = generate_task_performance_alerts(tasks_data, request.user)
        alerts.extend(performance_alerts)

        context = {
            'title': f' {title} (User tasks)',
            'event_statuses': statuses[0],
            'task_statuses': statuses[2],
            'project_statuses': statuses[1],
            'tasks_data': tasks_data,
            'active_tasks': active_tasks,
            'tasks_states': tasks_states,
            'total_tasks': total_tasks,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'pending_count': pending_count,
            'projects': projects,  # Add projects for filter dropdown
            'alerts': alerts,
        }
        return render(request, 'tasks/task_panel.html', context)

def change_task_status(request, task_id):
    try:
        if request.method != 'POST':
            return HttpResponse("Método no permitido", status=405)
        task = get_object_or_404(Task, pk=task_id)
        new_status_id = request.POST.get('new_status_id')
        new_status = get_object_or_404(TaskStatus, pk=new_status_id)
        if request.user is None:
            messages.error(request, "User is none: Usuario no autenticado")
            return redirect('index')
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

def update_status(obj, field_name, new_status, editor):
    old_value = getattr(obj, field_name).status_name
    setattr(obj, field_name, new_status)
    new_value = getattr(obj, field_name).status_name

    obj.record_edit(
        editor=editor,
        field_name=field_name,
        old_value=str(old_value),
        new_value=str(new_value),
    )
    obj.save()

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
    """AJAX endpoint to change task status (for Kanban drag & drop)"""
    if request.method == 'POST':
        try:
            task_id = request.POST.get('task_id')
            new_status_name = request.POST.get('new_status_name')

            task = get_object_or_404(Task, id=task_id)

            # Check permissions
            if task.host != request.user and request.user not in task.attendees.all():
                return JsonResponse({'success': False, 'error': 'Permission denied'})

            # Get the new status
            new_status = get_object_or_404(TaskStatus, status_name=new_status_name)

            # Record the change
            old_status = task.task_status
            task.record_edit(
                editor=request.user,
                field_name='task_status',
                old_value=str(old_status),
                new_value=str(new_status)
            )

            return JsonResponse({'success': True, 'message': f'Task status updated to {new_status_name}'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def inbox_view(request):
    """
    Vista de la bandeja de entrada GTD para capturar tareas rápidamente
    """
    from .models import InboxItem

    if request.method == 'POST':
        # Crear nuevo item en el inbox
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()

        if title:
            # Crear item con categorización inicial
            inbox_item = InboxItem.objects.create(
                title=title,
                description=description,
                created_by=request.user,
                gtd_category='pendiente',
                priority='media'
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Item agregado al inbox correctamente',
                    'item_id': inbox_item.id
                })
            else:
                messages.success(request, 'Item agregado al inbox correctamente')
                return redirect('inbox')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'El título es obligatorio'
                })
            else:
                messages.error(request, 'El título es obligatorio')
                return redirect('inbox')

    # Obtener items del inbox del usuario
    inbox_items = InboxItem.objects.filter(created_by=request.user)

    # Categorización GTD
    unprocessed_items = inbox_items.filter(is_processed=False)
    processed_items = inbox_items.filter(is_processed=True)

    # Items por categoría GTD
    accionables = unprocessed_items.filter(gtd_category='accionable')
    no_accionables = unprocessed_items.filter(gtd_category='no_accionable')
    pendientes = unprocessed_items.filter(gtd_category='pendiente')

    # Items por tipo de acción
    hacer_items = unprocessed_items.filter(action_type='hacer')
    delegar_items = unprocessed_items.filter(action_type='delegar')
    posponer_items = unprocessed_items.filter(action_type='posponer')
    proyecto_items = unprocessed_items.filter(action_type='proyecto')
    eliminar_items = unprocessed_items.filter(action_type='eliminar')
    archivar_items = unprocessed_items.filter(action_type='archivar')
    incubar_items = unprocessed_items.filter(action_type='incubar')

    # Estadísticas GTD
    gtd_stats = {
        'total': unprocessed_items.count(),
        'accionables': accionables.count(),
        'no_accionables': no_accionables.count(),
        'pendientes': pendientes.count(),
        'hacer': hacer_items.count(),
        'delegar': delegar_items.count(),
        'posponer': posponer_items.count(),
        'proyectos': proyecto_items.count(),
        'eliminar': eliminar_items.count(),
        'archivar': archivar_items.count(),
        'incubar': incubar_items.count(),
    }

    context = {
        'title': 'Bandeja de Entrada GTD',
        'unprocessed_items': unprocessed_items,
        'processed_items': processed_items,
        'total_unprocessed': unprocessed_items.count(),
        'total_processed': processed_items.count(),

        # Categorización GTD
        'accionables': accionables,
        'no_accionables': no_accionables,
        'pendientes': pendientes,

        # Tipos de acción
        'hacer_items': hacer_items,
        'delegar_items': delegar_items,
        'posponer_items': posponer_items,
        'proyecto_items': proyecto_items,
        'eliminar_items': eliminar_items,
        'archivar_items': archivar_items,
        'incubar_items': incubar_items,

        # Estadísticas
        'gtd_stats': gtd_stats,
    }

    return render(request, 'events/inbox.html', context)


@login_required
def inbox_stats_api(request):
    """
    API endpoint para obtener estadísticas del inbox GTD en tiempo real
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        from .models import InboxItem

        # Obtener items del inbox del usuario
        inbox_items = InboxItem.objects.filter(created_by=request.user)

        # Estadísticas básicas
        total_items = inbox_items.count()
        unprocessed_items = inbox_items.filter(is_processed=False)
        processed_items = inbox_items.filter(is_processed=True)

        # Items por categoría GTD
        accionables = unprocessed_items.filter(gtd_category='accionable')
        no_accionables = unprocessed_items.filter(gtd_category='no_accionable')
        pendientes = unprocessed_items.filter(gtd_category='pendiente')

        # Items por tipo de acción
        hacer_items = unprocessed_items.filter(action_type='hacer')
        delegar_items = unprocessed_items.filter(action_type='delegar')
        posponer_items = unprocessed_items.filter(action_type='posponer')
        proyecto_items = unprocessed_items.filter(action_type='proyecto')
        eliminar_items = unprocessed_items.filter(action_type='eliminar')
        archivar_items = unprocessed_items.filter(action_type='archivar')
        incubar_items = unprocessed_items.filter(action_type='incubar')

        # Items de hoy
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
        today_end = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))
        today_items = inbox_items.filter(created_at__range=(today_start, today_end))

        # Items recientes (últimas 24 horas)
        last_24h = timezone.now() - timedelta(hours=24)
        recent_items = inbox_items.filter(created_at__gte=last_24h)

        # Estadísticas detalladas
        stats = {
            'total': total_items,
            'unprocessed': unprocessed_items.count(),
            'processed': processed_items.count(),
            'today': today_items.count(),
            'recent': recent_items.count(),
            'gtd_categories': {
                'accionables': accionables.count(),
                'no_accionables': no_accionables.count(),
                'pendientes': pendientes.count(),
            },
            'action_types': {
                'hacer': hacer_items.count(),
                'delegar': delegar_items.count(),
                'posponer': posponer_items.count(),
                'proyectos': proyecto_items.count(),
                'eliminar': eliminar_items.count(),
                'archivar': archivar_items.count(),
                'incubar': incubar_items.count(),
            },
            'percentages': {
                'processed_rate': round((processed_items.count() / total_items * 100), 1) if total_items > 0 else 0,
                'unprocessed_rate': round((unprocessed_items.count() / total_items * 100), 1) if total_items > 0 else 0,
                'today_rate': round((today_items.count() / total_items * 100), 1) if total_items > 0 else 0,
            },
            'trends': {
                'today_vs_yesterday': today_items.count() - inbox_items.filter(
                    created_at__range=(
                        today_start - timedelta(days=1),
                        today_end - timedelta(days=1)
                    )
                ).count(),
                'processed_today': processed_items.filter(processed_at__date=today).count(),
            }
        }

        return JsonResponse({
            'success': True,
            'stats': stats,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def find_similar_tasks(user, title, description=None, threshold=0.6):
    """
    Busca tareas similares basadas en similitud de texto
    """
    from .models import Task

    # Obtener todas las tareas del usuario
    user_tasks = Task.objects.filter(
        Q(host=user) | Q(assigned_to=user)
    ).select_related('task_status', 'project', 'event')

    similar_tasks = []

    # Normalizar texto para comparación
    def normalize_text(text):
        if not text:
            return ""
        return re.sub(r'[^\w\s]', '', text.lower().strip())

    normalized_title = normalize_text(title)
    normalized_description = normalize_text(description) if description else ""

    for task in user_tasks:
        # Calcular similitud del título
        task_title_norm = normalize_text(task.title)
        title_similarity = SequenceMatcher(None, normalized_title, task_title_norm).ratio()

        # Calcular similitud de la descripción si existe
        desc_similarity = 0
        if normalized_description and task.description:
            task_desc_norm = normalize_text(task.description)
            desc_similarity = SequenceMatcher(None, normalized_description, task_desc_norm).ratio()
        elif not normalized_description and not task.description:
            desc_similarity = 0.5  # Considerar como parcialmente similar si ambos están vacíos

        # Calcular similitud ponderada (título tiene más peso)
        overall_similarity = (title_similarity * 0.7) + (desc_similarity * 0.3)

        if overall_similarity >= threshold:
            similar_tasks.append({
                'task': task,
                'similarity': overall_similarity,
                'title_similarity': title_similarity,
                'description_similarity': desc_similarity
            })

    # Ordenar por similitud descendente
    similar_tasks.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_tasks


def find_similar_projects(user, title, description=None, threshold=0.6):
    """
    Busca proyectos similares basados en similitud de texto
    """
    from .models import Project

    # Obtener todos los proyectos del usuario
    user_projects = Project.objects.filter(
        Q(host=user) | Q(assigned_to=user) | Q(attendees=user)
    ).distinct().select_related('project_status', 'event')

    similar_projects = []

    # Normalizar texto para comparación
    def normalize_text(text):
        if not text:
            return ""
        return re.sub(r'[^\w\s]', '', text.lower().strip())

    normalized_title = normalize_text(title)
    normalized_description = normalize_text(description) if description else ""

    for project in user_projects:
        # Calcular similitud del título
        project_title_norm = normalize_text(project.title)
        title_similarity = SequenceMatcher(None, normalized_title, project_title_norm).ratio()

        # Calcular similitud de la descripción si existe
        desc_similarity = 0
        if normalized_description and project.description:
            project_desc_norm = normalize_text(project.description)
            desc_similarity = SequenceMatcher(None, normalized_description, project_desc_norm).ratio()
        elif not normalized_description and not project.description:
            desc_similarity = 0.5  # Considerar como parcialmente similar si ambos están vacíos

        # Calcular similitud ponderada (título tiene más peso)
        overall_similarity = (title_similarity * 0.7) + (desc_similarity * 0.3)

        if overall_similarity >= threshold:
            similar_projects.append({
                'project': project,
                'similarity': overall_similarity,
                'title_similarity': title_similarity,
                'description_similarity': desc_similarity
            })

    # Ordenar por similitud descendente
    similar_projects.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_projects


@login_required
def process_inbox_item(request, item_id):
    """
    Vista para procesar un item del inbox siguiendo la metodología GTD
    """
    from .models import InboxItem
    from .forms import CreateNewTask

    try:
        inbox_item = InboxItem.objects.get(id=item_id, created_by=request.user)
    except InboxItem.DoesNotExist:
        messages.error(request, 'Item no encontrado')
        return redirect('inbox')

    if request.method == 'POST':
        action = request.POST.get('action')
        gtd_category = request.POST.get('gtd_category')
        action_type = request.POST.get('action_type')

        # Actualizar categorización GTD si se proporciona
        if gtd_category:
            inbox_item.gtd_category = gtd_category
        if action_type:
            inbox_item.action_type = action_type
        inbox_item.save()

        if action == 'convert_to_task':
            # Convertir en tarea usando TaskManager
            try:
                # Crear el TaskManager para el usuario
                task_manager = TaskManager(request.user)

                # Crear tarea usando el TaskManager (sin evento ni proyecto)
                task = task_manager.create_task(
                    title=inbox_item.title,
                    description=inbox_item.description,
                    important=False,
                    project=None,  # Tarea sin proyecto
                    event=None,    # Tarea sin evento
                    task_status=None,  # Usará 'To Do' por defecto
                    assigned_to=request.user,
                    ticket_price=0.07
                )

                # Marcar como procesado y vincular a la tarea
                from django.contrib.contenttypes.models import ContentType
                task_content_type = ContentType.objects.get_for_model(Task)

                inbox_item.is_processed = True
                inbox_item.processed_to_content_type = task_content_type
                inbox_item.processed_to_object_id = task.id
                inbox_item.processed_at = timezone.now()
                inbox_item.save()

                messages.success(request, f'Tarea "{task.title}" creada exitosamente desde el inbox GTD')
                return redirect('tasks', task.id)

            except Exception as e:
                messages.error(request, f'Error al crear la tarea: {e}')

        elif action == 'delete':
            # Eliminar item
            inbox_item.delete()
            messages.success(request, 'Item eliminado del inbox')
            return redirect('inbox')

        elif action == 'postpone':
            # Posponer (mantener sin procesar)
            messages.info(request, 'Item pospuesto para procesar después')
            return redirect('inbox')

        elif action == 'categorize':
            # Solo categorizar sin procesar
            messages.success(request, f'Item categorizado como {gtd_category}')
            return redirect('inbox')

        elif action == 'link_to_task':
            # Vincular a tarea existente
            task_id = request.POST.get('task_id')
            if task_id:
                try:
                    existing_task = Task.objects.get(id=task_id)

                    # Verificar permisos
                    if existing_task.host != request.user and request.user not in existing_task.attendees.all():
                        messages.error(request, 'No tienes permisos para vincular a esta tarea.')
                        return redirect('process_inbox_item', item_id=item_id)

                    # Marcar como procesado y vincular correctamente usando GenericForeignKey
                    from django.contrib.contenttypes.models import ContentType
                    task_content_type = ContentType.objects.get_for_model(Task)

                    inbox_item.is_processed = True
                    inbox_item.processed_to_content_type = task_content_type
                    inbox_item.processed_to_object_id = existing_task.id
                    inbox_item.processed_at = timezone.now()
                    inbox_item.save()

                    messages.success(request,
                        f'Item del inbox vinculado exitosamente a la tarea: "{existing_task.title}"')
                    return redirect('tasks', task_id=existing_task.id)

                except Task.DoesNotExist:
                    messages.error(request, 'La tarea objetivo no existe.')
                except Exception as e:
                    messages.error(request, f'Error al vincular: {e}')

        elif action == 'link_to_project':
            # Vincular a proyecto existente
            project_id = request.POST.get('project_id')
            if project_id:
                try:
                    existing_project = Project.objects.get(id=project_id)

                    # Verificar permisos
                    if existing_project.host != request.user and request.user not in existing_project.attendees.all():
                        messages.error(request, 'No tienes permisos para vincular a este proyecto.')
                        return redirect('process_inbox_item', item_id=item_id)

                    # Marcar como procesado y vincular al proyecto
                    from django.contrib.contenttypes.models import ContentType
                    project_content_type = ContentType.objects.get_for_model(Project)

                    inbox_item.is_processed = True
                    inbox_item.processed_to_content_type = project_content_type
                    inbox_item.processed_to_object_id = existing_project.id
                    inbox_item.processed_at = timezone.now()
                    inbox_item.save()

                    messages.success(request,
                        f'Item del inbox vinculado exitosamente al proyecto: "{existing_project.title}"')
                    return redirect('projects', project_id=existing_project.id)

                except Project.DoesNotExist:
                    messages.error(request, 'El proyecto objetivo no existe.')
                except Exception as e:
                    messages.error(request, f'Error al vincular: {e}')

        elif action == 'convert_to_project':
            # Convertir en proyecto usando ProjectManager
            try:
                # Crear el ProjectManager para el usuario
                project_manager = ProjectManager(request.user)

                # Crear proyecto usando el ProjectManager (sin evento)
                project = project_manager.create_project(
                    title=inbox_item.title,
                    description=inbox_item.description,
                    project_status=None,  # Usará 'Created' por defecto
                    assigned_to=request.user,
                    ticket_price=0.07
                )

                # Marcar como procesado y vincular al proyecto
                from django.contrib.contenttypes.models import ContentType
                project_content_type = ContentType.objects.get_for_model(Project)

                inbox_item.is_processed = True
                inbox_item.processed_to_content_type = project_content_type
                inbox_item.processed_to_object_id = project.id
                inbox_item.processed_at = timezone.now()
                inbox_item.save()

                messages.success(request, f'Proyecto "{project.title}" creado exitosamente desde el inbox GTD')
                return redirect('projects', project.id)

            except Exception as e:
                messages.error(request, f'Error al crear el proyecto: {e}')

        elif action == 'reference':
            # Guardar como referencia (no accionable)
            inbox_item.gtd_category = 'no_accionable'
            inbox_item.action_type = 'archivar'
            inbox_item.is_processed = True
            inbox_item.processed_at = timezone.now()
            inbox_item.save()

            messages.success(request, f'Item "{inbox_item.title}" guardado como referencia')
            return redirect('inbox')

        elif action == 'someday':
            # Guardar como "algún día/quizás" (no accionable)
            inbox_item.gtd_category = 'no_accionable'
            inbox_item.action_type = 'incubar'
            inbox_item.is_processed = True
            inbox_item.processed_at = timezone.now()
            inbox_item.save()

            messages.success(request, f'Item "{inbox_item.title}" guardado para "Algún día/Quizás"')
            return redirect('inbox')

        elif action == 'choose_existing_task':
            # Mostrar modal para elegir tarea existente
            # Esta acción solo muestra el modal, no procesa nada
            return redirect('process_inbox_item', item_id=item_id)

        elif action == 'choose_existing_project':
            # Mostrar modal para elegir proyecto existente
            # Esta acción solo muestra el modal, no procesa nada
            return redirect('process_inbox_item', item_id=item_id)

    # GET request - mostrar formulario de procesamiento
    # Obtener estadísticas del usuario para el template
    processed_count = InboxItem.objects.filter(created_by=request.user, is_processed=True).count()
    unprocessed_count = InboxItem.objects.filter(created_by=request.user, is_processed=False).count()

    # Buscar tareas y proyectos similares para evitar duplicados
    similar_tasks = find_similar_tasks(
        user=request.user,
        title=inbox_item.title,
        description=inbox_item.description,
        threshold=0.5  # Umbral más bajo para mostrar más resultados
    )

    similar_projects = find_similar_projects(
        user=request.user,
        title=inbox_item.title,
        description=inbox_item.description,
        threshold=0.5  # Umbral más bajo para mostrar más resultados
    )

    # Categorizar similitudes por nivel de confianza
    high_confidence_tasks = [t for t in similar_tasks if t['similarity'] >= 0.8]
    medium_confidence_tasks = [t for t in similar_tasks if 0.6 <= t['similarity'] < 0.8]
    low_confidence_tasks = [t for t in similar_tasks if 0.5 <= t['similarity'] < 0.6]

    high_confidence_projects = [p for p in similar_projects if p['similarity'] >= 0.8]
    medium_confidence_projects = [p for p in similar_projects if 0.6 <= p['similarity'] < 0.8]
    low_confidence_projects = [p for p in similar_projects if 0.5 <= p['similarity'] < 0.6]

    # Opciones GTD para el template
    gtd_categories = [
        {'value': 'accionable', 'label': 'Accionable', 'icon': 'bi-check-circle', 'color': 'success'},
        {'value': 'no_accionable', 'label': 'No Accionable', 'icon': 'bi-x-circle', 'color': 'info'},
    ]

    action_types = [
        {'value': 'hacer', 'label': 'Hacer', 'icon': 'bi-check2', 'color': 'success', 'category': 'accionable'},
        {'value': 'delegar', 'label': 'Delegar', 'icon': 'bi-people', 'color': 'warning', 'category': 'accionable'},
        {'value': 'posponer', 'label': 'Posponer', 'icon': 'bi-clock', 'color': 'info', 'category': 'accionable'},
        {'value': 'proyecto', 'label': 'Convertir en Proyecto', 'icon': 'bi-folder-plus', 'color': 'primary', 'category': 'accionable'},
        {'value': 'eliminar', 'label': 'Eliminar', 'icon': 'bi-trash', 'color': 'danger', 'category': 'no_accionable'},
        {'value': 'archivar', 'label': 'Archivar para Referencia', 'icon': 'bi-archive', 'color': 'secondary', 'category': 'no_accionable'},
        {'value': 'incubar', 'label': 'Incubar (Algún Día)', 'icon': 'bi-lightbulb', 'color': 'light', 'category': 'no_accionable'},
        {'value': 'esperar', 'label': 'Esperar Más Información', 'icon': 'bi-hourglass', 'color': 'warning', 'category': 'no_accionable'},
    ]

    context = {
        'title': 'Procesar Item del Inbox GTD',
        'inbox_item': inbox_item,
        'processed_count': processed_count,
        'unprocessed_count': unprocessed_count,
        # Resultados de búsqueda de duplicados
        'similar_tasks': similar_tasks,
        'similar_projects': similar_projects,
        'high_confidence_tasks': high_confidence_tasks,
        'medium_confidence_tasks': medium_confidence_tasks,
        'low_confidence_tasks': low_confidence_tasks,
        'high_confidence_projects': high_confidence_projects,
        'medium_confidence_projects': medium_confidence_projects,
        'low_confidence_projects': low_confidence_projects,
        'has_similar_items': len(similar_tasks) + len(similar_projects) > 0,
        # Opciones GTD
        'gtd_categories': gtd_categories,
        'action_types': action_types,
    }

    return render(request, 'events/process_inbox_item.html', context)

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
import logging


logger = logging.getLogger(__name__)

@login_required
def events(request):
    logger.info("Starting events view processing")
    
    try:
        today = timezone.now().date()
        title = "Events Origin"
        logger.debug(f"Current date: {today}, Page title: {title}")

        # Initialize session variables for first-time visitors
        if request.session.get('first_session', True):
            logger.info("Initializing session variables for new user session")
            try:
                status_in_progress = Status.objects.get(status_name='In Progress').id
                logger.debug(f"Found 'In Progress' status with ID: {status_in_progress}")
            except ObjectDoesNotExist:
                status_in_progress = None
                logger.warning("'In Progress' status not found in database")
            
            completed = request.session.setdefault('filtered_completed', True)
            status = request.session.setdefault('filtered_status', status_in_progress)
            date = request.session.setdefault('filtered_date', today.isoformat())
            request.session['first_session'] = False
            logger.debug(f"Initial filter values - Completed: {completed}, Status: {status}, Date: {date}")

        # Get events data
        logger.info("Retrieving events data")
        event_manager = EventManager(request.user)
        events, active_events = event_manager.get_all_events()
        event_statuses = Status.objects.all().order_by('status_name')
        logger.debug(f"Retrieved {len(events)} events and {event_statuses.count()} status options")

        if request.method == 'POST':
            logger.info("Processing POST request with new filters")
            completed = request.POST.get('completed', 'False').lower() == 'true'
            status = int(request.POST.get('status')) if request.POST.get('status') else None
            date = request.POST.get('date')
            logger.debug(f"Received filter values - Completed: {completed}, Status: {status}, Date: {date}")

            try:
                # Apply completed filter
                if completed:
                    logger.debug("Applying completed events filter")
                    status_completed = Status.objects.get(status_name='Completed')
                    events = [event for event in events if event['event'].event_status_id != status_completed.id]
                    request.session['filtered_completed'] = True
                    logger.info(f"Filtered out completed events, remaining: {len(events)}")
                else:
                    request.session['filtered_completed'] = False
                    logger.debug("Including completed events in results")

                # Apply status filter
                if status:
                    events = [event for event in events if event['event'].event_status_id == status]
                    request.session['filtered_status'] = status
                    logger.info(f"Filtered by status ID {status}, remaining: {len(events)}")
                else:
                    request.session['filtered_status'] = status
                    logger.debug("No status filter applied")

                # Apply date filter
                if date:
                    filter_date = datetime.date.fromisoformat(date)
                    events = [event for event in events if event['event'].updated_at.date() == filter_date]
                    request.session['filtered_date'] = date
                    logger.info(f"Filtered by date {date}, remaining: {len(events)}")
                else:
                    request.session['filtered_date'] = date
                    logger.debug("No date filter applied")

            except Status.DoesNotExist as e:
                logger.error(f"Status filtering error: {str(e)}", exc_info=True)
                messages.error(request, f'An error occurred while filtering events: {e}')
            except Exception as e:
                logger.error(f"Unexpected filtering error: {str(e)}", exc_info=True)
                messages.error(request, f'An error occurred while filtering events: {e}')

        else:  # GET request
            logger.info("Processing GET request with stored filters")
            status = request.session.get('filtered_status')
            date = request.session.get('filtered_date')
            completed = request.session.get('filtered_completed')
            logger.debug(f"Using stored filter values - Completed: {completed}, Status: {status}, Date: {date}")

            try:
                # Apply stored completed filter
                if completed:
                    logger.debug("Applying stored completed filter")
                    status_completed = Status.objects.get(status_name='Completed')
                    events = [event for event in events if event['event'].event_status_id != status_completed.id]
                    logger.info(f"Filtered out completed events, remaining: {len(events)}")

                # Apply stored status filter
                if status:
                    events = [event for event in events if event['event'].event_status_id == status]
                    logger.info(f"Filtered by stored status ID {status}, remaining: {len(events)}")

                # Apply stored date filter
                if date:
                    filter_date = datetime.date.fromisoformat(date)
                    events = [event for event in events if event['event'].updated_at.date() == filter_date]
                    logger.info(f"Filtered by stored date {date}, remaining: {len(events)}")

            except Status.DoesNotExist as e:
                logger.error(f"Status filtering error: {str(e)}", exc_info=True)
                messages.error(request, f'An error occurred while filtering events: {e}')
            except Exception as e:
                logger.error(f"Unexpected filtering error: {str(e)}", exc_info=True)
                messages.error(request, f'An error occurred while filtering events: {e}')
                return redirect('index')

        # Prepare response data
        count_events = len(events)
        events_updated_today = len([event for event in events if event['event'].updated_at.date() == today])
        events_states = EventState.objects.all().order_by('-start_time')[:10]
        
        logger.info(f"Preparing response with {count_events} events ({events_updated_today} updated today)")
        
        context = {
            'title': title,
            'events_updated_today': events_updated_today,
            'count_events': count_events,
            'events': events,
            'event_statuses': event_statuses,
            'events_states': events_states,
        }
        
        return render(request, 'events/events.html', context)

    except Exception as e:
        logger.critical(f"Unexpected error in events view: {str(e)}", exc_info=True)
        messages.error(request, f'An error occurred while processing events: {e}')
        return redirect('index')
        
@login_required
def assign_attendee_to_event(request, event_id, user_id):
    try:
        # Obtén el evento y el usuario basado en los IDs proporcionados
        event = get_object_or_404(Event, pk=event_id)
        user = get_object_or_404(User, pk=user_id)

        # Crea una nueva instancia de EventAttendee
        event_attendee, created = EventAttendee.objects.get_or_create(
            user=user,
            event=event
        )

        if created:
            # El asistente fue asignado al evento exitosamente
            messages.success(request, 'Asistente asignado al evento con éxito.')
        else:
            # El asistente ya estaba asignado al evento
            messages.info(request, 'El asistente ya estaba asignado a este evento.')

        # Redirige a la página que desees, por ejemplo, la página de detalles del evento
        return redirect('event_detail', event_id=event_id)
    except Exception as e:
        # Si ocurre un error, muestra un mensaje de alerta y redirige al usuario a la página de inicio
        messages.error(request, 'Ha ocurrido un error al asignar el asistente al evento: {}'.format(e))
        return redirect('index')

@login_required
def event_create(request):
    title="Create New Event"
    try:
        if request.method == 'GET':
            try:
                default_status = Status.objects.get(status_name='Created').id
            except Status.DoesNotExist:
                messages.error(request, 'El estado "Creado" no existe. ')
                return redirect('index')

            default = {
                'assigned_to': request.user.id,
                'host': request.user.id,
                'event_status': default_status
            }
            form = CreateNewEvent(initial=default)
            # El resto del código sigue aquí...

        else:
            form = CreateNewEvent(request.POST)
            if form.is_valid():
                try:
                    # Obtén el estado inicial basado en la solicitud
                    if 'inbound' in request.POST or (hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'SU'):
                        initial_status_id = request.POST.get('event_status')
                    else:
                        initial_status_id = Status.objects.get(status_name='Created').id

                    try:
                        initial_status = Status.objects.get(id=initial_status_id)
                    except Status.DoesNotExist:
                        messages.error(request, f'El estado con el ID "{initial_status_id}" no existe.')
                        return redirect('index')
                    
                    # El resto de tu código sigue aquí...
                    
                    # Crear el evento con los datos validados del formulario
                    new_event = form.save(commit=False)
                    new_event.event_status = initial_status
                    new_event.host = request.user  # El host es siempre el creador del evento
                    if not hasattr(request.user, 'profile') or not hasattr(request.user.profile, 'role') or request.user.profile.role != 'SU':
                        new_event.assigned_to = request.user  # Establecer automáticamente assigned_to como el usuario actual si el usuario no es un 'SU'
                    new_event.save()

                    # Si el usuario es un supervisor, puede asignar el evento a cualquier usuario
                    attendees = form.cleaned_data.get('attendees')
                    for attendee in attendees:
                        # Asignar el usuario asignado como atendedor
                        EventAttendee.objects.create(
                            user=attendee,
                            event=new_event
                        )

                    messages.success(request, 'Evento creado con éxito.')
                    return redirect('events')
                except IntegrityError as e:
                    messages.error(request, f'Hubo un error al crear el evento: {e}')
            else:
                # Si el formulario no es válido, agregar los errores del formulario a los mensajes
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Error en el campo {field}: {error}')

        return render(request, 'events/event_create.html', {
            'form': form,
            'title':title,
            })
    
    except ObjectDoesNotExist:
        messages.error(request, 'El objeto solicitado no existe.')
        return redirect('index')
    except Exception as e:
        messages.error(request, f'Ha ocurrido un error inesperado: {e}')
        return redirect('index')

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'events/event_detail.html', {
        'event' :event,
        'events':events
    })

def event_edit(request, event_id=None):
    title="Event Edit"
    try:
        if event_id is not None:
            # Estamos editando un evento existente
            try:
                event = get_object_or_404(Event, pk=event_id)
            except Http404:
                messages.error(request, 'El evento con el ID "{}" no existe.'.format(event_id))
                return redirect('index')

            if request.method == 'POST':
                form = CreateNewEvent(request.POST, instance=event)
                if form.is_valid():
                    # Asigna el usuario autenticado como el editor
                    event.editor = request.user
                    print('guardando via post si es valido')

                    # Guardar el evento con el editor actual (usuario que realiza la solicitud)
                    for field in form.changed_data:
                        old_value = getattr(event, field)
                        new_value = form.cleaned_data.get(field)
                        event.record_edit(
                            editor=request.user,
                            field_name=field,
                            old_value=str(old_value),
                            new_value=str(new_value),
                            )
                    form.save()

                    messages.success(request, 'Evento guardado con éxito.')
                    return redirect('event_panel')  # Redirige a la página de lista de edición
                else:
                    messages.error(request, 'Hubo un error al guardar el evento. Por favor, revisa el formulario.')
            
            else:
                form = CreateNewEvent(instance=event)
                print(event.title)
            return render(request, 'events/event_edit.html', {
                'event':event,
                'form': form,
                'title':title,
                })
        else:
            # Estamos manejando una solicitud GET sin argumentos
            # Verificar el rol del usuario
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'SU':
                # Si el usuario es un 'SU', puede ver todos los eventos
                events = Event.objects.all().order_by('-updated_at')
            else:
                # Si no, solo puede ver los eventos que le están asignados o a los que asiste
                events = Event.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
            return render(request, 'events/event_list.html', {
                'events': events,
                'title': title,
                })
            
    except Exception as e:
        messages.error(request, 'Ha ocurrido un error: {}'.format(e))
        return redirect('index')

def event_status_change(request, event_id):
    try:
        if request.method != 'POST':
            return HttpResponse("Método no permitido", status=405)
        event = get_object_or_404(Event, pk=event_id)
        new_status_id = request.POST.get('new_status_id')
        new_status = get_object_or_404(Status, pk=new_status_id)
        if request.user is None:
            messages.error(request, "User is none: Usuario no autenticado")
            return redirect('index')
        if event.host is not None and (event.host == request.user or request.user in event.attendees.all()):
            old_status = event.event_status
            print("old_status:", old_status)
            event.record_edit(
                editor=request.user,
                field_name='event_status',
                old_value=str(old_status),
                new_value=str(new_status)
            )
        else:
            return HttpResponse("No tienes permiso para editar este evento", status=403)
    except Exception as e:
        print(f"Error: {str(e)}")
        return HttpResponse(f"Error: {str(e)}", status=500)

    return redirect('events')

def event_delete(request, event_id):
    # Asegúrate de que solo se pueda acceder a esta vista mediante POST
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=event_id)

        # Verificar si el usuario es un 'SU'
        if not (hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'SU'):
            messages.error(request, 'No tienes permiso para eliminar este evento.')
            return redirect(reverse('event_panel'))

        event.delete()
        messages.success(request, 'El evento ha sido eliminado exitosamente.')
    else:
        messages.error(request, 'Método no permitido.')
    return redirect(reverse('event_panel'))

import logging
logger = logging.getLogger(__name__)

def event_panel(request, event_id=None):
    title = "Event Panel"
    event_statuses, project_statuses, task_statuses = statuses_get()
    events_states = EventState.objects.all().order_by('-start_time')[:10]
    status_var = 'In Progress'

    try:
        status = Status.objects.get(status_name=status_var)
    except Status.DoesNotExist:
        status = None
    except Status.MultipleObjectsReturned:
        status = None
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        status = None

    event_manager = EventManager(request.user)
    project_manager = ProjectManager(request.user)
    task_manager = TaskManager(request.user)

    if event_id:
        event_data = event_manager.get_event_by_id(event_id)
        logger.info(f"[event Panel] Event data: {event_data}")
        if event_data:
            try:
                if not event_data['projects']:
                    messages.error(request, 'El evento no existe. Verifica el ID del evento.')
                    projects_data= None
                else :
                    projects_data = [project_manager.get_project_data(project.id) for project in event_data['projects']]
                    logger.info(f"Projects data: {projects_data}")
                
                if not event_data['tasks']:
                    messages.error(request, 'El evento no tiene tareas asignadas.') 
                    tasks_data = None
                else:
                    tasks_data = [task_manager.get_task_data(task) for task in event_data['tasks']]
            
            except Exception as e:
                messages.error(request, f'Error al obtener información de proyectos o tareas: {e}')
                return redirect('events')

            context = {
                'page': 'event_detail',
                'title': title,
                'event_data': event_data,
                'projects_data': projects_data,
                'tasks_data': tasks_data,
                'event_statuses': event_statuses,
                'project_statuses': project_statuses,
                'task_statuses': task_statuses,
            }
            try:
                return render(request, "events/event_panel.html", context)
            except Exception as e:
                messages.error(request, f'Ha ocurrido un error: {e}')
                return redirect('events')
        else:
            return render(request, '404.html', status=404)
    else:
        events, active_events = event_manager.get_all_events()

        # Calculate statistics for the template
        total_events = len(events)
        in_progress_count = sum(1 for event in events if event['event'].event_status.status_name == 'In Progress')
        completed_count = sum(1 for event in events if event['event'].event_status.status_name == 'Completed')
        created_count = sum(1 for event in events if event['event'].event_status.status_name == 'Created')

        event_details = {}
        for event_data in events:
            event_details[event_data['event'].id] = {
                'projects': event_data['projects'],
                'tasks': event_data['tasks']
            }
        return render(request, 'events/event_panel.html', {
            'page': 'event_panel',
            'title': title,
            'events': events,
            'event_details': event_details,
            'event_statuses': event_statuses,
            'events_states': events_states,
            'active_events': active_events,
            'total_events': total_events,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'created_count': created_count,
        })

def event_export(request):
    """Export events data"""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="events_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Description', 'Status', 'Venue', 'Host', 'Created At'])

    events = Event.objects.all().select_related('event_status', 'host')
    for event in events:
        writer.writerow([
            event.id,
            event.title,
            event.description or '',
            event.event_status.status_name if event.event_status else '',
            event.venue or '',
            event.host.username if event.host else '',
            event.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response

def event_bulk_action(request):
    """Handle bulk actions for events"""
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_events = request.POST.getlist('selected_items')

        if not selected_events:
            messages.error(request, 'No events selected.')
            return redirect('event_panel')

        events = Event.objects.filter(id__in=selected_events)

        if action == 'delete':
            count = events.count()
            events.delete()
            messages.success(request, f'Successfully deleted {count} event(s).')
        elif action == 'activate':
            count = events.update(event_status=Status.objects.get(status_name='In Progress'))
            messages.success(request, f'Successfully activated {count} event(s).')
        elif action == 'complete':
            count = events.update(event_status=Status.objects.get(status_name='Completed'))
            messages.success(request, f'Successfully completed {count} event(s).')

    return redirect('event_panel')

def event_history(request, event_id=None):
    title = 'Event History'
    if not event_id:
        if request.method == 'POST':
            pass
        else:
            events_history = EventState.objects.all().order_by('-start_time')
            return render(request, 'events/event_history.html', {
                'title':title,
                'events_history':events_history,
            })
    else:
        productive_status_name='In Progress'
        productive_status=get_object_or_404(Status, status_name=productive_status_name)
        events_history = EventState.objects.filter(Q(event_id=event_id, event_status=productive_status)).order_by('-start_time')

        return render(request, 'events/event_history.html', {
            'title':title,
            'events_history':events_history,
        })

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
            return redirect('index')  
        
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
            return redirect('index')  
                
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
            return redirect('index')
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


def _log_schedule_changes(schedule, changed_fields, original_values=None):
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
                # Get old value
                if original_values:
                    old_value = original_values.get(model_field, 'N/A')
                else:
                    old_attr = f'_original_{field}'
                    old_value = getattr(schedule, old_attr, 'N/A')

                # Get new value
                new_value = getattr(schedule, model_field)
                changes.append(f"{field}: {old_value} → {new_value}")
            except AttributeError as e:
                # Skip fields that don't exist on the model
                print(f"Warning: Could not log change for field {field} (mapped to {model_field}): {e}")
                continue

        # Aquí se podría guardar en un log de auditoría
        print(f"[AUDIT] Schedule {schedule.id} changed: {', '.join(changes)}")


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


# ============================================================================
# INBOX ADMINISTRATION SYSTEM
# ============================================================================

@login_required
def inbox_admin_dashboard(request):
    """
    Panel de administración de inboxes - Vista principal para gestionar items del inbox
    """
    # Verificar permisos de administrador
    if not (hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role in ['SU', 'ADMIN']):
        messages.error(request, 'No tienes permisos para acceder al panel de administración de inboxes.')
        return redirect('inbox')

    # Filtros
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')
    user_filter = request.GET.get('user', 'all')
    search_query = request.GET.get('search', '')

    # Base queryset
    inbox_items = InboxItem.objects.select_related(
        'created_by'
    ).prefetch_related(
        'authorized_users',
        'classification_votes',
        'inboxitemclassification_set'
    )

    # Aplicar filtros
    if status_filter == 'processed':
        inbox_items = inbox_items.filter(is_processed=True)
    elif status_filter == 'unprocessed':
        inbox_items = inbox_items.filter(is_processed=False)
    elif status_filter == 'public':
        inbox_items = inbox_items.filter(is_public=True)

    if category_filter != 'all':
        inbox_items = inbox_items.filter(gtd_category=category_filter)

    if user_filter != 'all':
        inbox_items = inbox_items.filter(created_by=user_filter)

    if search_query:
        inbox_items = inbox_items.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(created_by__username__icontains=search_query)
        )

    # Estadísticas generales
    stats = {
        'total': InboxItem.objects.count(),
        'processed': InboxItem.objects.filter(is_processed=True).count(),
        'unprocessed': InboxItem.objects.filter(is_processed=False).count(),
        'public': InboxItem.objects.filter(is_public=True).count(),
        'private': InboxItem.objects.filter(is_public=False).count(),
        'today': InboxItem.objects.filter(created_at__date=timezone.now().date()).count(),
        'this_week': InboxItem.objects.filter(created_at__gte=timezone.now() - timedelta(days=7)).count(),
    }

    # Items recientes
    recent_items = inbox_items[:10]

    # Usuarios activos
    active_users = User.objects.filter(
        models.Q(inboxitem__isnull=False) |
        models.Q(authorized_inbox_items__isnull=False) |
        models.Q(classified_inbox_items__isnull=False)
    ).distinct()[:20]

    context = {
        'title': 'Administración de Inbox GTD',
        'inbox_items': inbox_items,
        'recent_items': recent_items,
        'stats': stats,
        'active_users': active_users,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'user_filter': user_filter,
        'search_query': search_query,
    }

    return render(request, 'events/inbox_admin_dashboard.html', context)


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
def inbox_item_detail_admin(request, item_id):
    """
    Vista detallada de un item del inbox para administración
    """
    # Verificar permisos
    if not request.user.profile.role in ['SU', 'ADMIN']:
        messages.error(request, 'No tienes permisos para ver detalles de items del inbox.')
        return redirect('inbox_admin_dashboard')

    try:
        inbox_item = InboxItem.objects.select_related(
            'created_by'
        ).prefetch_related(
            'authorized_users',
            'classification_votes',
            'inboxitemclassification_set__user',
            'inboxitemauthorization_set__user'
        ).get(id=item_id)

        # Incrementar contador de vistas
        inbox_item.increment_views()

        # Obtener clasificaciones existentes
        classifications = inbox_item.inboxitemclassification_set.all()

        # Calcular consenso
        consensus_category = inbox_item.get_classification_consensus()
        consensus_action = inbox_item.get_action_type_consensus()

        # Historial de actividad
        activity_history = InboxItemHistory.objects.filter(inbox_item=inbox_item)[:20]

        context = {
            'title': f'Administrar: {inbox_item.title}',
            'inbox_item': inbox_item,
            'classifications': classifications,
            'consensus_category': consensus_category,
            'consensus_action': consensus_action,
            'activity_history': activity_history,
        }

        return render(request, 'events/inbox_item_detail_admin.html', context)

    except InboxItem.DoesNotExist:
        messages.error(request, 'Item del inbox no encontrado.')
        return redirect('inbox_admin_dashboard')


@login_required
def classify_inbox_item_admin(request, item_id):
    """
    Vista para clasificar un item del inbox desde el panel de administración
    """
    # Verificar permisos
    if not request.user.profile.role in ['SU', 'ADMIN']:
        messages.error(request, 'No tienes permisos para clasificar items del inbox.')
        return redirect('inbox_admin_dashboard')

    try:
        inbox_item = InboxItem.objects.get(id=item_id)
    except InboxItem.DoesNotExist:
        messages.error(request, 'Item del inbox no encontrado.')
        return redirect('inbox_admin_dashboard')

    if request.method == 'POST':
        gtd_category = request.POST.get('gtd_category')
        action_type = request.POST.get('action_type')
        priority = request.POST.get('priority', 'media')
        confidence = request.POST.get('confidence', 50)
        notes = request.POST.get('notes', '')

        # Crear o actualizar clasificación
        classification, created = InboxItemClassification.objects.get_or_create(
            inbox_item=inbox_item,
            user=request.user,
            defaults={
                'gtd_category': gtd_category,
                'action_type': action_type,
                'priority': priority,
                'confidence': confidence,
                'notes': notes
            }
        )

        if not created:
            # Actualizar clasificación existente
            classification.gtd_category = gtd_category
            classification.action_type = action_type
            classification.priority = priority
            classification.confidence = confidence
            classification.notes = notes
            classification.save()

        # Registrar en el historial
        InboxItemHistory.objects.create(
            inbox_item=inbox_item,
            user=request.user,
            action='classified',
            old_values=None,
            new_values={
                'gtd_category': gtd_category,
                'action_type': action_type,
                'priority': priority,
                'confidence': confidence
            }
        )

        messages.success(request, f'Clasificación guardada para "{inbox_item.title}"')
        return redirect('inbox_item_detail_admin', item_id=item_id)

    # GET request - mostrar formulario
    context = {
        'title': f'Clasificar: {inbox_item.title}',
        'inbox_item': inbox_item,
    }

    return render(request, 'events/classify_inbox_item_admin.html', context)


@login_required
def authorize_inbox_item(request, item_id):
    """
    Vista para autorizar usuarios a ver/clasificar un item del inbox
    """
    # Verificar permisos
    if not request.user.profile.role in ['SU', 'ADMIN']:
        messages.error(request, 'No tienes permisos para autorizar usuarios.')
        return redirect('inbox_admin_dashboard')

    try:
        inbox_item = InboxItem.objects.get(id=item_id)
    except InboxItem.DoesNotExist:
        messages.error(request, 'Item del inbox no encontrado.')
        return redirect('inbox_admin_dashboard')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        permission_level = request.POST.get('permission_level', 'classify')

        try:
            user = User.objects.get(id=user_id)

            # Crear autorización
            authorization, created = InboxItemAuthorization.objects.get_or_create(
                inbox_item=inbox_item,
                user=user,
                defaults={
                    'granted_by': request.user,
                    'permission_level': permission_level
                }
            )

            if not created:
                authorization.permission_level = permission_level
                authorization.granted_by = request.user
                authorization.save()

            # Registrar en el historial
            InboxItemHistory.objects.create(
                inbox_item=inbox_item,
                user=request.user,
                action='authorized',
                old_values=None,
                new_values={
                    'authorized_user': user.username,
                    'permission_level': permission_level
                }
            )

            messages.success(request, f'Autorización actualizada para {user.username}')
            return redirect('inbox_item_detail_admin', item_id=item_id)

        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')

    # GET request - mostrar formulario
    context = {
        'title': f'Autorizar Usuarios: {inbox_item.title}',
        'inbox_item': inbox_item,
    }

    return render(request, 'events/authorize_inbox_item.html', context)


@login_required
def inbox_admin_bulk_action(request):
    """
    Vista para acciones masivas en items del inbox
    """
    # Verificar permisos
    if not request.user.profile.role in ['SU', 'ADMIN']:
        messages.error(request, 'No tienes permisos para realizar acciones masivas.')
        return redirect('inbox_admin_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        selected_items = request.POST.getlist('selected_items')

        if not selected_items:
            messages.error(request, 'No se seleccionaron items.')
            return redirect('inbox_admin_dashboard')

        items = InboxItem.objects.filter(id__in=selected_items)

        if action == 'make_public':
            count = items.update(is_public=True)
            messages.success(request, f'Se hicieron públicos {count} item(s).')

        elif action == 'make_private':
            count = items.update(is_public=False)
            messages.success(request, f'Se hicieron privados {count} item(s).')

        elif action == 'mark_processed':
            count = 0
            for item in items:
                if not item.is_processed:
                    item.is_processed = True
                    item.processed_at = timezone.now()
                    item.save()
                    count += 1
            messages.success(request, f'Se marcaron como procesados {count} item(s).')

        elif action == 'delete':
            count = items.count()
            items.delete()
            messages.success(request, f'Se eliminaron {count} item(s).')

    return redirect('inbox_admin_dashboard')


@login_required
def get_available_tasks(request):
    """
    API endpoint para obtener tareas disponibles para vincular con items del inbox
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        search_term = request.GET.get('search', '').strip()

        # Obtener tareas del usuario
        user_tasks = Task.objects.filter(
            Q(host=request.user) | Q(assigned_to=request.user)
        ).select_related('task_status', 'project').order_by('-updated_at')

        # Filtrar por término de búsqueda si se proporciona
        if search_term:
            user_tasks = user_tasks.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(project__title__icontains=search_term)
            )

        # Limitar resultados para mejor rendimiento
        user_tasks = user_tasks[:50]

        tasks_data = []
        for task in user_tasks:
            tasks_data.append({
                'id': task.id,
                'title': task.title,
                'description': task.description[:100] + '...' if task.description and len(task.description) > 100 else task.description,
                'status': task.task_status.status_name,
                'status_color': task.task_status.color,
                'project': task.project.title if task.project else 'Sin proyecto',
                'project_id': task.project.id if task.project else None,
                'updated_at': task.updated_at.strftime('%d/%m/%Y %H:%M'),
                'important': task.important
            })

        return JsonResponse({
            'success': True,
            'tasks': tasks_data,
            'total': len(tasks_data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def get_available_projects(request):
    """
    API endpoint para obtener proyectos disponibles para vincular con items del inbox
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        search_term = request.GET.get('search', '').strip()

        # Obtener proyectos del usuario
        user_projects = Project.objects.filter(
            Q(host=request.user) | Q(assigned_to=request.user) | Q(attendees=request.user)
        ).distinct().select_related('project_status', 'event').order_by('-updated_at')

        # Filtrar por término de búsqueda si se proporciona
        if search_term:
            user_projects = user_projects.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(event__title__icontains=search_term)
            )

        # Limitar resultados para mejor rendimiento
        user_projects = user_projects[:50]

        projects_data = []
        for project in user_projects:
            projects_data.append({
                'id': project.id,
                'title': project.title,
                'description': project.description[:100] + '...' if project.description and len(project.description) > 100 else project.description,
                'status': project.project_status.status_name,
                'status_color': project.project_status.color,
                'event': project.event.title if project.event else 'Sin evento',
                'event_id': project.event.id if project.event else None,
                'task_count': project.task_set.count(),
                'updated_at': project.updated_at.strftime('%d/%m/%Y %H:%M'),
                'important': getattr(project, 'important', False)  # Si el proyecto tiene campo importante
            })

        return JsonResponse({
            'success': True,
            'projects': projects_data,
            'total': len(projects_data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


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

    return redirect('reminders_dashboard')
