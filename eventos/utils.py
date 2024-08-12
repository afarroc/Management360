# utils.py

from decimal import Decimal
from django.contrib import messages
from .models import CreditAccount

def add_credits_to_user(user, amount):
    if not hasattr(user, 'creditaccount'):
        CreditAccount.objects.create(user=user)
    
    try:
        amount = Decimal(amount)
        user.creditaccount.add_credits(amount)
        return True, f"Monto agregado {amount}"
    except (ValueError, Decimal.InvalidOperation):
        return False, "Monto no válido"







# utils.py
from .event_manager import EventManager
from .project_manager import ProjectManager
from .task_manager import TaskManager

from collections import defaultdict
import datetime
from django.utils import timezone
from django.db.models import Count, F, ExpressionWrapper, DurationField
from .models import Project, Task, Event, TaskState, TaskStatus

def get_task_states_with_duration():
    in_progress_status = TaskStatus.objects.get(status_name='En Curso')
    task_states = TaskState.objects.filter(status=in_progress_status).annotate(
        duration_seconds=ExpressionWrapper(
            F('end_time') - F('start_time'),
            output_field=DurationField()
        )
    ).order_by('-start_time')
    
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
        for task_state in task_states
    ]

# utils.py

def get_bar_chart_data(task_states):
    # Contar la frecuencia de cada tarea en la lista
    task_count_dict = defaultdict(int)
    for task_state in task_states:
        task_title = task_state['task_state'].task.title
        task_count_dict[task_title] += 1
    
    # Ordenar las tareas por frecuencia y limitar a las 15 más frecuentes
    sorted_tasks = sorted(task_count_dict.items(), key=lambda x: x[1], reverse=True)[:15]
    categories, counts = zip(*sorted_tasks) if sorted_tasks else ([], [])
    
    return {
        'categories': list(categories),
        'counts': list(counts),
    }

def get_line_chart_data(task_states_last_month):
    # Contar la frecuencia de tareas por fecha
    date_count_dict = defaultdict(int)
    for task_state in task_states_last_month:
        start_date = task_state['task_state'].start_time.date()
        date_count_dict[start_date] += 1
    
    # Ordenar por fecha
    sorted_dates = sorted(date_count_dict.items())
    dates, counts = zip(*sorted_dates) if sorted_dates else ([], [])
    
    return {
        'dates': [date.strftime('%Y-%m-%d') for date in dates],
        'counts_over_time': list(counts),
    }


def filter_data_last_month(data, key_name, start_date):
    # Asegúrate de que data contenga objetos con el atributo 'created_at'
    filtered_data = [
        item for item in data
        if isinstance(item, dict) and item.get(key_name) and getattr(item[key_name], 'created_at', None) and item[key_name].created_at.date() >= start_date
    ]
    return count_created_per_day(filtered_data, key_name)



def count_created_per_day(data, key_name):
    counts = defaultdict(int)
    for item in data:
        created_date = getattr(item, key_name).created_at.date()
        if created_date:
            counts[created_date] += 1
    return counts

def fill_data_for_dates(date_range, counts):
    return [counts.get(date, 0) for date in date_range]

def get_combined_chart_data(projects, tasks, events, start_date, end_date):
    projects_created_per_day = filter_data_last_month(projects, 'project', start_date)
    tasks_created_per_day = filter_data_last_month(tasks, 'task', start_date)
    events_created_per_day = filter_data_last_month(events, 'event', start_date)

    all_dates = set(projects_created_per_day.keys()) | set(tasks_created_per_day.keys()) | set(events_created_per_day.keys())
    date_range = [start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1)]

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

def get_card_data(user, days):
    today = timezone.now().date()
    start_date = today - datetime.timedelta(days=days)

    project_manager = ProjectManager(user)
    task_manager = TaskManager(user)
    event_manager = EventManager(user)
    
    projects, _ = project_manager.get_all_projects()
    tasks, _ = task_manager.get_all_tasks()
    events, _ = event_manager.get_all_events()
    
    def calculate_percentage_increase(queryset, days):
        end_date = timezone.now()
        start_date = end_date - datetime.timedelta(days=days)
        previous_end_date = start_date
        previous_start_date = previous_end_date - datetime.timedelta(days=days)
        
        recent_objects = queryset.filter(created_at__range=(start_date, end_date))
        previous_objects = queryset.filter(created_at__range=(previous_start_date, previous_end_date))
        
        count_recent_objects = recent_objects.count()
        count_previous_objects = previous_objects.count()
        
        if count_previous_objects > 0:
            percentage_increase = round(((count_recent_objects - count_previous_objects) / count_previous_objects) * 100,2)
        else:
            percentage_increase = 100 if count_recent_objects > 0 else 0

        return {
            'percentage_increase': percentage_increase,
            'total_recent': count_recent_objects,
            'total_previous': count_previous_objects
        }

    projects_increase_data = calculate_percentage_increase(Project.objects.all(), days)
    tasks_increase_data = calculate_percentage_increase(Task.objects.all(), days)
    events_increase_data = calculate_percentage_increase(Event.objects.all(), days)

    return {
        'projects': {
            'count': len(projects),
            'increase': projects_increase_data['percentage_increase'],
            'recent_count': projects_increase_data['total_recent'],
            'previous_count': projects_increase_data['total_previous'],
            'start_date': start_date,
            'end_date': today,
        },
        'tasks': {
            'count': len(tasks),
            'increase': tasks_increase_data['percentage_increase'],
            'recent_count': tasks_increase_data['total_recent'],
            'previous_count': tasks_increase_data['total_previous'],
            'start_date': start_date,
            'end_date': today,
        },
        'events': {
            'count': len(events),
            'increase': events_increase_data['percentage_increase'],
            'recent_count': events_increase_data['total_recent'],
            'previous_count': events_increase_data['total_previous'],
            'start_date': start_date,
            'end_date': today,
        },
    }
