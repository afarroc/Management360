"""
Utilidades para gestión de tiempo y fechas
Centraliza funciones de cálculo temporal, rangos y formateo
"""

from datetime import datetime, date, timedelta
from django.utils import timezone
import calendar
import logging

logger = logging.getLogger(__name__)


def memento_mori(birth_date, death_date=None):
    """
    Calcula el tiempo de vida transcurrido y restante (Memento Mori)
    
    Args:
        birth_date (date): Fecha de nacimiento
        death_date (date, optional): Fecha de muerte estimada. 
                                     Por defecto: birth_date + 80 años
        
    Returns:
        dict: Estadísticas de tiempo de vida
    """
    now = datetime.now()
    
    if death_date is None:
        death_date = birth_date.replace(year=birth_date.year + 80)
    
    # Cálculos en días
    total_days = (death_date - birth_date).days
    passed_days = (now - birth_date).days
    left_days = total_days - passed_days
    
    # Cálculos en semanas
    total_weeks = int(total_days / 7)
    passed_weeks = int(passed_days / 7)
    left_weeks = int(left_days / 7)
    
    # Cálculos en años
    total_years = int(total_days / 365)
    
    # Porcentaje de vida transcurrido
    percentage_passed = round((passed_days / total_days) * 100, 2) if total_days > 0 else 0
    
    context = {
        'total_years': total_years,
        'now': now.strftime("%B %d, %Y"),
        'now_datetime': now,
        'total_days': total_days,
        'passed_days': passed_days,
        'left_days': left_days,
        'total_weeks': total_weeks,
        'passed_weeks': passed_weeks,
        'left_weeks': left_weeks,
        'percentage_passed': percentage_passed,
        'birth_date': birth_date.strftime("%B %d, %Y") if isinstance(birth_date, date) else str(birth_date),
        'death_date': death_date.strftime("%B %d, %Y") if isinstance(death_date, date) else str(death_date),
    }
    
    logger.debug(f"Memento Mori calculated for birth_date {birth_date}")
    return context


def get_date_range(days=30, end_date=None):
    """
    Genera un rango de fechas
    
    Args:
        days (int): Número de días en el rango
        end_date (date, optional): Fecha final. Por defecto: hoy
        
    Returns:
        tuple: (start_date, end_date)
    """
    if end_date is None:
        end_date = timezone.now().date()
    
    start_date = end_date - timedelta(days=days)
    
    return start_date, end_date


def format_date(date_obj, format_str="%Y-%m-%d"):
    """
    Formatea una fecha de manera segura
    
    Args:
        date_obj (date|datetime): Objeto fecha
        format_str (str): Formato de salida
        
    Returns:
        str: Fecha formateada o string vacío si es None
    """
    if not date_obj:
        return ""
    
    try:
        return date_obj.strftime(format_str)
    except Exception as e:
        logger.warning(f"Error formatting date {date_obj}: {e}")
        return str(date_obj)


def get_relative_time(dt):
    """
    Obtiene representación de tiempo relativo (hace X minutos, horas, días)
    
    Args:
        dt (datetime): Fecha/hora a comparar
        
    Returns:
        str: Texto descriptivo del tiempo transcurrido
    """
    if not dt:
        return "fecha desconocida"
    
    now = timezone.now()
    
    if not timezone.is_aware(dt) and timezone.is_aware(now):
        dt = timezone.make_aware(dt)
    
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "hace un momento"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"hace {minutes} minuto{'s' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"hace {hours} hora{'s' if hours != 1 else ''}"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"hace {days} día{'s' if days != 1 else ''}"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"hace {weeks} semana{'s' if weeks != 1 else ''}"
    else:
        return dt.strftime("%d/%m/%Y")


def get_week_range(date_obj=None):
    """
    Obtiene el rango de la semana para una fecha dada
    
    Args:
        date_obj (date, optional): Fecha. Por defecto: hoy
        
    Returns:
        tuple: (start_of_week, end_of_week)
    """
    if date_obj is None:
        date_obj = timezone.now().date()
    
    start_of_week = date_obj - timedelta(days=date_obj.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    return start_of_week, end_of_week


def get_month_range(date_obj=None):
    """
    Obtiene el rango del mes para una fecha dada
    
    Args:
        date_obj (date, optional): Fecha. Por defecto: hoy
        
    Returns:
        tuple: (start_of_month, end_of_month)
    """
    if date_obj is None:
        date_obj = timezone.now().date()
    
    start_of_month = date_obj.replace(day=1)
    
    _, last_day = calendar.monthrange(date_obj.year, date_obj.month)
    end_of_month = date_obj.replace(day=last_day)
    
    return start_of_month, end_of_month