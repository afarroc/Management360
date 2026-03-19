# analyst/forms.py
import traceback
import re
import logging
from django import forms
from django.apps import apps
from .constants import FORBIDDEN_MODELS, MAX_FILE_SIZE

logger = logging.getLogger(__name__)

def get_model_choices():
    """Retrieve available model choices, excluding forbidden models."""
    choices = []
    for app_config in apps.get_app_configs():
        # Skip forbidden apps
        if any(app_config.name.startswith(f) for f in ['auth', 'admin', 'contenttypes']):
            continue
            
        for model in app_config.get_models():
            model_path = f"{app_config.name}.{model.__name__}"
            
            # Check if the model is in the forbidden list
            is_forbidden = any(
                model_path == path or model_path.endswith(f".{path.split('.')[-1]}")
                for path in FORBIDDEN_MODELS.values()
            )
            
            if not is_forbidden and hasattr(model.objects, 'bulk_create'):
                app_verbose = getattr(app_config, 'verbose_name', app_config.name)
                model_verbose = getattr(model._meta, 'verbose_name', model.__name__)
                choices.append((
                    model_path,
                    f"{app_verbose} - {model_verbose}"
                ))
    
    return sorted(choices, key=lambda x: x[1])

# analyst/forms.py

class DataUploadForm(forms.Form):
    """Form for uploading CSV/Excel files to Django models."""
    
    model = forms.ChoiceField(
        label="Target Model",
        choices=get_model_choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    file = forms.FileField(
        label="File (CSV or Excel)",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xls,.xlsx'
        })
    )
    
    sheet_name = forms.CharField(
        label="Sheet (Excel only)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave empty for the first sheet'
        })
    )
    
    cell_range = forms.CharField(
        label="Range (Excel only)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'E.g., B2:G500'
        })
    )
    
    no_header = forms.BooleanField(
        label="Data has no header row",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    clear_existing = forms.BooleanField(
        label="Clear existing data before upload",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    

    def clean_model(self):
        """Validate the selected model."""
        model_path = self.cleaned_data['model']
        
        logger.debug(f"Validating model: '{model_path}'")
        
        # Validation 1: Basic data type check
        if not isinstance(model_path, str) or not model_path.strip():
            raise forms.ValidationError(
                "The model must be a non-empty string. "
                f"Received: '{model_path}'"
            )
        
        # Clean the path
        model_path = model_path.strip()
        
        # Validation 2: Forbidden models (flexible comparison)
        normalized_path = model_path.lower()
        for forbidden_path in FORBIDDEN_MODELS.values():
            if normalized_path == forbidden_path.lower():
                raise forms.ValidationError(
                    f"The model '{model_path}' is restricted and cannot be modified. "
                    "Contact the administrator if access is needed."
                )
        
        # Validation 3: General format (allows multiple dots)
        parts = model_path.split('.')
        if len(parts) < 2:
            raise forms.ValidationError(
                "Invalid model format. It must contain at least one dot. "
                "Valid examples:\n"
                "- app_label.model_name\n"
                "- app_label.subapp.model_name\n"
                f"Received: '{model_path}'"
            )
        
        # Extract components (handles multiple dots)
        app_label = parts[0]
        model_name = '.'.join(parts[1:])
        
        if not app_label or not model_name:
            raise forms.ValidationError(
                "app_label and model_name cannot be empty. "
                f"Received: '{model_path}'"
            )
        
        try:
            # First, try the standard form (app_label, model_name)
            logger.debug(f"Trying apps.get_model('{app_label}', '{model_name}')")
            model = apps.get_model(app_label, model_name)
            
            if model is None:
                # If it fails, try the full path as app_label
                logger.debug(f"Trying apps.get_model('{model_path}')")
                try:
                    model = apps.get_model(model_path)
                    if model is None:
                        raise forms.ValidationError(
                            f"The model '{model_path}' was not found. "
                            "Ensure the app is installed and the name is correct."
                        )
                except LookupError:
                    raise forms.ValidationError(
                        f"The model '{model_name}' does not exist in the app '{app_label}'"
                    )
            
            logger.debug(f"Model found: {model.__name__}")
            
            # Validate model capabilities
            if not hasattr(model.objects, 'bulk_create'):
                raise forms.ValidationError(
                    f"The model '{model._meta.verbose_name}' does not support bulk operations. "
                    "Import cannot proceed."
                )
            
            # Validate additional restrictions
            if getattr(model._meta, 'restricted', False):
                raise forms.ValidationError(
                    f"The model '{model._meta.verbose_name}' is restricted. "
                    "Modifications are not allowed."
                )
            
            return model
            
        except LookupError as e:
            logger.error(f"LookupError for model {model_path}: {str(e)}")
            # Special handling for Django models with multiple dots
            if 'django.contrib' in model_path:
                try:
                    model = apps.get_model(model_path)
                    if model:
                        return model
                except:
                    pass
            
            raise forms.ValidationError(
                f"Model not found: {model_path}\n"
                "Possible causes:\n"
                "1. The app is not installed\n"
                "2. The model name is incorrect\n"
                "3. A migration is missing"
            )
            
        except Exception as e:
            logger.error(f"Error validating model {model_path}: {str(e)}", exc_info=True)
            raise forms.ValidationError(
                "Internal error while validating the model. "
                "The technical team has been notified. Please try again later."
            )


    # analyst/forms.py


    def clean_file(self):
        """Validate the uploaded file."""
        file = self.cleaned_data.get('file')
        
        # Verificar si es una carga desde clipboard
        is_clipboard_load = self.data.get('is_clipboard_load') == 'true'
        
        # Si es clipboard, el archivo no es requerido
        if is_clipboard_load:
            return None
        
        # Si no es clipboard y no hay archivo, error
        if file is None:
            raise forms.ValidationError("This field is required.")
        
        # Validar extensión
        ext = file.name.split('.')[-1].lower()
        if ext not in ['csv', 'xls', 'xlsx']:
            raise forms.ValidationError("Only CSV or Excel files are allowed.")
        
        # Validar tamaño
        if file.size > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE // (1024 * 1024)
            raise forms.ValidationError(f"The file is too large. Maximum size: {max_mb}MB.")
        
        return file    

    def clean(self):
        """Perform additional validations."""
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        
        if file and file.name.lower().endswith(('.xls', '.xlsx')):
            if cleaned_data.get('cell_range') and not cleaned_data.get('sheet_name'):
                self.add_error('sheet_name', "You must specify a sheet when using a cell range.")
        
        return cleaned_data