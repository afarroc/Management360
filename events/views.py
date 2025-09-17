# Standard Library Imports
from datetime import timedelta
from decimal import Decimal
import datetime
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
    TaskProgram
)
from .forms import (
    CreateNewEvent, CreateNewProject, CreateNewTask, EditClassificationForm,
    EventStatusForm, TaskStatusForm, ProjectStatusForm
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
    project = get_object_or_404(Project, id=id)
    tasks=Task.objects.filter(project_id=id)
    return render(request, 'projects/detail.html', {
        'project' : project,
        'tasks':tasks
    })

def project_delete(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_id)
        if request.user.profile.role != 'SU':
            messages.error(request, 'No tienes permiso para eliminar este projecto.')
            return redirect(reverse('project_panel'))
        project.delete()
        messages.success(request, 'El pryecto ha sido eliminado exitosamente.')
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
            if request.user.profile.role != 'SU':
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

        return render(request, "tasks/tasks.html",{

            'instructions':instructions,
            'title':title,
            'urls':urls,
            'other_urls':other_urls,
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
        if request.user.profile.role != 'SU':
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
        if request.user.profile.role != 'SU':
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

def planning_task(request):
    # Define el rango de fechas para el horario (por ejemplo, una semana desde hoy)
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=7)
    
    # Obtener todas las tareas programadas dentro del rango de fechas
    task_programs = TaskProgram.objects.filter(start_time__date__range=(start_date, end_date))
    
    if not task_programs.exists():
        context = {
            'schedule': {},
            'days': [],
            'hours': range(0, 24),
        }
        return render(request, 'program/program.html', context)
    
    # Crear una matriz para el horario
    days = [(start_date + timedelta(days=i)) for i in range((end_date - start_date).days)]
    schedule = {day: {hour: [] for hour in range(24)} for day in days}
    
    min_hour = 24
    max_hour = 0
    
    # Llenar la matriz con las tareas programadas y determinar las horas mínimas y máximas
    for program in task_programs:
        day = program.start_time.date()
        hour = program.start_time.hour
        schedule[day][hour].append(program)
        if hour < min_hour:
            min_hour = hour
        if hour > max_hour:
            max_hour = hour
    
    # Ajustar las horas a mostrar
    hours = range(min_hour, max_hour + 1)
    
    context = {
        'schedule': schedule,
        'days': days,
        'hours': hours,
    }
    
    return render(request, 'program/program.html', context)

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
