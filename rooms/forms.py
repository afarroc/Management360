from django import forms
from .models import Room, Evaluation, EntranceExit, Portal, RoomObject, RoomConnection
import json
from django.db.models import Q
from django.utils.translation import gettext as _

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            # Información básica
            'name', 'description', 'room_type', 'capacity', 'permissions',
            'image', 'parent_room',

            # Dimensiones y posición
            'x', 'y', 'z', 'length', 'width', 'height', 'pitch', 'yaw', 'roll',

            # Apariencia y material
            'color_primary', 'color_secondary', 'material_type', 'texture_url', 'opacity',

            # Propiedades físicas
            'mass', 'density', 'friction', 'restitution',

            # Estado y funcionalidad
            'is_active', 'health', 'temperature', 'lighting_intensity',
            'sound_ambient', 'special_properties'
        ]
        widgets = {
            # Información básica
            'name': forms.TextInput(attrs={
                'placeholder': 'Nombre de la habitación',
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Descripción detallada',
                'class': 'form-control',
                'rows': 3
            }),
            'room_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Capacidad máxima',
                'min': 1
            }),
            'permissions': forms.Select(attrs={
                'class': 'form-select'
            }),

            # Dimensiones y posición
            'x': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Posición X'
            }),
            'y': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Posición Y'
            }),
            'z': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Posición Z'
            }),
            'length': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Longitud',
                'min': 1
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Anchura',
                'min': 1
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Altura',
                'min': 1
            }),
            'pitch': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rotación X (grados)'
            }),
            'yaw': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rotación Y (grados)'
            }),
            'roll': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rotación Z (grados)'
            }),

            # Apariencia y material
            'color_primary': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': '#2196f3'
            }),
            'color_secondary': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': '#1976d2'
            }),
            'material_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'texture_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com/textura.jpg'
            }),
            'opacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.0,
                'max': 1.0,
                'step': 0.1,
                'placeholder': '0.0 - 1.0'
            }),

            # Propiedades físicas
            'mass': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.1,
                'step': 0.1,
                'placeholder': 'Masa en kg'
            }),
            'density': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.1,
                'step': 0.1,
                'placeholder': 'Densidad en g/cm³'
            }),
            'friction': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.0,
                'max': 1.0,
                'step': 0.1,
                'placeholder': '0.0 - 1.0'
            }),
            'restitution': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.0,
                'max': 1.0,
                'step': 0.1,
                'placeholder': '0.0 - 1.0'
            }),

            # Estado y funcionalidad
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'health': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': '0-100'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 0.1,
                'placeholder': 'Temperatura en °C'
            }),
            'lighting_intensity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': '0-100'
            }),
            'sound_ambient': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sonido ambiente (opcional)'
            }),
            'special_properties': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Propiedades especiales en formato JSON'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['parent_room'].queryset = Room.objects.filter(
                Q(owner=user) | Q(administrators=user)
            ).distinct()

        # Configurar initial value para special_properties
        if self.instance and self.instance.pk and self.instance.special_properties:
            self.fields['special_properties'].initial = json.dumps(self.instance.special_properties, indent=2)

        # Configurar campos opcionales (con valores por defecto en el modelo)
        optional_fields = [
            'capacity', 'permissions', 'x', 'y', 'z', 'length', 'width', 'height',
            'pitch', 'yaw', 'roll', 'color_primary', 'color_secondary', 'material_type',
            'texture_url', 'opacity', 'mass', 'density', 'friction', 'restitution',
            'is_active', 'health', 'temperature', 'lighting_intensity', 'sound_ambient',
            'special_properties', 'description', 'image', 'parent_room'
        ]

        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

    def clean_special_properties(self):
        """Validar que special_properties sea JSON válido"""
        special_properties = self.cleaned_data.get('special_properties')
        if special_properties:
            try:
                # Si es string, intentar parsear como JSON
                if isinstance(special_properties, str):
                    return json.loads(special_properties)
                # Si ya es dict, devolverlo
                elif isinstance(special_properties, dict):
                    return special_properties
                else:
                    raise forms.ValidationError("Formato JSON inválido.")
            except json.JSONDecodeError:
                raise forms.ValidationError("Formato JSON inválido.")
        return {}  # Retornar dict vacío si no hay valor

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

class RoomConnectionForm(forms.ModelForm):
    class Meta:
        model = RoomConnection
        fields = ['from_room', 'to_room', 'entrance', 'bidirectional', 'energy_cost']
        widgets = {
            'from_room': forms.Select(attrs={
                'class': 'form-select',
                'id': 'fromRoomSelect'
            }),
            'to_room': forms.Select(attrs={
                'class': 'form-select',
                'id': 'toRoomSelect'
            }),
            'entrance': forms.Select(attrs={
                'class': 'form-select',
                'id': 'entranceSelect'
            }),
            'bidirectional': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'energy_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Costo de energía'
            })
        }

    def __init__(self, *args, **kwargs):
        room_id = kwargs.pop('room_id', None)
        super().__init__(*args, **kwargs)

        if room_id:
            # Filtrar habitaciones disponibles (excluyendo la actual)
            self.fields['to_room'].queryset = Room.objects.exclude(id=room_id)
            self.fields['from_room'].initial = room_id
            self.fields['from_room'].widget.attrs['disabled'] = True

            # Filtrar entradas de la habitación actual
            self.fields['entrance'].queryset = EntranceExit.objects.filter(room_id=room_id)

    def clean(self):
        cleaned_data = super().clean()
        from_room = cleaned_data.get('from_room')
        to_room = cleaned_data.get('to_room')
        entrance = cleaned_data.get('entrance')

        if from_room and to_room and entrance:
            # Verificar que la entrada pertenezca a la habitación de origen
            if entrance.room != from_room:
                raise forms.ValidationError("La entrada debe pertenecer a la habitación de origen.")

            # Verificar que no exista ya una conexión con la misma entrada
            if RoomConnection.objects.filter(entrance=entrance).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise forms.ValidationError("Esta entrada ya está conectada a otra habitación.")

        return cleaned_data