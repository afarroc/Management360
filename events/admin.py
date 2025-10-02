from django.contrib import admin
from django.utils import timezone
from .models import (
    Status, ProjectStatus, TaskStatus,
    Classification, Project, ProjectState, ProjectHistory, ProjectAttendee,
    Task, TaskState, TaskHistory, TaskProgram, TaskSchedule,
    Event, EventState, EventHistory, EventAttendee,
    Tag, TagCategory, Room, Message, CreditAccount,
    TaskDependency, ProjectTemplate, TemplateTask, InboxItem, Reminder,
    InboxItemAuthorization, InboxItemClassification, InboxItemHistory,
    GTDClassificationPattern, GTDLearningEntry, GTDProcessingSettings
)

# Modelos básicos
admin.site.register(Status)
admin.site.register(ProjectStatus)
admin.site.register(TaskStatus)
admin.site.register(Classification)

# Sistema de etiquetas mejorado
@admin.register(TagCategory)
class TagCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'color', 'is_system')
    list_filter = ('is_system',)
    search_fields = ('name', 'description')
    list_editable = ('color',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'color', 'is_system', 'created_at')
    list_filter = ('category', 'is_system', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('color',)

# Modelos de estados e historial
admin.site.register(ProjectState)
admin.site.register(ProjectHistory)
admin.site.register(TaskState)
admin.site.register(TaskHistory)
admin.site.register(EventState)
admin.site.register(EventHistory)

# Modelos con administración personalizada

# Proyecto
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'project_status', 'event', 'created_at', 'updated_at')
    list_filter = ('project_status', 'created_at', 'updated_at', 'event')
    search_fields = ('title', 'description', 'host__username', 'assigned_to__username')
    list_editable = ('project_status',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProjectAttendee)
class ProjectAttendeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'registration_time', 'has_paid', 'notes')
    list_filter = ('has_paid', 'registration_time')
    search_fields = ('user__username', 'project__title', 'notes')

# Tarea
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'task_status', 'assigned_to', 'important', 'created_at')
    list_filter = ('task_status', 'project', 'important', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'assigned_to__username', 'host__username')
    list_editable = ('task_status', 'important')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(TaskProgram)
class TaskProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'start_time', 'end_time', 'host', 'get_duration', 'get_status')
    list_filter = ('start_time', 'end_time', 'host')
    search_fields = ('title', 'task__title', 'host__username')
    date_hierarchy = 'start_time'
    readonly_fields = ('created_at',)

    def get_duration(self, obj):
        """Calcular y mostrar la duración del programa"""
        if obj.start_time and obj.end_time:
            duration = obj.end_time - obj.start_time
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "N/A"
    get_duration.short_description = 'Duración'

    def get_status(self, obj):
        """Mostrar el estado de la tarea asociada"""
        return obj.task.task_status.status_name
    get_status.short_description = 'Estado de Tarea'

    def get_queryset(self, request):
        """Optimizar las consultas para incluir las relaciones necesarias"""
        return super().get_queryset(request).select_related('task', 'host', 'task__task_status')

    actions = ['mark_completed', 'mark_in_progress', 'bulk_delete']

    def mark_completed(self, request, queryset):
        """Marcar las tareas asociadas como completadas"""
        updated = 0
        completed_status = TaskStatus.objects.get(status_name='Completed')
        for program in queryset:
            if program.task.task_status.status_name != 'Completed':
                program.task.task_status = completed_status
                program.task.save()
                updated += 1
        self.message_user(request, f'{updated} tareas marcadas como completadas.')
    mark_completed.short_description = 'Marcar tareas como completadas'

    def mark_in_progress(self, request, queryset):
        """Marcar las tareas asociadas como en progreso"""
        updated = 0
        in_progress_status = TaskStatus.objects.get(status_name='In Progress')
        for program in queryset:
            if program.task.task_status.status_name != 'In Progress':
                program.task.task_status = in_progress_status
                program.task.save()
                updated += 1
        self.message_user(request, f'{updated} tareas marcadas como en progreso.')
    mark_in_progress.short_description = 'Marcar tareas como en progreso'

    def bulk_delete(self, request, queryset):
        """Eliminar programas seleccionados"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} programas eliminados exitosamente.')
    bulk_delete.short_description = 'Eliminar programas seleccionados'

@admin.register(TaskSchedule)
class TaskScheduleAdmin(admin.ModelAdmin):
    list_display = ('task', 'host', 'recurrence_type', 'get_selected_days_display', 'start_time', 'duration', 'is_active', 'get_next_occurrence', 'get_programs_count', 'created_at')
    list_filter = ('recurrence_type', 'is_active', 'start_date', 'end_date', 'created_at', 'host')
    search_fields = ('task__title', 'host__username')
    list_editable = ('is_active',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Información Básica', {
            'fields': ('task', 'host', 'is_active')
        }),
        ('Configuración de Recurrencia', {
            'fields': ('recurrence_type', 'start_time', 'duration', 'start_date', 'end_date')
        }),
        ('Días de la Semana', {
            'fields': ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_selected_days_display(self, obj):
        """Mostrar los días seleccionados de manera legible"""
        return obj.get_selected_days_display()
    get_selected_days_display.short_description = 'Días Seleccionados'

    def get_next_occurrence(self, obj):
        """Mostrar la próxima ocurrencia"""
        next_occ = obj.get_next_occurrence()
        if next_occ:
            return f"{next_occ['date']} {next_occ['start_time'].strftime('%H:%M')}"
        return "Sin ocurrencias futuras"
    get_next_occurrence.short_description = 'Próxima Ocurrencia'

    def get_programs_count(self, obj):
        """Mostrar el número de programas generados"""
        from .models import TaskProgram
        return TaskProgram.objects.filter(task=obj.task, host=obj.host).count()
    get_programs_count.short_description = 'Programas Generados'

    def get_queryset(self, request):
        """Optimizar las consultas para incluir las relaciones necesarias"""
        return super().get_queryset(request).select_related('task', 'host')

    actions = ['activate_schedules', 'deactivate_schedules', 'generate_programs']

    def activate_schedules(self, request, queryset):
        """Activar programaciones seleccionadas"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} programaciones activadas exitosamente.')
    activate_schedules.short_description = 'Activar programaciones seleccionadas'

    def deactivate_schedules(self, request, queryset):
        """Desactivar programaciones seleccionadas"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} programaciones desactivadas exitosamente.')
    deactivate_schedules.short_description = 'Desactivar programaciones seleccionadas'

    def generate_programs(self, request, queryset):
        """Generar programas para las programaciones seleccionadas"""
        total_created = 0
        for schedule in queryset.filter(is_active=True):
            created_programs = schedule.create_task_programs()
            total_created += len(created_programs)
        self.message_user(request, f'Se generaron {total_created} programas para las programaciones seleccionadas.')
    generate_programs.short_description = 'Generar programas para programaciones activas'

# Evento
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'event_status', 'venue', 'event_category', 'created_at')
    list_filter = ('event_status', 'event_category', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'host__username', 'assigned_to__username', 'venue')
    list_editable = ('event_status',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registration_time', 'has_paid', 'notes')
    list_filter = ('has_paid', 'registration_time')
    search_fields = ('user__username', 'event__title', 'notes')

# Sistema de dependencias entre tareas
@admin.register(TaskDependency)
class TaskDependencyAdmin(admin.ModelAdmin):
    list_display = ('task', 'depends_on', 'dependency_type', 'created_at')
    list_filter = ('dependency_type', 'created_at')
    search_fields = ('task__title', 'depends_on__title')
    date_hierarchy = 'created_at'

# Sistema de plantillas de proyectos
@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'estimated_duration', 'is_public', 'created_by', 'created_at')
    list_filter = ('category', 'is_public', 'created_at')
    search_fields = ('name', 'description', 'category')
    list_editable = ('is_public',)
    date_hierarchy = 'created_at'

@admin.register(TemplateTask)
class TemplateTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'template', 'order', 'estimated_hours')
    list_filter = ('template', 'order')
    search_fields = ('title', 'description', 'template__name')
    list_editable = ('order', 'estimated_hours')

# Inbox GTD (Getting Things Done)
@admin.register(InboxItem)
class InboxItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'gtd_category', 'action_type', 'priority', 'created_by', 'assigned_to', 'is_processed', 'is_public', 'view_count', 'created_at', 'get_tags')
    list_filter = ('is_processed', 'gtd_category', 'action_type', 'priority', 'is_public', 'created_at', 'created_by', 'assigned_to', 'tags', 'energy_required')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_to__username', 'context', 'notes')
    list_editable = ('is_processed', 'gtd_category', 'action_type', 'priority', 'assigned_to')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'processed_at', 'last_activity', 'view_count')
    filter_horizontal = ('tags',)

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'created_by', 'assigned_to', 'is_public')
        }),
        ('Clasificación GTD', {
            'fields': ('gtd_category', 'action_type', 'priority', 'energy_required', 'context', 'estimated_time', 'due_date')
        }),
        ('Estado y Procesamiento', {
            'fields': ('is_processed', 'processed_to_content_type', 'processed_to_object_id')
        }),
        ('Etiquetas y Metadatos', {
            'fields': ('tags', 'notes', 'waiting_for', 'waiting_for_date', 'next_review_date', 'review_notes', 'created_during', 'user_context')
        }),
        ('Estadísticas', {
            'fields': ('view_count', 'last_activity'),
            'classes': ('collapse',)
        }),
        ('Campos de Solo Lectura', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )

    def get_tags(self, obj):
        """Mostrar las etiquetas asociadas al inbox item"""
        return ", ".join([tag.name for tag in obj.tags.all()]) or "Sin etiquetas"
    get_tags.short_description = 'Etiquetas'

    def get_queryset(self, request):
        """Optimizar las consultas para incluir las relaciones necesarias"""
        return super().get_queryset(request).select_related(
            'created_by', 'assigned_to'
        ).prefetch_related(
            'tags', 'authorized_users', 'classification_votes'
        )

    actions = ['mark_processed', 'mark_unprocessed', 'assign_to_current_user', 'make_public', 'make_private']

    def mark_processed(self, request, queryset):
        """Marcar items como procesados"""
        updated = queryset.update(is_processed=True, processed_at=timezone.now())
        self.message_user(request, f'{updated} items marcados como procesados.')
    mark_processed.short_description = 'Marcar como procesados'

    def mark_unprocessed(self, request, queryset):
        """Marcar items como no procesados"""
        updated = queryset.update(is_processed=False, processed_at=None)
        self.message_user(request, f'{updated} items marcados como no procesados.')
    mark_unprocessed.short_description = 'Marcar como no procesados'

    def assign_to_current_user(self, request, queryset):
        """Asignar items al usuario actual"""
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f'{updated} items asignados a {request.user.username}.')
    assign_to_current_user.short_description = 'Asignar a mí'

    def make_public(self, request, queryset):
        """Hacer items públicos"""
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} items hechos públicos.')
    make_public.short_description = 'Hacer públicos'

    def make_private(self, request, queryset):
        """Hacer items privados"""
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} items hechos privados.')
    make_private.short_description = 'Hacer privados'

# Sistema de recordatorios mejorados
@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'remind_at', 'reminder_type', 'is_sent', 'created_by', 'created_at')
    list_filter = ('reminder_type', 'is_sent', 'remind_at', 'created_at')
    search_fields = ('title', 'description', 'created_by__username')
    list_editable = ('is_sent',)
    date_hierarchy = 'remind_at'
    readonly_fields = ('created_at',)

# Otros modelos
@admin.register(CreditAccount)
class CreditAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'timestamp', 'message')
    list_filter = ('timestamp', 'room')
    search_fields = ('message', 'user__username', 'room__name')

# Sistema de autorización para items del inbox
@admin.register(InboxItemAuthorization)
class InboxItemAuthorizationAdmin(admin.ModelAdmin):
    list_display = ('inbox_item', 'user', 'permission_level', 'granted_by', 'granted_at')
    list_filter = ('permission_level', 'granted_at', 'granted_by')
    search_fields = ('inbox_item__title', 'user__username', 'granted_by__username')
    date_hierarchy = 'granted_at'
    readonly_fields = ('granted_at',)

# Sistema de clasificación colaborativa para items del inbox
@admin.register(InboxItemClassification)
class InboxItemClassificationAdmin(admin.ModelAdmin):
    list_display = ('inbox_item', 'user', 'gtd_category', 'action_type', 'priority', 'confidence', 'created_at')
    list_filter = ('gtd_category', 'action_type', 'priority', 'created_at', 'user')
    search_fields = ('inbox_item__title', 'user__username', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('confidence',)

# Historial de cambios en items del inbox
@admin.register(InboxItemHistory)
class InboxItemHistoryAdmin(admin.ModelAdmin):
    list_display = ('inbox_item', 'user', 'action', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('inbox_item__title', 'user__username', 'old_values', 'new_values')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'ip_address', 'user_agent')

# Sistema de patrones de clasificación automática GTD
@admin.register(GTDClassificationPattern)
class GTDClassificationPatternAdmin(admin.ModelAdmin):
    list_display = ('name', 'gtd_category', 'action_type', 'priority', 'is_active', 'usage_count', 'created_by', 'created_at')
    list_filter = ('gtd_category', 'action_type', 'priority', 'is_active', 'created_at', 'created_by')
    search_fields = ('name', 'description', 'keywords', 'created_by__username')
    list_editable = ('is_active',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'usage_count')

    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'is_active', 'created_by')
        }),
        ('Condiciones del Patrón', {
            'fields': ('keywords', 'keywords_operator')
        }),
        ('Resultados de Clasificación', {
            'fields': ('gtd_category', 'action_type', 'priority', 'energy_required')
        }),
        ('Configuración', {
            'fields': ('confidence_score', 'usage_count')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Sistema de aprendizaje automático simple para GTD
@admin.register(GTDLearningEntry)
class GTDLearningEntryAdmin(admin.ModelAdmin):
    list_display = ('inbox_item', 'user', 'user_gtd_category', 'user_action_type', 'was_correct', 'learned_at')
    list_filter = ('user_gtd_category', 'user_action_type', 'was_correct', 'learned_at', 'user')
    search_fields = ('inbox_item__title', 'user__username')
    date_hierarchy = 'learned_at'
    readonly_fields = ('learned_at',)

# Configuraciones de procesamiento GTD para el panel de gestión
@admin.register(GTDProcessingSettings)
class GTDProcessingSettingsAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'is_active', 'auto_email_processing', 'auto_call_queue', 'auto_chat_routing', 'created_at', 'updated_at')
    list_filter = ('is_active', 'auto_email_processing', 'auto_call_queue', 'auto_chat_routing', 'created_at', 'created_by')
    search_fields = ('created_by__username',)
    list_editable = ('is_active', 'auto_email_processing', 'auto_call_queue', 'auto_chat_routing')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Configuraciones de Procesamiento Automático', {
            'fields': ('auto_email_processing', 'auto_call_queue', 'auto_chat_routing', 'is_active')
        }),
        ('Configuraciones de Rendimiento', {
            'fields': ('processing_interval', 'max_concurrent_items')
        }),
        ('Configuraciones Específicas por Tipo', {
            'fields': ('email_batch_size', 'call_queue_timeout', 'chat_response_timeout')
        }),
        ('Configuraciones de Agentes/Bot', {
            'fields': ('enable_bot_cx', 'enable_bot_atc', 'enable_human_agents')
        }),
        ('Configuraciones de Prioridad', {
            'fields': ('auto_priority_assignment', 'priority_threshold_high', 'priority_threshold_medium')
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )