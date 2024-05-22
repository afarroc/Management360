from .models import Project, Task, Event, Status
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from .forms import CreateNewTask, CreateNewProject, CreateNewEvent, EventForm
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
# Create your views here.


def edit_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    return render(request, 'edit_event.html', {'form': form})









def signup(request):
    
    if request.method=="GET":
        return render(request, 'signup.html', {
            'form':UserCreationForm
        })       
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                # register user
                user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return(redirect('events'))
            
            except IntegrityError:
                
                return render(request, 'signup.html', {
                    'form': UserCreationForm,
                    "error": "User already exist"
                })       
        return render(request, 'signup.html', { 
            'form': UserCreationForm,
            "error": "Password do not match"
        })    
    
def signout(request):
    logout(request)
    return(redirect('index'))

def signin(request):
    if request.method == "GET":
        return render(request,'signin.html',{
            'form':AuthenticationForm,
            })
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request,'signin.html',{
                'form':AuthenticationForm,
                'error':'Username or password is incorrect'
            })
        else:
            login(request, user)
            return redirect('events')
            
def panel(request):
    events = Event.objects.all()
    return render(request, 'panel/panel.html', {'events': events})    

def delete_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.delete()
    return redirect(reverse('events'))
    
def index(request):
    title="Django Course!!"
    return render(request, "index.html",{
        'title':title
    })

def about(request):
    username = "Nano"
    return render(request, "about.html",{
        'username':username
    })

def change_event_status(request, event_id):
    # Obtener evento desde el event_id
    print("\n ---- Vista 'Cambio de estado' ----")
    print("Cambiando estado del evento con ID:", str(event_id))
    
    # Obtener evento
    event = get_object_or_404(Event, pk=event_id)
    
    print("Título:", str(event.title))
    print("Estado:", str(event.event_status.status_name))
    
    # Cambiar al nuevo estado el evento seleccionado
    print("Nuevo ID de estado:", str(request.POST.get('new_status_id')))
    
    new_status_id = request.POST.get('new_status_id')
    new_status = get_object_or_404(Status, pk=new_status_id)
    event.event_status = new_status
    
    # Guardar cambios
    event.save()
    
    # Guardar el estado del filtro en la sesión
    print('Estado filtrado:', request.POST.get('status'))

    print("---- Fin de vista 'cambio de estado' ----\n")
    
    print("contenido de post antes de redireccionar: ", request.POST )
    
    # Devolver la redirección a la página de eventos
    return redirect(reverse('events'))
    
def events(request):
    
    print("Inicio vista Events")
    print(request.POST)

    status = request.POST.get('status')
    date = request.POST.get('date')

    events = Event.objects.all().order_by('-created_at')    
    statuses = Status.objects.all().order_by('status_name')
    
    if request.method == 'POST':
        print("Solicitud POST")
        if status:
            events = events.filter(event_status_id=status)
            print("Filtardo por id de estado"," ",status)
        if date:
            events = events.filter(created_at__date=date)
            print("Filtrado por fecha"," ",date)
        print("Fin vista Events")
        
        return render(request, 'events/events.html', {
            'events': events,
            'statuses': statuses,
            'status': status
            })
    else:
        print("Solicitud GET")
        print("Fin vista Events")
        print(request.GET)
        return render(request, 'events/events.html', {
            'events': events,
            'statuses': statuses,
            'status': status
            })
 
def projects(request):
    projects = Project.objects.all()
    return render(request, "projects/projects.html",{
        'projects':projects
    })

def task(request):
    tasks = Task.objects.all()
    return render(request, "tasks/tasks.html",{
        'tasks':tasks
    })

def create_event(request):
    if request.method == 'GET':
        return render(request, 'events/create_event.html',{
            'form':CreateNewEvent()
            })
    else:
        Event.objects.create(title=request.POST['title'], description=request.POST['description'])
        return redirect('events')
    
def create_task(request):
    if request.method == 'GET':
        return render(request, 'tasks/create_task.html',{
            'form':CreateNewTask()
            })
    else:
        Task.objects.create(title=request.POST['title'], description=request.POST['description'], project_id=1)
        return redirect('tasks')

def create_project(request):
    if request.method == 'GET':
        return render(request, 'projects/create_project.html', {
            'form':CreateNewProject()
        })
    else:

        Project.objects.create(name=request.POST['name'])
        return redirect('projects')
  
def project_detail(request, id):
    project = get_object_or_404(Project, id=id)
    tasks=Task.objects.filter(project_id=id)
    return render(request, 'projects/detail.html', {
        'project' : project,
        'tasks':tasks
    })
    
def event_detail(request, id):
    event = get_object_or_404(Event, id=id)
    return render(request, 'events/detail.html', {
        'event' :event,
        'events':events
    })

