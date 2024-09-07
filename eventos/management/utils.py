from decimal import Decimal
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, F, ExpressionWrapper, DurationField
from collections import defaultdict
import datetime
from ..models import CreditAccount, Project, Task, Event, TaskState, TaskStatus
from .event_manager import EventManager
from .project_manager import ProjectManager
from .task_manager import TaskManager





def memento_mori(birth_date, death_date):
    # Define the birth and death dates
    now = datetime.datetime.now()

    # Calculate the total days, passed days, and left days
    total_days = (death_date - birth_date).days
    passed_days = (now - birth_date).days
    left_days = total_days - passed_days

    # Calculate the total years
    total_years = int(total_days / 365)

    # Calculate the total weeks, passed weeks, and left weeks
    total_weeks = int(total_days / 7)
    passed_weeks = int(passed_days / 7)
    left_weeks = int(left_days / 7)

    context = {
        'total_years': total_years,
        'now': now.strftime("%B %d, %Y"),
        'total_days': total_days,
        'passed_days': passed_days,
        'left_days': left_days,
        'total_weeks': total_weeks,
        'passed_weeks': passed_weeks,
        'left_weeks': left_weeks
    }

    return context



def add_credits_to_user(user, amount):
    if not hasattr(user, 'creditaccount'):
        CreditAccount.objects.create(user=user)
    
    try:
        amount = Decimal(amount)
        user.creditaccount.add_credits(amount)
        return True, f"Monto agregado {amount}"
    except (ValueError, Decimal.InvalidOperation):
        return False, "Monto no válido"

def get_task_states_with_duration(start_date=None, end_date=None):
    in_progress_status = TaskStatus.objects.get(status_name='En Curso')
    
    # Construir la consulta para obtener solo los registros en el rango de fechas
    queryset = TaskState.objects.filter(status=in_progress_status).annotate(
        duration_seconds=ExpressionWrapper(
            F('end_time') - F('start_time'),
            output_field=DurationField()
        )
    )
    
    if start_date:
        queryset = queryset.filter(start_time__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(start_time__date__lte=end_date)

    queryset = queryset.order_by('-start_time')

    return [
        {
            'task_state': task_state,
            'duration_seconds': (duration_seconds := round(task_state.duration_seconds.total_seconds())) if task_state.duration_seconds else None,
            'duration_minutes': round(duration_seconds / 60, 1) if task_state.duration_seconds else None,
            'duration_hours': round(duration_seconds / 3600, 4) if task_state.duration_seconds else None,
            'start_date': task_state.start_time.date(),
            'start_time': task_state.start_time.strftime('%H:%M'),
            'end_time': task_state.end_time.strftime('%H:%M') if task_state.end_time else None,
        }
        for task_state in queryset
    ]

def get_bar_chart_data(task_states):
    task_count_dict = defaultdict(int)
    for task_state in task_states:
        task_title = task_state['task_state'].task.title
        task_count_dict[task_title] += 1
    
    sorted_tasks = sorted(task_count_dict.items(), key=lambda x: x[1], reverse=True)[:15]
    categories, counts = zip(*sorted_tasks) if sorted_tasks else ([], [])
    
    return {
        'categories': list(categories),
        'counts': list(counts),
    }

def get_line_chart_data(task_states_last_month):
    date_task_counts = (
        TaskState.objects.filter(id__in=[task_state['task_state'].id for task_state in task_states_last_month])
        .values('start_time__date', 'task')
        .annotate(task_count=Count('task', distinct=True))
        .order_by('start_time__date')
    )
    
    date_count_dict = defaultdict(int)
    for entry in date_task_counts:
        start_date = entry['start_time__date']
        task_count = entry['task_count']
        date_count_dict[start_date] += task_count
    
    sorted_dates = sorted(date_count_dict.items())
    dates, counts = zip(*sorted_dates) if sorted_dates else ([], [])
    
    return {
        'dates': [date.strftime('%Y-%m-%d') for date in dates],
        'counts_over_time': list(counts),
    }


def filter_data_last_month(data, key_name, start_date):
    filtered_data = [item for item in data if getattr(item[key_name], 'created_at', None).date() >= start_date]

    return count_created_per_day(filtered_data, key_name)

def count_created_per_day(data, key_name):
    counts = defaultdict(int)
    for item in data:
        created_date = getattr(item[key_name], 'created_at', None).date()
        if created_date:
            counts[created_date] += 1
    return counts

def fill_data_for_dates(date_range, counts):
    return [counts.get(date, 0) for date in date_range]

from datetime import timedelta

def get_combined_chart_data(user, start_date, end_date):
    # Convertir las listas de proyectos, tareas y eventos en queryset si es necesario
    project_manager = ProjectManager(user)
    task_manager = TaskManager(user)
    event_manager = EventManager(user)
    
    projects, _ = project_manager.get_all_projects()
    tasks, _ = task_manager.get_all_tasks()
    events, _  = event_manager.get_all_events()
    
    # Obtener conteos de objetos por día
    projects_created_per_day = filter_data_last_month(projects, 'project', start_date)
    tasks_created_per_day = filter_data_last_month(tasks, 'task', start_date)
    events_created_per_day = filter_data_last_month(events, 'event', start_date)

    # Crear un rango de fechas completo
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

    return {
        'dates': [date.strftime('%Y-%m-%d') for date in date_range],
        'projects': fill_data_for_dates(date_range, projects_created_per_day),
        'tasks': fill_data_for_dates(date_range, tasks_created_per_day),
        'events': fill_data_for_dates(date_range, events_created_per_day),
    }

def get_duration_chart_data(task_states):
    task_durations = defaultdict(float)
    for task_state in task_states:
        task_name = task_state['task_state'].task.title
        if task_state['duration_seconds']:
            task_durations[task_name] += (task_state['duration_seconds'] / 3600)
    
    return {
        'task_names': list(task_durations.keys()),
        'durations': [round(duration, 2) for duration in task_durations.values()],
    }

def get_card_data(user, days, days_ago=None):
    today = timezone.now().date()
    
    # Determinar la fecha final basada en days_ago o usar hoy como fecha final
    if days_ago is not None:
        try:
            days_ago = int(days_ago)
            end_date = today - datetime.timedelta(days=days_ago)
        except ValueError:
            end_date = today  # Fallback a today si days_ago no es válido
    else:
        end_date = today

    # Calcular la fecha de inicio basada en el rango de días
    start_date = end_date - datetime.timedelta(days=days)

    project_manager = ProjectManager(user)
    task_manager = TaskManager(user)
    event_manager = EventManager(user)
    
    projects, _ = project_manager.get_all_projects()
    tasks, _ = task_manager.get_all_tasks()
    events, _ = event_manager.get_all_events()
    
    def calculate_percentage_increase(queryset, days, end_date):
        start_date = end_date - datetime.timedelta(days=days)
        previous_end_date = start_date
        previous_start_date = previous_end_date - datetime.timedelta(days=days)
        
        recent_objects = queryset.filter(created_at__range=(start_date, end_date))
        previous_objects = queryset.filter(created_at__range=(previous_start_date, previous_end_date))
        
        count_recent_objects = recent_objects.count()
        count_previous_objects = previous_objects.count()
        
        if count_previous_objects > 0:
            percentage_increase = round(((count_recent_objects - count_previous_objects) / count_previous_objects) * 100, 2)
        else:
            percentage_increase = 100 if count_recent_objects > 0 else 0

        return {
            'percentage_increase': percentage_increase,
            'total_recent': count_recent_objects,
            'total_previous': count_previous_objects
        }

    projects_increase_data = calculate_percentage_increase(Project.objects.all(), days, end_date)
    tasks_increase_data = calculate_percentage_increase(Task.objects.all(), days, end_date)
    events_increase_data = calculate_percentage_increase(Event.objects.all(), days, end_date)

    return {
        'projects': {
            'count': projects_increase_data['total_recent']+projects_increase_data['total_previous'],
            'increase': projects_increase_data['percentage_increase'],
            'recent_count': projects_increase_data['total_recent'],
            'previous_count': projects_increase_data['total_previous'],
            'start_date': start_date,
            'end_date': end_date,
        },
        'tasks': {
            'count': tasks_increase_data['total_recent']+tasks_increase_data['total_previous'],
            'increase': tasks_increase_data['percentage_increase'],
            'recent_count': tasks_increase_data['total_recent'],
            'previous_count': tasks_increase_data['total_previous'],
            'start_date': start_date,
            'end_date': end_date,
        },
        'events': {
            'count': events_increase_data['total_recent']+events_increase_data['total_previous'],
            'increase': events_increase_data['percentage_increase'],
            'recent_count': events_increase_data['total_recent'],
            'previous_count': events_increase_data['total_previous'],
            'start_date': start_date,
            'end_date': end_date,
        },
    }
