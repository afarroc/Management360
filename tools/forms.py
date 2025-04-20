import traceback
from django import forms
from django.apps import apps
import re
from .constants import FORBIDDEN_MODELS  # Importar desde constants.py

def get_model_choices():
    choices = []
    for app_config in apps.get_app_configs():
        # Omitir apps prohibidas
        if any(app_config.name.startswith(f) for f in ['auth', 'admin', 'contenttypes']):
            continue
            
        for model in app_config.get_models():
            model_path = f"{app_config.name}.{model.__name__}"
            
            # Verificar si el modelo está en la lista de prohibidos
            is_forbidden = any(
                model_path == path or model_path.endswith(f".{path.split('.')[-1]}")
                for path in FORBIDDEN_MODELS.values()
            )
            
            if not is_forbidden and hasattr(model.objects, 'bulk_create'):
                choices.append((
                    model_path,
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
        
        # Validación 1: Tipo de dato básico
        if not isinstance(model_path, str) or not model_path.strip():
            raise forms.ValidationError(
                "El modelo debe ser una cadena de texto no vacía. "
                f"Recibido: '{model_path}'"
            )
        
        # Validación 2: Modelos prohibidos (comparación flexible)
        normalized_path = model_path.lower().strip()
        for forbidden_path in FORBIDDEN_MODELS.values():
            if normalized_path == forbidden_path.lower():
                raise forms.ValidationError(
                    f"El modelo '{model_path}' está restringido y no puede ser modificado. "
                    "Contacte al administrador si necesita acceso."
                )
        
        # Validación 3: Formato general (permite múltiples puntos)
        parts = model_path.split('.')
        if len(parts) < 2:
            raise forms.ValidationError(
                "Formato de modelo inválido. Debe contener al menos un punto. "
                "Ejemplos válidos:\n"
                "- app_label.model_name\n"
                "- app_label.subapp.model_name\n"
                f"Recibido: '{model_path}'"
            )
        
        # Extraer componentes (maneja múltiples puntos)
        app_label = parts[0]
        model_name = '.'.join(parts[1:])
        
        if not app_label or not model_name:
            raise forms.ValidationError(
                "app_label y model_name no pueden estar vacíos. "
                f"Recibido: '{model_path}'"
            )
        
        try:
            # Primero intenta con la forma estándar (app_label, model_name)
            model = apps.get_model(app_label, model_name)
            
            if model is None:
                # Si falla, intenta con la ruta completa como app_label
                try:
                    model = apps.get_model(model_path)
                    if model is None:
                        raise forms.ValidationError(
                            f"No se encontró el modelo '{model_path}'. "
                            "Verifique que la aplicación esté instalada y el nombre sea correcto."
                        )
                except:
                    raise forms.ValidationError(
                        f"El modelo '{model_name}' no existe en la aplicación '{app_label}'"
                    )
            
            # Validación de capacidades del modelo
            if not hasattr(model.objects, 'bulk_create'):
                raise forms.ValidationError(
                    f"El modelo '{model._meta.verbose_name}' no soporta operaciones masivas. "
                    "No se puede realizar la importación."
                )
            
            # Validación de restricciones adicionales
            if getattr(model._meta, 'restricted', False):
                raise forms.ValidationError(
                    f"El modelo '{model._meta.verbose_name}' tiene acceso restringido. "
                    "No se permiten modificaciones."
                )
            
            return model
            
        except LookupError as e:
            # Manejo especial para modelos de Django con múltiples puntos
            if 'django.contrib' in model_path:
                try:
                    model = apps.get_model(model_path)
                    if model:
                        return model
                except:
                    pass
            
            raise forms.ValidationError(
                f"No se encontró el modelo: {model_path}\n"
                "Posibles causas:\n"
                "1. La aplicación no está instalada\n"
                "2. El nombre del modelo es incorrecto\n"
                "3. Falta una migración"
            )
            
        except Exception as e:
            import logging
            logging.error(
                "Error validando modelo",
                extra={
                    'model_path': model_path,
                    'user': getattr(self, 'user', None),
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
            raise forms.ValidationError(
                "Error interno al validar el modelo. "
                "El equipo técnico ha sido notificado. Por favor intente más tarde."
            )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.lower().endswith(('.csv', '.xls', '.xlsx')):
            raise forms.ValidationError("Solo se permiten archivos CSV o Excel")
        
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
            if cleaned_data.get('cell_range') and not cleaned_data.get('sheet_name'):
                self.add_error('sheet_name', "Debe especificar una hoja cuando usa un rango de celdas")
        
        return cleaned_data