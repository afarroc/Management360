# Standard library imports
import os
import csv
from io import BytesIO

# Third-party imports
import pandas as pd
import chardet

# Django imports
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.apps import apps

# Local imports
from .planning import (AgentsFTE, utilisation)
from .utils import calcular_trafico_intensidad
from .forms import DataUploadForm


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


# Helper functions for data processing
def detect_encoding(file):
    """Detectar codificación de archivos CSV"""
    raw_data = file.read(10240)
    result = chardet.detect(raw_data)
    file.seek(0)
    if result['encoding'] in ['ISO-8859-1', 'Windows-1252']:
        return 'latin-1'
    return result['encoding'] if result['confidence'] > 0.6 else 'latin-1'


def normalize_name(name):
    """Normalizar nombres de columnas"""
    name = name.strip().lower()
    replacements = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'}
    for orig, repl in replacements.items():
        name = name.replace(orig, repl)
    return name


def process_excel(file, model, sheet_name=None, cell_range=None):
    """Procesar archivo Excel y devolver registros, vista previa y columnas"""
    df = pd.read_excel(
        BytesIO(file.read()),
        sheet_name=sheet_name or 0,
        usecols=cell_range if cell_range else None
    )
    
    # Convertir a lista de diccionarios para vista previa
    preview_data = df.head().to_dict('records')
    columns = df.columns.tolist()
    
    # Obtener campos del modelo
    model_fields = {normalize_name(f.name): f for f in model._meta.get_fields() 
                   if f.concrete and not f.auto_created}
    
    # Procesar registros
    records = []
    for _, row in df.iterrows():
        instance_data = {}
        for field_name, field in model_fields.items():
            if field_name in df.columns:
                value = row[field_name]
                if pd.notna(value):
                    if field.get_internal_type() == 'IntegerField':
                        value = int(float(value))
                    elif field.get_internal_type() == 'FloatField':
                        value = float(value)
                    elif field.get_internal_type() == 'CharField':
                        value = str(value).strip()
                    
                    instance_data[field.name] = value
        
        if instance_data:
            records.append(model(**instance_data))
    
    return records, preview_data, columns


def process_excel_with_mapping(file, model, sheet_name, cell_range, column_mapping):
    """Procesar Excel con mapeo personalizado de columnas"""
    df = pd.read_excel(
        BytesIO(file.read()),
        sheet_name=sheet_name or 0,
        usecols=cell_range if cell_range else None
    )
    
    records = []
    for _, row in df.iterrows():
        instance_data = {}
        for csv_col, model_field in column_mapping.items():
            if model_field and csv_col in df.columns and pd.notna(row[csv_col]):
                field = model._meta.get_field(model_field)
                value = row[csv_col]
                
                if field.get_internal_type() == 'IntegerField':
                    value = int(float(value))
                elif field.get_internal_type() == 'FloatField':
                    value = float(value)
                elif field.get_internal_type() == 'CharField':
                    value = str(value).strip()
                
                instance_data[model_field] = value
        
        if instance_data:
            records.append(model(**instance_data))
    
    return records


# Data upload view
def upload_data(request):
    if request.method == 'POST':
        form = DataUploadForm(request.POST, request.FILES)
        if form.is_valid():
            model = form.cleaned_data['model']
            file = request.FILES['file']
            
            try:
                if form.cleaned_data['clear_existing']:
                    model.objects.all().delete()
                    messages.info(request, f"Datos existentes en {model._meta.verbose_name} eliminados")
                
                # Detección case-insensitive de extensión
                file_extension = os.path.splitext(file.name)[1].lower()
                
                if file_extension in ('.xls', '.xlsx'):
                    # Procesar Excel
                    records, preview_data, columns = process_excel(
                        file,
                        model,
                        form.cleaned_data['sheet_name'],
                        form.cleaned_data['cell_range']
                    )
                    
                    if 'preview' in request.POST:
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
                    
                    records = process_excel_with_mapping(
                        file,
                        model,
                        form.cleaned_data['sheet_name'],
                        form.cleaned_data['cell_range'],
                        column_mapping
                    )
                
                else:
                    # Procesar CSV
                    encoding = detect_encoding(file)
                    decoded_file = file.read().decode(encoding, errors='replace')
                    file.seek(0)
                    
                    reader = csv.DictReader(decoded_file.splitlines(), delimiter=';')
                    reader.fieldnames = [normalize_name(name) for name in reader.fieldnames]
                    
                    model_fields = {normalize_name(f.name): f for f in model._meta.get_fields() 
                                  if f.concrete and not f.auto_created}
                    
                    records = []
                    for row in reader:
                        instance_data = {}
                        for field_name, field in model_fields.items():
                            if field_name in reader.fieldnames and row[field_name]:
                                value = row[field_name].strip()
                                if field.get_internal_type() == 'IntegerField':
                                    value = int(float(value))
                                elif field.get_internal_type() == 'FloatField':
                                    value = float(value.replace(',', '.'))
                                elif field.get_internal_type() == 'CharField':
                                    value = str(value).strip()
                                
                                instance_data[field.name] = value
                        
                        if instance_data:
                            records.append(model(**instance_data))
                
                if records:
                    model.objects.bulk_create(records)
                    messages.success(request, f"{len(records)} registros cargados")
                    return redirect('upload_data')
                
            except Exception as e:
                messages.error(request, f"Error durante la carga: {str(e)}")
    
    return render(request, 'tools/upload_data.html', {'form': DataUploadForm()})