from django import forms
from django.apps import apps

def get_model_choices():
    """Obtener todos los modelos disponibles para carga de datos"""
    choices = []
    for app_config in apps.get_app_configs():
        if app_config.name != 'tools':  # Excluir la app actual
            for model in app_config.get_models():
                # Solo incluir modelos con método bulk_create
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
    
    csv_file = forms.FileField(
        label="Archivo CSV",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    clear_existing = forms.BooleanField(
        label="Limpiar datos existentes antes de cargar",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_model(self):
        model_path = self.cleaned_data['model']
        try:
            app_label, model_name = model_path.split('.')
            return apps.get_model(app_label, model_name)
        except (ValueError, LookupError):
            raise forms.ValidationError("Modelo no válido")
    
    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError("Solo se permiten archivos CSV")
        return file