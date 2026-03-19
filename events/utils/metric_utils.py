"""
Utilidades para métricas y KPIs
Centraliza funciones de cálculo de indicadores y tendencias
"""

from datetime import timedelta
from django.utils import timezone
from ..models import Project, Task, Event
from .managers import get_managers_for_user
import logging

logger = logging.getLogger(__name__)


def calculate_percentage_increase(queryset, days, end_date):
    """
    Calcula el porcentaje de incremento entre dos períodos
    
    Args:
        queryset: QuerySet de objetos
        days (int): Número de días por período
        end_date (date): Fecha final del período reciente
        
    Returns:
        dict: Datos de incremento
    """
    start_date = end_date - timedelta(days=days)
    previous_end_date = start_date
    previous_start_date = previous_end_date - timedelta(days=days)
    
    recent_objects = queryset.filter(created_at__range=(start_date, end_date))
    previous_objects = queryset.filter(created_at__range=(previous_start_date, previous_end_date))
    
    count_recent = recent_objects.count()
    count_previous = previous_objects.count()
    
    if count_previous > 0:
        percentage_increase = round(((count_recent - count_previous) / count_previous) * 100, 2)
    else:
        percentage_increase = 100 if count_recent > 0 else 0
    
    return {
        'percentage_increase': percentage_increase,
        'total_recent': count_recent,
        'total_previous': count_previous,
        'start_date': start_date,
        'end_date': end_date,
        'previous_start_date': previous_start_date,
        'previous_end_date': previous_end_date
    }


def get_card_data(user, days, days_ago=None):
    """
    Obtiene datos para tarjetas de métricas
    
    Args:
        user (User): Usuario
        days (int): Días del período actual
        days_ago (int, optional): Días hacia atrás para fecha final
        
    Returns:
        dict: Datos de métricas para proyectos, tareas y eventos
    """
    today = timezone.now().date()
    
    # Determinar fecha final
    if days_ago is not None:
        try:
            days_ago = int(days_ago)
            end_date = today - timedelta(days=days_ago)
        except (ValueError, TypeError):
            end_date = today
    else:
        end_date = today
    
    start_date = end_date - timedelta(days=days)
    
    # Calcular incrementos
    projects_data = calculate_percentage_increase(Project.objects.all(), days, end_date)
    tasks_data = calculate_percentage_increase(Task.objects.all(), days, end_date)
    events_data = calculate_percentage_increase(Event.objects.all(), days, end_date)
    
    return {
        'projects': {
            'count': projects_data['total_recent'] + projects_data['total_previous'],
            'increase': projects_data['percentage_increase'],
            'recent_count': projects_data['total_recent'],
            'previous_count': projects_data['total_previous'],
            'start_date': start_date,
            'end_date': end_date,
        },
        'tasks': {
            'count': tasks_data['total_recent'] + tasks_data['total_previous'],
            'increase': tasks_data['percentage_increase'],
            'recent_count': tasks_data['total_recent'],
            'previous_count': tasks_data['total_previous'],
            'start_date': start_date,
            'end_date': end_date,
        },
        'events': {
            'count': events_data['total_recent'] + events_data['total_previous'],
            'increase': events_data['percentage_increase'],
            'recent_count': events_data['total_recent'],
            'previous_count': events_data['total_previous'],
            'start_date': start_date,
            'end_date': end_date,
        },
    }


def get_metric_trend(current, previous):
    """
    Determina la tendencia de una métrica
    
    Args:
        current (float): Valor actual
        previous (float): Valor anterior
        
    Returns:
        dict: Información de tendencia
    """
    if previous == 0:
        if current > 0:
            return {'direction': 'up', 'icon': 'arrow-up', 'class': 'text-green-600'}
        elif current < 0:
            return {'direction': 'down', 'icon': 'arrow-down', 'class': 'text-red-600'}
        else:
            return {'direction': 'neutral', 'icon': 'minus', 'class': 'text-gray-600'}
    
    change = current - previous
    percentage = (change / abs(previous)) * 100
    
    if change > 0:
        return {
            'direction': 'up',
            'icon': 'arrow-up',
            'class': 'text-green-600',
            'change': change,
            'percentage': round(percentage, 2)
        }
    elif change < 0:
        return {
            'direction': 'down',
            'icon': 'arrow-down',
            'class': 'text-red-600',
            'change': abs(change),
            'percentage': round(abs(percentage), 2)
        }
    else:
        return {
            'direction': 'neutral',
            'icon': 'minus',
            'class': 'text-gray-600',
            'change': 0,
            'percentage': 0
        }


def format_percentage(value, include_symbol=True):
    """
    Formatea un valor como porcentaje
    
    Args:
        value (float): Valor a formatear
        include_symbol (bool): Incluir símbolo %
        
    Returns:
        str: Porcentaje formateado
    """
    try:
        formatted = f"{float(value):.1f}"
        if include_symbol:
            return f"{formatted}%"
        return formatted
    except (ValueError, TypeError):
        return "0.0%" if include_symbol else "0.0"


def format_metric_value(value, metric_type='number'):
    """
    Formatea valores de métricas según su tipo
    
    Args:
        value: Valor a formatear
        metric_type (str): Tipo de métrica ('number', 'currency', 'percentage', 'time')
        
    Returns:
        str: Valor formateado
    """
    try:
        if metric_type == 'number':
            return f"{int(value):,}".replace(',', '.')
        elif metric_type == 'currency':
            return f"${float(value):,.2f}".replace(',', '.')
        elif metric_type == 'percentage':
            return f"{float(value):.1f}%"
        elif metric_type == 'time':
            hours = float(value)
            if hours < 1:
                minutes = int(hours * 60)
                return f"{minutes} min"
            elif hours < 24:
                return f"{hours:.1f} h"
            else:
                days = hours / 24
                return f"{days:.1f} d"
        else:
            return str(value)
    except (ValueError, TypeError):
        return "0"