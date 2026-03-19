"""
Utilidades para gestión de managers
Centraliza la obtención de managers de eventos, proyectos y tareas
"""

from ..management.event_manager import EventManager
from ..management.project_manager import ProjectManager
from ..management.task_manager import TaskManager
import logging

logger = logging.getLogger(__name__)


def get_managers_for_user(user):
    """
    Obtiene instancias de todos los managers para un usuario
    
    Args:
        user (User): Usuario autenticado
        
    Returns:
        dict: Diccionario con instancias de managers
    """
    logger.debug(f"Getting managers for user: {user.username}")
    
    return {
        'event_manager': EventManager(user),
        'project_manager': ProjectManager(user),
        'task_manager': TaskManager(user)
    }


def get_manager_by_type(user, manager_type):
    """
    Obtiene un manager específico por tipo
    
    Args:
        user (User): Usuario autenticado
        manager_type (str): Tipo de manager ('event', 'project', 'task')
        
    Returns:
        object: Instancia del manager o None si no existe
    """
    managers = {
        'event': EventManager,
        'project': ProjectManager,
        'task': TaskManager
    }
    
    manager_class = managers.get(manager_type)
    if manager_class:
        return manager_class(user)
    
    logger.error(f"Unknown manager type: {manager_type}")
    return None