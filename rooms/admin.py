from django.contrib import admin
from .models import PlayerProfile, Room

# Modelos básicos
admin.site.register(Room)


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'current_room', 'state', 'last_state_change'
        )
