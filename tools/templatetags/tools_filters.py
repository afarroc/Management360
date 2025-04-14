from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Filtro para acceder a valores de diccionario en templates"""
    return dictionary.get(key, '')