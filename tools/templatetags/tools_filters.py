from django import template

register = template.Library()

@register.filter
def is_field_mapped(field_name, column_mapping_info):
    """
    Devuelve True si el campo requerido está mapeado en column_mapping_info.
    """
    if not field_name or not column_mapping_info:
        return False
    field_name = str(field_name).lower()
    for col_info in column_mapping_info:
        mapped_to = col_info.get('mapped_to')
        if mapped_to and str(mapped_to).lower() == field_name:
            return True
    return False

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