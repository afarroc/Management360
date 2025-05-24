from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Filtro para acceder a valores de diccionario en templates"""
    return dictionary.get(key, '')
    
@register.filter(name='is_excel_file')
def is_excel_file(value):
    if value:
        return value.name.endswith(('.xls', '.xlsx'))
    return False
