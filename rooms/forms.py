from django import forms
from .models import Room, Evaluation, EntranceExit, Portal

# forms.py
from django import forms
from .models import Room

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ( 'name',
            'description',
            'owner',
            'creator',
            'administrators',
            'capacity',
            'address',
            'image',
            'permissions',
            'x',
            'y',
            'z',
            'longitud',
            'anchura',
            'altura',
            'pitch',
            'yaw',
            'roll',
            'type',
            'beds',
            'bathrooms',
            'surface',
            'price',
            'available',
            'parent_room'
        )
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Nombre de la habitación'}),
            'description': forms.Textarea(attrs={'placeholder': 'Descripción de la habitación'}),
            'owner': forms.Select(attrs={'placeholder': 'Propietario'}),
            'creator': forms.Select(attrs={'placeholder': 'Creador'}),
            'administrators': forms.SelectMultiple(attrs={'placeholder': 'Administradores'}),
            'capacity': forms.NumberInput(attrs={'placeholder': 'Capacidad'}),
            'address': forms.TextInput(attrs={'placeholder': 'Dirección'}),
            'image': forms.FileInput(attrs={'placeholder': 'Imagen'}),
            'permissions': forms.Select(attrs={'placeholder': 'Permisos'}),
            'x': forms.NumberInput(attrs={'placeholder': 'Posición x'}),
            'y': forms.NumberInput(attrs={'placeholder': 'Posición y'}),
            'z': forms.NumberInput(attrs={'placeholder': 'Posición z'}),
            'longitud': forms.NumberInput(attrs={'placeholder': 'Longitud'}),
            'anchura': forms.NumberInput(attrs={'placeholder': 'Anchura'}),
            'altura': forms.NumberInput(attrs={'placeholder': 'Altura'}),
            'pitch': forms.NumberInput(attrs={'placeholder': 'Rotación x'}),
            'yaw': forms.NumberInput(attrs={'placeholder': 'Rotación y'}),
            'roll': forms.NumberInput(attrs={'placeholder': 'Rotación z'}),
            'type': forms.Select(attrs={'placeholder': 'Tipo de habitación'}),
            'beds': forms.NumberInput(attrs={'placeholder': 'Número de camas'}),
            'bathrooms': forms.NumberInput(attrs={'placeholder': 'Número de baños'}),
            'surface': forms.NumberInput(attrs={'placeholder': 'Superficie en metros cuadrados'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Precio por noche'}),
            'available': forms.CheckboxInput(attrs={'placeholder': 'Disponibilidad'}),
            'parent_room': forms.Select(attrs={'placeholder': 'Habitación contenedora'})
        }

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ('comment', 'rating')
        widgets = {
            'comment': forms.Textarea(attrs={'placeholder': 'Evaluación'}),
            'rating': forms.NumberInput(attrs={'placeholder': 'Calificación (1-5)'})
        }

class EntranceExitForm(forms.ModelForm):
  class Meta:
    model = EntranceExit
    fields = ('name', 'description', 'face', 'type')
    widgets = {
      'name': forms.TextInput(attrs={
        'placeholder': 'Nombre',
        'class': "form-control",
        'id':"floatingName"
      }),
      'description': forms.Textarea(attrs={
        'placeholder': 'Descripción',
        'class': "form-control",
        'id':"floatingTextarea",
        'style':"height: 100px",
      }),
      'face': forms.Select(attrs={
        'placeholder': 'Cara',
        'class': "form-select",
        'id':"floatingFace",
        'aria-label':"Cara",
      }),
      'type': forms.Select(attrs={
        'placeholder': 'Tipo',
        'class': "form-select",
        'id':"floatingType",
        'aria-label':"Tipo",
      })
    }
class PortalForm(forms.ModelForm):
  class Meta:
    model = Portal
    fields = ('name', 'description', 'entrance', 'exit')
    widgets = {
      'name': forms.TextInput(attrs={
        'placeholder': 'Nombre del portal',
        'class': "form-control",
        'id':"floatingPortalName"
      }),
      'description': forms.Textarea(attrs={
        'placeholder': 'Descripción del portal',
        'class': "form-control",
        'id':"floatingPortalDescription",
        'style':"height: 100px",
      }),
      'entrance': forms.Select(attrs={
        'placeholder': 'Entrada',
        'class': "form-select",
        'id':"floatingEntrance",
        'aria-label':"Entrada",
      }),
      'exit': forms.Select(attrs={
        'placeholder': 'Salida',
        'class': "form-select",
        'id':"floatingExit",
        'aria-label':"Salida",
      })
    }