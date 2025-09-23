#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from courses.models import Course, Module, Lesson, ContentBlock
from django.db import models

def check_course_50():
    try:
        course = Course.objects.get(id=50)
        print(f"Curso: {course.title}")
        print(f"Tutor: {course.tutor.username}")
        print(f"Publicado: {course.is_published}")
        print(f"Módulos: {course.modules.count()}")

        print("\nMódulos y lecciones:")
        for module in course.modules.all().order_by('order'):
            print(f"  - {module.title} (ID: {module.id})")
            lessons = module.lessons.all().order_by('order')
            print(f"    Lecciones: {lessons.count()}")
            for lesson in lessons:
                print(f"      * {lesson.title} (ID: {lesson.id}, Tipo: {lesson.lesson_type}, Gratuita: {lesson.is_free})")
                if lesson.structured_content:
                    print(f"        Contenido estructurado: {len(lesson.structured_content)} elementos")

        # Verificar bloques de contenido disponibles
        print(f"\nBloques de contenido disponibles: {ContentBlock.objects.filter(models.Q(author=course.tutor) | models.Q(is_public=True)).count()}")

        # Verificar lecciones independientes
        standalone_lessons = Lesson.objects.filter(author=course.tutor, module__isnull=True, is_published=True)
        print(f"Lecciones independientes: {standalone_lessons.count()}")

    except Course.DoesNotExist:
        print("Curso con ID 50 no encontrado")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_course_50()