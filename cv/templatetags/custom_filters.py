# cv/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='split')
def split(value, delimiter):
    """Divide una cadena por el delimitador y devuelve una lista"""
    if value:
        return value.split(delimiter)
    return []

@register.filter(name='get_field_label')
def get_field_label(form, field_name):
    """
    Obtiene la etiqueta (label) de un campo del formulario
    Uso: {{ form|get_field_label:'nombre_campo' }}
    """
    if form and field_name in form.fields:
        return form.fields[field_name].label or field_name.replace('_', ' ').title()
    return field_name.replace('_', ' ').title()

@register.filter(name='filename')
def filename(value):
    """Extrae el nombre de archivo de una ruta"""
    if value:
        return value.split('/')[-1]
    return ''

@register.filter(name='basename')
def basename(value):
    """Alias para filename"""
    return filename(value)

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Obtiene un elemento de un diccionario por su clave"""
    return dictionary.get(key, '')
    
@register.filter(name='field_type')
def field_type(field):
    """Devuelve el tipo de campo (útil para debugging)"""
    return field.field.widget.__class__.__name__

@register.filter(name='is_checkbox')
def is_checkbox(field):
    """Verifica si el campo es un checkbox"""
    return isinstance(field.field.widget, forms.CheckboxInput)

@register.filter(name='add_class')
def add_class(field, css_class):
    """Añade una clase CSS a un campo"""
    return field.as_widget(attrs={"class": css_class})

@register.filter(name='placeholder')
def placeholder(field, text):
    """Añade un placeholder a un campo"""
    return field.as_widget(attrs={"placeholder": text})