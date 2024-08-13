# myapp/templatetags/custom_tags.py
from django import template
from datetime import datetime

register = template.Library()

@register.simple_tag
def days_transcurridos_del_mes():
    today = datetime.today()
    return today.day - 1

@register.filter
def range_filter(value):
    return range(value)


