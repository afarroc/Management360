from django.contrib import admin
from .models import (
    Status, ProjectStatus, TaskStatus,
    Classification, Project, ProjectState, ProjectHistory, ProjectAttendee,
    Task, TaskState, TaskHistory, TaskProgram,
    Event, EventState, EventHistory, EventAttendee,
    Tag, TagCategory, Room, Message, CreditAccount,
    TaskDependency, ProjectTemplate, TemplateTask, InboxItem, Reminder
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
    list_display = ('title', 'task', 'start_time', 'end_time', 'host')
    list_filter = ('start_time', 'end_time', 'host')
    search_fields = ('title', 'task__title', 'host__username')
    date_hierarchy = 'start_time'

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
    list_display = ('title', 'description', 'created_by', 'is_processed', 'processed_at', 'processed_to', 'created_at', 'get_tags')
    list_filter = ('is_processed', 'created_at', 'processed_at', 'created_by', 'tags')
    search_fields = ('title', 'description', 'created_by__username', 'processed_to__title')
    list_editable = ('is_processed',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'processed_at')
    filter_horizontal = ('tags',)

    def get_tags(self, obj):
        """Mostrar las etiquetas asociadas al inbox item"""
        return ", ".join([tag.name for tag in obj.tags.all()])
    get_tags.short_description = 'Etiquetas'

    def get_queryset(self, request):
        """Optimizar las consultas para incluir las relaciones necesarias"""
        return super().get_queryset(request).select_related('created_by').prefetch_related('tags')

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