from django import forms
from django.contrib.auth.models import User
from .models import Task, Event, Profile, Experience, Education, Skill, Status, Document

class CreateNewEvent(forms.ModelForm):
    title = forms.CharField(max_length=200)
    description = forms.CharField(widget=forms.Textarea)
    venue = forms.CharField(max_length=200)
    event_status = forms.ModelChoiceField(queryset=Status.objects.all())
    event_category = forms.CharField(max_length=50)
    max_attendees = forms.IntegerField()
    ticket_price = forms.DecimalField(max_digits=6, decimal_places=2)
    assigned_to = forms.ModelChoiceField(queryset=User.objects.all())  # Un único usuario asignado
    attendees = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=False)  # Varios asistentes
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'venue', 'event_status', 'event_category', 'max_attendees', 'ticket_price', 'assigned_to', 'attendees']


class AssignAttendeesForm(forms.Form):
    attendees = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

class CreateNewTask(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'important', 'project']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'important': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
        }

class CreateNewProject(forms.Form):
    name = forms.CharField(label="Nombre del proyecto", max_length=200, widget=forms.TextInput(attrs={'class':'input'}))

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_status', 'venue', 'host', 'event_category', 'max_attendees', 'ticket_price']

class EventEditForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_status']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'profile_picture', 'linkedin_url']

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

class EditStatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['status_name', 'icon', 'active', 'color']

from django import forms
from django.core.validators import FileExtensionValidator

# Formulario para subir documentos
class DocumentForm(forms.Form):
    file = forms.FileField(validators=[FileExtensionValidator(['pdf', 'docx', 'ppt'])])

# Formulario para subir imágenes
class ImageForm(forms.Form):
    file = forms.FileField(validators=[FileExtensionValidator(['jpg', 'bmp', 'png'])])
