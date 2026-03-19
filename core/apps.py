from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """
        Método ejecutado cuando la app está lista.
        Aquí puedes registrar señales, importar módulos, etc.
        """
        # Importar señales (si las tienes)
        # import core.signals
        pass