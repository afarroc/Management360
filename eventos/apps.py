# apps.py
from django.apps import AppConfig

class EventosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'eventos'

    def ready(self):
        import eventos.templatetags.schedule_filters
        import eventos.templatetags.custom_tags
        import eventos.templatetags.signals

