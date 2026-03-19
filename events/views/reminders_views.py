# events/reminders_views.py
# ============================================================================
# VISTAS DE RECORDATORIOS
# ============================================================================

import datetime
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from ..models import Reminder
from ..forms import ReminderForm

logger = logging.getLogger(__name__)


# ============================================================================
# VISTAS PRINCIPALES DE RECORDATORIOS
# ============================================================================

@login_required
def reminders_dashboard(request):
    """
    Vista principal del dashboard de recordatorios
    """
    # Obtener recordatorios del usuario
    user_reminders = Reminder.objects.filter(created_by=request.user)

    # Separar por estado
    pending_reminders = user_reminders.filter(is_sent=False, remind_at__gte=timezone.now())
    sent_reminders = user_reminders.filter(is_sent=True)
    overdue_reminders = user_reminders.filter(is_sent=False, remind_at__lt=timezone.now())

    # Obtener recordatorios para hoy
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
    today_end = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))

    today_reminders = user_reminders.filter(
        remind_at__range=(today_start, today_end),
        is_sent=False
    )

    # Estadísticas
    total_reminders = user_reminders.count()
    pending_count = pending_reminders.count()
    sent_count = sent_reminders.count()
    overdue_count = overdue_reminders.count()

    context = {
        'title': 'Dashboard de Recordatorios',
        'user_reminders': user_reminders,
        'pending_reminders': pending_reminders,
        'sent_reminders': sent_reminders,
        'overdue_reminders': overdue_reminders,
        'today_reminders': today_reminders,
        'total_reminders': total_reminders,
        'pending_count': pending_count,
        'sent_count': sent_count,
        'overdue_count': overdue_count,
    }

    return render(request, 'events/reminders_dashboard.html', context)


# ============================================================================
# VISTAS CRUD DE RECORDATORIOS
# ============================================================================


@login_required
def create_reminder(request):
    """
    Vista para crear un nuevo recordatorio
    """
    from ..forms import ReminderForm

    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.created_by = request.user
            reminder.save()

            messages.success(request, f'Recordatorio "{reminder.title}" creado exitosamente')
            return redirect('reminders_dashboard')


    else:
        form = ReminderForm()

    context = {
        'title': 'Crear Recordatorio',
        'form': form,
    }

    return render(request, 'events/create_reminder.html', context)


@login_required
def edit_reminder(request, reminder_id):
    """
    Vista para editar un recordatorio existente
    """
    try:
        reminder = Reminder.objects.get(id=reminder_id, created_by=request.user)
    except Reminder.DoesNotExist:
        messages.error(request, 'Recordatorio no encontrado.')
        return redirect('reminders_dashboard')

    if request.method == 'POST':
        form = ReminderForm(request.POST, instance=reminder)
        if form.is_valid():
            form.save()
            messages.success(request, f'Recordatorio "{reminder.title}" actualizado exitosamente')
            return redirect('reminders_dashboard')
    else:
        form = ReminderForm(instance=reminder)

    context = {
        'title': 'Editar Recordatorio',
        'form': form,
        'reminder': reminder,
    }

    return render(request, 'events/edit_reminder.html', context)


@login_required
def delete_reminder(request, reminder_id):
    """
    Vista para eliminar un recordatorio
    """
    try:
        reminder = Reminder.objects.get(id=reminder_id, created_by=request.user)
    except Reminder.DoesNotExist:
        messages.error(request, 'Recordatorio no encontrado.')
        return redirect('reminders_dashboard')

    if request.method == 'POST':
        reminder_title = reminder.title
        reminder.delete()
        messages.success(request, f'Recordatorio "{reminder_title}" eliminado exitosamente')
        return redirect('reminders_dashboard')

    context = {
        'title': 'Eliminar Recordatorio',
        'reminder': reminder,
    }

    return render(request, 'events/delete_reminder.html', context)


# ============================================================================
# VISTAS DE ACCIONES Y API
# ============================================================================

@login_required
def mark_reminder_sent(request, reminder_id):
    """
    API endpoint para marcar un recordatorio como enviado
    """
    if request.method == 'POST':
        try:
            reminder = Reminder.objects.get(id=reminder_id, created_by=request.user)
            reminder.is_sent = True
            reminder.save()

            return JsonResponse({
                'success': True,
                'message': 'Recordatorio marcado como enviado'
            })
        except Reminder.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Recordatorio no encontrado'
            })

    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })


@login_required
def bulk_reminder_action(request):
    """
    Vista para acciones masivas en recordatorios
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_reminders = request.POST.getlist('selected_reminders')

        if not selected_reminders:
            messages.error(request, 'No se seleccionaron recordatorios.')
            return redirect('reminders_dashboard')

        reminders = Reminder.objects.filter(id__in=selected_reminders, created_by=request.user)

        if action == 'mark_sent':
            count = reminders.update(is_sent=True)
            messages.success(request, f'Se marcaron {count} recordatorio(s) como enviados.')

        elif action == 'delete':
            count = reminders.count()
            reminders.delete()
            messages.success(request, f'Se eliminaron {count} recordatorio(s).')

        elif action == 'duplicate':
            for reminder in reminders:
                Reminder.objects.create(
                    title=f"{reminder.title} (Copia)",
                    description=reminder.description,
                    remind_at=reminder.remind_at,
                    task=reminder.task,
                    project=reminder.project,
                    event=reminder.event,
                    created_by=request.user,
                    reminder_type=reminder.reminder_type
                )
            messages.success(request, f'Se duplicaron {reminders.count()} recordatorio(s).')
        else:
            messages.error(request, 'Acción no válida.')

    return redirect('reminders_dashboard')