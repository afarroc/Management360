from django import forms
from django.apps import apps

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
            return apps.get_model(app_label, model_name)
        except (ValueError, LookupError):
            raise forms.ValidationError("Modelo no válido")
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith(('.csv', '.xls', '.xlsx')):
            raise forms.ValidationError("Solo se permiten archivos CSV o Excel")
        return file