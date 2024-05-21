from django import forms

class CreateNewEvent(forms.Form):
    title = forms.CharField(label="Titulo de evento", max_length=200, widget=forms.TextInput(attrs={'class':'input'}))
    description = forms.CharField(label="Detalle del evento", widget=forms.Textarea(attrs={'class':'input'}))
    
class CreateNewTask(forms.Form):
    title = forms.CharField(label="Titulo de tarea", max_length=200, widget=forms.TextInput(attrs={'class':'input'}))
    description = forms.CharField(label="Detalle de la tarea", widget=forms.Textarea(attrs={'class':'input'}))

class CreateNewProject(forms.Form):
    name = forms.CharField(label="Nombre del proyecto", max_length=200, widget=forms.TextInput(attrs={'class':'input'}))


from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_status', 'venue', 'host', 'event_category', 'max_attendees', 'ticket_price']
