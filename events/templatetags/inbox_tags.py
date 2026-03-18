# events/templatetags/inbox_tags.py
from django import template
from django.urls import reverse

register = template.Library()

@register.filter
def get_linked_object_type(processed_to):
    """
    Devuelve el tipo de objeto vinculado como string
    """
    if not processed_to:
        return None
    
    # Obtener el nombre de la clase del objeto
    class_name = processed_to.__class__.__name__
    
    # Mapear nombres de clase a tipos más amigables
    type_map = {
        'Task': 'task',
        'Project': 'project',
        'Event': 'event',
    }
    
    return type_map.get(class_name, class_name.lower())

@register.filter
def get_linked_object_url(processed_to):
    """
    Devuelve la URL para el objeto vinculado
    """
    if not processed_to:
        return '#'
    
    class_name = processed_to.__class__.__name__
    
    try:
        if class_name == 'Task':
            return reverse('tasks_with_id', args=[processed_to.id])
        elif class_name == 'Project':
            return reverse('project_detail', args=[processed_to.id])
        elif class_name == 'Event':
            return reverse('event_detail', args=[processed_to.id])
    except:
        pass
    
    return '#'

@register.filter
def get_linked_object_icon(processed_to):
    """
    Devuelve el icono para el objeto vinculado
    """
    if not processed_to:
        return 'bi-question-circle'
    
    class_name = processed_to.__class__.__name__
    
    icon_map = {
        'Task': 'bi-check-circle',
        'Project': 'bi-folder',
        'Event': 'bi-calendar',
    }
    
    return icon_map.get(class_name, 'bi-question-circle')

@register.filter
def get_linked_object_button_class(processed_to):
    """
    Devuelve la clase del botón según el tipo de objeto
    """
    if not processed_to:
        return 'btn-secondary'
    
    class_name = processed_to.__class__.__name__
    
    class_map = {
        'Task': 'btn-success',
        'Project': 'btn-primary',
        'Event': 'btn-info',
    }
    
    return class_map.get(class_name, 'btn-secondary')