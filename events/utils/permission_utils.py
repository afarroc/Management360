"""
Utilidades para permisos y validaciones
Centraliza toda la lógica de permisos de usuarios
"""

from django.db.models import Q
from ..models import Event
from .profile_utils import is_superuser_role, get_user_role
import logging

logger = logging.getLogger(__name__)


def is_superuser(user):
    """
    Verifica si el usuario es superusuario (SU)
    
    Args:
        user (User): Instancia de usuario
        
    Returns:
        bool: True si es superusuario
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    return is_superuser_role(user)


def has_role(user, role):
    """
    Verifica si el usuario tiene un rol específico
    
    Args:
        user (User): Instancia de usuario
        role (str): Rol a verificar
        
    Returns:
        bool: True si tiene el rol
    """
    if not user.is_authenticated:
        return False
    
    user_role = get_user_role(user)
    return user_role == role


def has_event_permission(user, event, permission_type='view'):
    """
    Verifica permisos para eventos
    
    Args:
        user (User): Usuario
        event (Event): Evento
        permission_type (str): Tipo de permiso ('view', 'edit', 'delete')
        
    Returns:
        bool: True si tiene permiso
    """
    if not user.is_authenticated:
        return False
    
    # Superusuarios tienen todos los permisos
    if is_superuser(user):
        return True
    
    # Verificar según tipo de permiso
    if permission_type == 'view':
        return (event.host == user or 
                user in event.attendees.all() or 
                event.assigned_to == user)
    
    elif permission_type == 'edit':
        return (event.host == user or 
                event.assigned_to == user)
    
    elif permission_type == 'delete':
        # Solo superusuarios pueden eliminar eventos con relaciones
        return is_superuser(user) and not _has_related_objects(event)
    
    return False


def can_edit_event(user, event):
    """
    Verifica si el usuario puede editar el evento
    
    Args:
        user (User): Usuario
        event (Event): Evento
        
    Returns:
        bool: True si puede editar
    """
    return has_event_permission(user, event, 'edit')


def get_editable_events(user):
    """
    Obtiene eventos editables por el usuario
    
    Args:
        user (User): Usuario
        
    Returns:
        QuerySet: Eventos editables
    """
    if is_superuser(user):
        return Event.objects.all().select_related(
            'event_status', 'host'
        ).order_by('-updated_at')
    else:
        return Event.objects.filter(
            Q(host=user) | 
            Q(assigned_to=user)
        ).distinct().select_related(
            'event_status', 'host'
        ).order_by('-updated_at')


def check_edit_permissions(user, event):
    """
    Verifica permisos de edición y lanza excepción si no tiene
    
    Args:
        user (User): Usuario
        event (Event): Evento
        
    Raises:
        PermissionDenied: Si no tiene permisos
    """
    from django.core.exceptions import PermissionDenied
    
    if not can_edit_event(user, event):
        logger.warning(f"User {user.username} attempted to edit event {event.id} without permission")
        raise PermissionDenied('No tienes permisos para editar este evento.')
    
    return True


def _has_related_objects(event):
    """
    Verifica si el evento tiene objetos relacionados
    
    Args:
        event (Event): Evento
        
    Returns:
        bool: True si tiene proyectos o tareas
    """
    from ..models import Project, Task
    
    has_projects = Project.objects.filter(event=event).exists()
    has_tasks = Task.objects.filter(event=event).exists()
    
    return has_projects or has_tasks