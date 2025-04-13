from django.shortcuts import render
from .planning import (AgentsFTE, utilisation)

def calculate_agents(request):
    if request.method == 'POST':
        calls = int(request.POST.get('calls'))
        reporting_period = int(request.POST.get('reporting_period'))
        average_handling_time = float(request.POST.get('average_handling_time'))
        service_level_agreement = float(request.POST.get('service_level_agreement'))
        service_level_time = float(request.POST.get('service_level_time'))
        shrinkage = float(request.POST.get('shrinkage'))

        agents_required = AgentsFTE(calls, reporting_period, average_handling_time, service_level_agreement, service_level_time, shrinkage)
        utilization = utilisation(calls, agents_required)

        context = {'agents_required': agents_required, 'utilization': utilization}
        return render(request, 'calculator.html', context)
    else:
        return render(request, 'calculator.html')



    # myapp/views.py
from django.shortcuts import render
from django.http import JsonResponse
from .utils import calcular_trafico_intensidad

def calcular_trafico_intensidad_view(request):
    if request.method == 'POST':
        llamadas = int(request.POST.get('llamadas'))
        tiempo_manejo_promedio = int(request.POST.get('tiempo_manejo_promedio'))

        trafico_intensidad = calcular_trafico_intensidad(llamadas, tiempo_manejo_promedio)

        return JsonResponse({'trafico_intensidad': trafico_intensidad})

    return render(request, 'calculator.html')

import os
from django.http import JsonResponse
from django.conf import settings

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


import csv
import chardet
from django.shortcuts import render, redirect
from django.contrib import messages
from django.apps import apps
from .forms import DataUploadForm

def detect_encoding(file):
    raw_data = file.read(10240)
    result = chardet.detect(raw_data)
    file.seek(0)
    if result['encoding'] in ['ISO-8859-1', 'Windows-1252']:
        return 'latin-1'
    return result['encoding'] if result['confidence'] > 0.6 else 'latin-1'

def upload_data(request):
    if request.method == 'POST':
        form = DataUploadForm(request.POST, request.FILES)
        if form.is_valid():
            model = form.cleaned_data['model']
            csv_file = request.FILES['csv_file']
            
            try:
                # Limpiar datos existentes si se solicita
                if form.cleaned_data['clear_existing']:
                    model.objects.all().delete()
                    messages.info(request, f"Datos existentes en {model._meta.verbose_name} eliminados")
                
                # Detectar codificación
                encoding = detect_encoding(csv_file)
                try:
                    decoded_file = csv_file.read().decode(encoding)
                except UnicodeDecodeError:
                    decoded_file = csv_file.read().decode(encoding, errors='replace')
                    messages.warning(request, "Algunos caracteres fueron reemplazados")
                
                # Procesar CSV (usar delimitador ;)
                reader = csv.DictReader(decoded_file.splitlines(), delimiter=';')
                
                # Normalizar nombres de columnas (sin espacios, minúsculas, sin tildes)
                def normalize_name(name):
                    name = name.strip().lower()
                    replacements = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'}
                    for orig, repl in replacements.items():
                        name = name.replace(orig, repl)
                    return name
                
                reader.fieldnames = [normalize_name(name) for name in reader.fieldnames]
                
                # Obtener campos del modelo (nombres normalizados)
                model_fields = {normalize_name(f.name): f for f in model._meta.get_fields() 
                              if f.concrete and not f.auto_created}
                
                # Verificar campos requeridos
                required_fields = [name for name, field in model_fields.items() 
                                 if not field.blank and not field.null and not field.has_default()]
                
                missing_fields = [field for field in required_fields 
                                if field not in reader.fieldnames]
                
                if missing_fields:
                    raise ValueError(
                        f"Faltan campos requeridos: {', '.join(missing_fields)}. "
                        f"Columnas encontradas: {', '.join(reader.fieldnames)}"
                    )
                
                # Crear instancias del modelo
                records = []
                for row_num, row in enumerate(reader, start=2):
                    try:
                        instance_data = {}
                        for field_name, field in model_fields.items():
                            # Buscar el nombre normalizado en las columnas
                            csv_column = next(
                                (col for col in row.keys() if normalize_name(col) == field_name),
                                None
                            )
                            
                            if csv_column and row[csv_column]:
                                value = row[csv_column].strip()
                                
                                # Conversión de tipos según el campo del modelo
                                if field.get_internal_type() == 'IntegerField':
                                    value = int(float(value)) if value else 0
                                elif field.get_internal_type() == 'FloatField':
                                    value = float(value.replace(',', '.')) if value else 0.0
                                elif field.get_internal_type() == 'CharField':
                                    value = str(value).strip()
                                
                                instance_data[field.name] = value
                        
                        records.append(model(**instance_data))
                    except Exception as e:
                        messages.warning(request, f"Error en fila {row_num}: {str(e)} - Fila omitida")
                        continue
                
                # Guardar en lote
                if records:
                    model.objects.bulk_create(records)
                    messages.success(
                        request, 
                        f"{len(records)} registros cargados en {model._meta.verbose_name}"
                    )
                    return redirect('upload_data')
                else:
                    messages.info(request, "No se encontraron registros válidos para importar")
                
            except Exception as e:
                messages.error(request, f"Error durante la carga: {str(e)}")
    else:
        form = DataUploadForm()
    
    return render(request, 'tools/upload_data.html', {'form': form})