# events/templatetags/event_extras.py

from django import template
from django.utils.timesince import timesince
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def status_color(status_name):
    """
    Devuelve la clase de color de Bootstrap según el nombre del estado.
    Uso: {{ event.event_status.status_name|status_color }}
    """
    if not status_name:
        return 'secondary'
    
    # Normalizar: minúsculas y sin espacios extras
    key = status_name.lower().strip()
    
    color_map = {
        'created': 'secondary',
        'in progress': 'warning',
        'completed': 'success',
        'cancelled': 'danger',
        'planned': 'info',
        'on hold': 'dark',
        'pending': 'light',
        'approved': 'primary',
        'rejected': 'danger',
    }
    
    return color_map.get(key, 'light')

@register.filter
def duration(start_time, end_time=None):
    """
    Formatea la diferencia entre dos fechas (start_time y end_time).
    Si end_time es None, asume que la actividad sigue en curso.
    """
    if not start_time:
        return "—"
    
    if end_time is None:
        return "En curso"
    
    delta = end_time - start_time
    
    # Descomponer en días, horas, minutos, segundos
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 and days == 0:  # Mostrar minutos solo si es < 1 día
        parts.append(f"{minutes}m")
    elif days == 0 and hours == 0 and minutes == 0:
        return f"{seconds}s"
    
    return " ".join(parts) if parts else "0s"