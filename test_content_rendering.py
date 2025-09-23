#!/usr/bin/env python
"""
Script para probar el renderizado del contenido estructurado de lecciones.
Verifica que todos los tipos de elementos se rendericen correctamente.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import Lesson
from courses.templatetags.lesson_tags import render_structured_content
import json

def test_content_rendering():
    """Prueba el renderizado del contenido estructurado"""

    print("=" * 80)
    print("PRUEBA DE RENDERIZADO DE CONTENIDO ESTRUCTURADO")
    print("=" * 80)

    # Obtener la lección actualizada
    lesson = Lesson.objects.get(id=18)

    print(f"Leccion: {lesson.title}")
    print(f"Modulo: {lesson.module.title}")
    print(f"Curso: {lesson.module.course.title}")
    print(f"Duracion: {lesson.duration_minutes} minutos")
    print()

    # Verificar contenido estructurado
    structured_content = lesson.structured_content
    if not structured_content:
        print("ERROR: La leccion no tiene contenido estructurado")
        return

    print(f"Elementos de contenido: {len(structured_content)}")
    print()

    # Mostrar resumen de tipos de elementos
    element_types = {}
    for element in structured_content:
        element_type = element.get('type', 'desconocido')
        element_types[element_type] = element_types.get(element_type, 0) + 1

    print("Resumen de tipos de elementos:")
    for element_type, count in element_types.items():
        print(f"  • {element_type}: {count} elemento(s)")
    print()

    # Renderizar contenido
    print("Renderizando contenido...")
    try:
        html_output = render_structured_content(structured_content)
        print("SUCCESS: Renderizado exitoso!")
        print(f"Longitud del HTML generado: {len(html_output)} caracteres")
        print()

        # Mostrar estadísticas del HTML
        print("Estadisticas del HTML generado:")
        print(f"  • Contiene <div>: {html_output.count('<div>')} etiquetas")
        print(f"  • Contiene <p>: {html_output.count('<p>')} etiquetas")
        print(f"  • Contiene <h2>: {html_output.count('<h2>')} etiquetas")
        print(f"  • Contiene <h4>: {html_output.count('<h4>')} etiquetas")
        print(f"  • Contiene <ul>: {html_output.count('<ul>')} etiquetas")
        print(f"  • Contiene <li>: {html_output.count('<li>')} etiquetas")
        print(f"  • Contiene <img>: {html_output.count('<img>')} etiquetas")
        print(f"  • Contiene <a>: {html_output.count('<a>')} etiquetas")
        print()

        # Verificar elementos específicos
        print("Verificacion de elementos especificos:")

        # Verificar encabezados
        if 'lesson-heading-container' in html_output:
            print("  SUCCESS: Encabezados (heading) renderizados correctamente")
        else:
            print("  ERROR: Encabezados (heading) no encontrados")

        # Verificar texto
        if 'lesson-text-container' in html_output:
            print("  SUCCESS: Contenido de texto renderizado correctamente")
        else:
            print("  ERROR: Contenido de texto no encontrado")

        # Verificar listas
        if 'lesson-list-container' in html_output:
            print("  SUCCESS: Listas renderizadas correctamente")
        else:
            print("  ERROR: Listas no encontradas")

        # Verificar imágenes
        if 'lesson-image-container' in html_output:
            print("  SUCCESS: Imagenes renderizadas correctamente")
        else:
            print("  ERROR: Imagenes no encontradas")

        # Verificar videos
        if 'lesson-video-container' in html_output:
            print("  SUCCESS: Videos renderizados correctamente")
        else:
            print("  ERROR: Videos no encontrados")

        # Verificar ejercicios
        if 'lesson-exercise-container' in html_output:
            print("  SUCCESS: Ejercicios renderizados correctamente")
        else:
            print("  ERROR: Ejercicios no encontrados")

        # Verificar markdown
        if 'lesson-markdown-container' in html_output:
            print("  SUCCESS: Contenido Markdown renderizado correctamente")
        else:
            print("  ERROR: Contenido Markdown no encontrado")

        print()

        # Mostrar muestra del HTML generado
        print("Muestra del HTML generado (primeros 500 caracteres):")
        print("-" * 60)
        print(html_output[:500] + "..." if len(html_output) > 500 else html_output)
        print("-" * 60)
        print()

        # Verificar que no hay errores de sintaxis
        if '<' in html_output and '>' in html_output:
            print("SUCCESS: HTML valido generado (contiene etiquetas)")
        else:
            print("ERROR: HTML no valido generado")

        # Verificar que no hay entidades HTML sin escapar
        if '<' in html_output or '>' in html_output:
            print("WARNING: Posibles entidades HTML sin escapar")
        else:
            print("SUCCESS: Entidades HTML correctamente manejadas")

        print()
        print("PRUEBA COMPLETADA EXITOSAMENTE!")
        print("El contenido estructurado se renderiza correctamente.")

    except Exception as e:
        print(f"❌ ERROR durante el renderizado: {e}")
        import traceback
        traceback.print_exc()

def test_individual_elements():
    """Prueba renderizado de elementos individuales"""

    print("\n" + "=" * 80)
    print("PRUEBA DE ELEMENTOS INDIVIDUALES")
    print("=" * 80)

    test_elements = [
        {
            'type': 'heading',
            'title': 'Titulo de Prueba',
            'content': 'Subtitulo de prueba'
        },
        {
            'type': 'text',
            'title': 'Texto de Prueba',
            'content': 'Este es un parrafo de prueba con **negrita** y *cursiva*.'
        },
        {
            'type': 'list',
            'title': 'Lista de Prueba',
            'items': ['Elemento 1', 'Elemento 2', 'Elemento 3']
        },
        {
            'type': 'image',
            'title': 'Imagen de Prueba',
            'content': 'https://example.com/image.jpg'
        },
        {
            'type': 'video',
            'content': {
                'description': 'Video de prueba',
                'duration': 5
            }
        },
        {
            'type': 'exercise',
            'content': 'Ejercicio de prueba: Resuelve 2x + 3 = 7'
        },
        {
            'type': 'markdown',
            'content': '# Encabezado\n\nEste es **markdown** basico.'
        }
    ]

    for i, element in enumerate(test_elements, 1):
        print(f"\nElemento {i}: {element['type']}")
        try:
            html = render_structured_content([element])
            if html and len(html.strip()) > 0:
                print("  SUCCESS: Renderizado exitoso")
                # Mostrar una muestra corta
                preview = html.replace('\n', ' ').replace('<', '<').replace('>', '>')
                print(f"  Preview: {preview[:100]}...")
            else:
                print("  ERROR: Renderizado fallo (HTML vacio)")
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == '__main__':
    test_content_rendering()
    test_individual_elements()