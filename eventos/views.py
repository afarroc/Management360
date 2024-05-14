from .models import Project, Task, Event, Status
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from .forms import CreateNewTask, CreateNewProject, CreateNewEvent
from django.urls import reverse

# Create your views here.

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
    username = "Fazt"
    return render(request, "about.html",{
        'username':username
    })
# Vista Cambio de evento

def change_event_status(request, event_id):
    # Obtener evento desde el event_id
    print("\n ---- Vista 'Cambio de estado' ----")
    print("Cambiando estado del evento con  ID:", str(event_id))
    
    # Obtener evento
    event = get_object_or_404(Event, pk=event_id)
    print("titulo:",str(event.title))
    print("estado:",str(event.event_status.status_name))
    # Cambiar al nuevo estado el evento seleccionado
    print("Nuevo id de estado: ",str(request.POST.get('new_status_id')))
    new_status_id = request.POST.get('new_status_id')
    new_status = get_object_or_404(Status, pk=new_status_id)
    event.event_status = new_status
    
    # Guardar Cambios
    event.save()
    
    # Guardar el estado del filtro en la sesión
    request.session['status'] = request.POST.get('status')

    print("\n ---- Fin de vista 'cambio de estado' ----")
    return redirect(reverse('events'))

def events(request):
    # Obtener las variables de la solicitud 
    status_id = request.POST.get('status') or request.session.get('status')
    date = request.POST.get('date')

    print(status_id)
    print(date)
    
    # Obtener Eventos ordenados descendentemente por fecha de creacion 
    events = Event.objects.all().order_by('-created_at')    

    # Obtener Estados disponibles ordenados por nombre
    statuses = Status.objects.all().order_by('status_name')
    
    # aplicar filtros si existen datos en la solicitud
    if status_id:
        events = events.filter(event_status_id=status_id)
        print("Filtardo por id"," ",status_id)
    if date:
        events = events.filter(created_at__date=date)
        print("Filtrado por fecha"," ",date)

    # devolver solcitud

    return render(request, 'events/events.html', {
        'events': events,
        'statuses': statuses,
        'status': status_id
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

