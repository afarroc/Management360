from django.contrib import admin
from .models import (
    Status, ProjectStatus, TaskStatus,
    Classification, Project, ProjectState, ProjectHistory, ProjectAttendee,
    Task, TaskState, TaskHistory, TaskProgram,
    Event, EventState, EventHistory, EventAttendee,
    Tag, Room, Message, CreditAccount
)

# Modelos básicos
admin.site.register(Status)
admin.site.register(ProjectStatus)
admin.site.register(TaskStatus)
admin.site.register(Classification)
admin.site.register(Tag)

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
    list_display = ('title', 'host', 'project_status', 'created_at')
    list_filter = ('project_status', 'created_at')
    search_fields = ('title', 'host__username')

@admin.register(ProjectAttendee)
class ProjectAttendeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'registration_time', 'has_paid')
    list_filter = ('has_paid', 'registration_time')

# Tarea
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'task_status', 'assigned_to')
    list_filter = ('task_status', 'project')
    search_fields = ('title', 'assigned_to__username')

@admin.register(TaskProgram)
class TaskProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'start_time', 'end_time')
    list_filter = ('start_time', 'end_time')

# Evento
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'event_status', 'venue')
    list_filter = ('event_status', 'event_category')
    search_fields = ('title', 'host__username')

@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registration_time', 'has_paid')
    list_filter = ('has_paid', 'registration_time')

# Otros modelos
@admin.register(CreditAccount)
class CreditAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'timestamp')
    list_filter = ('timestamp', 'room')