"""
Sistema de funciones ejecutables para el asistente IA
Permite al asistente ejecutar comandos CRUD básicos a través del chat
"""

import re
import time
from typing import Dict, Any, Optional, Callable
from django.contrib.auth.models import User
from events.models import Project, ProjectStatus, Task, TaskStatus, Event, Status
from .models import CommandLog


class FunctionRegistry:
    """Registro de funciones disponibles para el asistente"""

    def __init__(self):
        self.functions: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, func: Callable, description: str,
                 parameters: Dict[str, str], examples: list):
        """Registra una función en el sistema"""
        self.functions[name] = {
            'function': func,
            'description': description,
            'parameters': parameters,
            'examples': examples
        }

    def get_function(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtiene una función por nombre"""
        return self.functions.get(name)

    def list_functions(self) -> Dict[str, Dict[str, Any]]:
        """Lista todas las funciones registradas"""
        return self.functions


# Instancia global del registro
function_registry = FunctionRegistry()


def execute_and_log_command(user: User, command: str, function_name: str, func: Callable, **kwargs) -> Dict[str, Any]:
    """
    Ejecuta una función y registra el comando en el log
    """
    start_time = time.time()

    try:
        # Ejecutar la función
        result = func(user, **kwargs)
        execution_time = time.time() - start_time

        # Registrar en el log
        CommandLog.objects.create(
            user=user,
            command=command,
            function_name=function_name,
            parameters=kwargs,
            result=result,
            success=result.get('success', True),
            execution_time=execution_time
        )

        return result

    except Exception as e:
        execution_time = time.time() - start_time

        # Registrar error en el log
        error_result = {
            'success': False,
            'message': f'Error ejecutando {function_name}: {str(e)}'
        }

        CommandLog.objects.create(
            user=user,
            command=command,
            function_name=function_name,
            parameters=kwargs,
            result=error_result,
            success=False,
            execution_time=execution_time
        )

        return error_result


def parse_command(message: str) -> Optional[Dict[str, Any]]:
    """
    Parsea un mensaje para detectar si es un comando ejecutable
    Retorna dict con 'function_name' y 'params' si es comando, None si no
    """
    message = message.lower().strip()

    # Patrones para detectar comandos de proyectos
    project_patterns = {
        'create_project': [
            r'crea(?:r)?\s+un\s+proyecto\s+(?:llamado\s+)?["\']?([^"\']+)["\']?(?:\s+con\s+descripción\s+["\']?([^"\']*)["\']?)?',
            r'nuevo\s+proyecto\s+(?:llamado\s+)?["\']?([^"\']+)["\']?(?:\s+con\s+descripción\s+["\']?([^"\']*)["\']?)?',
        ],
        'list_projects': [
            r'lista\s+(?:mis\s+)?proyectos',
            r'muestra\s+(?:mis\s+)?proyectos',
            r'ver\s+(?:mis\s+)?proyectos',
        ],
        'update_project': [
            r'actualiza\s+proyecto\s+(\d+)\s+(.+)',
            r'cambia\s+proyecto\s+(\d+)\s+(.+)',
            r'modifica\s+proyecto\s+(\d+)\s+(.+)',
        ],
        'delete_project': [
            r'elimina\s+proyecto\s+(\d+)',
            r'borra\s+proyecto\s+(\d+)',
            r'delete\s+proyecto\s+(\d+)',
        ]
    }

    for func_name, patterns in project_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if func_name == 'create_project':
                    title = match.group(1).strip()
                    description = match.group(2).strip() if match.group(2) else ""
                    return {
                        'function_name': func_name,
                        'params': {'title': title, 'description': description}
                    }
                elif func_name == 'list_projects':
                    return {
                        'function_name': func_name,
                        'params': {}
                    }
                elif func_name == 'update_project':
                    project_id = int(match.group(1))
                    changes_str = match.group(2).strip()
                    # Parse simple: campo=valor
                    changes = {}
                    for change in changes_str.split(','):
                        if '=' in change:
                            field, value = change.split('=', 1)
                            changes[field.strip()] = value.strip()
                    return {
                        'function_name': func_name,
                        'params': {'project_id': project_id, 'changes': changes}
                    }
                elif func_name == 'delete_project':
                    project_id = int(match.group(1))
                    return {
                        'function_name': func_name,
                        'params': {'project_id': project_id}
                    }

    return None


# Funciones helper para logging
def log_command_execution(user: User, command: str, function_name: str, params: Dict[str, Any], result: Dict[str, Any], execution_time: float):
    """Registra la ejecución de un comando"""
    from .models import CommandLog
    CommandLog.objects.create(
        user=user,
        command=command,
        function_name=function_name,
        params=params,
        result=result,
        success=result.get('success', False),
        execution_time=execution_time,
        error_message=result.get('message', '') if not result.get('success', False) else ''
    )

def execute_with_logging(user: User, command: str, function_name: str, func, **kwargs) -> Dict[str, Any]:
    """Ejecuta una función con logging automático"""
    import time
    start_time = time.time()

    try:
        result = func(user, **kwargs)
        execution_time = time.time() - start_time
        log_command_execution(user, command, function_name, kwargs, result, execution_time)
        return result
    except Exception as e:
        execution_time = time.time() - start_time
        error_result = {
            'success': False,
            'message': f'Error interno: {str(e)}'
        }
        log_command_execution(user, command, function_name, kwargs, error_result, execution_time)
        return error_result

# Funciones CRUD para proyectos

def create_project(user: User, title: str, description: str = "") -> Dict[str, Any]:
    """Crea un nuevo proyecto"""
    try:
        # Obtener status por defecto (asumiendo que existe uno con nombre 'Planning' o similar)
        default_status = ProjectStatus.objects.filter(active=True).first()
        if not default_status:
            # Crear uno básico si no existe
            default_status = ProjectStatus.objects.create(
                status_name='Planning',
                icon='fas fa-tasks',
                active=True,
                color='blue'
            )

        project = Project.objects.create(
            title=title,
            description=description,
            host=user,
            assigned_to=user,
            project_status=default_status
        )

        return {
            'success': True,
            'message': f'Proyecto "{title}" creado exitosamente con ID {project.id}',
            'project_id': project.id
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error al crear proyecto: {str(e)}'
        }


def create_project_logged(user: User, command: str, title: str, description: str = "") -> Dict[str, Any]:
    """Crea un proyecto con logging"""
    return execute_and_log_command(user, command, 'create_project', create_project, title=title, description=description)


# Funciones logged disponibles globalmente
logged_functions = {
    'create_project_logged': create_project_logged,
    'list_projects_logged': lambda user, command: execute_and_log_command(user, command, 'list_projects', list_projects),
    'update_project_logged': lambda user, command, project_id, changes: execute_and_log_command(user, command, 'update_project', update_project, project_id=project_id, changes=changes),
    'delete_project_logged': lambda user, command, project_id: execute_and_log_command(user, command, 'delete_project', delete_project, project_id=project_id),
}


def list_projects(user: User) -> Dict[str, Any]:
    """Lista los proyectos del usuario"""
    try:
        projects = Project.objects.filter(host=user).order_by('-created_at')[:10]  # Últimos 10

        project_list = []
        for p in projects:
            project_list.append({
                'id': p.id,
                'title': p.title,
                'description': p.description[:50] + '...' if p.description and len(p.description) > 50 else p.description,
                'status': p.project_status.status_name,
                'created_at': p.created_at.strftime('%d/%m/%Y')
            })

        return {
            'success': True,
            'message': f'Encontrados {len(project_list)} proyectos',
            'projects': project_list
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error al listar proyectos: {str(e)}'
        }


def update_project(user: User, project_id: int, changes: Dict[str, str]) -> Dict[str, Any]:
    """Actualiza un proyecto"""
    try:
        project = Project.objects.get(id=project_id, host=user)

        # Campos permitidos para actualización
        allowed_fields = ['title', 'description']

        updated_fields = []
        for field, value in changes.items():
            if field in allowed_fields:
                setattr(project, field, value)
                updated_fields.append(field)

        if updated_fields:
            project.save()
            return {
                'success': True,
                'message': f'Proyecto {project_id} actualizado: {", ".join(updated_fields)}'
            }
        else:
            return {
                'success': False,
                'message': 'No se actualizó ningún campo válido'
            }
    except Project.DoesNotExist:
        return {
            'success': False,
            'message': f'Proyecto {project_id} no encontrado o no tienes permisos'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error al actualizar proyecto: {str(e)}'
        }


def delete_project(user: User, project_id: int) -> Dict[str, Any]:
    """Elimina un proyecto"""
    try:
        project = Project.objects.get(id=project_id, host=user)
        title = project.title
        project.delete()

        return {
            'success': True,
            'message': f'Proyecto "{title}" (ID {project_id}) eliminado exitosamente'
        }
    except Project.DoesNotExist:
        return {
            'success': False,
            'message': f'Proyecto {project_id} no encontrado o no tienes permisos'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error al eliminar proyecto: {str(e)}'
        }


def list_projects_logged(user: User, command: str) -> Dict[str, Any]:
    """Lista proyectos con logging"""
    return execute_and_log_command(user, command, 'list_projects', list_projects)


def update_project_logged(user: User, command: str, project_id: int, changes: Dict[str, str]) -> Dict[str, Any]:
    """Actualiza proyecto con logging"""
    return execute_and_log_command(user, command, 'update_project', update_project, project_id=project_id, changes=changes)


def delete_project_logged(user: User, command: str, project_id: int) -> Dict[str, Any]:
    """Elimina proyecto con logging"""
    return execute_and_log_command(user, command, 'delete_project', delete_project, project_id=project_id)


# Funciones wrapper con logging
def create_project_logged(user: User, command: str, title: str, description: str = "") -> Dict[str, Any]:
    return execute_with_logging(user, command, 'create_project', create_project, title=title, description=description)

def list_projects_logged(user: User, command: str) -> Dict[str, Any]:
    return execute_with_logging(user, command, 'list_projects', list_projects)

def update_project_logged(user: User, command: str, project_id: int, changes: Dict[str, str]) -> Dict[str, Any]:
    return execute_with_logging(user, command, 'update_project', update_project, project_id=project_id, changes=changes)

def delete_project_logged(user: User, command: str, project_id: int) -> Dict[str, Any]:
    return execute_with_logging(user, command, 'delete_project', delete_project, project_id=project_id)

# Registro de funciones
function_registry.register(
    'create_project',
    create_project_logged,
    'Crear un nuevo proyecto',
    {'title': 'Título del proyecto', 'description': 'Descripción opcional'},
    [
        'crea un proyecto llamado "Desarrollo Web"',
        'nuevo proyecto "App Móvil" con descripción "Desarrollo de aplicación iOS/Android"'
    ]
)

function_registry.register(
    'list_projects',
    list_projects_logged,
    'Listar tus proyectos',
    {},
    [
        'lista mis proyectos',
        'muestra proyectos'
    ]
)

function_registry.register(
    'update_project',
    update_project_logged,
    'Actualizar un proyecto existente',
    {'project_id': 'ID del proyecto', 'changes': 'Cambios en formato campo=valor'},
    [
        'actualiza proyecto 1 title="Nuevo Título"',
        'cambia proyecto 2 description="Nueva descripción"'
    ]
)

function_registry.register(
    'delete_project',
    delete_project_logged,
    'Eliminar un proyecto',
    {'project_id': 'ID del proyecto a eliminar'},
    [
        'elimina proyecto 1',
        'borra proyecto 5'
    ]
)

# Diccionario de funciones logged para acceso rápido
logged_functions = {
    'create_project_logged': create_project_logged,
    'list_projects_logged': list_projects_logged,
    'update_project_logged': update_project_logged,
    'delete_project_logged': delete_project_logged,
}