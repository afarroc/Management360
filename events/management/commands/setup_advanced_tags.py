from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import TagCategory, Tag

class Command(BaseCommand):
    help = 'Configura las etiquetas avanzadas para las metodologías GTD, Kanban, Eisenhower y MoSCoW'

    def handle(self, *args, **kwargs):
        self.stdout.write('Configurando etiquetas avanzadas del sistema...')

        # Crear categorías de etiquetas
        categories_data = [
            {
                'name': 'GTD',
                'description': 'Etiquetas para Getting Things Done - contextos y acciones',
                'color': '#28a745',
                'icon': 'bi-check2-square',
                'is_system': True,
                'tags': [
                    {'name': '@trabajo', 'description': 'Tareas relacionadas con el trabajo', 'color': '#007bff'},
                    {'name': '@casa', 'description': 'Tareas del hogar y personales', 'color': '#28a745'},
                    {'name': '@teléfono', 'description': 'Llamadas y comunicaciones', 'color': '#17a2b8'},
                    {'name': '@computadora', 'description': 'Tareas que requieren computadora', 'color': '#6c757d'},
                    {'name': '@reunión', 'description': 'Reuniones y citas', 'color': '#fd7e14'},
                    {'name': '@email', 'description': 'Responder correos electrónicos', 'color': '#dc3545'},
                    {'name': '@leer', 'description': 'Lectura y revisión de documentos', 'color': '#6f42c1'},
                    {'name': '@escribir', 'description': 'Redacción y documentación', 'color': '#e83e8c'},
                ]
            },
            {
                'name': 'Priority',
                'description': 'Etiquetas de prioridad para MoSCoW y otros sistemas',
                'color': '#dc3545',
                'icon': 'bi-exclamation-triangle',
                'is_system': True,
                'tags': [
                    {'name': 'Must have', 'description': 'Crítico para el éxito - MoSCoW', 'color': '#dc3545'},
                    {'name': 'Should have', 'description': 'Importante pero no crítico - MoSCoW', 'color': '#fd7e14'},
                    {'name': 'Could have', 'description': 'Deseable pero no necesario - MoSCoW', 'color': '#ffc107'},
                    {'name': 'Won\'t have', 'description': 'Excluido de este ciclo - MoSCoW', 'color': '#6c757d'},
                    {'name': 'Alta', 'description': 'Prioridad alta', 'color': '#dc3545'},
                    {'name': 'Media', 'description': 'Prioridad media', 'color': '#fd7e14'},
                    {'name': 'Baja', 'description': 'Prioridad baja', 'color': '#28a745'},
                ]
            },
            {
                'name': 'Context',
                'description': 'Etiquetas de contexto para diferentes situaciones',
                'color': '#17a2b8',
                'icon': 'bi-geo-alt',
                'is_system': True,
                'tags': [
                    {'name': 'Oficina', 'description': 'Solo se puede hacer en la oficina', 'color': '#007bff'},
                    {'name': 'Casa', 'description': 'Solo se puede hacer en casa', 'color': '#28a745'},
                    {'name': 'En línea', 'description': 'Requiere conexión a internet', 'color': '#17a2b8'},
                    {'name': 'Sin conexión', 'description': 'Se puede hacer sin internet', 'color': '#6c757d'},
                    {'name': 'Individual', 'description': 'Trabajo individual', 'color': '#6f42c1'},
                    {'name': 'Equipo', 'description': 'Requiere colaboración', 'color': '#e83e8c'},
                ]
            },
            {
                'name': 'Kanban',
                'description': 'Etiquetas para el flujo de trabajo Kanban',
                'color': '#6f42c1',
                'icon': 'bi-kanban',
                'is_system': True,
                'tags': [
                    {'name': 'Bloqueado', 'description': 'Tarea bloqueada por dependencias', 'color': '#dc3545'},
                    {'name': 'En revisión', 'description': 'Pendiente de revisión', 'color': '#fd7e14'},
                    {'name': 'Testing', 'description': 'En fase de pruebas', 'color': '#ffc107'},
                    {'name': 'Documentar', 'description': 'Requiere documentación', 'color': '#17a2b8'},
                    {'name': 'Deploy', 'description': 'Listo para despliegue', 'color': '#28a745'},
                ]
            },
            {
                'name': 'Eisenhower',
                'description': 'Etiquetas para la matriz de Eisenhower',
                'color': '#e83e8c',
                'icon': 'bi-grid-3x3-gap',
                'is_system': True,
                'tags': [
                    {'name': 'Urgente e Importante', 'description': 'Hacer inmediatamente', 'color': '#dc3545'},
                    {'name': 'Importante no Urgente', 'description': 'Planificar para hacer', 'color': '#ffc107'},
                    {'name': 'Urgente no Importante', 'description': 'Delegar si es posible', 'color': '#fd7e14'},
                    {'name': 'No Urgente no Importante', 'description': 'Eliminar o posponer', 'color': '#6c757d'},
                ]
            },
            {
                'name': 'Custom',
                'description': 'Etiquetas personalizadas definidas por el usuario',
                'color': '#6c757d',
                'icon': 'bi-tag',
                'is_system': True,
                'tags': []
            }
        ]

        created_count = 0
        for category_data in categories_data:
            # Crear o obtener la categoría
            category, created = TagCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'color': category_data['color'],
                    'icon': category_data['icon'],
                    'is_system': category_data['is_system']
                }
            )

            if created:
                self.stdout.write(f'[OK] Categoría creada: {category.name}')
                created_count += 1

            # Crear etiquetas para esta categoría
            for tag_data in category_data['tags']:
                tag, tag_created = Tag.objects.get_or_create(
                    name=tag_data['name'],
                    category=category,
                    defaults={
                        'description': tag_data['description'],
                        'color': tag_data['color'],
                        'is_system': True
                    }
                )

                if tag_created:
                    self.stdout.write(f'  [OK] Etiqueta creada: {tag.name}')
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Configuración completada. Se crearon {created_count} elementos.'))

        # Mostrar resumen
        total_categories = TagCategory.objects.count()
        total_tags = Tag.objects.count()

        self.stdout.write(self.style.SUCCESS(f'Total de categorías: {total_categories}'))
        self.stdout.write(self.style.SUCCESS(f'Total de etiquetas: {total_tags}'))

        # Mostrar etiquetas por categoría
        for category in TagCategory.objects.all():
            tag_count = Tag.objects.filter(category=category).count()
            self.stdout.write(f'  {category.name}: {tag_count} etiquetas')