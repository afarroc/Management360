from django import forms
from django.apps import apps
import re

def get_model_choices():
    """Obtener todos los modelos disponibles para carga de datos"""
    choices = []
    for app_config in apps.get_app_configs():
        if app_config.name != 'tools':  # Excluir la app actual
            for model in app_config.get_models():
                if hasattr(model.objects, 'bulk_create'):
                    choices.append((
                        f"{app_config.name}.{model.__name__}",
                        f"{app_config.verbose_name} - {model._meta.verbose_name}"
                    ))
    return sorted(choices, key=lambda x: x[1])

class DataUploadForm(forms.Form):
    model = forms.ChoiceField(
        label="Modelo destino",
        choices=get_model_choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    file = forms.FileField(
        label="Archivo (CSV o Excel)",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xls,.xlsx'
        })
    )
    
    sheet_name = forms.CharField(
        label="Hoja (solo Excel)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dejar vacío para primera hoja'
        })
    )
    
    cell_range = forms.CharField(
        label="Rango (solo Excel)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: B2:G500'
        })
    )
    
    clear_existing = forms.BooleanField(
        label="Limpiar datos existentes antes de cargar",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_model(self):
        model_path = self.cleaned_data['model']
        try:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)
            if not hasattr(model.objects, 'bulk_create'):
                raise forms.ValidationError("Este modelo no soporta carga masiva de datos")
            return model
        except (ValueError, LookupError):
            raise forms.ValidationError("Modelo no válido")
    
    def clean_file(self):
        file = self.cleaned_data['file']
        # Validar extensión
        if not file.name.lower().endswith(('.csv', '.xls', '.xlsx')):
            raise forms.ValidationError("Solo se permiten archivos CSV o Excel")
        
        # Validar tamaño (10MB máximo)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise forms.ValidationError("El archivo es demasiado grande. Tamaño máximo: 10MB")
        
        return file
    
    def clean_cell_range(self):
        cell_range = self.cleaned_data.get('cell_range', '').strip()
        if cell_range and not re.match(r'^[A-Za-z]+\d+:[A-Za-z]+\d+$', cell_range, re.IGNORECASE):
            raise forms.ValidationError("Formato de rango inválido. Use formato como 'B2:G500'")
        return cell_range
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        
        if file and file.name.lower().endswith(('.xls', '.xlsx')):
            # Validar que si hay rango, haya nombre de hoja
            if cleaned_data.get('cell_range') and not cleaned_data.get('sheet_name'):
                self.add_error('sheet_name', "Debe especificar una hoja cuando usa un rango de celdas")
        
        return cleaned_data