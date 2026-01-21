import logging

logger = logging.getLogger(__name__)

def event_assign(request, event_id=None):
    """
    Vista para asignar proyectos y tareas a un evento específico.
    Si no se proporciona un event_id, se muestra una lista de eventos disponibles.
    """
    title = "Event Assign"
    
    try:
        # Obtener los estados utilizando la función statuses_get
        event_statuses, project_statuses, task_statuses = statuses_get()

        if event_id:
            # Obtener el evento específico utilizando EventManager
            event_manager = EventManager(request.user)
            event_data = event_manager.get_event_by_id(event_id)
            
            if not event_data:
                messages.error(request, 'El evento no existe.')
                return redirect('index')

            # Obtener los proyectos y tareas disponibles utilizando ProjectManager y TaskManager
            project_manager = ProjectManager(request.user)
            task_manager = TaskManager(request.user)
            
            available_projects = project_manager.user_projects.exclude(id__in=[project.id for project in event_data['projects']])
            available_tasks = task_manager.user_tasks.exclude(id__in=[task.id for task in event_data['tasks']])

            if request.method == 'POST':
                assign_task_id = request.POST.get('assign_task_id')
                assign_project_id = request.POST.get('assign_project_id')

                if assign_task_id:
                    # Asignar tarea al evento
                    task_to_assign = get_object_or_404(Task, id=assign_task_id)
                    task_to_assign.event_id = event_id
                    task_to_assign.save()
                    messages.success(request, f'La tarea {task_to_assign.id} ha sido asignada al evento {event_id} exitosamente.')
                    return redirect('event_assign', event_id=event_id)

                elif assign_project_id:
                    # Asignar proyecto al evento
                    project_to_assign = get_object_or_404(Project, id=assign_project_id)
                    project_to_assign.event_id = event_id
                    project_to_assign.save()
                    messages.success(request, f'El proyecto {project_to_assign.id} ha sido asignado al evento {event_id} exitosamente.')
                    return redirect('event_assign', event_id=event_id)

                else:
                    messages.error(request, 'No se proporcionó un id de tarea o proyecto válido.')
                    return redirect('event_assign', event_id=event_id)

            else:
                # Renderizar la plantilla con los datos necesarios
                return render(request, "events/event_assign.html", {
                    'title': f'{title} (GET With Id)',
                    'event': event_data,
                    'available_projects': available_projects,
                    'available_tasks': available_tasks,
                    'event_statuses': event_statuses,
                    'project_statuses': project_statuses,
                    'task_statuses': task_statuses,
                })

        else:
            # Si no se proporciona event_id, mostrar todos los eventos disponibles
            event_manager = EventManager(request.user)
            events, _ = event_manager.get_all_events()
            return render(request, "events/event_assign.html", {
                'title': f'{title} (No ID)',
                'events': events,
            })
    except Exception as e:
        # Manejo de errores
        messages.error(request, f'Ha ocurrido un error: {e}')
        return redirect('index')

@login_required
def events(request):
    logger.info("Starting events view processing")
    
    try:
        today = timezone.now().date()
        title = "Events Origin"
        logger.debug(f"Current date: {today}, Page title: {title}")

        # Initialize session variables for first-time visitors
        if request.session.get('first_session', True):
            logger.info("Initializing session variables for new user session")
            try:
                status_in_progress = Status.objects.get(status_name='In Progress').id
                logger.debug(f"Found 'In Progress' status with ID: {status_in_progress}")
            except ObjectDoesNotExist:
                status_in_progress = None
                logger.warning("'In Progress' status not found in database")

            completed = request.session.setdefault('filtered_completed', True)
            status = request.session.setdefault('filtered_status', status_in_progress)
            date_str = request.session.setdefault('filtered_date', today.isoformat())
            request.session['first_session'] = False
            logger.debug(f"Initial filter values - Completed: {completed}, Status: {status}, Date: {date_str}")

        # Get events data
        logger.info("Retrieving events data")
        event_manager = EventManager(request.user)
        events, active_events = event_manager.get_all_events()
        event_statuses = Status.objects.all().order_by('status_name')
        logger.debug(f"Retrieved {len(events)} events and {event_statuses.count()} status options")

        if request.method == 'POST':
            logger.info("Processing POST request with new filters")
            completed = request.POST.get('completed', 'False').lower() == 'true'
            status = int(request.POST.get('status')) if request.POST.get('status') else None
            date_str = request.POST.get('date')
            logger.debug(f"Received filter values - Completed: {completed}, Status: {status}, Date: {date_str}")

            try:
                # Apply completed filter
                if completed:
                    logger.debug("Applying completed events filter")
                    status_completed = Status.objects.get(status_name='Completed')
                    events = [event for event in events if event['event'].event_status_id != status_completed.id]
                    request.session['filtered_completed'] = True
                    logger.info(f"Filtered out completed events, remaining: {len(events)}")
                else:
                    request.session['filtered_completed'] = False
                    logger.debug("Including completed events in results")

                # Apply status filter
                if status:
                    events = [event for event in events if event['event'].event_status_id == status]
                    request.session['filtered_status'] = status
                    logger.info(f"Filtered by status ID {status}, remaining: {len(events)}")
                else:
                    request.session['filtered_status'] = status
                    logger.debug("No status filter applied")

                # Apply date filter
                if date_str:
                    filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    events = [event for event in events if event['event'].updated_at.date() == filter_date]
                    request.session['filtered_date'] = date_str
                    logger.info(f"Filtered by date {date_str}, remaining: {len(events)}")
                else:
                    request.session['filtered_date'] = date_str
                    logger.debug("No date filter applied")

            except Status.DoesNotExist as e:
                logger.error(f"Status filtering error: {str(e)}", exc_info=True)
                messages.error(request, f'An error occurred while filtering events: {e}')
            except Exception as e:
                logger.error(f"Unexpected filtering error: {str(e)}", exc_info=True)
                messages.error(request, f'An error occurred while filtering events: {e}')

        else:  # GET request
            logger.info("Processing GET request with stored filters")
            status = request.session.get('filtered_status')
            date_str = request.session.get('filtered_date')
            completed = request.session.get('filtered_completed')
            logger.debug(f"Using stored filter values - Completed: {completed}, Status: {status}, Date: {date_str}")

            try:
                # Apply stored completed filter
                if completed:
                    logger.debug("Applying stored completed filter")
                    status_completed = Status.objects.get(status_name='Completed')
                    events = [event for event in events if event['event'].event_status_id != status_completed.id]
                    logger.info(f"Filtered out completed events, remaining: {len(events)}")

                # Apply stored status filter
                if status:
                    events = [event for event in events if event['event'].event_status_id == status]
                    logger.info(f"Filtered by stored status ID {status}, remaining: {len(events)}")

                # Apply stored date filter
                if date_str:
                    filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    events = [event for event in events if event['event'].updated_at.date() == filter_date]
                    logger.info(f"Filtered by stored date {date_str}, remaining: {len(events)}")

            except Status.DoesNotExist as e:
                logger.error(f"Status filtering error: {str(e)}", exc_info=True)
                messages.error(request, f'An error occurred while filtering events: {e}')
            except Exception as e:
                logger.error(f"Unexpected filtering error: {str(e)}", exc_info=True)
                messages.error(request, f'An error occurred while filtering events: {e}')
                return redirect('index')

        # Prepare response data
        count_events = len(events)
        events_updated_today = len([event for event in events if event['event'].updated_at.date() == today])
        events_states = EventState.objects.all().order_by('-start_time')[:10]
        
        logger.info(f"Preparing response with {count_events} events ({events_updated_today} updated today)")
        
        context = {
            'title': title,
            'events_updated_today': events_updated_today,
            'count_events': count_events,
            'events': events,
            'event_statuses': event_statuses,
            'events_states': events_states,
        }
        
        return render(request, 'events/events.html', context)

    except Exception as e:
        logger.critical(f"Unexpected error in events view: {str(e)}", exc_info=True)
        messages.error(request, f'An error occurred while processing events: {e}')
        return redirect('index')

@login_required
def event_create(request):
    title="Create New Event"
    try:
        if request.method == 'GET':
            try:
                default_status = Status.objects.get(status_name='Created').id
            except Status.DoesNotExist:
                messages.error(request, 'El estado "Creado" no existe. ')
                return redirect('index')

            default = {
                'assigned_to': request.user.id,
                'host': request.user.id,
                'event_status': default_status
            }
            form = CreateNewEvent(initial=default)
            # El resto del código sigue aquí...

        else:
            form = CreateNewEvent(request.POST)
            if form.is_valid():
                try:
                    # Obtén el estado inicial basado en la solicitud
                    if 'inbound' in request.POST or (hasattr(request.user, 'profile') and hasattr(request.user.cv, 'role') and request.user.cv.role == 'SU'):
                        initial_status_id = request.POST.get('event_status')
                    else:
                        initial_status_id = Status.objects.get(status_name='Created').id

                    try:
                        initial_status = Status.objects.get(id=initial_status_id)
                    except Status.DoesNotExist:
                        messages.error(request, f'El estado con el ID "{initial_status_id}" no existe.')
                        return redirect('index')
                    
                    # El resto de tu código sigue aquí...
                    
                    # Crear el evento con los datos validados del formulario
                    new_event = form.save(commit=False)
                    new_event.event_status = initial_status
                    new_event.host = request.user  # El host es siempre el creador del evento
                    if not hasattr(request.user, 'profile') or not hasattr(request.user.cv, 'role') or request.user.cv.role != 'SU':
                        new_event.assigned_to = request.user  # Establecer automáticamente assigned_to como el usuario actual si el usuario no es un 'SU'
                    new_event.save()

                    # Si el usuario es un supervisor, puede asignar el evento a cualquier usuario
                    attendees = form.cleaned_data.get('attendees')
                    for attendee in attendees:
                        # Asignar el usuario asignado como atendedor
                        EventAttendee.objects.create(
                            user=attendee,
                            event=new_event
                        )

                    messages.success(request, 'Evento creado con éxito.')
                    return redirect('events')
                except IntegrityError as e:
                    messages.error(request, f'Hubo un error al crear el evento: {e}')
            else:
                # Si el formulario no es válido, agregar los errores del formulario a los mensajes
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Error en el campo {field}: {error}')

        return render(request, 'events/event_create.html', {
            'form': form,
            'title':title,
            })
    
    except ObjectDoesNotExist:
        messages.error(request, 'El objeto solicitado no existe.')
        return redirect('index')
    except Exception as e:
        messages.error(request, f'Ha ocurrido un error inesperado: {e}')
        return redirect('index')

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'events/event_detail.html', {
        'event' :event,
        'events':events
    })

def event_edit(request, event_id=None):
    title="Event Edit"
    try:
        if event_id is not None:
            # Estamos editando un evento existente
            try:
                event = get_object_or_404(Event, pk=event_id)
            except Http404:
                messages.error(request, 'El evento con el ID "{}" no existe.'.format(event_id))
                return redirect('index')

            if request.method == 'POST':
                form = CreateNewEvent(request.POST, instance=event)
                if form.is_valid():
                    # Asigna el usuario autenticado como el editor
                    event.editor = request.user
                    print('guardando via post si es valido')

                    # Guardar el evento con el editor actual (usuario que realiza la solicitud)
                    for field in form.changed_data:
                        old_value = getattr(event, field)
                        new_value = form.cleaned_data.get(field)
                        event.record_edit(
                            editor=request.user,
                            field_name=field,
                            old_value=str(old_value),
                            new_value=str(new_value),
                            )
                    form.save()

                    messages.success(request, 'Evento guardado con éxito.')
                    return redirect('event_panel')  # Redirige a la página de lista de edición
                else:
                    messages.error(request, 'Hubo un error al guardar el evento. Por favor, revisa el formulario.')
            
            else:
                form = CreateNewEvent(instance=event)
                print(event.title)
            return render(request, 'events/event_edit.html', {
                'event':event,
                'form': form,
                'title':title,
                })
        else:
            # Estamos manejando una solicitud GET sin argumentos
            # Verificar el rol del usuario
            if hasattr(request.user, 'profile') and hasattr(request.user.cv, 'role') and request.user.cv.role == 'SU':
                # Si el usuario es un 'SU', puede ver todos los eventos
                events = Event.objects.all().order_by('-updated_at')
            else:
                # Si no, solo puede ver los eventos que le están asignados o a los que asiste
                events = Event.objects.filter(Q(assigned_to=request.user) | Q(attendees=request.user)).distinct().order_by('-updated_at')
            return render(request, 'events/event_list.html', {
                'events': events,
                'title': title,
                })
            
    except Exception as e:
        messages.error(request, 'Ha ocurrido un error: {}'.format(e))
        return redirect('index')

def event_status_change(request, event_id):
    try:
        if request.method != 'POST':
            return HttpResponse("Método no permitido", status=405)
        event = get_object_or_404(Event, pk=event_id)
        new_status_id = request.POST.get('new_status_id')
        new_status = get_object_or_404(Status, pk=new_status_id)
        if request.user is None:
            messages.error(request, "User is none: Usuario no autenticado")
            return redirect('index')
        if event.host is not None and (event.host == request.user or request.user in event.attendees.all()):
            old_status = event.event_status
            print("old_status:", old_status)
            event.record_edit(
                editor=request.user,
                field_name='event_status',
                old_value=str(old_status),
                new_value=str(new_status)
            )
        else:
            return HttpResponse("No tienes permiso para editar este evento", status=403)
    except Exception as e:
        print(f"Error: {str(e)}")
        return HttpResponse(f"Error: {str(e)}", status=500)

    return redirect('events')

def event_delete(request, event_id):
    # Asegúrate de que solo se pueda acceder a esta vista mediante POST
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=event_id)

        # Verificar si el usuario es un 'SU'
        if not (hasattr(request.user, 'profile') and hasattr(request.user.cv, 'role') and request.user.cv.role == 'SU'):
            messages.error(request, 'No tienes permiso para eliminar este evento.')
            return redirect(reverse('event_panel'))

        event.delete()
        messages.success(request, 'El evento ha sido eliminado exitosamente.')
    else:
        messages.error(request, 'Método no permitido.')
    return redirect(reverse('event_panel'))

def event_panel(request, event_id=None):
    title = "Event Panel"
    event_statuses, project_statuses, task_statuses = statuses_get()
    events_states = EventState.objects.all().order_by('-start_time')[:10]
    status_var = 'In Progress'

    try:
        status = Status.objects.get(status_name=status_var)
    except Status.DoesNotExist:
        status = None
    except Status.MultipleObjectsReturned:
        status = None
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        status = None

    event_manager = EventManager(request.user)
    project_manager = ProjectManager(request.user)
    task_manager = TaskManager(request.user)

    if event_id:
        event_data = event_manager.get_event_by_id(event_id)
        logger.info(f"[event Panel] Event data: {event_data}")
        if event_data:
            try:
                if not event_data['projects']:
                    messages.error(request, 'El evento no existe. Verifica el ID del evento.')
                    projects_data= None
                else :
                    projects_data = [project_manager.get_project_data(project.id) for project in event_data['projects']]
                    logger.info(f"Projects data: {projects_data}")
                
                if not event_data['tasks']:
                    messages.error(request, 'El evento no tiene tareas asignadas.') 
                    tasks_data = None
                else:
                    tasks_data = [task_manager.get_task_data(task) for task in event_data['tasks']]
            
            except Exception as e:
                messages.error(request, f'Error al obtener información de proyectos o tareas: {e}')
                return redirect('events')

            context = {
                'page': 'event_detail',
                'title': title,
                'event_data': event_data,
                'projects_data': projects_data,
                'tasks_data': tasks_data,
                'event_statuses': event_statuses,
                'project_statuses': project_statuses,
                'task_statuses': task_statuses,
            }
            try:
                return render(request, "events/event_panel.html", context)
            except Exception as e:
                messages.error(request, f'Ha ocurrido un error: {e}')
                return redirect('events')
        else:
            return render(request, '404.html', status=404)
    else:
        events, active_events = event_manager.get_all_events()

        # Calculate statistics for the template
        total_events = len(events)
        in_progress_count = sum(1 for event in events if event['event'].event_status.status_name == 'In Progress')
        completed_count = sum(1 for event in events if event['event'].event_status.status_name == 'Completed')
        created_count = sum(1 for event in events if event['event'].event_status.status_name == 'Created')

        event_details = {}
        for event_data in events:
            event_details[event_data['event'].id] = {
                'projects': event_data['projects'],
                'tasks': event_data['tasks']
            }
        return render(request, 'events/event_panel.html', {
            'page': 'event_panel',
            'title': title,
            'events': events,
            'event_details': event_details,
            'event_statuses': event_statuses,
            'events_states': events_states,
            'active_events': active_events,
            'total_events': total_events,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'created_count': created_count,
        })

def event_export(request):
    """Export events data"""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="events_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Description', 'Status', 'Venue', 'Host', 'Created At'])

    events = Event.objects.all().select_related('event_status', 'host')
    for event in events:
        writer.writerow([
            event.id,
            event.title,
            event.description or '',
            event.event_status.status_name if event.event_status else '',
            event.venue or '',
            event.host.username if event.host else '',
            event.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response

def event_bulk_action(request):
    """Handle bulk actions for events"""
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_events = request.POST.getlist('selected_items')

        if not selected_events:
            messages.error(request, 'No events selected.')
            return redirect('event_panel')

        events = Event.objects.filter(id__in=selected_events)

        if action == 'delete':
            count = events.count()
            events.delete()
            messages.success(request, f'Successfully deleted {count} event(s).')
        elif action == 'activate':
            count = events.update(event_status=Status.objects.get(status_name='In Progress'))
            messages.success(request, f'Successfully activated {count} event(s).')
        elif action == 'complete':
            count = events.update(event_status=Status.objects.get(status_name='Completed'))
            messages.success(request, f'Successfully completed {count} event(s).')

    return redirect('event_panel')

def event_history(request, event_id=None):
    title = 'Event History'
    if not event_id:
        if request.method == 'POST':
            pass
        else:
            events_history = EventState.objects.all().order_by('-start_time')
            return render(request, 'events/event_history.html', {
                'title':title,
                'events_history':events_history,
            })
    else:
        productive_status_name='In Progress'
        productive_status=get_object_or_404(Status, status_name=productive_status_name)
        events_history = EventState.objects.filter(Q(event_id=event_id, event_status=productive_status)).order_by('-start_time')

        return render(request, 'events/event_history.html', {
            'title':title,
            'events_history':events_history,
        })

@login_required
def assign_attendee_to_event(request, event_id, user_id):
    try:
        # Obtén el evento y el usuario basado en los IDs proporcionados
        event = get_object_or_404(Event, pk=event_id)
        user = get_object_or_404(User, pk=user_id)

        # Crea una nueva instancia de EventAttendee
        event_attendee, created = EventAttendee.objects.get_or_create(
            user=user,
            event=event
        )

        if created:
            # El asistente fue asignado al evento exitosamente
            messages.success(request, 'Asistente asignado al evento con éxito.')
        else:
            # El asistente ya estaba asignado al evento
            messages.info(request, 'El asistente ya estaba asignado a este evento.')

        # Redirige a la página que desees, por ejemplo, la página de detalles del evento
        return redirect('event_detail', event_id=event_id)
    except Exception as e:
        # Si ocurre un error, muestra un mensaje de alerta y redirige al usuario a la página de inicio
        messages.error(request, 'Ha ocurrido un error al asignar el asistente al evento: {}'.format(e))
        return redirect('index')
