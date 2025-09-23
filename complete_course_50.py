#!/usr/bin/env python
import os
import sys
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from courses.models import Course, Module, Lesson, ContentBlock
from django.contrib.auth.models import User

def create_algebra_content_blocks():
    """Crear bloques de contenido útiles para álgebra"""
    try:
        # Obtener el tutor del curso
        course = Course.objects.get(id=50)
        tutor = course.tutor

        # Bloques de fórmulas matemáticas
        formula_blocks = [
            {
                'title': 'Fórmulas Básicas de Álgebra',
                'content_type': 'text',
                'html_content': '''
<h4>Fórmulas Fundamentales</h4>
<ul>
<li><strong>Propiedad Distributiva:</strong> a(b + c) = ab + ac</li>
<li><strong>Propiedad Asociativa:</strong> (a + b) + c = a + (b + c)</li>
<li><strong>Propiedad Conmutativa:</strong> a + b = b + a</li>
<li><strong>Binomio al Cuadrado:</strong> (a + b)² = a² + 2ab + b²</li>
<li><strong>Diferencia de Cuadrados:</strong> a² - b² = (a - b)(a + b)</li>
</ul>
                ''',
                'category': 'matemáticas',
                'tags': 'álgebra,fórmulas,básico'
            },
            {
                'title': 'Operaciones con Fracciones Algebraicas',
                'content_type': 'text',
                'html_content': '''
<h4>Reglas para Fracciones Algebraicas</h4>
<p><strong>Suma y Resta:</strong></p>
<ul>
<li>Mismo denominador: <code>a/b ± c/b = (a ± c)/b</code></li>
<li>Diferente denominador: <code>a/b ± c/d = (a×d ± c×b)/(b×d)</code></li>
</ul>
<p><strong>Multiplicación:</strong> <code>(a/b) × (c/d) = (a×c)/(b×d)</code></p>
<p><strong>División:</strong> <code>(a/b) ÷ (c/d) = (a/b) × (d/c) = (a×d)/(b×c)</code></p>
                ''',
                'category': 'matemáticas',
                'tags': 'fracciones,álgebra,operaciones'
            },
            {
                'title': 'Ejemplos de Ecuaciones Lineales',
                'content_type': 'list',
                'json_content': {
                    'type': 'unordered',
                    'items': [
                        '2x + 3 = 7 → 2x = 4 → x = 2',
                        '3(x - 1) = 9 → 3x - 3 = 9 → 3x = 12 → x = 4',
                        'x/2 + 1 = 5 → x/2 = 4 → x = 8',
                        '2x - 5 = x + 7 → x = 12',
                        '4(x + 2) = 3(x - 1) → 4x + 8 = 3x - 3 → x = -11'
                    ]
                },
                'category': 'matemáticas',
                'tags': 'ecuaciones,lineales,ejemplos'
            },
            {
                'title': 'Consejos para Resolver Ecuaciones',
                'content_type': 'text',
                'html_content': '''
<h4>Estrategias para Resolver Ecuaciones</h4>
<ol>
<li><strong>Simplifica ambos lados:</strong> Combina términos semejantes</li>
<li><strong>Usa la propiedad inversa:</strong> Suma para cancelar restas, multiplica para cancelar divisiones</li>
<li><strong>Verifica la solución:</strong> Sustituye el resultado en la ecuación original</li>
<li><strong>Trabaja de adentro hacia afuera:</strong> Resuelve paréntesis primero</li>
<li><strong>Mantén el equilibrio:</strong> Lo que hagas a un lado, hazlo al otro</li>
</ol>
                ''',
                'category': 'matemáticas',
                'tags': 'ecuaciones,consejos,resolver'
            },
            {
                'title': 'Conceptos Básicos de Funciones',
                'content_type': 'text',
                'html_content': '''
<h4>¿Qué es una Función?</h4>
<p>Una función es una relación entre dos conjuntos donde cada elemento del primer conjunto se relaciona con exactamente un elemento del segundo conjunto.</p>

<h5>Notación:</h5>
<ul>
<li><strong>f(x) = 2x + 1</strong> - Función lineal</li>
<li><strong>Dominio:</strong> Conjunto de valores de entrada</li>
<li><strong>Rango:</strong> Conjunto de valores de salida</li>
<li><strong>Variable independiente:</strong> x (entrada)</li>
<li><strong>Variable dependiente:</strong> f(x) (salida)</li>
</ul>
                ''',
                'category': 'matemáticas',
                'tags': 'funciones,conceptos,básico'
            }
        ]

        created_blocks = []
        for block_data in formula_blocks:
            block, created = ContentBlock.objects.get_or_create(
                title=block_data['title'],
                author=tutor,
                defaults={
                    'content_type': block_data['content_type'],
                    'html_content': block_data.get('html_content', ''),
                    'json_content': block_data.get('json_content', {}),
                    'markdown_content': block_data.get('markdown_content', ''),
                    'category': block_data.get('category', ''),
                    'tags': block_data.get('tags', ''),
                    'is_public': True,
                    'is_featured': True
                }
            )
            if created:
                created_blocks.append(block.title)
                print(f"[+] Creado bloque: {block.title}")
            else:
                print(f"[-] Bloque ya existe: {block.title}")

        print(f"\nBloques creados: {len(created_blocks)}")
        return created_blocks

    except Exception as e:
        print(f"Error creando bloques: {e}")
        return []

def add_free_lessons_to_course():
    """Agregar lecciones gratuitas al curso"""
    try:
        course = Course.objects.get(id=50)
        tutor = course.tutor

        # Obtener el último módulo para agregar lecciones gratuitas
        last_module = course.modules.order_by('-order').first()
        if not last_module:
            print("No se encontraron módulos en el curso")
            return []

        free_lessons_data = [
            {
                'title': 'Repaso de Conceptos Básicos',
                'module': last_module,
                'lesson_type': 'text',
                'is_free': True,
                'structured_content': [
                    {
                        'type': 'heading',
                        'title': 'Repaso General de Álgebra'
                    },
                    {
                        'type': 'text',
                        'title': '¿Qué hemos aprendido?',
                        'content': 'En este curso hemos cubierto los fundamentos del álgebra, desde conceptos básicos hasta funciones lineales. Este repaso te ayudará a consolidar el conocimiento adquirido.'
                    },
                    {
                        'type': 'list',
                        'title': 'Temas principales cubiertos',
                        'items': [
                            'Variables y expresiones algebraicas',
                            'Operaciones con monomios y polinomios',
                            'Propiedades de los números reales',
                            'Ecuaciones lineales y sistemas',
                            'Factorización y productos notables',
                            'Introducción a las funciones'
                        ]
                    },
                    {
                        'type': 'text',
                        'content': 'Recuerda practicar regularmente para mantener tus habilidades algebraicas afiladas. ¡El álgebra es fundamental para muchas áreas de las matemáticas y ciencias!'
                    }
                ]
            },
            {
                'title': 'Ejercicios Prácticos Resueltos',
                'module': last_module,
                'lesson_type': 'text',
                'is_free': True,
                'structured_content': [
                    {
                        'type': 'heading',
                        'title': 'Ejercicios Resueltos Paso a Paso'
                    },
                    {
                        'type': 'text',
                        'title': 'Ejercicio 1: Simplificación de expresiones',
                        'content': 'Simplifica: 3x + 2(x - 1) - 4\n\nSolución:\n3x + 2(x - 1) - 4 = 3x + 2x - 2 - 4 = 5x - 6'
                    },
                    {
                        'type': 'text',
                        'title': 'Ejercicio 2: Resolución de ecuaciones',
                        'content': 'Resuelve: 2(x + 3) = 5x - 7\n\nSolución:\n2(x + 3) = 5x - 7\n2x + 6 = 5x - 7\n6 + 7 = 5x - 2x\n13 = 3x\nx = 13/3'
                    },
                    {
                        'type': 'text',
                        'title': 'Ejercicio 3: Factorización',
                        'content': 'Factoriza: x² - 9\n\nSolución:\nUsando diferencia de cuadrados: x² - 9 = (x - 3)(x + 3)'
                    }
                ]
            }
        ]

        created_lessons = []
        for lesson_data in free_lessons_data:
            lesson = Lesson.objects.create(
                module=lesson_data['module'],
                title=lesson_data['title'],
                lesson_type=lesson_data['lesson_type'],
                content='Contenido generado automáticamente',
                structured_content=lesson_data['structured_content'],
                is_free=lesson_data['is_free'],
                duration_minutes=15,
                order=lesson_data.get('order', 99)  # Orden alto para que aparezca al final
            )
            created_lessons.append(lesson.title)
            print(f"[+] Creada leccion gratuita: {lesson.title}")

        print(f"\nLecciones gratuitas creadas: {len(created_lessons)}")
        return created_lessons

    except Exception as e:
        print(f"Error creando lecciones gratuitas: {e}")
        return []

def create_standalone_lessons():
    """Crear lecciones independientes adicionales"""
    try:
        course = Course.objects.get(id=50)
        tutor = course.tutor

        standalone_lessons_data = [
            {
                'title': 'Álgebra en la Vida Cotidiana',
                'lesson_type': 'text',
                'description': 'Descubre cómo el álgebra se aplica en situaciones reales de la vida diaria',
                'is_published': True,
                'structured_content': [
                    {
                        'type': 'heading',
                        'title': 'El Álgebra en tu Vida Diaria'
                    },
                    {
                        'type': 'text',
                        'content': 'Aunque no lo parezca, el álgebra está presente en muchas situaciones cotidianas. Vamos a explorar algunos ejemplos prácticos.'
                    },
                    {
                        'type': 'text',
                        'title': 'Finanzas Personales',
                        'content': 'Cuando calculas cuánto dinero te queda después de pagar tus gastos, estás resolviendo ecuaciones lineales. Si ganas $2000 al mes y gastas $1500, ¿cuánto ahorras? La ecuación sería: 2000 - 1500 = x'
                    },
                    {
                        'type': 'text',
                        'title': 'Cocina y Recetas',
                        'content': 'Si una receta es para 4 personas pero quieres cocinar para 6, necesitas ajustar las cantidades. Si la receta original lleva 2 tazas de harina para 4 personas, para 6 personas necesitarías: (2 × 6) ÷ 4 = 3 tazas'
                    },
                    {
                        'type': 'text',
                        'title': 'Deportes y Estadísticas',
                        'content': 'Los deportes están llenos de álgebra. Calcular promedios de bateo, porcentajes de tiros libres, o predecir resultados basados en estadísticas anteriores.'
                    },
                    {
                        'type': 'text',
                        'title': 'Viajes y Distancia',
                        'content': 'Si viajas a 80 km/h y tienes que recorrer 240 km, ¿cuánto tiempo tardarás? La ecuación sería: tiempo = distancia ÷ velocidad = 240 ÷ 80 = 3 horas'
                    }
                ]
            },
            {
                'title': 'Errores Comunes en Álgebra',
                'lesson_type': 'text',
                'description': 'Aprende a identificar y evitar los errores más frecuentes al trabajar con álgebra',
                'is_published': True,
                'structured_content': [
                    {
                        'type': 'heading',
                        'title': 'Errores Frecuentes que Debes Evitar'
                    },
                    {
                        'type': 'text',
                        'content': 'Todos cometemos errores cuando aprendemos álgebra. Lo importante es identificarlos y aprender de ellos.'
                    },
                    {
                        'type': 'list',
                        'title': 'Errores más comunes',
                        'items': [
                            'Olvidar los signos cuando distribuyes: 3(x - 2) ≠ 3x - 2, debe ser 3x - 6',
                            'No aplicar la propiedad distributiva correctamente: 2(x + y) = 2x + 2y, no 2x + y',
                            'Confundir términos semejantes: 2x y 2x² no se pueden combinar',
                            'Olvidar cambiar el signo cuando pasas términos al otro lado: x - 3 = 7 → x = 7 + 3',
                            'No verificar la solución sustituyéndola en la ecuación original'
                        ]
                    },
                    {
                        'type': 'text',
                        'title': 'Cómo Evitar Estos Errores',
                        'content': 'La práctica constante y la verificación de resultados son las mejores formas de evitar errores. Siempre pregunta: "¿Esto tiene sentido lógico?"'
                    }
                ]
            },
            {
                'title': 'Historia del Álgebra',
                'lesson_type': 'text',
                'description': 'Un breve recorrido por la evolución histórica del álgebra desde la antigüedad hasta nuestros días',
                'is_published': True,
                'structured_content': [
                    {
                        'type': 'heading',
                        'title': 'La Evolución del Álgebra a Través del Tiempo'
                    },
                    {
                        'type': 'text',
                        'content': 'El álgebra tiene raíces antiguas y ha evolucionado significativamente a lo largo de la historia de la humanidad.'
                    },
                    {
                        'type': 'text',
                        'title': 'Orígenes Antiguos',
                        'content': 'Los babilonios (alrededor del 2000 a.C.) resolvían ecuaciones cuadráticas. Los egipcios usaban métodos algebraicos para resolver problemas prácticos como la distribución de alimentos.'
                    },
                    {
                        'type': 'text',
                        'title': 'Contribuciones Islámicas',
                        'content': 'En el siglo IX, el matemático persa Al-Juarismi escribió "El Compendio de Cálculo por Restauración y Comparación", donde introdujo el término "álgebra". Su trabajo influyó en el desarrollo de la matemática europea.'
                    },
                    {
                        'type': 'text',
                        'title': 'Renacimiento Europeo',
                        'content': 'En el siglo XVI, matemáticos como François Viète introdujeron el uso de letras para representar números variables, sentando las bases del álgebra simbólica moderna.'
                    },
                    {
                        'type': 'text',
                        'title': 'Álgebra Moderna',
                        'content': 'Hoy en día, el álgebra es fundamental en ciencias, ingeniería, economía y tecnología. Las computadoras y el machine learning dependen fuertemente de conceptos algebraicos.'
                    }
                ]
            }
        ]

        created_lessons = []
        for lesson_data in standalone_lessons_data:
            lesson = Lesson.objects.create(
                author=tutor,
                title=lesson_data['title'],
                description=lesson_data['description'],
                lesson_type=lesson_data['lesson_type'],
                content='Contenido generado automáticamente',
                structured_content=lesson_data['structured_content'],
                is_published=lesson_data['is_published'],
                duration_minutes=20
            )
            created_lessons.append(lesson.title)
            print(f"[+] Creada leccion independiente: {lesson.title}")

        print(f"\nLecciones independientes creadas: {len(created_lessons)}")
        return created_lessons

    except Exception as e:
        print(f"Error creando lecciones independientes: {e}")
        return []

def main():
    print("=== COMPLETANDO CURSO DE ÁLGEBRA (ID: 50) ===\n")

    # 1. Crear bloques de contenido
    print("1. Creando bloques de contenido CMS...")
    created_blocks = create_algebra_content_blocks()

    # 2. Agregar lecciones gratuitas
    print("\n2. Agregando lecciones gratuitas al curso...")
    created_free_lessons = add_free_lessons_to_course()

    # 3. Crear lecciones independientes
    print("\n3. Creando lecciones independientes...")
    created_standalone = create_standalone_lessons()

    # 4. Resumen final
    print("\n=== RESUMEN DE CAMBIOS ===")
    print(f"Bloques de contenido creados: {len(created_blocks)}")
    print(f"Lecciones gratuitas agregadas: {len(created_free_lessons)}")
    print(f"Lecciones independientes creadas: {len(created_standalone)}")

    # Verificar estado final
    print("\n=== ESTADO FINAL DEL CURSO ===")
    course = Course.objects.get(id=50)
    total_lessons = Lesson.objects.filter(module__course=course).count()
    free_lessons = Lesson.objects.filter(module__course=course, is_free=True).count()
    total_blocks = ContentBlock.objects.filter(author=course.tutor).count()
    standalone_lessons = Lesson.objects.filter(author=course.tutor, module__isnull=True, is_published=True).count()

    print(f"Total de lecciones en el curso: {total_lessons}")
    print(f"Lecciones gratuitas: {free_lessons}")
    print(f"Bloques de contenido: {total_blocks}")
    print(f"Lecciones independientes: {standalone_lessons}")

    print("\n[SUCCESS] Curso completado exitosamente!")

if __name__ == "__main__":
    main()