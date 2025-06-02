from django import forms
from .models import Room, Evaluation, EntranceExit, Portal, RoomObject
import json
from django.db.models import Q
from django.utils.translation import gettext as _

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            'name', 'description', 'room_type', 'capacity',
            'permissions', 'image', 'parent_room',
            'x', 'y', 'z', 'length', 'width', 'height',
            'pitch', 'yaw', 'roll'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Nombre de la habitación',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Descripción detallada',
                'class': 'form-control',
                'rows': 3
            }),
            'room_type': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Tipo de habitación'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Capacidad máxima'
            }),
            'length': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Longitud (unidades)'
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Anchura (unidades)'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Altura (unidades)'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['parent_room'].queryset = Room.objects.filter(
                Q(owner=user) | Q(administrators=user)
            ).distinct()

class RoomObjectForm(forms.ModelForm):
    class Meta:
        model = RoomObject
        fields = ['name', 'object_type', 'position_x', 'position_y', 'effect']
        widgets = {
            'position_x': forms.NumberInput(attrs={
                'min': 0,
                'max': 30,
                'class': 'form-control'
            }),
            'position_y': forms.NumberInput(attrs={
                'min': 0,
                'max': 30,
                'class': 'form-control'
            }),
            'effect': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'JSON: {"energy": 5, "productivity": 10}'
            })
        }
        
        def clean(self):
            cleaned_data = super().clean()
            if self.instance.room:
                if cleaned_data.get('position_x') > self.instance.room.length:
                    raise forms.ValidationError("La posición X excede el largo de la habitación.")
                if cleaned_data.get('position_y') > self.instance.room.width:
                    raise forms.ValidationError("La posición Y excede el ancho de la habitación.")

        def clean_effect(self):
            effect = self.cleaned_data.get('effect')
            try:
                json.loads(effect)
            except json.JSONDecodeError:
                raise forms.ValidationError("Formato JSON inválido.")
            return effect

class EvaluationForm(forms.ModelForm):
    class Meta:
        
        model = Evaluation
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tu evaluación...'
            }),
            'rating': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'class': 'form-control'
            })
        }
        labels = {
            'comment': _('Comentario'),
            'rating': _('Puntuación'),
        }

class EntranceExitForm(forms.ModelForm):
    class Meta:
        model = EntranceExit
        fields = ['name', 'description', 'face', 'position_x', 'position_y']
        widgets = {
            'face': forms.Select(attrs={
                'class': 'form-select',
                'id': 'faceSelect'
            }),
            'position_x': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-posicionar si vacío'
            }),
            'position_y': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-posicionar si vacío'
            })
        }

class PortalForm(forms.ModelForm):
    class Meta:
        model = Portal
        fields = ['name', 'entrance', 'exit', 'energy_cost', 'cooldown']
        widgets = {
            'entrance': forms.Select(attrs={
                'class': 'form-select entrance-select'
            }),
            'exit': forms.Select(attrs={
                'class': 'form-select exit-select'
            }),
            'energy_cost': forms.NumberInput(attrs={
                'min': 0,
                'class': 'form-control'
            }),
            'cooldown': forms.NumberInput(attrs={
                'min': 0,
                'class': 'form-control'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        entrance = cleaned_data.get('entrance')
        exit = cleaned_data.get('exit')
        
        if entrance and exit:
            if entrance.room == exit.room:
                raise forms.ValidationError("La entrada y salida deben estar en habitaciones distintas.")
            
            # Verificar que no exista ya un portal con estas entradas/salidas
            if Portal.objects.filter(entrance=entrance, exit=exit).exists():
                raise forms.ValidationError("Ya existe un portal con estas entradas y salidas.")
        
        return cleaned_data

    def __init__(self, *args, **kwargs):
        room_id = kwargs.pop('room_id', None)
        super().__init__(*args, **kwargs)
        
        if room_id:
            self.fields['entrance'].queryset = EntranceExit.objects.filter(room_id=room_id)
            self.fields['exit'].queryset = EntranceExit.objects.exclude(room_id=room_id)