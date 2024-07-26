# Django imports
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum, Count
from django.forms import formset_factory
from django.http import Http404, HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import FormView
from django.core.files.storage import FileSystemStorage
from django.db.models.functions import TruncDate

# Local imports from .models
from .models import Classification, Document, Image, Database, Event, EventAttendee, ProjectStatus, TaskStatus, Profile, Project, Status, Task, EventState, ProjectState, TaskState, TaskProgram

# Local imports from .forms
from .forms import (CreateNewEvent, CreateNewProject,CreateNewTask, CreateNewTask, EditClassificationForm, EducationForm,  ExperienceForm, ImageForm, DocumentForm, DatabaseForm, ProfileForm, SkillForm, EventStatusForm, TaskStatusForm, ProjectStatusForm
)

# Formsets
EducationFormSet = formset_factory(EducationForm, extra=1, can_delete=True)
ExperienceFormSet = formset_factory(ExperienceForm, extra=1, can_delete=True)
SkillFormSet = formset_factory(SkillForm, extra=1, can_delete=True)

# Create your views here.

# Principal

from datetime import timedelta
from django.utils import timezone

def calculate_percentage_increase(queryset, days):
    # Filtra los objetos actualizados en los últimos 'days' días
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    recent_objects = queryset.filter(created_at__range=(start_date, end_date))
    # Filtra los objetos actualizados antes de ese período
    previous_objects = queryset.filter(created_at__lt=start_date)
    # Calcula el número total de objetos en cada período
    count_recent_objects = recent_objects.count()
    count_previous_objects = previous_objects.count()
    print(count_recent_objects,count_previous_objects)
    # Calcula el porcentaje de incremento
    if count_previous_objects > 0:
        percentage_increase = ((count_recent_objects - count_previous_objects) / count_previous_objects) * 100
    else:
        percentage_increase = 0

    return percentage_increase

def index(request):
    title = "Pagina Principal"

    projects = Project.objects.all()
    count_projects = projects.count()  # Recuento de objetos en la lista
    
    tasks = Task.objects.all()
    count_tasks = tasks.count()  # Recuento de objetos en la lista
    
    events = Event.objects.all()
    count_events = events.count()  # Recuento de objetos en la lista
    
    # Ejemplo de uso:
    days_to_check = 7  # Cambia esto al número de días que desees analizar
    projects_increase = calculate_percentage_increase(projects, days_to_check)
    tasks_increase = calculate_percentage_increase(tasks, days_to_check)
    events_increase = calculate_percentage_increase(events, days_to_check)
    
    events_states = EventState.objects.all().order_by('-start_time')[:10]
    
    
    return render(request, "index/index.html", {
        'projects': projects,
        'tasks': tasks,
        'days_to_check': days_to_check,
        'events': events,
        'projects_increase': f"{projects_increase:.2f}%",
        'tasks_increase': f"{tasks_increase:.2f}%",
        'events_increase': f"{events_increase:.2f}%",
        'title': title,
        'count_projects': count_projects,
        'count_tasks': count_tasks,
        'count_events': count_events,
        'events_states': events_states,
    })

def home(request):
    return render(request, 'layouts/main.html')

def about(request):
    username = "Nano"
    return render(request, "about/about.html",{
        'username':username
    })

def blank(request):
        title="Blank Page"
        return render(request, "layouts/blank.html",{
            'title':title
    })

# Sessions

def signup(request):
    if request.method=="GET":
        return render(request, 'accounts/signup.html', {
            'form':UserCreationForm
        })       
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                # register user
                user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return(redirect('index'))  # Modificado aquí
            
            except IntegrityError:
                
                return render(request, 'accounts/signup.html', {
                    'form': UserCreationForm,
                    "error": "User already exist"
                })       
        return render(request, 'accounts/signup.html', { 
            'form': UserCreationForm,
            "error": "Password do not match"
        })    
    
def signout(request):
    logout(request)
    return(redirect('index'))

def signin(request):
    if request.method == "GET":
        return render(request,'accounts/signin.html',{
            'form':AuthenticationForm,
            })
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            print('user is none')
            return render(request,'accounts/signin.html',{
                'form':AuthenticationForm,
                'error':'Username or password is incorrect'
            })
        else:
            login(request, user)
            request.session.setdefault('first_session', True)
            return redirect('events')

# Proyects

# Project dashboard
    
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

### Panel de Proyectos ###
### V2 ###

from django.db.models import Q
from .models import Project, Task, ProjectStatus

def statuses_get():
    event_statuses = Status.objects.all().order_by('status_name')
    project_statuses = ProjectStatus.objects.all().order_by('status_name')
    task_statuses = TaskStatus.objects.all().order_by('status_name')
    return event_statuses, project_statuses, task_statuses

def projects_get(user):
    if hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'SU':
        user_projects = Project.objects.all().order_by('-updated_at')
    else:
        user_projects = Project.objects.filter(
            Q(assigned_to=user) | Q(attendees=user)
        ).distinct().order_by('-updated_at')
    tasks_by_project = {}
    for project in user_projects:
        tasks_by_project[project.id] = Task.objects.filter(project_id=project.id)
    projects = []
    active_status = ProjectStatus.objects.get(status_name='En Curso')
    for project in user_projects:
        tasks = tasks_by_project.get(project.id, [])
        project_data = {
            'project': project,
            'count_tasks': len(tasks),
            'tasks': tasks
        }
        projects.append(project_data)
    active_projects = [
        project_data for project_data in projects
        if project_data['project'].project_status_id == active_status.id
    ]
    return projects, active_projects

def project_panel(request, proeject_id=None):
    # Título de la página
    title = 'Projects Panel'
    objects = projects_get(request.user)
    statuses = statuses_get()
    # Creando el contexto para la plantilla

    try:
        if request.method=='POST':
            pass
        else:
            context = {
                'title': title,
                'event_statuses': statuses[0],
                'project_statuses': statuses[1],
                'task_statuses': statuses[2],
                'projects': objects[0],
                'active_projects': objects[1]
            }

            return render(request, 'projects/project_panel.html',context)
    except Exception  as e:
        messages.error(request,f'Ha ocurrido un error:({e})')
        return redirect('index')

def project_panel_(request, project_id=None):
    # Título del Proyecto
    title = "Panel de Proyectos"
    # Diccionarios de URLs e instrucciones
    urls = [
        {'url': 'task_create', 'name': 'Crear Tarea'},
        {'url': 'task_edit', 'name': 'Editar Tarea'},
    ]
    instructions = [
        {'instruction': 'Selecciona un elemento para ver detalles', 'name': 'Elementos'},
    ]
    projects_states = ProjectState.objects.all().order_by('-start_time')[:10]

    # Obtener las tareas para todos los proyectos
    tasks_by_project = {project.id: Task.objects.filter(project_id=project.id) for project in Project.objects.all()}

    status_var = 'En Curso'
    status = get_object_or_404(ProjectStatus, status_name=status_var)
    active_projects=Project.objects.filter(Q(project_status=status)).distinct().order_by('-updated_at')

    event_statuses = Status.objects.all().order_by('status_name')
    task_statuses = TaskStatus.objects.all().order_by('status_name')
    project_statuses = ProjectStatus.objects.all().order_by('status_name')

    try:
        if project_id:
            project = Project.objects.get(id=project_id)
            tasks = tasks_by_project.get(project_id, [])
            return render(request, "projects/project_panel.html", {
                'title': title,
                'urls': urls,
                'instructions': instructions,
                'project': project,
                'tasks': tasks,
                'event_statuses': event_statuses,
                'task_statuses': task_statuses,
                'project_statuses': project_statuses,
                'projects_states': projects_states,
            })
        else:
            # Verificar si el usuario es un superusuario ('SU')
            if request.user.is_superuser:
                user_projects = Project.objects.all().order_by('-updated_at')
            else:
                user_projects = Project.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')

            projects_with_task_count = [(project, tasks_by_project.get(project.id, []).count()) for project in user_projects]
            return render(request, 'projects/project_panel.html', {
                'active_projects': active_projects,
                'projects_with_task_count': projects_with_task_count,
                'instructions': instructions,
                'urls': urls,
                'title': title,
                'projects': user_projects,
                'event_statuses': event_statuses,
                'task_statuses': task_statuses,
                'project_statuses': project_statuses,
                'projects_states': projects_states,
            })
    except (Project.DoesNotExist, Task.DoesNotExist) as e:
        messages.error(request, f'Ha ocurrido un error: {e}')
        return redirect('project_panel')

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
        
def event_assign(request, event_id=None):
    title="Event Assign"
    try:
        if event_id:
            event = get_object_or_404(Event, id=event_id)
            all_projects = Project.objects.all().order_by('-updated_at')
            all_tasks = Task.objects.all().order_by('-updated_at')
            event_projects = all_projects.filter(event_id=event_id)
            event_tasks = all_tasks.filter(event_id=event_id)
            event_statuses = Status.objects.all().order_by('status_name')
            project_statuses = ProjectStatus.objects.all().order_by('status_name')
            task_statuses = TaskStatus.objects.all().order_by('status_name')

            # Excluimos los proyectos que ya están asociados a cualquier evento
            assigned_projects = Project.objects.filter(event__isnull=False)
            available_projects = all_projects.exclude(id__in=assigned_projects.values('id'))

            # Excluimos las tareas que ya están asociadas a cualquier evento
            assigned_tasks = Task.objects.filter(event__isnull=False)
            print(assigned_tasks)
            available_tasks = all_tasks.exclude(id__in=assigned_tasks.values('id'))

            if request.method == 'POST':
                assign_task_id = request.POST.get('assign_task_id')
                assign_project_id = request.POST.get('assign_project_id')

                if assign_task_id:
                    # Aquí va el código para manejar la asignación de tareas
                    task_to_assign = get_object_or_404(Task, id=assign_task_id)
                    task_to_assign.event_id = event_id
                    task_to_assign.save()
                    messages.success(request, f'La tarea {task_to_assign.id} ha sido asignada al evento {event_id} exitosamente.')
                    return redirect('event_assign')

                elif assign_project_id:
                    # Aquí va el código para manejar la asignación de proyectos
                    project_to_assign = get_object_or_404(Project, id=assign_project_id)
                    project_to_assign.event_id = event_id
                    project_to_assign.save()
                    messages.success(request, f'El proyecto {project_to_assign.id} ha sido asignado al evento {event_id} exitosamente.')
                    return redirect('event_assign')

                else:
                    messages.error(request, 'No se proporcionó un id de tarea o proyecto válido.')
                    return redirect('event_assign')

                
            else:
                print('my tasks', event_tasks)
                print('my projects',event_projects)
                
                return render(request, "events/event_assign.html", {
                    'title': f'{title} (GET With Id)',                
                    'event': event,
                    'available_projects': available_projects,
                    'available_tasks': available_tasks,
                    'event_projects': event_projects,
                    'event_tasks': event_tasks,
                    'event_statuses': event_statuses,
                    'project_statuses': project_statuses,
                    'task_statuses': task_statuses,
                })

        else:
            events = Event.objects.all().order_by('-updated_at')
            return render(request, "events/event_assign.html",{
                'title':f'{title} (No iD)',
                'events':events,
            })
            
    except Exception as e:
        messages.error(request, f'Ha ocurrido un error: {e}')
        return redirect('index')

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
        if project_id:
            # Aquí debes asignar el formulario con el proyecto seleccionado
            form = CreateNewTask(initial={'project': project_id})
        else:
            # Aquí puedes asignar el formulario sin ningún valor inicial
            form = CreateNewTask()

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

                    messages.success(request, 'Tareato guardado con éxito.')
                    return redirect('task_edit')  # Redirige a la página de lista de edición
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
            return render(request, 'tasks/task_list.html', {'tasks': tasks})
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
    
    title="Task Panel"
    event_statuses = Status.objects.all().order_by('status_name')
    task_statuses = TaskStatus.objects.all().order_by('status_name')
    project_statuses = ProjectStatus.objects.all().order_by('status_name')
    tasks_states = TaskState.objects.all().order_by('-start_time')[:10]

    if task_id:
        try:
            task = get_object_or_404(Task, id=task_id)
            project = task.project
            event = None  # Inicializa event
            if task.event_id:
                event = get_object_or_404(Event, pk=task.event_id)
            
            event_statuses = Status.objects.all().order_by('status_name')
            project_statuses = ProjectStatus.objects.all().order_by('status_name')
            task_statuses = TaskStatus.objects.all().order_by('status_name')
            return render(request, "tasks/task_panel.html", {
                'event_statuses': event_statuses,
                'project_statuses': project_statuses,
                'task_statuses': task_statuses,
                'title': title,
                'task': task,
                'project': project,
                'event': event,  # Pasa el evento a la plantilla
            })
        except Task.DoesNotExist:
            messages.error(request, 'La tarea no existe. Verifica el ID de la tarea.')
            return redirect('task_panel')
        except Exception as e:
            messages.error(request, 'Ha ocurrido un error: {}'.format(e))
            print(e)
            return redirect('task_panel')


        except Exception as e:
            messages.error(request, 'Ha ocurrido un error: {}'.format(e))
            print(e)
            return redirect('task_panel')
    else:
        
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'SU':
            # Si el usuario es un 'SU', puede ver todos los proyectos
            tasks = Task.objects.all().order_by('-updated_at')
        else:
            # Si no, solo puede ver los proyectos que le están asignados o a los que asiste
            tasks = Task.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
        status_var = 'En Curso'
        status = get_object_or_404(TaskStatus, status_name=status_var)
        active_tasks=Task.objects.filter(Q(task_status=status)).distinct().order_by('-updated_at')
        return render(request, 'tasks/task_panel.html', {
            'title':title,
            'event_statuses':event_statuses,
            'task_statuses':task_statuses,
            'project_statuses':project_statuses,
            'tasks': tasks,
            'active_tasks':active_tasks,
            'tasks_states':tasks_states,
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

def task_activate(request, task_id=None):
    switch ='En Curso'
    title='Task Activate'
    if task_id:
        task = get_object_or_404(Task, pk=task_id)
        event = get_object_or_404(Event, pk=task.event.id)
        if task.task_status.status_name == switch:
            switch ='Finalizado'
            
        try:
            new_task_status = TaskStatus.objects.get(status_name=switch)
            old_value = task.task_status.status_name
            task.task_status = new_task_status            
            new_value = task.task_status.status_name
            
            task.record_edit(
                editor=request.user,
                field_name='task_status',
                old_value=str(old_value),
                new_value=str(new_value),
                )
            task.save()
            messages.success(request, f'La tarea ha sido cambiada a estado {switch} exitosamente.')


            new_event_status = Status.objects.get(status_name=switch)
            old_value = event.event_status.status_name
            event.event_status = new_event_status
            new_value = event.event_status.status_name

            event.record_edit(
                editor=request.user,
                field_name='event_status',
                old_value=str(old_value),
                new_value=str(new_value),
                )
            
            event.save()
            messages.success(request, f'El evento ha sido cambiado a estado {switch} exitosamente.')

            
            
        except TaskStatus.DoesNotExist:
            messages.error(request, 'El estado "En Curso" no existe en la base de datos.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al intentar activar la tarea: {e}')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
        tasks = Task.objects.all().order_by('-updated_at')
        # Crea una lista para almacenar los proyectos y sus recuentos de tareas
        try:
            return render(request, "tasks/task_activate.html",{
                'title':f'{title} (No iD)',
                'tasks':tasks,
            })
        except Exception as e:
            messages.error(request, 'Ha ocurrido un error: {}'.format(e))
            return redirect('task_panel')



# Events
@login_required
def events(request):
    today = timezone.now().date()
    title="Events Origen"
    
    if request.session['first_session'] == True:
        try:
            status_en_curso = Status.objects.get(status_name='En curso').id
        except ObjectDoesNotExist:
            status_en_curso = None
        cerrado = request.session.setdefault('filtered_cerrado', True)
        status = request.session.setdefault('filtered_status', status_en_curso)
        date = request.session.setdefault('filtered_date', timezone.now().date().isoformat())
        request.session['first_session'] = False  

    try:
        if hasattr(request.user, 'profile'):
            if request.user.profile.role == 'SU':
                events = Event.objects.all().order_by('-updated_at')
            else:
                events = Event.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')                
        else:
            events = Event.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
            
        event_statuses = Status.objects.all().order_by('status_name')
        
        if request.method == 'POST':
            cerrado = request.POST.get('cerrado', 'False').lower() == 'true'
            status = int(request.POST.get('status')) if request.POST.get('status') else None
            date = request.POST.get('date')
                        
            try:
                if cerrado:
                    status_cerrado = Status.objects.get(status_name='Cerrado')
                    events = events.exclude(event_status_id=status_cerrado.id)
                    request.session['filtered_cerrado'] = True
                else:
                    request.session['filtered_cerrado'] = False

            except Status.DoesNotExist:
                messages.error(request, f'Ha ocurrido un error al filtrar los eventos: {e}')
                
            if status:
                events = events.filter(event_status_id=status)
                request.session['filtered_status'] = status
            else:
                request.session['filtered_status'] = status
                
            if date:
                events = events.filter(updated_at__date=date)
                request.session['filtered_date'] = date
            else:
                request.session['filtered_date'] = date
            
            count_events = events.count()  # Aquí es donde obtienes el recuento de eventos
            # Filtra los eventos que fueron actualizados hoy y cuenta el número de esos eventos
            events_updated_today = events.filter(updated_at__date=today).count()
            
            events_states = EventState.objects.all().order_by('-start_time')[:10]

            return render(request, 'events/events.html', {
                'title': title,
                'events_updated_today': events_updated_today,
                'count_events': count_events,
                'events': events,
                'event_statuses': event_statuses,
                'events_states': events_states,
            })
            
        else:
            status = request.session['filtered_status'] 
            date = request.session['filtered_date']
            cerrado = request.session['filtered_cerrado']
            try:
                if cerrado:
                    status_cerrado = Status.objects.get(status_name='Cerrado')
                    events = events.exclude(event_status_id=status_cerrado.id)                    
                if status:
                    events = events.filter(event_status_id=status)
                if date:
                    events = events.filter(updated_at__date=date)

                                  
            except Status.DoesNotExist:
                messages.error(request, f'Ha ocurrido un error al filtrar los eventos: {e}')
                
            except Exception as e:
                messages.error(request, f'Ha ocurrido un error al filtrar los eventos: {e}')
                return redirect('index')
            
            count_events = events.count()  # Aquí es donde obtienes el recuento de eventos
            events_updated_today = events.filter(updated_at__date=today).count()
            events_states = EventState.objects.all().order_by('-start_time')[:10]

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
    title="Event Panel"
    event_statuses = Status.objects.all().order_by('status_name')
    project_statuses = ProjectStatus.objects.all().order_by('status_name')
    task_statuses = TaskStatus.objects.all().order_by('status_name')
    events_states = EventState.objects.all().order_by('-start_time')[:10]
    
    status_var = 'En Curso'
    status = get_object_or_404(Status, status_name=status_var)
    active_events=Event.objects.filter(Q(event_status=status)).distinct().order_by('-updated_at')


    if event_id:
        try:
            event = get_object_or_404(Event, id=event_id)
            print(event)
            try:
                projects = Project.objects.filter(event_id=event_id)
            except Project.DoesNotExist:
                projects= None

            try:
                tasks = Task.objects.filter(event_id=event_id)
            except Task.DoesNotExist:
                tasks= None
                
            if projects:
                print(projects)
            else:
                print('No projects')

            if tasks:
                print(tasks)
            else:
                print('No tasks')
                
            return render(request, "events/event_panel.html",{
                'title':title,
                'event':event,
                'tasks':tasks,
                'projects':projects,
                'event_statuses':event_statuses,
                'project_statuses':project_statuses,
                'task_statuses':task_statuses,                
            })

        except Exception as e:
            messages.error(request, 'Ha ocurrido un error!: {}'.format(e))
            return redirect('event_panel')

    else:
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'SU':
            # Si el usuario es un 'SU', puede ver todos los proyectos
            events = Event.objects.all().order_by('-updated_at')
        else:
            # Si no, solo puede ver los proyectos que le están asignados o a los que asiste
            events = Event.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
            
        return render(request, 'events/event_panel.html', {
            'title':title,
            'events': events,
            'event_statuses':event_statuses,
            'events_states':events_states,
            'active_events':active_events,

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
        
        events_history = EventState.objects.filter(Q(event_id=event_id)).order_by('-start_time')

        return render(request, 'events/event_history.html', {
            'title':title,
            'events_history':events_history,
        })
    
        
# Panel

def panel(request):
    events = Event.objects.all().order_by('-created_at')
    #events = events.filter(event_status_id = 2)
    return render(request, 'panel/panel.html', {'events': events})    

# Vistas para perfil de usuario

class ProfileView(View):
    def get(self, request, user_id=None):
        print(request.GET,user_id)
        try:
            if user_id:
                
                profile = Profile.objects.get(user_id=user_id)
                profile_form = ProfileForm(instance=profile)
                experience_formset = ExperienceFormSet(prefix='experiences', queryset=profile.experiences.all())
                education_formset = EducationFormSet(prefix='education', queryset=profile.education.all())
                skill_formset = SkillFormSet(prefix='skills', queryset=profile.skills.all())
            else:
                profile_form = ProfileForm()
                experience_formset = ExperienceFormSet(prefix='experiences')
                education_formset = EducationFormSet(prefix='education')
                skill_formset = SkillFormSet(prefix='skills')

            return render(request, 'profiles/profile_form.html', {
                'profile_form': profile_form,
                'experience_formset': experience_formset,
                'education_formset': education_formset,
                'skill_formset': skill_formset
            })
        except Exception as e:
            return render(request, 'profiles/error.html', {'message': str(e)})

    @transaction.atomic
    def post(self, request, user_id=None):
        try:
            profile = Profile.objects.get(user_id=user_id) if user_id else None
            profile_form = ProfileForm(request.POST, instance=profile)
            experience_formset = ExperienceFormSet(request.POST, prefix='experiences')
            education_formset = EducationFormSet(request.POST, prefix='education')
            skill_formset = SkillFormSet(request.POST, prefix='skills')

            if profile_form.is_valid() and all(formset.is_valid() for formset in [experience_formset, education_formset, skill_formset]):
                profile = profile_form.save(commit=False)
                profile.user = request.user
                profile.save()

                for form in experience_formset:
                    if form.cleaned_data.get('DELETE'):
                        if form.instance.pk:
                            form.instance.delete()
                    else:
                        experience = form.save(commit=False)
                        experience.profile = profile
                        experience.save()

                for form in education_formset:
                    if form.cleaned_data.get('DELETE'):
                        if form.instance.pk:
                            form.instance.delete()
                    else:
                        education = form.save(commit=False)
                        education.profile = profile
                        education.save()

                for form in skill_formset:
                    if form.cleaned_data.get('DELETE'):
                        if form.instance.pk:
                            form.instance.delete()
                    else:
                        skill = form.save(commit=False)
                        skill.profile = profile
                        skill.save()

                return redirect('view_profile')

            return render(request, 'profiles/profile_form.html', {
                'profile_form': profile_form,
                'experience_formset': experience_formset,
                'education_formset': education_formset,
                'skill_formset': skill_formset
            })
        except IntegrityError as e:
            return render(request, 'profiles/error.html', {'message': f"An error occurred. Please make sure all fields are filled out correctly. Error: {e}"})
        except Exception as e:
            return render(request, 'profiles/error.html', {'message': str(e)})

class ViewProfileView(View):
    def get(self, request, user_id):
        profile = Profile.objects.get(user_id=user_id)
        experiences = profile.experiences.all()
        education = profile.education.all()
        skills = profile.skills.all()

        return render(request, 'profiles/view_profile.html', {
            'profile': profile,
            'experiences': experiences,
            'education': education,
            'skills': skills
        })

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

# Document viewer

def document_view(request):
    documents = Document.objects.all()  # Obtiene todos los documentos
    images = Image.objects.all()        # Obtiene todas las imágenes
    databases = Database.objects.all()        # Obtiene todas las imágenes
    context = {
        'documents': documents,
        'images': images,
        'databases': databases,
    }
    return render(request, 'documents/docsview.html', context)

def delete_file(request, file_id, file_type):
    if file_type == 'document':
        file_model = Document
    elif file_type == 'image':
        file_model = Image
    else:
        messages.error(request, 'Tipo de archivo no válido.')
        return redirect('docsview')

    file_instance = get_object_or_404(file_model, id=file_id)
    if request.method == 'POST':
        file_instance.upload.delete()  # Esto elimina el archivo del sistema de archivos.
        file_instance.delete()         # Esto elimina la instancia del modelo de la base de datos.
        messages.success(request, f'El {file_type} ha sido eliminado exitosamente.')
        return redirect('docsview')
    else:
        # Si no es una solicitud POST, muestra la página de confirmación.
        return render(request, 'documents/confirmar_eliminacion.html', {'file': file_instance, 'type': file_type})

# Vista para subir documentos
class DocumentUploadView(FormView):
    template_name = 'documents/upload.html' # El nombre del template que quieres usar
    form_class = DocumentForm # El formulario que quieres usar
    success_url = reverse_lazy('docsview')# La url a la que quieres redirigir después de subir el archivo
    def form_valid(self, form):
        # Este método se ejecuta si el formulario es válido
        # Aquí puedes guardar el archivo en tu modelo
        file = form.cleaned_data['file'] # Obtiene el archivo del formulario
        document = Document(upload=file) # Crea una instancia de tu modelo con el archivo
        document.save() # Guarda el archivo en la base de datos
        return super().form_valid(form) # Retorna la vista de éxito

# Vista para subir imágenes
class ImageUploadView(FormView):
    template_name = 'documents/upload.html' # El nombre del template que quieres usar
    form_class = ImageForm # El formulario que quieres usar
    success_url = reverse_lazy('docsview')# La url a la que quieres redirigir después de subir el archivo

    def form_valid(self, form):
        # Este método se ejecuta si el formulario es válido
        # Aquí puedes guardar el archivo en tu modelo
        file = form.cleaned_data['file'] # Obtiene el archivo del formulario
        image = Image(upload=file) # Crea una instancia de tu modelo con el archivo
        image.save() # Guarda el archivo en la base de datos
        return super().form_valid(form) # Retorna la vista de éxito
    
    # Vista para subir db

# Vista para subir bases de datos
class UploadDatabase(FormView):
    template_name = 'documents/upload.html' # El nombre del template que quieres usar
    form_class = DatabaseForm # El formulario que quieres usar
    success_url = reverse_lazy('docsview')# La url a la que quieres redirigir después de subir el archivo

    def form_valid(self, form):
        # Este método se ejecuta si el formulario es válido
        # Aquí puedes guardar el archivo en tu modelo
        file = form.cleaned_data['file'] # Obtiene el archivo del formulario
        db = Database(upload=file) # Crea una instancia de tu modelo con el archivo
        db.save() # Guarda el archivo en la base de datos
        return super().form_valid(form) # Retorna la vista de éxito


# Vista para subir bases de datos

# views.py

from django.shortcuts import render
from openpyxl import load_workbook
from io import BytesIO

def upload_xlsx(request):
    if request.method == 'POST':
        form = DatabaseForm(request.POST, request.FILES)
        if form.is_valid():
            file_in_memory = request.FILES['file'].read()
            wb = load_workbook(filename=BytesIO(file_in_memory))
            print('Form is valid')
            # Procesa el archivo y realiza las operaciones necesarias
            # (filtrar columnas, cambiar títulos, etc.)
            # Luego, crea un nuevo archivo o modelo con los datos finales.
            # ...
            # Devuelve una respuesta al usuario (descargar archivo o mostrar datos).
    else:
        form = DatabaseForm()
    return render(request, 'documents/upload_xlsx.html', {'form': form})


# about upload

def upload_image(request):
    if request.method == 'POST':
        try:
            image = request.FILES['image']
            fs = FileSystemStorage()
            filename = fs.save(image.name, image)
            uploaded_file_url = fs.url(filename)
            messages.success(request, 'Imagen subida con éxito.')
            return redirect('about')
        except KeyError:
            messages.error(request, 'Por favor, selecciona una imagen para subir.')
    return render(request, 'about/about.html')

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

# views.py
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import TaskProgram

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

# views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CreditAccount
from decimal import Decimal

@login_required
def add_credits(request):
    user = request.user
    if not hasattr(user, 'creditaccount'):
        CreditAccount.objects.create(user=user)

    if request.method == 'POST':
        amount = request.POST['amount']
        try:
            amount = Decimal(amount)  # Convertir a Decimal
            user.creditaccount.add_credits(amount)
            messages.success(request,"Monto agregado")

            return redirect('index')  # Redirige a alguna página de perfil u otra página adecuada
            
        except (ValueError, Decimal.InvalidOperation):
            return render(request, 'credits/add_credits.html', {'error': 'Monto no válido'})

    return render(request, 'credits/add_credits.html')



from django.shortcuts import render, get_object_or_404
from .models import Project, Task, TaskStatus, ProjectStatus, Event

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
