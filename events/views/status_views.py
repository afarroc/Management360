# events/status_views.py
# ============================================================================
# VISTAS PARA LA GESTIÓN DE ESTADOS (Event, Project, Task)
# ============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from ..models import Status, ProjectStatus, TaskStatus
from ..forms import EventStatusForm, ProjectStatusForm, TaskStatusForm


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
                