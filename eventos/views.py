from .models import Project, Task, Event, Status
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from .forms import CreateNewTask, CreateNewProject, CreateNewEvent
from django.urls import reverse

# Create your views here.

def panel(request):
    events = Event.objects.all()
    return render(request, 'panel/panel.html', {'events': events})    

def change_event_status(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    new_status_id = request.POST.get('new_status_id')
    new_status = get_object_or_404(Status, pk=new_status_id)
    event.event_status = new_status
    event.save()
    return redirect(reverse('events'))

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

def hello(request, username):
    return HttpResponse("<h2>Hello %s</h2>"%username)

def events(request):
    
    status_id = request.GET.get('status')
    date = request.GET.get('date')
    
    events = Event.objects.all().order_by('-created_at')    
    
    if status_id:
        events = events.filter(event_status_id=status_id)
    if date:
        events = events.filter(created_at__date=date)


    statuses = Status.objects.all().order_by('status_name')
    return render(request, 'events/events.html', {'events': events, 'statuses': statuses})
    
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

