# analyst/utils/calculations.py
import logging
import math

logger = logging.getLogger(__name__)

def calcular_trafico_intensidad(calls: int, average_handling_time: int) -> float:
    """
    Calcula la intensidad de tráfico en Erlangs
    
    Args:
        calls: Número de llamadas
        average_handling_time: Tiempo promedio de manejo en minutos
    
    Returns:
        float: Intensidad de tráfico en Erlangs
    """
    try:
        call_minutes = calls * average_handling_time
        call_hours = call_minutes / 60
        logger.debug(f"Intensidad calculada: {call_hours} Erlangs")
        return call_hours
    except Exception as e:
        logger.error(f"Error calculando intensidad: {str(e)}")
        raise ValueError(f"Error en cálculo de intensidad: {str(e)}")


def factorial(n: int) -> int:
    """Calcula factorial de forma segura"""
    if n < 0:
        raise ValueError("Factorial no definido para números negativos")
    if n > 170:  # Límite para evitar overflow
        raise ValueError("Número demasiado grande para calcular factorial")
    return math.factorial(n)