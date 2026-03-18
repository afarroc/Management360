# events/tests/test_runner.py
"""
Configuración personalizada para ejecutar tests con cobertura
"""

from django.test.runner import DiscoverRunner
from django.conf import settings

class EventTestRunner(DiscoverRunner):
    """Test runner personalizado para eventos"""
    
    def setup_databases(self, **kwargs):
        """Configurar bases de datos para tests"""
        # Usar base de datos en memoria para tests rápidos
        settings.DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
        settings.DATABASES['default']['NAME'] = ':memory:'
        return super().setup_databases(**kwargs)
    
    def run_tests(self, test_labels, **kwargs):
        """Ejecutar tests con configuración específica"""
        # Solo ejecutar tests de events si no se especifica otra cosa
        if not test_labels:
            test_labels = ['events.tests']
        return super().run_tests(test_labels, **kwargs)