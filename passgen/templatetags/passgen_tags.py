from django import template

register = template.Library()

@register.filter(name='call')
def call_method(obj, method_name, *args):
    """Template filter to call a method with arguments"""
    method = getattr(obj, method_name)
    return method(*args)