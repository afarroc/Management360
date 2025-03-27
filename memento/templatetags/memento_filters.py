from django import template

register = template.Library()

@register.filter
def percentage(part, whole):
    try:
        return float(part) / float(whole) * 100
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def range_filter(number):
    """Creates a range up to the given number for template iteration"""
    try:
        return range(int(number))
    except (ValueError, TypeError):
        return range(0)