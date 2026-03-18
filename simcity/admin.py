from django.contrib import admin
from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_by', 'money', 'size', 'engine_game_id', 'created_at', 'updated_at')
    list_filter = ('size', 'created_at')
    search_fields = ('name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at', 'engine_game_id', 'map_data', 'abm_state')
    ordering = ('-created_at',)

    fieldsets = (
        ('Partida', {
            'fields': ('name', 'created_by', 'money', 'size')
        }),
        ('Engine', {
            'fields': ('engine_game_id',),
            'description': 'Vinculación con el engine Micropolis en proot:8001'
        }),
        ('Estado (solo lectura)', {
            'fields': ('map_data', 'abm_state'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
