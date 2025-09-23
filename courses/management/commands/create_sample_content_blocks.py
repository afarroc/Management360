from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from courses.models import ContentBlock

class Command(BaseCommand):
    help = 'Crear bloques de contenido de ejemplo'

    def handle(self, *args, **options):
        # Obtener el primer usuario con CV para usar como autor
        try:
            author = User.objects.filter(cv__isnull=False).first()
            if not author:
                self.stdout.write(self.style.ERROR('No hay usuarios con CV. Crea un usuario con CV primero.'))
                return
        except:
            self.stdout.write(self.style.ERROR('No hay usuarios con CV. Crea un usuario con CV primero.'))
            return

        # Crear bloques de contenido de ejemplo
        content_blocks = [
            {
                'title': 'Introducción a Matemáticas',
                'slug': 'introduccion-matematicas',
                'description': 'Bloque introductorio para cursos de matemáticas',
                'content_type': 'html',
                'html_content': '''
                <div class="alert alert-info">
                    <h4><i class="bi bi-calculator me-2"></i>¡Bienvenido a las Matemáticas!</h4>
                    <p>Las matemáticas son el lenguaje del universo. En este curso aprenderás conceptos fundamentales que te ayudarán a entender el mundo que nos rodea.</p>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <h5>¿Qué aprenderás?</h5>
                        <ul>
                            <li>Conceptos básicos de álgebra</li>
                            <li>Operaciones matemáticas</li>
                            <li>Resolución de problemas</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h5>Requisitos</h5>
                        <ul>
                            <li>Ganas de aprender</li>
                            <li>Conocimientos básicos de aritmética</li>
                            <li>Acceso a internet</li>
                        </ul>
                    </div>
                </div>
                ''',
                'category': 'Introducción',
                'tags': 'matemáticas, introducción, bienvenida',
                'is_featured': True
            },
            {
                'title': 'Conceptos Básicos de Álgebra',
                'slug': 'conceptos-basicos-algebra',
                'description': 'Explicación de variables, constantes y expresiones',
                'content_type': 'markdown',
                'markdown_content': '''
# Conceptos Básicos de Álgebra

## Variables
Una **variable** es un símbolo que representa un número desconocido o que puede cambiar.

**Ejemplos de variables:**
- x, y, z (letras minúsculas)
- a, b, c (letras minúsculas al inicio del alfabeto)

## Constantes
Una **constante** es un valor fijo que no cambia.

**Ejemplos:**
- Números: 2, 3.14, -5
- Símbolos especiales: π (pi), e (número e)

## Expresiones Algebraicas
Combinación de variables, constantes y operaciones matemáticas.

**Ejemplos:**
- 2x + 3
- x² + 2x - 1
- (a + b) × c

> **Nota:** Las expresiones algebraicas pueden contener números, variables y operaciones matemáticas.
                ''',
                'category': 'Conceptos Fundamentales',
                'tags': 'álgebra, variables, constantes, expresiones',
                'is_featured': True
            },
            {
                'title': 'Ejemplos Prácticos',
                'slug': 'ejemplos-practicos',
                'description': 'Ejercicios y ejemplos aplicados',
                'content_type': 'html',
                'html_content': '''
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="bi bi-lightbulb me-2"></i>Ejemplos Prácticos</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Problema 1: Edades</h6>
                                <p>María tiene el doble de edad que Juan. Si juntos tienen 30 años, ¿cuántos años tiene cada uno?</p>
                                <div class="alert alert-success">
                                    <strong>Solución:</strong><br>
                                    Sea x la edad de Juan<br>
                                    María tiene 2x años<br>
                                    x + 2x = 30<br>
                                    3x = 30<br>
                                    x = 10<br>
                                    María: 20 años, Juan: 10 años
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h6>Problema 2: Mezclas</h6>
                                <p>Un comerciante mezcla café a $5/kg con café a $3/kg para obtener 100kg a $4/kg. ¿Cuántos kg de cada tipo usa?</p>
                                <div class="alert alert-success">
                                    <strong>Solución:</strong><br>
                                    Sea x kg de café caro ($5/kg)<br>
                                    100 - x kg de café barato ($3/kg)<br>
                                    5x + 3(100 - x) = 4 × 100<br>
                                    5x + 300 - 3x = 400<br>
                                    2x = 100<br>
                                    x = 50kg de café caro
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                ''',
                'category': 'Ejercicios',
                'tags': 'ejemplos, problemas, aplicación',
                'is_featured': True
            },
            {
                'title': 'Glosario de Términos',
                'slug': 'glosario-terminos',
                'description': 'Definiciones importantes del curso',
                'content_type': 'json',
                'json_content': {
                    'términos': [
                        {
                            'término': 'Variable',
                            'definición': 'Símbolo que representa un valor desconocido o que puede cambiar',
                            'ejemplo': 'x, y, z'
                        },
                        {
                            'término': 'Constante',
                            'definición': 'Valor fijo que no cambia',
                            'ejemplo': '2, π, e'
                        },
                        {
                            'término': 'Expresión algebraica',
                            'definición': 'Combinación de variables, constantes y operaciones',
                            'ejemplo': '2x + 3y - 5'
                        },
                        {
                            'término': 'Ecuación',
                            'definición': 'Afirmación matemática que establece que dos expresiones son iguales',
                            'ejemplo': '2x + 3 = 7'
                        }
                    ]
                },
                'category': 'Referencia',
                'tags': 'glosario, términos, definiciones',
                'is_featured': False
            },
            {
                'title': 'Imagen de Bienvenida',
                'slug': 'imagen-bienvenida',
                'description': 'Imagen decorativa para la portada del curso',
                'content_type': 'image',
                'json_content': {
                    'url': 'https://via.placeholder.com/800x400/667eea/ffffff?text=Bienvenido+a+Matemáticas',
                    'alt': 'Imagen de bienvenida al curso de matemáticas',
                    'caption': '¡Comienza tu viaje en el mundo de las matemáticas!'
                },
                'category': 'Multimedia',
                'tags': 'imagen, bienvenida, portada',
                'is_featured': True
            },
            {
                'title': 'Video Introductorio',
                'slug': 'video-introductorio',
                'description': 'Video de presentación del curso',
                'content_type': 'video',
                'json_content': {
                    'url': 'https://www.youtube.com/embed/dQw4w9WgXcQ'
                },
                'category': 'Multimedia',
                'tags': 'video, introducción, presentación',
                'is_featured': True
            },
            {
                'title': 'Cita Inspiracional',
                'slug': 'cita-inspiracional',
                'description': 'Cita motivacional sobre el aprendizaje',
                'content_type': 'quote',
                'json_content': {
                    'text': 'El aprendizaje nunca agota la mente.',
                    'author': 'Leonardo da Vinci'
                },
                'category': 'Motivación',
                'tags': 'cita, motivación, aprendizaje',
                'is_featured': False
            },
            {
                'title': 'Código Python Básico',
                'slug': 'codigo-python-basico',
                'description': 'Ejemplo de código Python para principiantes',
                'content_type': 'code',
                'json_content': {
                    'language': 'python',
                    'code': 'def saludar(nombre):\n    print(f"¡Hola, {nombre}!")\n    return f"Saludo enviado a {nombre}"\n\n# Uso de la función\nresultado = saludar("Estudiante")\nprint(resultado)'
                },
                'category': 'Programación',
                'tags': 'python, código, ejemplo',
                'is_featured': False
            },
            {
                'title': 'Lista de Temas',
                'slug': 'lista-temas',
                'description': 'Lista ordenada de temas del curso',
                'content_type': 'list',
                'json_content': {
                    'type': 'ordered',
                    'items': [
                        'Números y operaciones básicas',
                        'Álgebra elemental',
                        'Geometría plana',
                        'Estadística básica',
                        'Resolución de problemas'
                    ]
                },
                'category': 'Contenido',
                'tags': 'temas, lista, syllabus',
                'is_featured': False
            },
            {
                'title': 'Tabla de Calificaciones',
                'slug': 'tabla-calificaciones',
                'description': 'Sistema de calificación del curso',
                'content_type': 'table',
                'json_content': {
                    'headers': ['Rango', 'Calificación', 'Descripción'],
                    'rows': [
                        ['90-100', 'A', 'Excelente'],
                        ['80-89', 'B', 'Muy Bueno'],
                        ['70-79', 'C', 'Bueno'],
                        ['60-69', 'D', 'Satisfactorio'],
                        ['0-59', 'F', 'Insuficiente']
                    ]
                },
                'category': 'Evaluación',
                'tags': 'calificaciones, tabla, evaluación',
                'is_featured': False
            },
            {
                'title': 'Tarjeta Informativa',
                'slug': 'tarjeta-informativa',
                'description': 'Tarjeta con información importante',
                'content_type': 'card',
                'json_content': {
                    'header': 'Información Importante',
                    'title': 'Horario de Clases',
                    'text': 'Las clases se dictan de lunes a viernes de 6:00 PM a 8:00 PM. No hay clases los días feriados.',
                    'button': {
                        'url': '/contacto',
                        'text': 'Contactar'
                    }
                },
                'category': 'Información',
                'tags': 'tarjeta, información, horario',
                'is_featured': False
            },
            {
                'title': 'Mensaje de Éxito',
                'slug': 'mensaje-exito',
                'description': 'Mensaje de felicitación por completar una lección',
                'content_type': 'alert',
                'json_content': {
                    'type': 'success',
                    'message': '¡Felicitaciones! Has completado exitosamente esta lección. Continúa con la siguiente para seguir aprendiendo.'
                },
                'category': 'Feedback',
                'tags': 'éxito, felicitación, progreso',
                'is_featured': False
            },
            {
                'title': 'Botón de Acción',
                'slug': 'boton-accion',
                'description': 'Botón para acceder a recursos adicionales',
                'content_type': 'button',
                'json_content': {
                    'url': '/recursos',
                    'text': 'Ver Recursos',
                    'style': 'primary',
                    'size': 'lg',
                    'icon': 'bi-book'
                },
                'category': 'Navegación',
                'tags': 'botón, acción, recursos',
                'is_featured': False
            },
            {
                'title': 'Barra de Progreso',
                'slug': 'barra-progreso',
                'description': 'Indicador visual del progreso del estudiante',
                'content_type': 'progress',
                'json_content': {
                    'value': 75,
                    'color': 'success'
                },
                'category': 'Progreso',
                'tags': 'progreso, barra, indicador',
                'is_featured': False
            },
            {
                'title': 'Insignia de Completado',
                'slug': 'insignia-completado',
                'description': 'Insignia que indica que una tarea está completada',
                'content_type': 'badge',
                'json_content': {
                    'text': 'Completado',
                    'color': 'success',
                    'icon': 'bi-check-circle'
                },
                'category': 'Estado',
                'tags': 'insignia, completado, estado',
                'is_featured': False
            }
        ]

        created_count = 0
        for block_data in content_blocks:
            block, created = ContentBlock.objects.get_or_create(
                slug=block_data['slug'],
                defaults={
                    'title': block_data['title'],
                    'description': block_data['description'],
                    'content_type': block_data['content_type'],
                    'html_content': block_data.get('html_content', ''),
                    'markdown_content': block_data.get('markdown_content', ''),
                    'json_content': block_data.get('json_content', {}),
                    'category': block_data.get('category', ''),
                    'tags': block_data.get('tags', ''),
                    'is_public': True,
                    'is_featured': block_data.get('is_featured', False),
                    'author': author
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Bloque "{block.title}" creado.'))
                created_count += 1
            else:
                self.stdout.write(f'Bloque "{block.title}" ya existe.')

        self.stdout.write(self.style.SUCCESS(f'Se crearon {created_count} bloques de contenido de ejemplo.'))