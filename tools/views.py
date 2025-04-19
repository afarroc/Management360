# Standard library imports
import os
import csv
from io import BytesIO, StringIO

# Third-party imports
import pandas as pd
import chardet

# Django imports
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist

# Local imports
from .planning import (AgentsFTE, utilisation)
from .utils import calcular_trafico_intensidad
from .forms import DataUploadForm





class FileProcessor:
    """Clase para unificar el procesamiento de archivos CSV y Excel"""
    
    @staticmethod
    def detect_encoding(file):
        """Detectar codificación de archivos CSV"""
        raw_data = file.read(10240)
        result = chardet.detect(raw_data)
        file.seek(0)
        if result['encoding'] in ['ISO-8859-1', 'Windows-1252']:
            return 'latin-1'
        return result['encoding'] if result['confidence'] > 0.6 else 'latin-1'
    
    @staticmethod
    def normalize_name(name):
        """Normalizar nombres de columnas"""
        if not name:
            return ''
        name = str(name).strip().lower()
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            ' ': '_', '-': '_', '.': '_', '/': '_'
        }
        for orig, repl in replacements.items():
            name = name.replace(orig, repl)
        return name
    
    @classmethod
    def get_model_fields(cls, model):
        """Obtener campos del modelo normalizados"""
        return {
            cls.normalize_name(f.name): f 
            for f in model._meta.get_fields() 
            if f.concrete and not f.auto_created
        }
    
    @classmethod
    def process_file(cls, file, model, sheet_name=None, cell_range=None, column_mapping=None):
        """Procesar archivo (CSV o Excel) y devolver registros y metadatos"""  # Corregido typo
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension in ('.xls', '.xlsx'):
            return cls.process_excel(file, model, sheet_name, cell_range, column_mapping)
        else:
            return cls.process_csv(file, model, column_mapping)
      
    @classmethod
    def process_excel(cls, file, model, sheet_name=None, cell_range=None, column_mapping=None):
        """Procesar archivo Excel"""
        try:
            df = pd.read_excel(
                BytesIO(file.read()),
                sheet_name=sheet_name or 0,
                usecols=cell_range if cell_range else None
            )
            file.seek(0)
            
            preview_data = df.head().to_dict('records')
            columns = [str(col) for col in df.columns.tolist()]
            
            if column_mapping:
                records = cls._create_instances_with_mapping(df, model, column_mapping)
            else:
                records = cls._create_instances_auto(df, model)
            
            return records, preview_data, columns
        
        except Exception as e:
            raise ValueError(f"Error al procesar Excel: {str(e)}")
    
    @classmethod
    def process_csv(cls, file, model, column_mapping=None, delimiter=';'):  # Delimiter configurable
        """Procesar archivo CSV"""
        try:
            encoding = cls.detect_encoding(file)
            decoded_file = file.read().decode(encoding, errors='replace')
            file.seek(0)
            
            reader = csv.DictReader(StringIO(decoded_file), delimiter=delimiter)  # Usar parámetro
            reader.fieldnames = [cls.normalize_name(name) for name in (reader.fieldnames or [])]

            reader.fieldnames = [cls.normalize_name(name) for name in (reader.fieldnames or [])]
            
            # Convertir a DataFrame para consistencia con Excel
            df = pd.DataFrame(list(reader))
            preview_data = df.head().to_dict('records')
            columns = [str(col) for col in (df.columns.tolist() if not df.empty else [])]
            
            if column_mapping:
                records = cls._create_instances_with_mapping(df, model, column_mapping)
            else:
                records = cls._create_instances_auto(df, model)
            
            return records, preview_data, columns
        
        except Exception as e:
            raise ValueError(f"Error al procesar CSV: {str(e)}")
    
    @classmethod
    def _create_instances_auto(cls, df, model):
        """Crear instancias del modelo con mapeo automático"""
        model_fields = cls.get_model_fields(model)
        records = []
        
        for _, row in df.iterrows():
            instance_data = {}
            for field_name, field in model_fields.items():
                if field_name in df.columns and pd.notna(row[field_name]):
                    instance_data[field.name] = cls._convert_value(field, row[field_name])
            
            if instance_data:
                records.append(model(**instance_data))
        
        return records
    
    @classmethod
    def _create_instances_with_mapping(cls, df, model, column_mapping):
        """Crear instancias del modelo con mapeo personalizado"""
        records = []
        
        for _, row in df.iterrows():
            instance_data = {}
            for csv_col, model_field in column_mapping.items():
                if model_field and csv_col in df.columns and pd.notna(row[csv_col]):
                    try:
                        field = model._meta.get_field(model_field)
                        instance_data[model_field] = cls._convert_value(field, row[csv_col])
                    except FieldDoesNotExist:
                        continue
            
            if instance_data:
                records.append(model(**instance_data))
        
        return records
    
    @staticmethod
    def _convert_value(field, value):
        """Convertir valor según el tipo de campo"""
        if pd.isna(value):
            return None
            
        if field.get_internal_type() == 'IntegerField':
            return int(float(value))
        elif field.get_internal_type() == 'FloatField':
            if isinstance(value, str):
                value = value.replace(',', '.')
            return float(value)
        elif field.get_internal_type() == 'CharField':
            return str(value).strip()
        elif field.get_internal_type() == 'BooleanField':
            return bool(value)
        return value


# Calculator views
def calculate_agents(request):
    if request.method == 'POST':
        calls = int(request.POST.get('calls'))
        reporting_period = int(request.POST.get('reporting_period'))
        average_handling_time = float(request.POST.get('average_handling_time'))
        service_level_agreement = float(request.POST.get('service_level_agreement'))
        service_level_time = float(request.POST.get('service_level_time'))
        shrinkage = float(request.POST.get('shrinkage'))

        agents_required = AgentsFTE(calls, reporting_period, average_handling_time, 
                                  service_level_agreement, service_level_time, shrinkage)
        utilization = utilisation(calls, agents_required)

        context = {'agents_required': agents_required, 'utilization': utilization}
        return render(request, 'calculator.html', context)
    else:
        return render(request, 'calculator.html')


def calcular_trafico_intensidad_view(request):
    if request.method == 'POST':
        llamadas = int(request.POST.get('llamadas'))
        tiempo_manejo_promedio = int(request.POST.get('tiempo_manejo_promedio'))

        trafico_intensidad = calcular_trafico_intensidad(llamadas, tiempo_manejo_promedio)

        return JsonResponse({'trafico_intensidad': trafico_intensidad})

    return render(request, 'calculator.html')


# File management views
def file_tree_view(request):
    """
    Generate a JSON response with the file tree structure of a given app directory.
    If no app_name is provided, list all apps in the project.
    """
    app_name = request.GET.get("app_name", "")  # Get the app name from the query parameters

    if not app_name:
        # List all apps in the project
        apps_dir = os.path.join(settings.BASE_DIR)
        apps = [
            {"name": app, "type": "directory"}
            for app in os.listdir(apps_dir)
            if os.path.isdir(os.path.join(apps_dir, app)) and not app.startswith("__")
        ]
        return JsonResponse(apps, safe=False)

    # Generate file tree for the specified app
    base_dir = os.path.join(settings.BASE_DIR, app_name)
    if not os.path.exists(base_dir):
        return JsonResponse({"error": f"The app '{app_name}' does not exist or its directory is invalid."}, status=400)

    def get_file_tree(directory):
        tree = []
        for entry in os.listdir(directory):
            entry_path = os.path.join(directory, entry)
            if os.path.isdir(entry_path):
                tree.append({"name": entry, "type": "directory", "children": get_file_tree(entry_path)})
            else:
                tree.append({"name": entry, "type": "file"})
        return tree

    file_tree = get_file_tree(base_dir)
    return JsonResponse(file_tree, safe=False)

# Data upload view
def upload_data(request):
    if request.method == 'POST':
        form = DataUploadForm(request.POST, request.FILES)
        if form.is_valid():
            model = form.cleaned_data['model']
            file = request.FILES['file']
            
            try:
                # Limpiar datos existentes si se solicita
                if form.cleaned_data['clear_existing']:
                    model.objects.all().delete()
                    messages.info(request, f"Datos existentes en {model._meta.verbose_name} eliminados")
                
                # Procesar según el tipo de acción
                if 'preview' in request.POST:
                    # Vista previa para ambos tipos de archivo
                    records, preview_data, columns = FileProcessor.process_file(
                        file,
                        model,
                        form.cleaned_data.get('sheet_name'),
                        form.cleaned_data.get('cell_range')
                    )
                    
                    model_fields = [f.name for f in model._meta.get_fields() 
                                 if f.concrete and not f.auto_created]
                    
                    return render(request, 'tools/upload_data.html', {
                        'form': form,
                        'preview_data': preview_data,
                        'columns': columns,
                        'model_fields': model_fields,
                        'show_preview': True
                    })
                
                elif 'confirm_import' in request.POST:
                    # Procesar con mapeo personalizado
                    column_mapping = {
                        col: request.POST.get(f'map_{col}')
                        for col in request.POST.keys() if col.startswith('map_')
                    }
                    
                    records, _, _ = FileProcessor.process_file(
                        file,
                        model,
                        form.cleaned_data.get('sheet_name'),
                        form.cleaned_data.get('cell_range'),
                        column_mapping
                    )
                    
                    if records:
                        model.objects.bulk_create(records)
                        messages.success(request, f"{len(records)} registros cargados")
                        return redirect('upload_data')
                    else:
                        messages.warning(request, "No se encontraron datos válidos para importar")
                
                else:
                    # Procesamiento normal (sin vista previa)
                    records, _, _ = FileProcessor.process_file(
                        file,
                        model,
                        form.cleaned_data.get('sheet_name'),
                        form.cleaned_data.get('cell_range')
                    )
                    
                    if records:
                        model.objects.bulk_create(records)
                        messages.success(request, f"{len(records)} registros cargados")
                        return redirect('upload_data')
                    else:
                        messages.warning(request, "No se encontraron datos válidos para importar")
            
            except Exception as e:
                messages.error(request, f"Error durante la carga: {str(e)}")
                # Log the full error for debugging
                import logging
                logging.error("Error en upload_data: %s", str(e), exc_info=True)
    
    return render(request, 'tools/upload_data.html', {'form': DataUploadForm()})


