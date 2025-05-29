from django import template

register = template.Library()

@register.filter(name='is_excel_file')
def is_excel_file(value):
    if value:
        return value.name.endswith(('.xls', '.xlsx'))
    return False
    

@register.filter
def get_item(container, key):
    """
    Filtro seguro para obtener elementos de diccionarios o listas.
    Maneja ambos tipos de contenedores y devuelve '' si la clave/índice no existe.
    """
    try:
        if isinstance(container, dict):
            return container.get(key, '')
        elif isinstance(container, (list, tuple)) and isinstance(key, int):
            return container[key] if 0 <= key < len(container) else ''
        return ''
    except (TypeError, KeyError, IndexError, AttributeError):
        return ''