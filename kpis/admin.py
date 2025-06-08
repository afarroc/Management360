from django.contrib import admin
from .models import CallRecord, ExchangeRate

class CallRecordAdmin(admin.ModelAdmin):
    list_display = (
        'semana',
        'agente',
        'supervisor',
        'servicio',
        'canal',
        'eventos',
        'aht',
        'evaluaciones',
        'satisfaccion',
        'custom_satisfaction'
    )
    
    list_filter = ('semana', 'servicio', 'canal')
    search_fields = ('agente', 'supervisor')
    
    def custom_satisfaction(self, obj):
        """Método personalizado para mostrar la satisfacción con el símbolo %"""
        if obj.satisfaccion is not None:
            return f"{obj.satisfaccion}%"
        return "-"
    custom_satisfaction.short_description = 'Satisfacción (%)'
    custom_satisfaction.admin_order_field = 'satisfaccion'  # Permite ordenar por este campo

class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'period_display',
        'rate',
        'created_at'
    )
    
    list_filter = ('date',)
    search_fields = ('period_display',)
    ordering = ('-date',)
    date_hierarchy = 'date'
    
    def period_display(self, obj):
        """Muestra el periodo en formato MmmYY (ej. Ago94)"""
        return obj.date.strftime('%b%y').lower()
    period_display.short_description = 'Periodo'
    period_display.admin_order_field = 'date'  # Ordenar por la fecha real

admin.site.register(CallRecord, CallRecordAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)