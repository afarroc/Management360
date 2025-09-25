#!/usr/bin/env python
"""
Script para probar el procesamiento de Markdown en elementos exercise
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import Lesson
from courses.templatetags.lesson_tags import process_markdown

def test_exercise_markdown():
    """Prueba el procesamiento de Markdown en elementos exercise"""

    try:
        # Obtener la lección específica
        lesson = Lesson.objects.get(id=18)

        # Encontrar elementos exercise
        exercise_elements = []
        for i, elem in enumerate(lesson.structured_content):
            if elem.get('type') == 'exercise':
                exercise_elements.append((i, elem))

        print(f"Encontrados {len(exercise_elements)} elementos exercise en la lección '{lesson.title}'")
        print()

        for idx, (pos, elem) in enumerate(exercise_elements, 1):
            print(f"EXERCISE {idx} (Posición {pos+1}):")
            print("-" * 50)

            content = elem.get('content', '')
            print("Contenido original:")
            print(content[:300] + "..." if len(content) > 300 else content)
            print()

            # Probar procesamiento de Markdown
            try:
                processed = process_markdown(content)
                print("Contenido procesado (HTML):")
                print(processed[:500] + "..." if len(processed) > 500 else processed)
                print()

                # Verificar si contiene elementos HTML esperados
                checks = [
                    ('<strong>', 'negrita (**texto**)'),
                    ('<em>', 'itálica (*texto*)'),
                    ('<p>', 'párrafos'),
                    ('<ul>', 'listas'),
                    ('<ol>', 'listas numeradas'),
                    ('<h1>', 'encabezados'),
                    ('<h2>', 'encabezados h2'),
                    ('<code>', 'código inline'),
                ]

                print("Verificaciones de elementos HTML:")
                for tag, description in checks:
                    found = tag in processed
                    status = "[OK]" if found else "[MISSING]"
                    print(f"  {status} {description}: {tag}")

                print()

            except Exception as e:
                print(f"Error procesando Markdown: {e}")
                print()

        # Probar renderizado completo del elemento exercise
        print("PRUEBA DE RENDERIZADO COMPLETO:")
        print("=" * 60)

        from courses.templatetags.lesson_tags import render_structured_content

        # Crear una lista con solo el primer exercise
        single_exercise = [exercise_elements[0][1]]
        rendered = render_structured_content(single_exercise)

        print("HTML renderizado del primer exercise:")
        print(rendered)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_exercise_markdown()