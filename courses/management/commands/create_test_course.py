from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson, CourseCategory
from cv.models import Curriculum

class Command(BaseCommand):
    help = 'Crear un curso de prueba de Álgebra Básica para Principiantes'

    def handle(self, *args, **options):
        # Obtener o crear categoría
        category, created = CourseCategory.objects.get_or_create(
            name='Matemáticas',
            defaults={'description': 'Cursos de matemáticas básicas y avanzadas'}
        )

        # Obtener un tutor con CV (asumir el primer usuario con CV)
        try:
            tutor = User.objects.filter(cv__isnull=False).first()
            if not tutor:
                self.stdout.write(self.style.ERROR('No hay usuarios con CV. Crea un usuario con CV primero.'))
                return
        except Curriculum.DoesNotExist:
            self.stdout.write(self.style.ERROR('No hay usuarios con CV. Crea un usuario con CV primero.'))
            return

        # Syllabus del curso
        syllabus = """
Syllabus: Curso de Álgebra Básica para Principiantes

Estructura General del Curso

Curso: Álgebra Básica para Principiantes
Duración:8 semanas
Nivel:Principiante
Objetivo:Desarrollar competencias fundamentales en álgebra para resolver problemas matemáticos básicos

---

Módulo 1: Fundamentos del Álgebra

Duración: 1 semana
Objetivo:Comprender los conceptos básicos del lenguaje algebraico

Lección 1.1: Introducción al Álgebra

Elementos de la lección:

· Texto: ¿Qué es el álgebra? Importancia en la vida diaria
· Video: [5 min] Historia y aplicaciones del álgebra
· Imagen: Diagrama de evolución de la aritmética al álgebra
· Ejercicios interactivos: Identificar variables vs constantes
· Markdown: Lista de conceptos clave
· Enlaces: Recursos adicionales de introducción

Lección 1.2: Variables y Expresiones Algebraicas

Elementos:

· Texto: Definición de variable, constante y expresión algebraica
· Video: [7 min] Cómo leer expresiones algebraicas
· Imagen: Ejemplos visuales de expresiones algebraicas
· Ejercicios: Traducir frases a expresiones algebraicas
· Quiz: Evaluación de comprensión
· Enlaces: Calculadora algebraica básica

Lección 1.3: Propiedades de los Números Reales

Elementos:

· Texto: Propiedades conmutativa, asociativa, distributiva
· Video: [10 min] Demostración de propiedades con ejemplos
· Imagen: Diagrama de propiedades numéricas
· Ejercicios: Aplicar propiedades en operaciones
· Markdown: Tabla resumen de propiedades

---

Módulo 2: Operaciones Algebraicas Básicas

Duración: 2 semanas
Objetivo:Dominar operaciones fundamentales con expresiones algebraicas

Lección 2.1: Operaciones con Monomios

Elementos:

· Texto: Suma, resta, multiplicación y división de monomios
· Video: [12 min] Resolución paso a paso
· Imagen: Ejemplos gráficos de operaciones
· Ejercicios interactivos: Practicar cada operación
· PDF descargable: Guía de procedimientos

Lección 2.2: Polinomios y sus Operaciones

Elementos:

· Texto: Definición y clasificación de polinomios
· Video: [15 min] Operaciones con polinomios
· Imagen: Estructura de un polinomio
· Ejercicios: Suma, resta y multiplicación de polinomios
· Simulador: Armar polinomios interactivamente

Lección 2.3: Leyes de los Exponentes

Elementos:

· Texto: Reglas de exponentes con ejemplos
· Video: [10 min] Aplicación de leyes de exponentes
· Infografía: Resumen visual de las 7 leyes principales
· Ejercicios: Simplificar expresiones exponenciales
· Quiz: Evaluación de leyes de exponentes

---

Módulo 3: Ecuaciones Lineales

Duración: 2 semanas
Objetivo:Resolver ecuaciones de primer grado y aplicarlas a problemas

Lección 3.1: Ecuaciones de Primer Grado

Elementos:

· Texto: Concepto de ecuación y solución
· Video: [12 min] Métodos de solución
· Imagen: Balance de una ecuación
· Ejercicios interactivos: Resolver ecuaciones paso a paso
· Calculadora: Verificación de soluciones

Lección 3.2: Aplicaciones Prácticas

Elementos:

· Texto: Plantear ecuaciones desde problemas verbales
· Video: [15 min] Análisis de problemas reales
· Caso de estudio: Problema de edades, mezclas, distancias
· Ejercicios: Resolver problemas contextualizados
· Proyecto: Crear tu propio problema algebraico

Lección 3.3: Sistemas de Ecuaciones

Elementos:

· Texto: Métodos de solución (sustitución, igualación, reducción)
· Video: [18 min] Comparación de métodos
· Simulador gráfico: Visualización de sistemas 2x2
· Ejercicios: Resolver sistemas diversos
· Markdown: Ventajas y desventajas de cada método

---

Módulo 4: Factorización y Productos Notables

Duración: 2 semanas
Objetivo:Dominar técnicas de factorización y reconocer productos notables

Lección 4.1: Factor Común y Agrupación

Elementos:

· Texto: Técnicas básicas de factorización
· Video: [10 min] Identificación de factores comunes
· Imagen: Diagrama de flujo para factorización
· Ejercicios: Factorizar expresiones simples
· Juego: "Caza del factor común"

Lección 4.2: Productos Notables

Elementos:

· Texto: Binomio al cuadrado, diferencia de cuadrados
· Video: [12 min] Demostración geométrica
· Animación: Desarrollo visual de productos notables
· Ejercicios: Aplicar fórmulas de productos notables
· Fórmula sheet: Descargable para referencia

Lección 4.3: Factorización de Trinomios

Elementos:

· Texto: Métodos para factorizar trinomios
· Video: [15 min] Tanteo y fórmula general
· Calculadora paso a paso: Factorización guiada
· Ejercicios: Factorizar trinomios de diferentes tipos
· Reto: Factorización de expresiones complejas

---

Módulo 5: Introducción a las Funciones

Duración: 1 semana
Objetivo:Comprender el concepto de función y su representación gráfica

Lección 5.1: Concepto de Función

Elementos:

· Texto: Definición de función, dominio y rango
· Video: [10 min] ¿Qué es una función?
· Diagrama interactivo: Relaciones vs funciones
· Ejercicios: Identificar funciones en diferentes contextos
· Quiz: Evaluación de conceptos básicos

Lección 5.2: Funciones Lineales

Elementos:

· Texto: Función lineal y su representación
· Video: [12 min] Gráfica de una función lineal
· Graficador interactivo: Experimentar con pendientes
· Ejercicios: Graficar funciones lineales
· Aplicación: Modelado de situaciones lineales

---

Recursos Generales del Curso

Elementos Transversales:

· Foro de discusión: Por módulo para dudas y colaboración
· Glosario interactivo: Términos algebraicos con ejemplos
· Biblioteca digital: Recursos adicionales por tema
· App móvil: Acceso offline a lecciones básicas
· Sistema de progreso: Barra de avance y logros

Evaluación:

· Quiz por lección: 5-10 preguntas de comprensión
· Examen por módulo: Evaluación integral
· Proyecto final: Aplicación práctica de conceptos
· Certificado: Al completar ?80% del curso

Características Técnicas:

· Responsive: Adaptable a web, tablet y móvil
· Accesibilidad: Texto a voz, alto contraste
· Modo offline: Descarga de materiales esenciales
· Sincronización: Progreso guardado en la nube

---
"""

        # Crear el curso
        course = Course.objects.create(
            title='Álgebra Básica para Principiantes',
            description='Curso completo de álgebra básica diseñado para principiantes. Aprende desde los fundamentos hasta conceptos avanzados con ejercicios prácticos y aplicaciones reales.',
            short_description='Desarrolla competencias fundamentales en álgebra para resolver problemas matemáticos básicos.',
            tutor=tutor,
            category=category,
            level='beginner',
            price=49.99,
            duration_hours=64,  # 8 semanas * 8 horas/semana approx
            is_published=True
        )

        self.stdout.write(self.style.SUCCESS(f'Curso "{course.title}" creado exitosamente.'))

        # Parsear módulos y lecciones
        modules_data = self.parse_syllabus(syllabus)

        for module_data in modules_data:
            module = Module.objects.create(
                course=course,
                title=module_data['title'],
                description=module_data['objective'],
                order=module_data['order']
            )
            self.stdout.write(f'Módulo "{module.title}" creado.')

            for lesson_data in module_data['lessons']:
                lesson = Lesson.objects.create(
                    module=module,
                    title=lesson_data['title'],
                    lesson_type='text',  # Por defecto texto, pero con structured_content
                    content='',  # Usar structured_content
                    structured_content=lesson_data['elements'],
                    duration_minutes=lesson_data['duration'],
                    order=lesson_data['order']
                )
                self.stdout.write(f'  Lección "{lesson.title}" creada.')

        self.stdout.write(self.style.SUCCESS('Curso de prueba creado exitosamente.'))

    def parse_syllabus(self, syllabus):
        modules = []
        lines = syllabus.strip().split('\n')
        current_module = None
        current_lesson = None
        module_order = 0
        lesson_order = 0

        for line in lines:
            line = line.strip()
            if line.startswith('Módulo'):
                if current_module:
                    modules.append(current_module)
                module_order += 1
                title = line.split(':')[1].strip()
                current_module = {
                    'title': title,
                    'objective': '',
                    'order': module_order,
                    'lessons': []
                }
                lesson_order = 0
            elif line.startswith('Objetivo:') and current_module:
                current_module['objective'] = line.replace('Objetivo:', '').strip()
            elif line.startswith('Lección'):
                if current_lesson:
                    current_module['lessons'].append(current_lesson)
                lesson_order += 1
                title = line.split(':')[1].strip()
                current_lesson = {
                    'title': title,
                    'duration': 0,
                    'order': lesson_order,
                    'elements': []
                }
            elif line.startswith('Elementos:') or line.startswith('Elementos de la lección:'):
                # Los elementos están en las líneas siguientes
                continue
            elif line.startswith('· ') and current_lesson:
                element = line[2:].strip()
                element_type, content = self.parse_element(element)
                current_lesson['elements'].append({
                    'type': element_type,
                    'content': content
                })

        if current_module:
            if current_lesson:
                current_module['lessons'].append(current_lesson)
            modules.append(current_module)

        return modules

    def parse_element(self, element):
        if element.startswith('Texto:'):
            return 'text', element.replace('Texto:', '').strip()
        elif element.startswith('Video:'):
            content = element.replace('Video:', '').strip()
            # Extraer duración si está presente
            duration = 0
            if '[' in content and 'min]' in content:
                duration_str = content.split('[')[1].split('min]')[0].strip()
                try:
                    duration = int(duration_str)
                except:
                    pass
            return 'video', {'description': content, 'duration': duration}
        elif element.startswith('Imagen:'):
            return 'image', element.replace('Imagen:', '').strip()
        elif element.startswith('Ejercicios') or element.startswith('Ejercicio'):
            return 'exercise', element.replace('Ejercicios:', '').replace('Ejercicio:', '').strip()
        elif element.startswith('Quiz:'):
            return 'quiz', element.replace('Quiz:', '').strip()
        elif element.startswith('Markdown:'):
            return 'markdown', element.replace('Markdown:', '').strip()
        elif element.startswith('Enlaces:'):
            return 'link', element.replace('Enlaces:', '').strip()
        elif element.startswith('PDF descargable:'):
            return 'pdf', element.replace('PDF descargable:', '').strip()
        elif element.startswith('Simulador:'):
            return 'simulator', element.replace('Simulador:', '').strip()
        elif element.startswith('Infografía:'):
            return 'infographic', element.replace('Infografía:', '').strip()
        elif element.startswith('Calculadora:'):
            return 'calculator', element.replace('Calculadora:', '').strip()
        elif element.startswith('Caso de estudio:'):
            return 'case_study', element.replace('Caso de estudio:', '').strip()
        elif element.startswith('Proyecto:'):
            return 'project', element.replace('Proyecto:', '').strip()
        elif element.startswith('Animación:'):
            return 'animation', element.replace('Animación:', '').strip()
        elif element.startswith('Fórmula sheet:'):
            return 'formula_sheet', element.replace('Fórmula sheet:', '').strip()
        elif element.startswith('Diagrama interactivo:'):
            return 'interactive_diagram', element.replace('Diagrama interactivo:', '').strip()
        elif element.startswith('Graficador interactivo:'):
            return 'interactive_grapher', element.replace('Graficador interactivo:', '').strip()
        elif element.startswith('Aplicación:'):
            return 'application', element.replace('Aplicación:', '').strip()
        elif element.startswith('Juego:'):
            return 'game', element.replace('Juego:', '').strip()
        else:
            return 'text', element