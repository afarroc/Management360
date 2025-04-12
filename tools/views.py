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