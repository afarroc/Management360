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