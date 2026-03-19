# events/services/bot_simulation.py
from decimal import Decimal
from django.utils import timezone
from ..models import Project, Task, InboxItem, TaskStatus, ProjectStatus

# Funciones de simulación para bots

def create_project_simulation(user):
    """Simula la creación de un proyecto"""
    from .models import Project, ProjectStatus
    from django.utils import timezone

    # Obtener estado por defecto
    try:
        default_status = ProjectStatus.objects.get(status_name='Created')
    except ProjectStatus.DoesNotExist:
        default_status = ProjectStatus.objects.filter(status_name__icontains='created').first()
        if not default_status:
            default_status = ProjectStatus.objects.first()

    # Crear proyecto simulado
    project = Project.objects.create(
        title=f"Proyecto Simulado - {timezone.now().strftime('%Y%m%d_%H%M%S')}",
        description="Proyecto creado automáticamente por el Bot de Proyectos",
        host=user,
        assigned_to=user,
        project_status=default_status,
        ticket_price=Decimal('0.10')
    )

    return f"Proyecto '{project.title}' creado exitosamente (ID: {project.id})"


def manage_tasks_simulation(user):
    """Simula la gestión de tareas"""
    from .models import Task, TaskStatus, Project

    # Obtener proyectos del usuario
    projects = Project.objects.filter(host=user)[:3]  # Limitar a 3 proyectos

    tasks_created = 0
    for project in projects:
        try:
            default_status = TaskStatus.objects.get(status_name='To Do')
        except TaskStatus.DoesNotExist:
            default_status = TaskStatus.objects.filter(status_name__icontains='to do').first()
            if not default_status:
                default_status = TaskStatus.objects.first()

        # Crear tarea para el proyecto
        task = Task.objects.create(
            title=f"Tarea Simulada para {project.title}",
            description="Tarea creada automáticamente por el Bot de Proyectos",
            host=user,
            assigned_to=user,
            project=project,
            task_status=default_status,
            ticket_price=Decimal('0.05')
        )
        tasks_created += 1

    return f"{tasks_created} tareas creadas en {len(projects)} proyectos"


def generate_reports_simulation(user):
    """Simula la generación de reportes"""
    from .models import Project

    projects = Project.objects.filter(host=user)
    report_data = {
        'total_projects': projects.count(),
        'active_projects': projects.filter(project_status__status_name__in=['In Progress', 'Created']).count(),
        'completed_projects': projects.filter(project_status__status_name='Completed').count()
    }

    return f"Reporte generado: {report_data['total_projects']} proyectos totales, {report_data['active_projects']} activos, {report_data['completed_projects']} completados"


def simulate_inbox_simulation(user):
    """Simula la creación de items en el inbox"""
    from .models import InboxItem

    # Crear varios items de inbox simulados
    inbox_items = []
    for i in range(3):
        item = InboxItem.objects.create(
            title=f"Item de Inbox Simulado {i+1}",
            description="Item creado automáticamente por el Bot de Proyectos",
            created_by=user,
            gtd_category='accionable',
            priority='media',
            action_type='hacer'
        )
        inbox_items.append(item)

    return f"{len(inbox_items)} items de inbox creados"


def create_course_simulation(user):
    """Simula la creación de un curso"""
    # Nota: Esta función requiere que exista el modelo Course en la app courses
    try:
        from courses.models import Course

        course = Course.objects.create(
            title=f"Curso Simulado - {timezone.now().strftime('%Y%m%d_%H%M%S')}",
            description="Curso creado automáticamente por el Bot Profesor",
            instructor=user,
            price=Decimal('50.00')
        )

        return f"Curso '{course.title}' creado exitosamente (ID: {course.id})"
    except ImportError:
        return "Simulación: Módulo Course no disponible"
    except Exception as e:
        return f"Error en simulación de curso: {str(e)}"


def create_lesson_simulation(user):
    """Simula la creación de lecciones"""
    try:
        from courses.models import Course, Lesson

        # Obtener cursos del instructor
        courses = Course.objects.filter(instructor=user)[:2]

        lessons_created = 0
        for course in courses:
            lesson = Lesson.objects.create(
                course=course,
                title=f"Lección Simulada para {course.title}",
                content="Contenido creado automáticamente por el Bot Profesor",
                order=lessons_created + 1
            )
            lessons_created += 1

        return f"{lessons_created} lecciones creadas en {len(courses)} cursos"
    except ImportError:
        return "Simulación: Módulos Course/Lesson no disponibles"
    except Exception as e:
        return f"Error en simulación de lecciones: {str(e)}"


def create_content_simulation(user):
    """Simula la creación de contenido"""
    try:
        from courses.models import Course, ContentBlock

        courses = Course.objects.filter(instructor=user)[:2]

        content_created = 0
        for course in courses:
            content = ContentBlock.objects.create(
                course=course,
                title=f"Contenido Simulado para {course.title}",
                content="Contenido educativo creado automáticamente por el Bot Profesor",
                block_type='text'
            )
            content_created += 1

        return f"{content_created} bloques de contenido creados en {len(courses)} cursos"
    except ImportError:
        return "Simulación: Módulos Course/ContentBlock no disponibles"
    except Exception as e:
        return f"Error en simulación de contenido: {str(e)}"


def manage_students_simulation(user):
    """Simula la gestión de estudiantes"""
    try:
        from courses.models import Course, Enrollment

        courses = Course.objects.filter(instructor=user)[:2]

        enrollments_created = 0
        for course in courses:
            # Simular inscripción de estudiantes (esto es solo una simulación)
            # En un escenario real, se seleccionarían usuarios existentes
            enrollments_created += 1

        return f"Simulación: {enrollments_created} estudiantes inscritos en cursos"
    except ImportError:
        return "Simulación: Módulos Course/Enrollment no disponibles"
    except Exception as e:
        return f"Error en simulación de estudiantes: {str(e)}"


def simulate_client_inbox(user):
    """Simula consultas de clientes en el inbox"""
    from .models import InboxItem

    client_queries = [
        "Consulta sobre producto X",
        "Problema con la entrega",
        "Solicitud de información",
        "Queja sobre servicio"
    ]

    inbox_items = []
    for query in client_queries:
        item = InboxItem.objects.create(
            title=f"Consulta Cliente: {query}",
            description="Consulta simulada de cliente creada por el Bot Cliente",
            created_by=user,
            gtd_category='accionable',
            priority='alta',
            action_type='responder'
        )
        inbox_items.append(item)

    return f"{len(inbox_items)} consultas de cliente simuladas en inbox"


def simulate_email_sending(user):
    """Simula envío de emails"""
    # Esta es una simulación - en un escenario real enviaría emails
    emails_simulated = 5
    return f"Simulación: {emails_simulated} emails enviados a clientes"


def create_support_tickets(user):
    """Simula creación de tickets de soporte"""
    from .models import InboxItem

    tickets = []
    for i in range(3):
        ticket = InboxItem.objects.create(
            title=f"Ticket de Soporte #{i+1}",
            description="Ticket de soporte simulado creado por el Bot Cliente",
            created_by=user,
            gtd_category='accionable',
            priority='alta',
            action_type='resolver'
        )
        tickets.append(ticket)

    return f"{len(tickets)} tickets de soporte creados"


def simulate_phone_calls(user):
    """Simula registros de llamadas telefónicas"""
    from .models import InboxItem

    calls = []
    call_types = ["Consulta técnica", "Soporte urgente", "Información general"]

    for call_type in call_types:
        call = InboxItem.objects.create(
            title=f"Llamada: {call_type}",
            description="Registro de llamada telefónica simulada por el Bot Cliente",
            created_by=user,
            gtd_category='accionable',
            priority='media',
            action_type='seguir'
        )
        calls.append(call)

    return f"{len(calls)} registros de llamadas telefónicas creados"
