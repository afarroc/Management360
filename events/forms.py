from django import forms
from django.contrib.auth.models import User
from .models import Task, Event, Status, ProjectStatus, TaskStatus, Classification, Project

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