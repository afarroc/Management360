# templatetags/schedule_filters.py
# my_tags.py

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def dict_item(dictionary, key):
    return dictionary.get(key)

@register.filter
@stringfilter
def only_hours(value):
    """
    Filtro: elimina los minutos, segundos y microsegundos de un objeto datetime.
    Ejemplo de uso en la plantilla: {{ my_datetime|only_hours|timesince }}
    Esto mostrará las horas en my_datetime sin mostrar los minutos ni los segundos.
    """
    # replace devuelve un nuevo objeto en lugar de modificarlo directamente
    return value.replace(minute=0, second=0, microsecond=0)
