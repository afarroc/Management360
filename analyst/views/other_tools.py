# analyst/views/other_tools.py
import logging
from django.shortcuts import render
from django.http import JsonResponse
from analyst.services.planning import (
    AgentsFTE, utilisation, ErlangC, ServiceLevel
)
from analyst.utils.calculations import calcular_trafico_intensidad

logger = logging.getLogger(__name__)

def calculate_agents(request):
    """
    Vista para calcular agentes requeridos usando Erlang-C
    """
    logger.info("Accediendo a calculadora de agentes")
    
    if request.method == 'POST':
        try:
            # Extraer parámetros
            calls = int(request.POST.get('calls', 0))
            reporting_period = int(request.POST.get('reporting_period', 60))
            average_handling_time = float(request.POST.get('average_handling_time', 0))
            service_level_agreement = float(request.POST.get('service_level_agreement', 0))
            service_level_time = float(request.POST.get('service_level_time', 0))
            shrinkage = float(request.POST.get('shrinkage', 0))

            logger.debug(f"Calculando agentes - Calls: {calls}, AHT: {average_handling_time}")

            # Calcular agentes requeridos
            agents_required = AgentsFTE(
                calls, reporting_period, average_handling_time,
                service_level_agreement, service_level_time, shrinkage
            )
            
            # Calcular utilización
            intensity = (calls / (reporting_period * 60)) * average_handling_time
            util = utilisation(intensity, agents_required * (1 - shrinkage))
            
            # Calcular Erlang-C
            erlang_c = ErlangC(intensity, int(agents_required * (1 - shrinkage)))

            context = {
                'agents_required': round(agents_required, 2),
                'agents_fte': round(agents_required, 0),
                'utilization': round(util * 100, 2),
                'erlang_c': round(erlang_c * 100, 2),
                'calls': calls,
                'reporting_period': reporting_period,
                'average_handling_time': average_handling_time,
                'service_level_agreement': service_level_agreement,
                'service_level_time': service_level_time,
                'shrinkage': shrinkage,
            }
            
            logger.info(f"Cálculo completado - Agentes: {context['agents_required']}")
            return render(request, 'analyst/calculator.html', context)
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error en cálculo: {str(e)}")
            context = {'error': str(e)}
            return render(request, 'analyst/calculator.html', context)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}", exc_info=True)
            context = {'error': 'Error inesperado en el cálculo'}
            return render(request, 'analyst/calculator.html', context)
    
    return render(request, 'analyst/calculator.html')


def calcular_trafico_intensidad_view(request):
    """
    Vista para calcular intensidad de tráfico en Erlangs
    """
    logger.info("Calculando intensidad de tráfico")
    
    if request.method == 'POST':
        try:
            llamadas = int(request.POST.get('llamadas', 0))
            tiempo_manejo_promedio = int(request.POST.get('tiempo_manejo_promedio', 0))

            trafico_intensidad = calcular_trafico_intensidad(llamadas, tiempo_manejo_promedio)
            
            logger.debug(f"Intensidad calculada: {trafico_intensidad} Erlangs")
            return JsonResponse({
                'trafico_intensidad': round(trafico_intensidad, 2),
                'unidad': 'Erlangs'
            })
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculando intensidad: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Error inesperado'}, status=500)

    return render(request, 'analyst/calculator.html')