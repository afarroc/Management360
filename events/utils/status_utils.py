"""
Utilidades para gestión de estados
Centraliza funciones relacionadas con Status, ProjectStatus y TaskStatus
"""

from ..models import Status, ProjectStatus, TaskStatus
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


def statuses_get():
    """
    Obtiene todos los tipos de estados
    
    Returns:
        tuple: (event_statuses, project_statuses, task_statuses)
    """
    event_statuses = Status.objects.all().order_by('status_name')
    project_statuses = ProjectStatus.objects.all().order_by('status_name')
    task_statuses = TaskStatus.objects.all().order_by('status_name')
    
    logger.debug(f"Retrieved statuses: {event_statuses.count()} events, "
                 f"{project_statuses.count()} projects, {task_statuses.count()} tasks")
    
    return event_statuses, project_statuses, task_statuses


def get_default_status(model_type='event', default_name='Created'):
    """
    Obtiene el estado por defecto para un modelo
    
    Args:
        model_type (str): Tipo de modelo ('event', 'project', 'task')
        default_name (str): Nombre del estado por defecto
        
    Returns:
        object: Instancia del estado o None
    """
    model_map = {
        'event': Status,
        'project': ProjectStatus,
        'task': TaskStatus
    }
    
    model = model_map.get(model_type)
    if not model:
        logger.error(f"Invalid model type: {model_type}")
        return None
    
    try:
        status = model.objects.get(status_name=default_name)
        logger.debug(f"Default {model_type} status found: {status.status_name} (ID: {status.id})")
        return status
    except ObjectDoesNotExist:
        logger.warning(f"Default {model_type} status '{default_name}' not found")
        
        # Intentar obtener el primer estado disponible
        first_status = model.objects.first()
        if first_status:
            logger.info(f"Using first available {model_type} status: {first_status.status_name}")
            return first_status
        
        logger.error(f"No {model_type} statuses found in database")
        return None
    except Exception as e:
        logger.exception(f"Error getting default {model_type} status: {e}")
        return None


def get_active_status(model_type='event'):
    """
    Obtiene el estado activo (In Progress) para un modelo
    
    Args:
        model_type (str): Tipo de modelo ('event', 'project', 'task')
        
    Returns:
        object: Instancia del estado activo o None
    """
    return get_default_status(model_type, default_name='In Progress')


def ensure_default_statuses():
    """
    Asegura que existan los estados por defecto en todos los modelos
    
    Returns:
        dict: Estados creados/encontrados
    """
    from django.db import transaction
    
    default_statuses = {
        'event': ['Created', 'In Progress', 'Completed', 'Cancelled', 'Planned'],
        'project': ['Created', 'In Progress', 'Completed', 'On Hold', 'Cancelled'],
        'task': ['To Do', 'In Progress', 'Completed', 'Blocked', 'Cancelled']
    }
    
    models = {
        'event': Status,
        'project': ProjectStatus,
        'task': TaskStatus
    }
    
    result = {
        'created': [],
        'existing': [],
        'failed': []
    }
    
    with transaction.atomic():
        for model_type, status_names in default_statuses.items():
            model = models[model_type]
            
            for status_name in status_names:
                try:
                    status, created = model.objects.get_or_create(
                        status_name=status_name,
                        defaults={'description': f'{status_name} status for {model_type}'}
                    )
                    
                    if created:
                        result['created'].append(f"{model_type}.{status_name}")
                        logger.info(f"Created {model_type} status: {status_name}")
                    else:
                        result['existing'].append(f"{model_type}.{status_name}")
                        
                except Exception as e:
                    result['failed'].append(f"{model_type}.{status_name}: {str(e)}")
                    logger.error(f"Failed to create {model_type} status '{status_name}': {e}")
    
    logger.info(f"Status check complete. Created: {len(result['created'])}, "
                f"Existing: {len(result['existing'])}, Failed: {len(result['failed'])}")
    
    return result

def update_status(obj, field_name, new_status, editor):
    old_value = getattr(obj, field_name).status_name
    setattr(obj, field_name, new_status)
    new_value = getattr(obj, field_name).status_name

    obj.record_edit(
        editor=editor,
        field_name=field_name,
        old_value=str(old_value),
        new_value=str(new_value),
    )
    obj.save()
