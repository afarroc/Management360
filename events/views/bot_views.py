# events/bot_views.py
# ============================================================================
# VISTAS DE BOTS Y AUTOMATIZACIONES
# ============================================================================

import re
import logging
from io import StringIO

from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.http import JsonResponse

from ..utils import check_root_access

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURACIÓN DE BOTS
# ============================================================================

BOT_CONFIGS = {
    'project_bot': {
        'name': 'Bot de Proyectos',
        'tasks': {
            'create_project': 'create_project_simulation',
            'manage_tasks': 'manage_tasks_simulation',
            'generate_reports': 'generate_reports_simulation',
            'simulate_inbox': 'simulate_inbox_simulation'
        }
    },
    'teacher_bot': {
        'name': 'Bot Profesor',
        'tasks': {
            'create_course': 'create_course_simulation',
            'create_lesson': 'create_lesson_simulation',
            'create_content': 'create_content_simulation',
            'manage_students': 'manage_students_simulation'
        }
    },
    'client_bot': {
        'name': 'Bot Cliente',
        'tasks': {
            'simulate_inbox': 'simulate_client_inbox',
            'send_emails': 'simulate_email_sending',
            'create_tickets': 'create_support_tickets',
            'simulate_calls': 'simulate_phone_calls'
        }
    }
}


# ============================================================================
# API ENDPOINTS PARA PROCESAMIENTO DE CORREOS
# ============================================================================

@login_required
def check_new_emails_api(request):
    """
    API endpoint para verificar y procesar correos nuevos manualmente
    """
    # Verificar permisos usando la misma lógica que el dashboard root
    if not check_root_access(request.user):
        return JsonResponse({
            'success': False, 
            'error': 'No tienes permisos para acceder a esta funcionalidad'
        })

    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'error': 'Método no permitido'
        })

    try:
        # Capturar la salida del comando
        output = StringIO()
        call_command('process_cx_emails', stdout=output, max_emails=20)

        # Analizar la salida para extraer información
        output_str = output.getvalue()
        processed_count = 0

        # Buscar el número de emails procesados en la salida
        match = re.search(r'Processed (\d+) CX emails successfully', output_str)
        if match:
            processed_count = int(match.group(1))

        return JsonResponse({
            'success': True,
            'processed_count': processed_count,
            'message': f'Se procesaron {processed_count} emails CX exitosamente',
            'details': output_str
        })

    except Exception as e:
        logger.error(f"Error en check_new_emails_api: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def process_cx_emails_api(request):
    """
    API endpoint para procesar emails CX manualmente (versión más específica)
    """
    # Verificar permisos usando la misma lógica que el dashboard root
    if not check_root_access(request.user):
        return JsonResponse({
            'success': False, 
            'error': 'No tienes permisos para acceder a esta funcionalidad'
        })

    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'error': 'Método no permitido'
        })

    try:
        # Ejecutar el comando de procesamiento CX
        output = StringIO()
        call_command('process_cx_emails', stdout=output, max_emails=50, dry_run=False)

        # Analizar la salida
        output_str = output.getvalue()
        processed_count = 0

        # Extraer información de la salida
        match = re.search(r'Processed (\d+) CX emails successfully', output_str)
        if match:
            processed_count = int(match.group(1))

        return JsonResponse({
            'success': True,
            'processed_count': processed_count,
            'message': f'Procesamiento CX completado: {processed_count} emails procesados',
            'details': output_str
        })

    except Exception as e:
        logger.error(f"Error en process_cx_emails_api: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ============================================================================
# ACTIVACIÓN DE BOTS
# ============================================================================

@login_required
def activate_bot(request):
    """
    Vista para activar bots que simulan tareas usando credenciales de usuarios reales
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'error': 'Método no permitido'
        })

    # Verificar permisos - solo administradores pueden activar bots
    if not _user_can_activate_bots(request.user):
        return JsonResponse({
            'success': False, 
            'error': 'No tienes permisos para activar bots'
        })

    try:
        bot_id = request.POST.get('bot_id')
        selected_tasks = request.POST.getlist('tasks[]')

        # Validaciones iniciales
        validation_error = _validate_bot_request(bot_id, selected_tasks)
        if validation_error:
            return validation_error

        # Obtener configuración del bot
        bot_config = BOT_CONFIGS.get(bot_id)
        
        # Ejecutar tareas seleccionadas
        executed_tasks = _execute_bot_tasks(bot_config, selected_tasks, request.user)

        # Registrar la activación del bot
        logger.info(
            f"Bot {bot_config['name']} activado por {request.user.username}. "
            f"Tareas ejecutadas: {len(executed_tasks)}"
        )

        return JsonResponse({
            'success': True,
            'message': f'Bot {bot_config["name"]} activado exitosamente',
            'executed_tasks': executed_tasks,
            'bot_name': bot_config['name']
        })

    except Exception as e:
        logger.error(f"Error en activate_bot: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def _user_can_activate_bots(user):
    """
    Verifica si un usuario tiene permisos para activar bots
    """
    return (
        user.is_superuser or
        (hasattr(user, 'cv') and 
         hasattr(user.cv, 'role') and
         user.cv.role in ['SU', 'ADMIN', 'GTD_ANALYST'])
    )


def _validate_bot_request(bot_id, selected_tasks):
    """
    Valida los parámetros de la solicitud de activación de bot
    """
    if not bot_id:
        return JsonResponse({
            'success': False, 
            'error': 'Bot requerido'
        })

    if not selected_tasks:
        return JsonResponse({
            'success': False, 
            'error': 'Debes seleccionar al menos una tarea'
        })

    if bot_id not in BOT_CONFIGS:
        return JsonResponse({
            'success': False, 
            'error': 'Bot no válido'
        })

    return None


def _execute_bot_tasks(bot_config, selected_tasks, user):
    """
    Ejecuta las tareas seleccionadas del bot
    """
    executed_tasks = []

    for task_id in selected_tasks:
        if task_id in bot_config['tasks']:
            task_function_name = bot_config['tasks'][task_id]
            result = _execute_single_task(task_function_name, user)
            executed_tasks.append(result)

    return executed_tasks


def _execute_single_task(task_function_name, user):
    """
    Ejecuta una tarea individual del bot
    """
    try:
        # Obtener la función del ámbito global
        task_function = globals().get(task_function_name)
        
        if task_function and callable(task_function):
            result = task_function(user)
            return {
                'task_id': task_function_name,
                'status': 'success',
                'result': result
            }
        else:
            return {
                'task_id': task_function_name,
                'status': 'error',
                'error': f'Función {task_function_name} no encontrada'
            }
            
    except Exception as e:
        logger.error(f"Error ejecutando tarea {task_function_name}: {str(e)}", exc_info=True)
        return {
            'task_id': task_function_name,
            'status': 'error',
            'error': str(e)
        }


# ============================================================================
# FUNCIONES DE SIMULACIÓN (PLACEHOLDERS)
# ============================================================================

# Estas funciones son placeholders que deberían implementarse según necesidades reales
# Actualmente retornan mensajes de simulación

def create_project_simulation(user):
    """Simula la creación de un proyecto"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} creó un proyecto")
    return {"simulated": True, "action": "create_project", "user": user.username}


def manage_tasks_simulation(user):
    """Simula la gestión de tareas"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} gestionó tareas")
    return {"simulated": True, "action": "manage_tasks", "user": user.username}


def generate_reports_simulation(user):
    """Simula la generación de reportes"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} generó reportes")
    return {"simulated": True, "action": "generate_reports", "user": user.username}


def simulate_inbox_simulation(user):
    """Simula la creación de items en inbox"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} simuló inbox")
    return {"simulated": True, "action": "simulate_inbox", "user": user.username}


def create_course_simulation(user):
    """Simula la creación de un curso"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} creó un curso")
    return {"simulated": True, "action": "create_course", "user": user.username}


def create_lesson_simulation(user):
    """Simula la creación de una lección"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} creó una lección")
    return {"simulated": True, "action": "create_lesson", "user": user.username}


def create_content_simulation(user):
    """Simula la creación de contenido educativo"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} creó contenido")
    return {"simulated": True, "action": "create_content", "user": user.username}


def manage_students_simulation(user):
    """Simula la gestión de estudiantes"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} gestionó estudiantes")
    return {"simulated": True, "action": "manage_students", "user": user.username}


def simulate_client_inbox(user):
    """Simula la creación de inbox de cliente"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} simuló inbox de cliente")
    return {"simulated": True, "action": "simulate_client_inbox", "user": user.username}


def simulate_email_sending(user):
    """Simula el envío de emails"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} envió emails simulados")
    return {"simulated": True, "action": "send_emails", "user": user.username}


def create_support_tickets(user):
    """Simula la creación de tickets de soporte"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} creó tickets de soporte")
    return {"simulated": True, "action": "create_tickets", "user": user.username}


def simulate_phone_calls(user):
    """Simula llamadas telefónicas"""
    logger.info(f"SIMULACIÓN: Usuario {user.username} simuló llamadas")
    return {"simulated": True, "action": "simulate_calls", "user": user.username}