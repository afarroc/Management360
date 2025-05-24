# tools/templatetags/excel_filters.py
from django import template

register = template.Library()

@register.filter(name='get_excel_column_name')
def get_excel_column_name(value):
    """Convierte un número a letra de columna Excel (1->A, 26->Z, 27->AA)"""
    result = []
    while value > 0:
        value, remainder = divmod(value - 1, 26)
        result.append(chr(65 + remainder))
    return ''.join(reversed(result))