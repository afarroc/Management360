# schedule_filters.py
from django import template
import re

register = template.Library()

@register.filter
def only_hours(value):
    """
    Filtro: convierte una cadena de tiempo en formato 'X days X hours X minutes'
    a un formato 'X hrs XX min'.
    Ejemplo de uso en la plantilla: {{ my_datetime|timesince:item.end_time|only_hours }}
    """
    if isinstance(value, str):
        hours = 0
        minutes = 0

        # Buscar horas en la cadena
        hour_match = re.search(r'(\d+)\s*hour', value)
        if hour_match:
            hours = int(hour_match.group(1))

        # Buscar minutos en la cadena
        minute_match = re.search(r'(\d+)\s*minute', value)
        if minute_match:
            minutes = int(minute_match.group(1))

        # Formatear la cadena en 'X hrs XX min'
        return f'{hours} hr{"s" if hours != 1 else ""} {minutes} min'
    return value

@register.filter
def dict_item(dictionary, key):
    """
    Filtro: obtiene un elemento de un diccionario.
    Ejemplo de uso en la plantilla: {{ my_dict|dict_item:key }}
    """
    return dictionary.get(key)
