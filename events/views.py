# Standard Library Imports
from datetime import timedelta
from decimal import Decimal
import datetime
from collections import defaultdict

# Django Imports
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum, Count, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate
from django.http import Http404, HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
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
    TaskStatus, Project, Status, Task, EventState, ProjectState, TaskState,
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

# Proyects
def projects(request, project_id=None):

    # Obtén la cantidad de eventos, proyectos y tareas por día
    events_per_day = Event.objects.annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')
    projects_per_day = Project.objects.annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')
    tasks_per_day = Task.objects.annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')

    # Extrae solo los conteos y conviértelos en listas
    events_data = [item['count'] for item in events_per_day]
    projects_data = [item['count'] for item in projects_per_day]
    tasks_data = [item['count'] for item in tasks_per_day]

    # Obtén las fechas de los eventos, proyectos y tareas
    event_dates = Event.objects.dates('created_at', 'day')
    project_dates = Project.objects.dates('created_at', 'day')
    task_dates = Task.objects.dates('created_at', 'day')

    # Convierte los QuerySets a listas para usar en el gráfico
    event_dates = [date.strftime('%Y-%m-%dT%H:%M:%S.000Z') for date in event_dates]
    project_dates = [date.strftime('%Y-%m-%dT%H:%M:%S.000Z') for date in project_dates]
    task_dates = [date.strftime('%Y-%m-%dT%H:%M:%S.000Z') for date in task_dates]

    print(projects_data)

    print(project_dates)
    
    title="Projects"   
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
        {'instruction': 'Fill carefully the metadata.', 'name': 'Form'},
    ]
    project_statuses = ProjectStatus.objects.all().order_by('status_name')
    projects = Project.objects.all().order_by('-updated_at')
    total_projects = Project.objects.count()

    total_ticket_price = projects.aggregate(Sum('ticket_price'))

    # Define la fecha de referencia
    date = timezone.now() - timezone.timedelta(days=1)  # hace 30 días

    # Cuenta cuántos proyectos se han creado desde la fecha de referencia
    increase = Project.objects.filter(created_at__gte=date).count()
    
    print(total_ticket_price['ticket_price__sum'])
    
    if project_id:
        
        
        return render(request, "projects/projects.html",{
            'total_ticket_price':total_ticket_price['ticket_price__sum'],
            'instructions':instructions,
            'urls':urls,

        })
    else:
        return render(request, "projects/projects.html",{
            'total_ticket_price':total_ticket_price['ticket_price__sum'],
            'other_urls':other_urls,
            'urls':urls,
            'instructions':instructions,
            'increase':increase,
            'projects':projects,
            'total_projects':total_projects,
            'project_statuses':project_statuses,
            'title':title,
            'events_data':events_data,
            'projects_data':projects_data,
            'tasks_data':tasks_data,
            'event_dates':event_dates,
        
        })

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
                status = get_object_or_404(Status,status_name='Creado')
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

def project_panel(request, project_id=None):
    # Title of the page
    title = "Project detail"

    # Retrieve projects and statuses
    project_manager = ProjectManager(request.user)
    statuses = statuses_get()

    try:

        if project_id:
            # If a specific project_id is provided, handle it here
            project_data = project_manager.get_project_data(project_id)
            
            if project_data:
                context = {
                    'title': title,
                    'project_data': project_data,
                    'event_statuses': statuses[0],
                    'project_statuses': statuses[1],
                    'task_statuses': statuses[2],
                }
                return render(request, 'projects/project_panel.html', context)
            else:
                messages.error(request, f'Project with id {project_id} not found')
                return redirect('index')
        else:
            projects, active_projects = project_manager.get_all_projects()

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
                    'active_projects': active_projects
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
            active_status = ProjectStatus.objects.get(status_name='En Curso')
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
        
        return render(request, "tasks/tasks.html",{
            
            'instructions':instructions,
            'title':title,
            'urls':urls,
            'other_urls':other_urls,
            'task':task,
            'task_statuses':task_statuses,
            
        })

    else:  
        
        if not project_id:
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(project_id=project_id)

        return render(request, "tasks/tasks.html",{
            'title':title,
            'tasks':tasks
        })
            
@login_required
def task_create(request, project_id=None):
    title="Create New Task"
    
    if request.method == 'GET':
        try:
            initial_status_name = 'Creado'
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
                status = get_object_or_404(Status, status_name='Creado')
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
    print(f"Contexto cargado: {request.user}")
    if task_id:

        print(f"Task Id: {task_id}")
        task_data = task_manager.get_task_data(task_id)

        try:
            print(f"Trying: {type(task_data)}")
            if not task_data:
                messages.error(request, 'La tarea no existe. Verifica el ID de la tarea.')
                return redirect('task_panel')

            task = task_data['task']
            project_info = project_manager.get_project_data(task.project.id) if task.project else None
            event_info = event_manager.get_event_data(task.event) if task.event else None
            
            return render(request, "tasks/task_panel.html", {
                'event_statuses': statuses[0],
                'project_statuses': statuses[1],
                'task_statuses': statuses[2],
                'title': title,
                'task_data': task_data,
                'project_info': project_info,
                'event_info': event_info,
            })
        except Exception as e:
            messages.error(request, 'Ha ocurrido un error: {}'.format(e))
            print(e)
            return redirect('task_panel')
    else:
        tasks, active_tasks = task_manager.get_all_tasks()

        return render(request, 'tasks/task_panel.html', {
            'title': title,
            'event_statuses': statuses[0],
            'task_statuses': statuses[2],
            'project_statuses': statuses[1],
            'tasks': tasks,
            'active_tasks': active_tasks,
            'tasks_states': tasks_states,
        })

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

def task_activate(request, task_id=None):
    switch = 'En Curso'
    title = 'Task Activate'
    
    if task_id:
        task = get_object_or_404(Task, pk=task_id)
        event = task.event
        project = task.project
        project_event = project.event
        amount = 0
        
        if task.task_status.status_name == switch:
            switch = 'Finalizado'
            amount += 1           

        try:
            new_task_status = TaskStatus.objects.get(status_name=switch)
            update_status(task, 'task_status', new_task_status, request.user)
            messages.success(request, f'La tarea ha sido cambiada a estado {switch} exitosamente.')

            new_event_status = Status.objects.get(status_name=switch)
            update_status(event, 'event_status', new_event_status, request.user)
            messages.success(request, f'El evento de la tarea ha sido cambiado a estado {switch} exitosamente.')

            tasks_in_progress = Task.objects.filter(project_id=project.id, task_status__status_name='En Curso')

            if switch == 'Finalizado' and tasks_in_progress.exists():
                messages.success(request, f'There are tasks in progress: {tasks_in_progress}')
            else:
                new_project_status = ProjectStatus.objects.get(status_name=switch)
                update_status(project, 'project_status', new_project_status, request.user)
                messages.success(request, f'El proyecto ha sido cambiado a estado {switch} exitosamente.')
                
                update_status(project_event, 'event_status', new_event_status, request.user)
                messages.success(request, f'El evento del proyecto ha sido cambiado a estado {switch} exitosamente.')

            if task.task_status.status_name == "Finalizado":
                task_state = TaskState.objects.filter(
                    task=task,
                    status__status_name='En Curso'
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

from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from .models import Event, Status, EventState
from django.contrib.auth.decorators import login_required

@login_required
def events(request):
    print("Iniciando la función events...")
    today = timezone.now().date()
    title = "Events Origen"
    print(f"Fecha actual: {today}")
    print(f"Título: {title}")

    if request.session.get('first_session', True):
        print("Primera sesión detectada.")
        try:
            status_en_curso = Status.objects.get(status_name='En curso').id
            print(f"Status 'En curso' encontrado: {status_en_curso}")
        except ObjectDoesNotExist:
            status_en_curso = None
            print("Status 'En curso' no encontrado.")
        
        cerrado = request.session.setdefault('filtered_cerrado', True)
        status = request.session.setdefault('filtered_status', status_en_curso)
        date = request.session.setdefault('filtered_date', today.isoformat())
        request.session['first_session'] = False
        print(f"Valores iniciales - cerrado: {cerrado}, status: {status}, date: {date}")

    try:
        if hasattr(request.user, 'profile'):
            if request.user.profile.role == 'SU':
                events = Event.objects.all().order_by('-updated_at')
                print("Usuario con perfil SU, obteniendo todos los eventos.")
            else:
                events = Event.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
                print("Usuario sin perfil SU, filtrando eventos asignados o atendidos por el usuario.")
        else:
            events = Event.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
            print("Usuario sin perfil, filtrando eventos asignados o atendidos por el usuario.")
        
        event_statuses = Status.objects.all().order_by('status_name')
        print(f"Event statuses obtenidos: {event_statuses.count()}")

        if request.method == 'POST':
            print("Método POST detectado.")
            cerrado = request.POST.get('cerrado', 'False').lower() == 'true'
            status = int(request.POST.get('status')) if request.POST.get('status') else None
            date = request.POST.get('date')
            print(f"Valores POST - cerrado: {cerrado}, status: {status}, date: {date}")

            try:
                if cerrado:
                    status_cerrado = Status.objects.get(status_name='Cerrado')
                    events = events.exclude(event_status_id=status_cerrado.id)
                    request.session['filtered_cerrado'] = True
                    print("Eventos cerrados excluidos.")
                else:
                    request.session['filtered_cerrado'] = False
                    print("No se excluyen eventos cerrados.")

            except Status.DoesNotExist as e:
                messages.error(request, f'Ha ocurrido un error al filtrar los eventos: {e}')
                print(f"Error al filtrar eventos: {e}")
                
            if status:
                events = events.filter(event_status_id=status)
                request.session['filtered_status'] = status
                print(f"Eventos filtrados por status: {status}")
            else:
                request.session['filtered_status'] = status
                print("No se aplica filtro por status.")

            if date:
                events = events.filter(updated_at__date=date)
                request.session['filtered_date'] = date
                print(f"Eventos filtrados por fecha: {date}")
            else:
                request.session['filtered_date'] = date
                print("No se aplica filtro por fecha.")
            
            count_events = events.count()
            events_updated_today = events.filter(updated_at__date=today).count()
            events_states = EventState.objects.all().order_by('-start_time')[:10]

            print(f"Eventos actualizados hoy: {events_updated_today}")
            print(f"Total de eventos filtrados: {count_events}")
            print(events)
            return render(request, 'events/events.html', {
                'title': title,
                'events_updated_today': events_updated_today,
                'count_events': count_events,
                'events': events,
                'event_statuses': event_statuses,
                'events_states': events_states,
            })
            
        else:
            print("Método GET detectado.")
            status = request.session.get('filtered_status')
            date = request.session.get('filtered_date')
            cerrado = request.session.get('filtered_cerrado')
            print(f"Valores de sesión - cerrado: {cerrado}, status: {status}, date: {date}")

            try:
                if cerrado:
                    status_cerrado = Status.objects.get(status_name='Cerrado')
                    events = events.exclude(event_status_id=status_cerrado.id)
                    print("Eventos cerrados excluidos.")
                if status:
                    events = events.filter(event_status_id=status)
                    print(f"Eventos filtrados por status: {status}")
                if date:
                    events = events.filter(updated_at__date=date)
                    print(f"Eventos filtrados por fecha: {date}")

            except Status.DoesNotExist as e:
                messages.error(request, f'Ha ocurrido un error al filtrar los eventos: {e}')
                print(f"Error al filtrar eventos: {e}")
                
            except Exception as e:
                messages.error(request, f'Ha ocurrido un error al filtrar los eventos: {e}')
                print(f"Error inesperado al filtrar eventos: {e}")
                return redirect('index')
            
            count_events = events.count()
            events_updated_today = events.filter(updated_at__date=today).count()
            events_states = EventState.objects.all().order_by('-start_time')[:10]

            print(f"Eventos actualizados hoy: {events_updated_today}")
            print(f"Total de eventos filtrados: {count_events}")
            for event_data in events:
                print(event_data.id)
                pass
            
            return render(request, 'events/events.html', {
                'events_updated_today': events_updated_today,
                'count_events': count_events,
                'events': events,
                'event_statuses': event_statuses,
                'title': title,
                'events_states': events_states,
            })
            
    except Exception as e:
        messages.error(request, 'Ha ocurrido un error al obtener los eventos: {}'.format(e))
        print(f"Error inesperado en la función events: {e}")
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
                default_status = Status.objects.get(status_name='Creado').id
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
                        initial_status_id = Status.objects.get(status_name='Creado').id

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

def event_panel(request, event_id=None):
    title = "Event Panel"
    event_statuses, project_statuses, task_statuses = statuses_get()
    events_states = EventState.objects.all().order_by('-start_time')[:10]
    status_var = 'En Curso'

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
        print(event_data)
        if event_data:

            projects_info = [project_manager.get_project_data(project.id) for project in event_data['projects']]
            tasks_info = [task_manager.get_task_data(task) for task in event_data['tasks']]
            
            return render(request, "events/event_panel.html", {
                'title': title,
                'event_data': event_data,
                'projects_info': projects_info,
                'tasks_info': tasks_info,
                'event_statuses': event_statuses,
                'project_statuses': project_statuses,
                'task_statuses': task_statuses,
            })
        else:
            return render(request, '404.html', status=404)

    else:
        events, active_events = event_manager.get_all_events()
        
        event_details = {}
        for event_data in events:
            event_details[event_data['event'].id] = {
                'projects': event_data['projects'],
                'tasks': event_data['tasks']
            }

        return render(request, 'events/event_panel.html', {
            'title': title,
            'events': events,
            'event_details': event_details,
            'event_statuses': event_statuses,
            'events_states': events_states,
            'active_events': active_events,
        })

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
        productive_status_name='En Curso'
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

def management(request):
    # Obtén los eventos asignados al usuario logueado
    eventos_asignados = Event.objects.filter(assigned_to=request.user).order_by('-created_at')
    classifications = Classification.objects.all()

    if request.method == 'POST':
        # Obtén el evento y la clasificación del formulario
        evento_id = request.POST.get('evento')
        classification_id = request.POST.get('classification')
        comentario = request.POST.get('comentario')

        # Encuentra el evento y la clasificación en la base de datos
        evento = Event.objects.get(id=evento_id)
        classification = Classification.objects.get(id=classification_id)

        # Actualiza el evento
        evento.classification = classification
        evento.comentario = comentario
        evento.estado = 'Finalizado'
        evento.save()

        messages.success(request, 'Evento actualizado con éxito.')
        return redirect(reverse('manager'))

    return render(request, 'management/manager.html', {
        'eventos_asignados': eventos_asignados,
        'classifications': classifications
        })

# Añade esta función a tu vista 
def update_event(request):
    if request.method == 'POST':
        # Obtén el ID del evento y si está seleccionado o no
        evento_id = request.POST.get('evento')
        selected = request.POST.get('selected') == 'true'

        # Encuentra el evento en la base de datos
        evento = Event.objects.get(id=evento_id)

        # Actualiza el estado del evento
        evento.estado = 'Finalizado' if selected else 'No finalizado'
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
    task_active_status = TaskStatus.objects.filter(status_name='En curso').first()
    task_finished_status = TaskStatus.objects.filter(status_name='Finalizado').first()
    project_active_status = ProjectStatus.objects.filter(status_name='En curso').first()
    project_finished_status = ProjectStatus.objects.filter(status_name='Finalizado').first()

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

            # Actualizar el estado del proyecto a finalizado
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
    
    # Obtener el estado 'En Curso'
    in_progress_status = get_object_or_404(TaskStatus, status_name='En Curso')
    
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
