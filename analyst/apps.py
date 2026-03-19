from django.apps import AppConfig

class AnalystConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analyst'
    verbose_name = 'Analyst Tools & Data Processing'
    
    def ready(self):
        """
        Inicialización cuando la app está lista
        """
        import analyst.signals  # Si tienes señales
        pass