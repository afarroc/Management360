#!/usr/bin/env python
"""
Script para probar el renderizado específico de la lección con ID 18
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append(os.path.dirname(__file__))
django.setup()

from courses.models import Lesson
from courses.templatetags.lesson_tags import render_structured_content
import json

def test_specific_lesson_rendering():
    print("=== PRUEBA DE RENDERIZADO ESPECÍFICO DE LECCIÓN ID 18 ===\n")

    try:
        # Obtener la lección específica
        lesson = Lesson.objects.get(id=18)

        print(f"Lección encontrada: {lesson.title}")
        print(f"Módulo: {lesson.module.title}")
        print(f"Curso: {lesson.module.course.title}")
        print(f"Tipo: {lesson.get_lesson_type_display()}")
        print(f"Duración: {lesson.duration_minutes} minutos")
        print()

        # Mostrar contenido estructurado en JSON
        print("=== CONTENIDO ESTRUCTURADO (JSON) ===")
        structured_content = lesson.structured_content
        if structured_content:
            print(json.dumps(structured_content, indent=2, ensure_ascii=False))
        else:
            print("No hay contenido estructurado")
        print()

        # Probar renderizado
        print("=== RENDERIZADO HTML ===")
        if structured_content:
            html_output = render_structured_content(structured_content)
            print("HTML generado:")
            print("=" * 50)
            print(html_output)
            print("=" * 50)
            print(f"Longitud del HTML: {len(html_output)} caracteres")

            # Verificar que contiene los elementos esperados
            checks = [
                ('Texto', '<div class="lesson-text-container">' in html_output),
                ('Imagen', '<div class="lesson-image-container">' in html_output),
                ('Video', '<div class="lesson-video-container">' in html_output),
                ('Ejercicio', '<div class="lesson-exercise-container">' in html_output),
                ('Markdown', '<div class="lesson-markdown-container">' in html_output),
                ('Enlace', '<div class="lesson-link-container">' in html_output),
                ('Iconos', 'bi bi-' in html_output),
            ]

            print("\n=== VERIFICACIONES ===")
            for check_name, result in checks:
                status = "Paso" if result else "Fallo"
                print(f"{check_name}: {status}")

        else:
            print("No se puede renderizar - no hay contenido estructurado")

        print("\n=== ANÁLISIS DETALLADO ===")

        if structured_content:
            print(f"Número de elementos: {len(structured_content)}")

            for i, element in enumerate(structured_content, 1):
                element_type = element.get('type', 'desconocido')
                title = element.get('title', '')
                content = element.get('content', '')
                items = element.get('items', [])

                print(f"\nElemento {i}: {element_type.upper()}")
                if title:
                    print(f"  Título: {title}")
                if content:
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    print(f"  Contenido: {content_preview}")
                if items:
                    print(f"  Items en lista: {len(items)}")
                    for j, item in enumerate(items[:3], 1):  # Mostrar primeros 3
                        print(f"    {j}. {item}")
                    if len(items) > 3:
                        print(f"    ... y {len(items) - 3} más")

        print("\n=== FIN DE PRUEBA ===")

    except Lesson.DoesNotExist:
        print("ERROR: La lección con ID 18 no existe")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_specific_lesson_rendering()