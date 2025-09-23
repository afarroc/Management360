#!/usr/bin/env python
"""
Script de prueba para verificar el contenido estructurado de las lecciones
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append(os.path.dirname(__file__))
django.setup()

from courses.models import Lesson, Course
import json

def test_lesson_content():
    print("=== PRUEBA DE CONTENIDO ESTRUCTURADO DE LECCIONES ===\n")

    # Obtener todas las lecciones del curso de prueba
    course = Course.objects.filter(title__icontains='Algebra').first()
    if not course:
        print("ERROR: No se encontro el curso de Algebra Basica")
        return

    print(f"Curso encontrado: {course.title}")
    print(f"Numero de modulos: {course.modules.count()}")
    print(f"Numero total de lecciones: {Lesson.objects.filter(module__course=course).count()}\n")

    # Verificar cada leccion
    lessons = Lesson.objects.filter(module__course=course).order_by('module__order', 'order')

    for i, lesson in enumerate(lessons, 1):
        print(f"--- Leccion {i}: {lesson.title} ---")
        print(f"Modulo: {lesson.module.title}")
        print(f"Tipo: {lesson.get_lesson_type_display()}")
        print(f"Duracion: {lesson.duration_minutes} minutos")
        print(f"Orden: {lesson.order}")
        print(f"Gratuita: {'Si' if lesson.is_free else 'No'}")

        # Verificar contenido estructurado
        if lesson.structured_content:
            print(f"Contenido estructurado: {len(lesson.structured_content)} elementos")
            for j, element in enumerate(lesson.structured_content, 1):
                print(f"  {j}. Tipo: {element.get('type', 'N/A')}")
                if 'title' in element and element['title']:
                    print(f"     Titulo: {element['title']}")
                if 'content' in element and element['content']:
                    content_preview = str(element['content'])[:50] + "..." if len(str(element['content'])) > 50 else str(element['content'])
                    print(f"     Contenido: {content_preview}")
                if 'items' in element and element['items']:
                    print(f"     Items: {len(element['items'])} elementos en lista")
        else:
            print("Contenido estructurado: VACIO")

        # Verificar otros campos
        if lesson.content:
            print(f"Contenido simple: {lesson.content[:50]}...")
        if lesson.video_url:
            print(f"Video URL: {lesson.video_url}")
        if lesson.quiz_questions:
            print(f"Quiz: {len(lesson.quiz_questions)} preguntas")
        if lesson.assignment_instructions:
            print(f"Tarea: {lesson.assignment_instructions[:50]}...")

        print()

    # Prueba de renderizado
    print("=== PRUEBA DE RENDERIZADO ===")

    # Verificar si existe el template tag para renderizar
    try:
        from courses.templatetags.lesson_tags import render_structured_content

        lesson_with_content = lessons.filter(structured_content__isnull=False).exclude(structured_content=[]).first()
        if lesson_with_content:
            print(f"Probando renderizado de: {lesson_with_content.title}")
            rendered = render_structured_content(lesson_with_content.structured_content)
            print("Renderizado exitoso")
            print(f"Longitud del HTML generado: {len(rendered)} caracteres")
        else:
            print("No hay lecciones con contenido estructurado para probar renderizado")

    except Exception as e:
        print(f"Error en renderizado: {e}")

    print("\n=== FIN DE PRUEBA ===")

if __name__ == '__main__':
    test_lesson_content()