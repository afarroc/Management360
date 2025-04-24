# Standard library imports
import logging
import os

# Third-party imports
import pandas as pd

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
from .file_processor import FileProcessor
from .constants import FORBIDDEN_MODELS, MAX_RECORDS_FOR_DELETION, MAX_RECORDS_FOR_IMPORT

# View to calculate required agents and utilization
def calculate_agents(request):
    if request.method == 'POST':
        # Extract input parameters from the request
        calls = int(request.POST.get('calls'))
        reporting_period = int(request.POST.get('reporting_period'))
        average_handling_time = float(request.POST.get('average_handling_time'))
        service_level_agreement = float(request.POST.get('service_level_agreement'))
        service_level_time = float(request.POST.get('service_level_time'))
        shrinkage = float(request.POST.get('shrinkage'))

        # Perform calculations
        agents_required = AgentsFTE(
            calls, reporting_period, average_handling_time,
            service_level_agreement, service_level_time, shrinkage
        )
        utilization = utilisation(calls, agents_required)

        # Render the results in the template
        context = {'agents_required': agents_required, 'utilization': utilization}
        return render(request, 'calculator.html', context)
    return render(request, 'calculator.html')


# View to calculate traffic intensity
def calcular_trafico_intensidad_view(request):
    if request.method == 'POST':
        # Extract input parameters from the request
        llamadas = int(request.POST.get('llamadas'))
        tiempo_manejo_promedio = int(request.POST.get('tiempo_manejo_promedio'))

        # Perform calculation
        trafico_intensidad = calcular_trafico_intensidad(llamadas, tiempo_manejo_promedio)
        return JsonResponse({'trafico_intensidad': trafico_intensidad})

    return render(request, 'calculator.html')


# View to generate a file tree structure for a given app directory
def file_tree_view(request):
    app_name = request.GET.get("app_name", "")

    if not app_name:
        # List all apps in the project if no app name is provided
        apps_dir = os.path.join(settings.BASE_DIR)
        apps = [
            {"name": app, "type": "directory"}
            for app in os.listdir(apps_dir)
            if os.path.isdir(os.path.join(apps_dir, app)) and not app.startswith("__")
        ]
        return JsonResponse(apps, safe=False)

    base_dir = os.path.join(settings.BASE_DIR, app_name)
    if not os.path.exists(base_dir):
        return JsonResponse({"error": f"The app '{app_name}' does not exist or its directory is invalid."}, status=400)

    # Recursively build the file tree
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


# View to handle data upload and processing
def upload_data(request):
    if request.method == 'POST':
        form = DataUploadForm(request.POST, request.FILES)
        is_confirmation = request.POST.get('is_confirmation') == 'true'

        # Rebuild the form if it's a confirmation step
        if is_confirmation:
            form_data = request.POST.copy()
            form_files = request.FILES.copy()
            if not form_files.get('file') and 'original_filename' in request.POST:
                form = DataUploadForm(form_data, form_files)
            else:
                form = DataUploadForm(request.POST, request.FILES)
        else:
            form = DataUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # Extract model and file from the form
                model = form.cleaned_data['model']
                file = form.cleaned_data.get('file')
                if is_confirmation and not file:
                    file = request.FILES.get('file')
                if not file:
                    messages.error(request, "File not found for processing")
                    return redirect('upload_data')

                # Validate model permissions
                model_path = f"{model._meta.app_label}.{model.__name__}"
                if model_path in FORBIDDEN_MODELS:
                    raise PermissionError(
                        f"Access denied: The model '{model._meta.verbose_name}' ({model_path}) is restricted."
                    )
                if not request.user.is_superuser and hasattr(model, 'is_restricted') and model.is_restricted:
                    raise PermissionError(
                        f"Access denied: Insufficient permissions to modify the model '{model._meta.verbose_name}'."
                    )

                # Clear existing records if requested
                if form.cleaned_data['clear_existing']:
                    record_count = model.objects.count()
                    if record_count > MAX_RECORDS_FOR_DELETION:
                        raise SecurityError(
                            f"Operation canceled: Attempt to delete {record_count} records exceeds the limit of {MAX_RECORDS_FOR_DELETION}."
                        )
                    model.objects.all().delete()
                    messages.info(request, f"All records in {model._meta.verbose_name} have been deleted.")

                # Handle different actions: preview, confirm import, or direct import
                if 'preview' in request.POST:
                    return handle_preview(request, form, model, file)
                elif 'confirm_import' in request.POST:
                    return handle_import_with_mapping(request, form, model, file)
                else:
                    return handle_direct_import(request, form, model, file)

            except PermissionError as e:
                messages.error(request, str(e))
            except SecurityError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error processing data: {str(e)}")
        else:
            # Display form errors
            messages.error(request, "Form error. Please check the entered data.")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, 'tools/upload_data.html', {'form': form})

    return render(request, 'tools/upload_data.html', {'form': form if 'form' in locals() else DataUploadForm()})


# Helper function to handle preview requests
def handle_preview(request, form, model, file):
    records, preview_data, columns = FileProcessor.process_file(
        file,
        model,
        form.cleaned_data.get('sheet_name'),
        form.cleaned_data.get('cell_range')
    )
    model_fields = [f.name for f in model._meta.get_fields() if f.concrete and not f.auto_created]
    return render(request, 'tools/upload_data.html', {
        'form': form,
        'preview_data': preview_data,
        'columns': columns,
        'model_fields': model_fields,
        'show_preview': True
    })


# Helper function to handle import with column mapping
def handle_import_with_mapping(request, form, model, file):
    try:
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
            if len(records) > MAX_RECORDS_FOR_IMPORT:
                raise SecurityError(f"Too many records to import at once (limit: {MAX_RECORDS_FOR_IMPORT})")
            model.objects.bulk_create(records)
            messages.success(request, f"{len(records)} records successfully imported into {model._meta.verbose_name}.")
            return redirect('upload_data')
        messages.warning(request, "No valid data found for import.")
        return redirect('upload_data')
    except Exception as e:
        messages.error(request, f"Error importing data: {str(e)}")
        return redirect('upload_data')


# Helper function to handle direct import without preview
def handle_direct_import(request, form, model, file):
    records, _, _ = FileProcessor.process_file(
        file,
        model,
        form.cleaned_data.get('sheet_name'),
        form.cleaned_data.get('cell_range')
    )
    if records:
        if len(records) > 10000:
            raise SecurityError("Too many records to import at once (limit: 10,000).")
        model.objects.bulk_create(records)
        messages.success(request, f"{len(records)} records successfully imported into {model._meta.verbose_name}.")
        return redirect('upload_data')
    messages.warning(request, "No valid data found for import.")
    return redirect('upload_data')


# Custom exception for security-related issues
class SecurityError(Exception):
    pass


