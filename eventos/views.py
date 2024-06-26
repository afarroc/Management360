# Django imports
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.forms import formset_factory
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views import View

# Local imports from .forms
from .forms import (CreateNewEvent, CreateNewProject, CreateNewTask, EducationForm, EventEditForm, ExperienceForm, ProfileForm, SkillForm, EditStatusForm)
EducationFormSet = formset_factory(EducationForm, extra=1, can_delete=True)
ExperienceFormSet = formset_factory(ExperienceForm, extra=1, can_delete=True)
SkillFormSet = formset_factory(SkillForm, extra=1, can_delete=True)

# Local imports from .models
from .models import Event, EventAttendee, EventState, Profile, Project, Status, Task

# Create your views here.

# Principal

def index(request):
    title="Pagina Pricipal"
    return render(request, "index/index.html",{
        'title':title
    })

def home(request):
    return render(request, 'layouts/main.html')



def about(request):
    username = "Nano"
    return render(request, "about/about.html",{
        'username':username
    })

# Sessions

def signup(request):
    if request.method=="GET":
        return render(request, 'acounts/signup.html', {
            'form':UserCreationForm
        })       
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                # register user
                user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return(redirect('accounts/signup'))  # Modificado aquí
            
            except IntegrityError:
                
                return render(request, 'accounts/signup.html', {
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
        return render(request,'acounts/signin.html',{
            'form':AuthenticationForm,
            })
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            print('user is none')
            return render(request,'acounts/signin.html',{
                'form':AuthenticationForm,
                'error':'Username or password is incorrect'
            })
        else:
            login(request, user)
            return redirect('events')

# Proyects
            
def projects(request):
    projects = Project.objects.all()
    return render(request, "projects/projects.html",{
        'projects':projects
    })

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

# Tasks
     
def task(request):
    tasks = Task.objects.all()
    return render(request, "tasks/tasks.html",{
        'tasks':tasks
    })

@login_required
def create_task(request):
    if request.method == 'GET':
        form = CreateNewTask()
    else:
        form = CreateNewTask(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user  # Asignar el usuario actual como el creador de la tarea
            task.project = form.cleaned_data['project']
            try:
                with transaction.atomic():
                    task.save()
                    messages.success(request, 'Task created successfully!')
                    return redirect('tasks')
            except IntegrityError:
                messages.error(request, 'There was a problem saving the task.')
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'tasks/create_task.html', {'form': form})

# Events


from django.utils import timezone

def events(request):
    # Intenta obtener el ID del estado 'En curso'
    try:
        status_en_curso = Status.objects.get(status_name='En curso').id
    except ObjectDoesNotExist:
        status_en_curso = None

    # Si 'filtered_status' no está en la sesión, establece 'status' como el ID del estado 'En curso'
    status = request.session.setdefault('filtered_status', status_en_curso)  # Obtiene 'filtered_status' de la sesión

    # Si 'filtered_cerrado' no está en la sesión, establece 'cerrado' como True
    cerrado = request.session.setdefault('filtered_cerrado', "true")  # Obtiene 'filtered_cerrado' de la sesión

    # Si 'filtered_date' no está en la sesión, establece 'date' como la fecha actual
    date = request.session.setdefault('filtered_date', timezone.now().date().isoformat())  # Obtiene 'filtered_date' de la sesión

    # El resto del código sigue aquí...    
    
    try:
        # Aquí va el código para interactuar con la base de datos...
        # Verificar si el usuario tiene un perfil
        if hasattr(request.user, 'profile'):
            # Verificar el rol del usuario
            if request.user.profile.role == 'SU':
                # Si el usuario es un 'SU', puede ver todos los eventos
                events = Event.objects.all().order_by('-updated_at')
            else:
                # Si no, solo puede ver los eventos que le están asignados o a los que asiste
                events = Event.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
        else:
            # Si el usuario no tiene un perfil, puedes manejarlo de la manera que prefieras.
            # Por ejemplo, podrías redirigir al usuario a una página de error.
            events = Event.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
        
        statuses = Status.objects.all().order_by('status_name')

        if request.method == 'POST':
            print("Solicitud POST")
            print(request.POST)
            status = request.POST.get('status')
            date = request.POST.get('date')
            cerrado = request.POST.get('cerrado')

            try:
                # Obtén el estado 'Cerrado'
                status_cerrado = Status.objects.get(status_name='Cerrado')

                # Filtrar eventos basados en si están cerrados o no
                if cerrado:
                    events = events.exclude(event_status_id=status_cerrado.id)
                    request.session['filtered_cerrado'] = "true"
                    print("Filtrado por <> cerrado", cerrado)
                else:
                    request.session['filtered_cerrado'] = ""
            except Status.DoesNotExist:
                print('El estado "Cerrado" no existe.')

            # El resto del código sigue aquí...

            # Filtrar eventos basados en el estado seleccionado
            if status:
                events = events.filter(event_status_id=status)
                request.session['filtered_status'] = status
                print("Filtrado por id de estado", status)
            else:
                request.session['filtered_status'] = ""

            # Filtrar eventos basados en la fecha seleccionada
            if date:
                events = events.filter(updated_at__date=date)
                request.session['filtered_date'] = date
                print("Filtrado por fecha", date)
            else:
                request.session['filtered_date'] = ""

            print("Fin vista Events")
            return render(request, 'events/events.html', {
                'events': events,
                'statuses': statuses,
            })

        else:
            
            try:
                # Obtén el estado 'Cerrado'
                status_cerrado = Status.objects.get(status_name='Cerrado')

                # Filtrar eventos basados en si están cerrados o no
                if cerrado:
                    events = events.exclude(event_status_id=status_cerrado.id)

                # Filtrar eventos basados en el estado seleccionado
                if status:
                    events = events.filter(event_status_id=status)
                    print("Filtrado por id de estado", status)

                # Filtrar eventos basados en la fecha seleccionada
                if date:
                    events = events.filter(created_at__date=date)
                    print("Filtrado por fecha", date)
                    
            except Status.DoesNotExist:
                print('El estado "Cerrado" no existe.')
                
            except Exception as e:
                messages.error(request, f'Ha ocurrido un error al filtrar los eventos: {e}')
                return redirect('index')

            print(status, date)
            print("Fin vista Events")
            return render(request, 'events/events.html', {
                'events': events,
                'statuses': statuses,
            })

    except Exception as e:
        # Si ocurre un error, muestra un mensaje de alerta y redirige al usuario a la página de inicio
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
def create_event(request):
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

        return render(request, 'events/create_event.html', {'form': form})
    
    except ObjectDoesNotExist:
        messages.error(request, 'El objeto solicitado no existe.')
        return redirect('index')
    except Exception as e:
        messages.error(request, f'Ha ocurrido un error inesperado: {e}')
        return redirect('index')

def event_detail(request, id):
    event = get_object_or_404(Event, id=id)
    return render(request, 'events/detail.html', {
        'event' :event,
        'events':events
    })

def edit_event(request, event_id=None):
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
                    print('gusardando via post si es valido')

                    # Guardar el evento con el editor actual (usuario que realiza la solicitud)
                    for field in form.changed_data:
                        old_value = getattr(event, field)
                        new_value = form.cleaned_data.get(field)
                        event.record_edit(
                            editor=request.user,
                            field_name=field,
                            old_value=str(old_value),
                            new_value=str(new_value)
                        )
                    form.save()

                    messages.success(request, 'Evento guardado con éxito.')
                    return redirect('edit_event')  # Redirige a la página de lista de edición
                else:
                    messages.error(request, 'Hubo un error al guardar el evento. Por favor, revisa el formulario.')
            else:
                form = CreateNewEvent(instance=event)
            return render(request, 'events/event_edit.html', {'form': form})
        else:
            # Estamos manejando una solicitud GET sin argumentos
            # Verificar el rol del usuario
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'SU':
                # Si el usuario es un 'SU', puede ver todos los eventos
                events = Event.objects.all().order_by('-updated_at')
            else:
                # Si no, solo puede ver los eventos que le están asignados o a los que asiste
                events = Event.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
            return render(request, 'events/event_list.html', {'events': events})
    except Exception as e:
        messages.error(request, 'Ha ocurrido un error: {}'.format(e))
        return redirect('index')


from django.contrib.messages import get_messages

def change_event_status(request, event_id):
    print("Inicio de vista change_event_status")
    try:
        if request.method != 'POST':
            print("solicitud GET")
            return HttpResponse("Método no permitido", status=405)
        print("solicitud Post:", request.POST)
        event = get_object_or_404(Event, pk=event_id)
        print("ID a cambiar:", str(event.id))
        new_status_id = request.POST.get('new_status_id')
        new_status = get_object_or_404(Status, pk=new_status_id)
        print("new_status_id", str(new_status))
        if request.user is None:
            print("User is none: Usuario no autenticado")
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

def delete_event(request, event_id):
    # Asegúrate de que solo se pueda acceder a esta vista mediante POST
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=event_id)

        # Verificar si el usuario es un 'SU'
        if request.user.profile.role != 'SU':
            messages.error(request, 'No tienes permiso para eliminar este evento.')
            return redirect(reverse('events'))

        event.delete()
        messages.success(request, 'El evento ha sido eliminado exitosamente.')
    else:
        messages.error(request, 'Método no permitido.')
    return redirect(reverse('events'))

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

def create_status(request):
    if request.method == 'POST':
        form = EditStatusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('status_list')
    else:
        form = EditStatusForm()
    return render(request, 'configuration/create_status.html', {'form': form})

def edit_status(request, status_id):
    status = get_object_or_404(Status, id=status_id)
    if request.method == 'POST':
        form = EditStatusForm(request.POST, instance=status)
        if form.is_valid():
            form.save()
            return redirect('status_list')
    else:
        form = EditStatusForm(instance=status)
    return render(request, 'configuration/edit_status.html', {'form': form})

def delete_status(request, status_id):
    status = get_object_or_404(Status, id=status_id)
    if request.method == 'POST':
        status.delete()
        return redirect('status_list')
    return render(request, 'configuration/confirm_delete.html', {'object': status})

def status_list(request):
    statuses = Status.objects.all()
    return render(request, 'configuration/status_list.html', {'statuses': statuses})

# Document viewer

from django.views.generic import FormView
from .forms import DocumentForm, ImageForm
from .models import Document, Image
from django.urls import reverse_lazy
from .forms import DocumentForm
from .models import Document
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages

def document_view(request):
    documents = Document.objects.all()  # Obtiene todos los documentos
    images = Image.objects.all()        # Obtiene todas las imágenes
    context = {
        'documents': documents,
        'images': images
    }
    return render(request, 'documents/docsview.html', context)


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Document, Image  # Asegúrate de importar el modelo Image

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
