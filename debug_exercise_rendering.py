#!/usr/bin/env python
"""
Script para investigar por qué los elementos 'exercise' no renderizan correctamente
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
from courses.templatetags.lesson_tags import render_structured_content

def debug_exercise_rendering():
    """Investiga el problema con el renderizado de elementos exercise"""

    try:
        # Obtener la lección específica
        lesson = Lesson.objects.get(id=18)
        print(f"Lección encontrada: {lesson.title}")
        print(f"ID: {lesson.id}")
        print()

        # Encontrar elementos exercise
        exercise_elements = []
        for i, elem in enumerate(lesson.structured_content):
            if elem.get('type') == 'exercise':
                exercise_elements.append((i, elem))

        print(f"Encontrados {len(exercise_elements)} elementos exercise:")
        for idx, (pos, elem) in enumerate(exercise_elements, 1):
            print(f"\nExercise {idx} (posición {pos+1}):")
            print(f"  Keys: {list(elem.keys())}")
            print(f"  Type: {elem.get('type')}")
            print(f"  Title: {elem.get('title', 'No title')}")
            print(f"  Content length: {len(str(elem.get('content', '')))} chars")

            # Mostrar una parte del contenido si existe
            content = elem.get('content', '')
            if content:
                content_preview = str(content)[:200] + "..." if len(str(content)) > 200 else str(content)
                print(f"  Content preview: {content_preview}")
        print()

        # Probar renderizado completo
        print("Probando renderizado completo de la lección...")
        try:
            rendered_html = render_structured_content(lesson.structured_content)
            print(f"Renderizado exitoso: {len(rendered_html)} caracteres")

            # Buscar si los elementos exercise aparecen en el HTML
            exercise_count = rendered_html.count('lesson-exercise-container')
            print(f"Contenedores exercise encontrados en HTML: {exercise_count}")

            # Mostrar una parte del HTML donde deberían estar los exercises
            if 'lesson-exercise-container' in rendered_html:
                # Encontrar la posición del primer exercise
                pos = rendered_html.find('lesson-exercise-container')
                start = max(0, pos - 200)
                end = min(len(rendered_html), pos + 400)
                print(f"\nHTML alrededor del primer exercise (pos {pos}):")
                print("-" * 60)
                print(rendered_html[start:end])
                print("-" * 60)
            else:
                print("No se encontraron contenedores exercise en el HTML renderizado")

        except Exception as e:
            print(f"Error en renderizado: {e}")

        print(f"\nURL de preview: http://127.0.0.1:8000/courses/manage/{lesson.module.course.slug}/modules/{lesson.module.id}/lessons/{lesson.id}/preview/")

    except Lesson.DoesNotExist:
        print("Error: Lección con ID 18 no encontrada")
    except Exception as e:
        print(f"Error general: {e}")

if __name__ == "__main__":
    debug_exercise_rendering()