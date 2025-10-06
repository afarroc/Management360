from django import forms
from tinymce.widgets import TinyMCE
from .models import BitacoraEntry, BitacoraAttachment

class BitacoraEntryForm(forms.ModelForm):
    class Meta:
        model = BitacoraEntry
        fields = [
            'titulo', 'contenido', 'categoria', 'tags',
            'related_event', 'related_task', 'related_project', 'related_room',
            'latitud', 'longitud', 'is_public', 'mood'
        ]
        widgets = {
            'contenido': TinyMCE(attrs={'cols': 80, 'rows': 30}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'latitud': forms.NumberInput(attrs={'step': 'any'}),
            'longitud': forms.NumberInput(attrs={'step': 'any'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            # Filtrar eventos, tareas, etc. del usuario
            self.fields['related_event'].queryset = self.fields['related_event'].queryset.filter(host=self.user)
            self.fields['related_task'].queryset = self.fields['related_task'].queryset.filter(host=self.user)
            self.fields['related_project'].queryset = self.fields['related_project'].queryset.filter(host=self.user)
            self.fields['related_room'].queryset = self.fields['related_room'].queryset.filter(owner=self.user)

class BitacoraAttachmentForm(forms.ModelForm):
    class Meta:
        model = BitacoraAttachment
        fields = ['archivo', 'tipo', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }