from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import Task, Event, Status, ProjectStatus, TaskStatus, Classification, Project, ProjectTemplate, TemplateTask, Tag

class CreateNewEvent(forms.ModelForm):

    class Meta:
        model = Event
        fields = ['title', 'description', 'attendees', 'venue', 'event_status', 'event_category', 'max_attendees', 'ticket_price', 'assigned_to']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'attendees': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'event_status': forms.Select(attrs={'class': 'form-select'}),
            'event_category': forms.TextInput(attrs={'class': 'form-control'}),
            'max_attendees': forms.NumberInput(attrs={'class': 'form-control'}),
            'ticket_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

class AssignAttendeesForm(forms.Form):
    attendees = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

class CreateNewTask(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'important', 'project', 'task_status', 'event', 'assigned_to','ticket_price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'important': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'task_status': forms.Select(attrs={'class': 'form-select'}),
            'event': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'ticket_price': forms.NumberInput(attrs={'class': 'form-control'}),

        }

class CreateNewProject(forms.ModelForm):
    

    class Meta:
        model = Project
        fields = ['title', 'description', 'event', 'assigned_to', 'attendees', 'project_status', 'ticket_price', ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'event': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'attendees': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'project_status': forms.Select(attrs={'class': 'form-select'}),
            'ticket_price': forms.NumberInput(attrs={'class': 'form-control'}),

        }
       
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_status', 'venue', 'host', 'event_category', 'max_attendees', 'ticket_price']

class EventEditForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_status']




class EventStatusForm(forms.ModelForm):
    color = forms.CharField(
        widget=forms.TextInput(attrs={'type': 'color'}),
        required=False,
    )
    class Meta:
        model = Status
        fields = ['status_name', 'icon', 'active', 'color']

class TaskStatusForm(forms.ModelForm):
    color = forms.CharField(
        widget=forms.TextInput(attrs={'type': 'color'}),
        required=False,
    )
    class Meta:
        model = TaskStatus
        fields = ['status_name', 'icon', 'active', 'color']

class ProjectStatusForm(forms.ModelForm):
    color = forms.CharField(
        widget=forms.TextInput(attrs={'type': 'color'}),
        required=False,
    )
    class Meta:
        model = ProjectStatus
        fields = ['status_name', 'icon', 'active', 'color']



class EditClassificationForm(forms.ModelForm):
    class Meta:
        model = Classification
        fields = ['nombre', 'descripcion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].label = "Nombre de la Tipificación"
        self.fields['descripcion'].label = "Descripción de la Tipificación"


from django import forms
from .models import Room

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ('name', 'description')


# Formularios para plantillas de proyectos
class ProjectTemplateForm(forms.ModelForm):
    class Meta:
        model = ProjectTemplate
        fields = ['name', 'description', 'category', 'estimated_duration', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Lanzamiento de Producto, Desarrollo Web, etc.'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe qué tipo de proyecto cubre esta plantilla...'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Marketing, Desarrollo, Diseño, etc.'
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Duración en días'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nombre de la Plantilla',
            'description': 'Descripción',
            'category': 'Categoría',
            'estimated_duration': 'Duración Estimada (días)',
            'is_public': '¿Es pública?',
        }
        help_texts = {
            'is_public': 'Si está marcada, otros usuarios podrán usar esta plantilla',
        }


class TemplateTaskForm(forms.ModelForm):
    class Meta:
        model = TemplateTask
        fields = ['title', 'description', 'estimated_hours', 'required_skills']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la tarea'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción de la tarea...'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.5',
                'step': '0.5',
                'placeholder': 'Horas estimadas'
            }),
            'required_skills': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '3'
            }),
        }
        labels = {
            'title': 'Título de la Tarea',
            'description': 'Descripción',
            'estimated_hours': 'Horas Estimadas',
            'required_skills': 'Habilidades Requeridas',
        }


# FormSet para tareas de plantilla
TemplateTaskFormSet = inlineformset_factory(
    ProjectTemplate,
    TemplateTask,
    form=TemplateTaskForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# Formulario para recordatorios
class ReminderForm(forms.ModelForm):
    class Meta:
        model = None  # Se asignará dinámicamente
        fields = ['title', 'description', 'remind_at', 'task', 'project', 'event', 'reminder_type']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Revisar proyecto, Recordar reunión, etc.'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalles adicionales del recordatorio...'
            }),
            'remind_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'task': forms.Select(attrs={
                'class': 'form-select'
            }),
            'project': forms.Select(attrs={
                'class': 'form-select'
            }),
            'event': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reminder_type': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Título del Recordatorio',
            'description': 'Descripción',
            'remind_at': 'Fecha y Hora del Recordatorio',
            'task': 'Tarea Relacionada (Opcional)',
            'project': 'Proyecto Relacionado (Opcional)',
            'event': 'Evento Relacionado (Opcional)',
            'reminder_type': 'Tipo de Notificación',
        }
        help_texts = {
            'remind_at': 'Selecciona cuándo quieres recibir el recordatorio',
            'reminder_type': 'Elige cómo quieres recibir la notificación',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Importar aquí para evitar circular imports
        from .models import Reminder

        # Asignar el modelo
        self.Meta.model = Reminder

        # Filtrar querysets por usuario si es necesario
        if self.user:
            from .models import Task, Project, Event
            self.fields['task'].queryset = Task.objects.filter(
                Q(host=self.user) | Q(assigned_to=self.user)
            ).distinct()
            self.fields['project'].queryset = Project.objects.filter(
                Q(host=self.user) | Q(assigned_to=self.user) | Q(attendees=self.user)
            ).distinct()
            self.fields['event'].queryset = Event.objects.filter(
                Q(host=self.user) | Q(assigned_to=self.user) | Q(attendees=self.user)
            ).distinct()

        # Hacer los campos de relación opcionales
        self.fields['task'].required = False
        self.fields['task'].empty_label = "Sin tarea específica"
        self.fields['project'].required = False
        self.fields['project'].empty_label = "Sin proyecto específico"
        self.fields['event'].required = False
        self.fields['event'].empty_label = "Sin evento específico"

    def clean_remind_at(self):
        remind_at = self.cleaned_data.get('remind_at')
        if remind_at and remind_at <= timezone.now():
            raise forms.ValidationError('La fecha del recordatorio debe ser futura.')
        return remind_at