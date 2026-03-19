# events/views.py
# deleted, moved or updated views
# Projects - Optimized Version

def project_panel(request, project_id=None):
    # Title of the page
    title = "Project Panel"

    # Retrieve projects and statuses
    project_manager = ProjectManager(request.user)
    statuses = statuses_get()

    try:

        if project_id:
            # If a specific project_id is provided, handle it here
            project_data = project_manager.get_project_data(project_id)

            if project_data:
                # Generate alerts for specific project
                alerts = generate_project_alerts(project_data, request.user)

                context = {
                    'title': title,
                    'project_data': project_data,
                    'event_statuses': statuses[0],
                    'project_statuses': statuses[1],
                    'task_statuses': statuses[2],
                    'alerts': alerts,
                }
                return render(request, 'projects/project_panel.html', context)
            else:
                messages.error(request, f'Project with id {project_id} not found')
                return redirect('index')
        else:
            projects, active_projects = project_manager.get_all_projects()

            # Calculate statistics
            total_projects = len(projects)
            in_progress_count = sum(1 for p in projects if p['project'].project_status.status_name == 'In Progress')
            completed_count = sum(1 for p in projects if p['project'].project_status.status_name == 'Completed')
            total_tasks = sum(p['count_tasks'] for p in projects)

            # Generate comprehensive alerts for all projects
            alerts = generate_projects_overview_alerts(projects, request.user)

            # If no specific project_id is provided
            if request.method == 'POST':
                # Handle POST request logic here
                pass
            else:
                # Create context for the template for GET requests
                title = "Projects Panel"
                context = {
                    'title': title,
                    'event_statuses': statuses[0],
                    'project_statuses': statuses[1],
                    'task_statuses': statuses[2],
                    'projects': projects,
                    'active_projects': active_projects,
                    'total_projects': total_projects,
                    'in_progress_count': in_progress_count,
                    'completed_count': completed_count,
                    'total_tasks': total_tasks,
                    'alerts': alerts,
                }
                return render(request, 'projects/project_panel.html', context)

    except Exception as e:
        messages.error(request, f'An error occurred: ({e})')
        return redirect('index')

def projects(request, project_id=None):
    """
    Optimized projects view with database query improvements and caching
    """
    from django.core.cache import cache
    from django.db.models import Prefetch

    # Cache key for this view
    cache_key = f'projects_view_{request.user.id}_{project_id or "all"}'
    cached_data = cache.get(cache_key)

    if cached_data and not request.method == 'POST':
        return cached_data

    title = "Projects"
    urls = [
        {'url': 'project_create', 'name': 'Project Create'},
        {'url': 'project_edit', 'name': 'Project Edit'},
    ]
    other_urls = [
        {'url': 'events', 'id': None, 'name': 'Events Panel'},
        {'url': 'projects', 'id': None, 'name': 'Projects Panel'},
        {'url': 'tasks', 'id': None, 'name': 'Tasks Panel'},
    ]
    instructions = [
        {'instruction': 'Fill carefully the metadata.', 'name': 'Form'},
    ]

    # Optimized: Single query with select_related for related objects
    project_statuses = ProjectStatus.objects.all().order_by('status_name')

    # Optimized: Use select_related and prefetch_related to avoid N+1 queries
    projects_queryset = Project.objects.select_related(
        'host', 'assigned_to', 'project_status', 'event'
    ).prefetch_related(
        'attendees',
        Prefetch('task_set', queryset=Task.objects.select_related('task_status'))
    ).order_by('-updated_at')

    # Get statistics in a single optimized query
    projects_stats = projects_queryset.aggregate(
        total_projects=Count('id'),
        total_ticket_price=Sum('ticket_price'),
        increase=Count('id', filter=Q(created_at__gte=timezone.now() - timezone.timedelta(days=1)))
    )

    # Optimized chart data generation - single query per model
    chart_data, chart_data_json = _get_optimized_chart_data()

    if project_id:
        # Single optimized query for specific project
        try:
            project = projects_queryset.get(id=project_id)
            context = {
                'project': project,
                'total_ticket_price': projects_stats['total_ticket_price'],
                'instructions': instructions,
                'urls': urls,
            }
            response = render(request, "projects/project_detail.html", context)
        except Project.DoesNotExist:
            raise Http404("Project not found")
    else:
        # Optimized: Use pagination for large datasets
        from django.core.paginator import Paginator
        paginator = Paginator(projects_queryset, 20)  # 20 projects per page
        page_number = request.GET.get('page')
        projects_page = paginator.get_page(page_number)

        # Get status counts for distribution
        status_counts = {}
        for status in project_statuses:
            status_counts[status.id] = projects_queryset.filter(project_status=status).count()
            status.projects_count = status_counts[status.id]

        context = {
            'total_ticket_price': projects_stats['total_ticket_price'],
            'other_urls': other_urls,
            'urls': urls,
            'instructions': instructions,
            'increase': projects_stats['increase'],
            'projects': projects_page,
            'total_projects': projects_stats['total_projects'],
            'in_progress_count': projects_queryset.filter(project_status__status_name='In Progress').count(),
            'completed_count': projects_queryset.filter(project_status__status_name='Completed').count(),
            'project_statuses': project_statuses,
            'title': title,
            'chart_data': chart_data,  # Pass chart_data as a single object
            'chart_data_json': chart_data_json,  # Pass JSON string for template
        }
        response = render(request, "projects/projects.html", context)

    # Cache the response for 5 minutes
    cache.set(cache_key, response, 300)
    return response

def project_detail(request, id):
    """
    Vista detallada de un proyecto individual con estadísticas completas
    """
    from django.db.models import Q, Count

    project = get_object_or_404(Project, id=id)

    # Verificar permisos
    if not (project.host == request.user or request.user in project.attendees.all()):
        messages.error(request, 'No tienes permisos para ver este proyecto.')
        return redirect('projects')

    # Obtener tareas del proyecto con información detallada
    tasks = Task.objects.filter(project_id=id).select_related(
        'task_status', 'assigned_to', 'host'
    ).order_by('created_at')

    # Calcular estadísticas del proyecto
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(task_status__status_name='Completed').count()
    in_progress_tasks = tasks.filter(task_status__status_name='In Progress').count()
    pending_tasks = tasks.filter(task_status__status_name='To Do').count()

    # Calcular progreso
    progress_percentage = 0
    if total_tasks > 0:
        progress_percentage = (completed_tasks / total_tasks) * 100

    # Tareas por estado para gráficos
    tasks_by_status = tasks.values('task_status__status_name').annotate(
        count=Count('id')
    ).order_by('task_status__status_name')

    # Tareas importantes
    important_tasks = tasks.filter(important=True).exclude(
        task_status__status_name='Completed'
    )

    # Actividad reciente (últimas 5 tareas actualizadas)
    recent_tasks = tasks.order_by('-updated_at')[:5]

    # Estadísticas de tiempo (si hay campo de tiempo estimado)
    estimated_time_total = 0
    actual_time_total = 0

    # Preparar datos para gráficos
    status_data = []
    status_colors = []
    for status_item in tasks_by_status:
        status_data.append(status_item['count'])
        # Obtener color del estado (si existe)
        try:
            status_obj = TaskStatus.objects.get(status_name=status_item['task_status__status_name'])
            status_colors.append(status_obj.color)
        except:
            status_colors.append('#6c757d')  # Color por defecto

    context = {
        'project': project,
        'tasks': tasks,

        # Estadísticas
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'pending_tasks': pending_tasks,
        'progress_percentage': progress_percentage,
        'important_tasks_count': important_tasks.count(),

        # Datos para gráficos
        'tasks_by_status': tasks_by_status,
        'status_data': status_data,
        'status_colors': status_colors,

        # Actividad
        'recent_tasks': recent_tasks,
        'important_tasks': important_tasks,

        # Tiempos
        'estimated_time_total': estimated_time_total,
        'actual_time_total': actual_time_total,
    }

    return render(request, 'projects/project_detail.html', context)

def change_project_status(request, project_id):
    print("Inicio de vista change_project_status")
    try:
        if request.method != 'POST':
            print("solicitud GET")
            return HttpResponse("Método no permitido", status=405)
        print("solicitud Post:", request.POST)
        project = get_object_or_404(Project, pk=project_id)
        print("ID a cambiar:", str(project.id))
        new_status_id = request.POST.get('new_status_id')
        new_status = get_object_or_404(ProjectStatus, pk=new_status_id)
        print("new_status_id", str(new_status))
        if request.user is None:
            print("User is none: Usuario no autenticado")
            messages.error(request, "User is none: Usuario no autenticado")
            return redirect('index')
        if project.host is not None and (project.host == request.user or request.user in project.attendees.all()):
            old_status = project.project_status
            print("old_status:", old_status)
            project.record_edit(
                editor=request.user,
                field_name='project_status',
                old_value=str(old_status),
                new_value=str(new_status)
            )
        else:
            return HttpResponse("No tienes permiso para editar este projecto", status=403)
    except Exception as e:
        print(f"Error: {str(e)}")
        return HttpResponse(f"Error: {str(e)}", status=500)
    messages.success(request, 'Project status edited successfully!')

    return redirect('project_panel')

def generate_project_alerts(project_data, user):
    """
    Generate contextual alerts for a specific project
    """
    alerts = []
    project = project_data['project']
    tasks = project_data.get('tasks', [])

    # Alert: Project overdue
    if project.updated_at and (timezone.now() - project.updated_at).days > 7:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-exclamation-triangle',
            'title': 'Proyecto inactivo',
            'message': f'El proyecto "{project.title}" no ha sido actualizado en {(timezone.now() - project.updated_at).days} días.',
            'action_url': f'/events/projects/edit/{project.id}',
            'action_text': 'Actualizar proyecto'
        })

    # Alert: Tasks completion status
    completed_tasks = sum(1 for task in tasks if task.task_status.status_name == 'Completed')
    total_tasks = len(tasks)
    if total_tasks > 0:
        completion_rate = (completed_tasks / total_tasks) * 100
        if completion_rate < 30:
            alerts.append({
                'type': 'danger',
                'icon': 'bi-graph-down',
                'title': 'Bajo progreso',
                'message': f'Solo {completion_rate:.1f}% de las tareas completadas ({completed_tasks}/{total_tasks}).',
                'action_url': f'/events/tasks/?project_id={project.id}',
                'action_text': 'Ver tareas'
            })
        elif completion_rate > 90 and project.project_status.status_name != 'Completed':
            alerts.append({
                'type': 'success',
                'icon': 'bi-check-circle',
                'title': '¡Casi listo!',
                'message': f'{completion_rate:.1f}% de las tareas completadas. ¿Listo para finalizar?',
                'action_url': f'/events/projects/edit/{project.id}',
                'action_text': 'Marcar como completado'
            })

    # Alert: Multiple assignees
    if project.attendees.count() > 3:
        alerts.append({
            'type': 'info',
            'icon': 'bi-people',
            'title': 'Proyecto colaborativo',
            'message': f'{project.attendees.count()} personas trabajando en este proyecto.',
            'action_url': f'/events/projects/detail/{project.id}',
            'action_text': 'Ver detalles'
        })

    # Alert: High priority tasks
    high_priority_tasks = [task for task in tasks if task.important and task.task_status.status_name != 'Completed']
    if high_priority_tasks:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-star-fill',
            'title': 'Tareas prioritarias',
            'message': f'{len(high_priority_tasks)} tarea(s) de alta prioridad pendiente(s).',
            'action_url': f'/events/tasks/?project_id={project.id}',
            'action_text': 'Revisar prioridades'
        })

    return alerts

def generate_projects_overview_alerts(projects, user):
    """
    Generate overview alerts for all projects
    """
    alerts = []

    if not projects:
        alerts.append({
            'type': 'info',
            'icon': 'bi-info-circle',
            'title': '¡Bienvenido!',
            'message': 'No tienes proyectos activos. ¿Quieres crear uno nuevo?',
            'action_url': '/events/projects/create/',
            'action_text': 'Crear proyecto'
        })
        return alerts

    # Alert: Overall completion rate
    total_tasks = sum(p['count_tasks'] for p in projects)
    completed_tasks = 0
    for p in projects:
        project_tasks = p.get('tasks', [])
        completed_tasks += sum(1 for task in project_tasks if task.task_status.status_name == 'Completed')

    if total_tasks > 0:
        overall_completion = (completed_tasks / total_tasks) * 100
        if overall_completion < 50:
            alerts.append({
                'type': 'warning',
                'icon': 'bi-bar-chart',
                'title': 'Progreso general bajo',
                'message': f'Solo {overall_completion:.1f}% de todas las tareas completadas.',
                'action_url': '/events/projects/',
                'action_text': 'Ver todos los proyectos'
            })

    # Alert: Projects without recent activity
    inactive_projects = []
    for p in projects:
        if p['project'].updated_at and (timezone.now() - p['project'].updated_at).days > 14:
            inactive_projects.append(p['project'])

    if inactive_projects:
        alerts.append({
            'type': 'danger',
            'icon': 'bi-clock',
            'title': 'Proyectos inactivos',
            'message': f'{len(inactive_projects)} proyecto(s) sin actividad reciente.',
            'action_url': '/events/projects/',
            'action_text': 'Revisar proyectos'
        })

    # Alert: High number of in-progress projects
    in_progress_projects = sum(1 for p in projects if p['project'].project_status.status_name == 'In Progress')
    if in_progress_projects > 5:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-exclamation-circle',
            'title': 'Demasiados proyectos activos',
            'message': f'Tienes {in_progress_projects} proyectos en progreso. Considera priorizar.',
            'action_url': '/events/projects/',
            'action_text': 'Gestionar prioridades'
        })

    # Alert: Projects nearing completion
    nearly_complete = []
    for p in projects:
        if p['count_tasks'] > 0:
            project_tasks = p.get('tasks', [])
            completed = sum(1 for task in project_tasks if task.task_status.status_name == 'Completed')
            if completed / p['count_tasks'] > 0.8 and p['project'].project_status.status_name != 'Completed':
                nearly_complete.append(p['project'])

    if nearly_complete:
        alerts.append({
            'type': 'success',
            'icon': 'bi-trophy',
            'title': '¡Proyectos casi listos!',
            'message': f'{len(nearly_complete)} proyecto(s) están cerca de completarse.',
            'action_url': '/events/projects/',
            'action_text': 'Finalizar proyectos'
        })

    return alerts

def generate_performance_alerts(projects, user):
    """
    Generate performance-based alerts for projects
    """
    alerts = []

    # Calculate performance metrics
    total_projects = len(projects)
    if total_projects == 0:
        return alerts

    # Completion rate analysis
    completion_rates = []
    for p in projects:
        if p['count_tasks'] > 0:
            project_tasks = p.get('tasks', [])
            completed = sum(1 for task in project_tasks if task.task_status.status_name == 'Completed')
            rate = (completed / p['count_tasks']) * 100
            completion_rates.append(rate)

    if completion_rates:
        avg_completion = sum(completion_rates) / len(completion_rates)

        if avg_completion < 25:
            alerts.append({
                'type': 'danger',
                'icon': 'bi-graph-down',
                'title': 'Rendimiento bajo',
                'message': f'El promedio de completación de proyectos es solo {avg_completion:.1f}%.',
                'action_url': '/events/projects/',
                'action_text': 'Mejorar rendimiento'
            })
        elif avg_completion > 75:
            alerts.append({
                'type': 'success',
                'icon': 'bi-graph-up',
                'title': '¡Excelente rendimiento!',
                'message': f'Promedio de completación del {avg_completion:.1f}%. ¡Sigue así!',
                'action_url': '/events/projects/',
                'action_text': 'Ver estadísticas'
            })

    # Task distribution analysis
    total_tasks = sum(p['count_tasks'] for p in projects)
    if total_tasks > 0:
        avg_tasks_per_project = total_tasks / total_projects

        if avg_tasks_per_project > 10:
            alerts.append({
                'type': 'warning',
                'icon': 'bi-list-check',
                'title': 'Proyectos complejos',
                'message': f'Promedio de {avg_tasks_per_project:.1f} tareas por proyecto. Considera dividir en proyectos más pequeños.',
                'action_url': '/events/projects/create/',
                'action_text': 'Crear subproyectos'
            })

    # Time-based analysis
    recent_projects = [p for p in projects if p['project'].created_at > timezone.now() - timezone.timedelta(days=7)]
    if recent_projects:
        alerts.append({
            'type': 'info',
            'icon': 'bi-calendar-plus',
            'title': 'Actividad reciente',
            'message': f'{len(recent_projects)} proyecto(s) creado(s) en la última semana.',
            'action_url': '/events/projects/',
            'action_text': 'Ver proyectos nuevos'
        })

    return alerts



