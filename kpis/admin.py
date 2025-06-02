from django.contrib import admin
from .models import CallRecord

@admin.register(CallRecord)
class CallRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'semana', 'agente', 'supervisor', 'servicio',
        'canal', 'eventos', 'aht', 'evaluaciones', 'satisfaccion'
    )
