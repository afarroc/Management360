from django import forms
from django.contrib.auth.models import User
from .models import Task, Event, Profile, Experience, Education, Skill, Status, ProjectStatus, TaskStatus, Classification, Project
from django.core.validators import FileExtensionValidator


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

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.core.files.images import get_image_dimensions
from .models import Profile

class ProfileForm(forms.ModelForm):
    bio = forms.CharField(max_length=500)
    location = forms.CharField(max_length=30)
    linkedin_url = forms.URLField(required=False)
    github_url = forms.URLField(required=False)
    twitter_url = forms.URLField(required=False)
    facebook_url = forms.URLField(required=False)
    instagram_url = forms.URLField(required=False)
    company = forms.CharField(max_length=100)
    job_title = forms.CharField(max_length=100)
    country = forms.CharField(max_length=50)
    address = forms.CharField(max_length=200)
    phone = forms.CharField(max_length=20)

    class Meta:
        model = Profile
        fields = ('bio', 'location', 'profile_picture', 'linkedin_url', 'github_url', 'twitter_url', 'facebook_url', 'instagram_url', 'company', 'job_title', 'country', 'address', 'phone')

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not phone.isdigit():
            raise ValidationError('El teléfono debe contener solo números.')
        return phone

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data['profile_picture']
        if profile_picture:
            if profile_picture.size > 2 * 1024 * 1024:
                raise ValidationError('El tamaño de la imagen no debe exceder los 2MB.')
            width, height = get_image_dimensions(profile_picture)
            if width > 1024 or height > 1024:
                raise ValidationError('La imagen no debe exceder 1024x1024 píxeles.')
        return profile_picture

    def clean(self):
        super().clean()
        for field in ['linkedin_url', 'github_url', 'twitter_url', 'facebook_url', 'instagram_url']:
            url = self.cleaned_data.get(field)
            if url:
                try:
                    URLValidator()(url)
                except ValidationError:
                    self.add_error(field, 'URL inválida')

                    
class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['job_title', 'company_name', 'start_date', 'end_date', 'description']

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if not start_date:
            raise forms.ValidationError("Start date is required.")
        return start_date

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['institution_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['skill_name', 'proficiency_level']

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

# Formulario para subir documentos
class DocumentForm(forms.Form):
    file = forms.FileField(validators=[FileExtensionValidator(['pdf', 'docx', 'ppt'])])

# Formulario para subir imágenes
class ImageForm(forms.Form):
    file = forms.FileField(validators=[FileExtensionValidator(['jpg', 'bmp', 'png'])])

class DatabaseForm(forms.Form):
    file = forms.FileField(validators=[FileExtensionValidator(['csv', 'txt', 'xlsx', 'xlsm'])])

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