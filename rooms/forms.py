from django import forms
from .models import Room, Evaluation

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ('name', 'description', 'capacity', 'address', 'image', 'permissions')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Nombre de la sala'}),
            'description': forms.Textarea(attrs={'placeholder': 'Descripcion de la sala'}),
            'capacity': forms.NumberInput(attrs={'placeholder': 'Capacidad'}),
            'address': forms.TextInput(attrs={'placeholder': 'Direccion'}),
            'permissions': forms.Select(attrs={'placeholder': 'Permisos'})
        }

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ('text', 'rating')
        widgets = {
            'text': forms.Textarea(attrs={'placeholder': 'Evaluacion'}),
            'rating': forms.NumberInput(attrs={'placeholder': 'Calificacion (1-5)'})
        }