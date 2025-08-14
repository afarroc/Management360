import traceback
from django import forms
from django.apps import apps
import re
from .constants import FORBIDDEN_MODELS  # Imported from constants.py

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
                choices.append((
                    model_path,
                    f"{app_config.verbose_name} - {model._meta.verbose_name}"
                ))
    
    return sorted(choices, key=lambda x: x[1])

class DataUploadForm(forms.Form):
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
    
    clear_existing = forms.BooleanField(
        label="Clear existing data before upload",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_model(self):
        """Validate the selected model."""
        model_path = self.cleaned_data['model']
        
        # Validation 1: Basic data type check
        if not isinstance(model_path, str) or not model_path.strip():
            raise forms.ValidationError(
                "The model must be a non-empty string. "
                f"Received: '{model_path}'"
            )
        
        # Validation 2: Forbidden models (flexible comparison)
        normalized_path = model_path.lower().strip()
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
            model = apps.get_model(app_label, model_name)
            
            if model is None:
                # If it fails, try the full path as app_label
                try:
                    model = apps.get_model(model_path)
                    if model is None:
                        raise forms.ValidationError(
                            f"The model '{model_path}' was not found. "
                            "Ensure the app is installed and the name is correct."
                        )
                except:
                    raise forms.ValidationError(
                        f"The model '{model_name}' does not exist in the app '{app_label}'"
                    )
            
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
            import logging
            logging.error(
                "Error validating model",
                extra={
                    'model_path': model_path,
                    'user': getattr(self, 'user', None),
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
            raise forms.ValidationError(
                "Internal error while validating the model. "
                "The technical team has been notified. Please try again later."
            )
    
    def clean_file(self):
        """Validate the uploaded file."""
        file = self.cleaned_data['file']
        if not file.name.lower().endswith(('.csv', '.xls', '.xlsx')):
            raise forms.ValidationError("Only CSV or Excel files are allowed.")
        
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise forms.ValidationError("The file is too large. Maximum size: 10MB.")
        
        return file
    
    def number_to_excel_column(self, n):
        """Convierte un número a letra de columna Excel (1->A, 26->Z, 27->AA, etc.)"""
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string
    
    def clean_cell_range(self):
        """Validate the cell range format and check against file dimensions."""
        cell_range = self.cleaned_data.get('cell_range', '').strip()
        if not cell_range:
            return cell_range

        # Validar formato básico (permitir columnas de varias letras)
        if not re.match(r'^[A-Za-z]{1,3}\d+:[A-Za-z]{1,3}\d+$', cell_range, re.IGNORECASE):
            raise forms.ValidationError("Formato de rango inválido. Use formato como 'B2:G500'")

        try:
            # Parsear el rango
            start, end = cell_range.split(':')

            def split_col_row(cell):
                col = ''.join([c for c in cell if c.isalpha()])
                row = ''.join([c for c in cell if c.isdigit()])
                if not col or not row:
                    raise ValueError()
                return col.upper(), int(row)

            start_col, start_row = split_col_row(start)
            end_col, end_row = split_col_row(end)

            # Convertir letras de columna a números
            def col_to_num(col):
                num = 0
                for c in col:
                    num = num * 26 + (ord(c.upper()) - ord('A') + 1)
                return num

            start_col_num = col_to_num(start_col)
            end_col_num = col_to_num(end_col)

            # Validar orden de columnas y filas
            if start_col_num > end_col_num:
                raise forms.ValidationError("La columna inicial debe estar antes de la columna final")

            if start_row > end_row:
                raise forms.ValidationError("La fila inicial debe ser menor o igual a la fila final")

            # Validar contra dimensiones del archivo (si está disponible)
            if hasattr(self, 'file_data'):
                max_col = self.file_data['max_col']
                max_row = self.file_data['max_row']

                if start_col_num > max_col or end_col_num > max_col:
                    available_cols = f"A-{self.number_to_excel_column(max_col)}"
                    raise forms.ValidationError(
                        f"El rango excede las columnas disponibles ({available_cols})"
                    )

                if end_row > max_row:
                    raise forms.ValidationError(
                        f"El rango excede las filas disponibles (máx: {max_row})"
                    )

        except (ValueError, IndexError) as e:
            raise forms.ValidationError("Formato de rango inválido. Use formato como 'B2:G500'")

        return cell_range


    def clean(self):
        """Perform additional validations."""
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        
        if file and file.name.lower().endswith(('.xls', '.xlsx')):
            if cleaned_data.get('cell_range') and not cleaned_data.get('sheet_name'):
                self.add_error('sheet_name', "You must specify a sheet when using a cell range.")
        
        return cleaned_data