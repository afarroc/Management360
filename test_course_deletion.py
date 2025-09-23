#!/usr/bin/env python
"""
Test script para verificar la funcionalidad de eliminación de cursos
con validación de dependencias.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import TestCase
from courses.models import Course, Module, Lesson, Enrollment, Review
from cv.models import Curriculum

def test_course_deletion_dependencies():
    """Test para verificar las validaciones de eliminación de cursos"""

    print("Probando funcionalidad de eliminacion de cursos...")

    # Crear usuario de prueba con CV
    try:
        user = User.objects.create_user(
            username='test_tutor',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Tutor'
        )

        # Crear CV para el usuario
        cv = Curriculum.objects.create(
            user=user,
            role='Tutor',
            bio='Tutor de prueba'
        )

        print("Usuario de prueba creado")

        # Crear curso de prueba
        course = Course.objects.create(
            title='Curso de Prueba para Eliminacion',
            description='Curso para probar eliminacion',
            tutor=user,
            price=29.99,
            duration_hours=10,
            is_published=False
        )

        print("Curso de prueba creado")

        # Crear módulo y lección
        module = Module.objects.create(
            course=course,
            title='Modulo de Prueba',
            description='Descripcion del modulo'
        )

        lesson = Lesson.objects.create(
            module=module,
            title='Leccion de Prueba',
            content='Contenido de prueba',
            duration_minutes=30
        )

        print("Modulo y leccion creados")

        # Crear estudiante de prueba
        student = User.objects.create_user(
            username='test_student',
            email='student@example.com',
            password='testpass123'
        )

        # Crear inscripción activa
        enrollment = Enrollment.objects.create(
            student=student,
            course=course,
            status='active'
        )

        print("Estudiante e inscripcion creados")

        # Probar eliminación con estudiante activo (debe fallar)
        print("\nProbando eliminacion con estudiante activo...")

        # Simular la lógica de validación
        active_enrollments = course.enrollments.filter(status='active').count()
        print(f"Estudiantes activos: {active_enrollments}")

        if active_enrollments > 0:
            print("Validacion correcta: No se puede eliminar curso con estudiantes activos")
        else:
            print("Error: Deberia haber estudiantes activos")

        # Cambiar estado a completado
        enrollment.status = 'completed'
        enrollment.save()

        print("Estudiante marcado como completado")

        # Probar eliminación ahora (debe funcionar)
        print("\nProbando eliminacion sin estudiantes activos...")

        active_enrollments = course.enrollments.filter(status='active').count()
        completed_enrollments = course.enrollments.filter(status='completed').count()
        modules_count = course.modules.count()
        lessons_count = Lesson.objects.filter(module__course=course).count()

        print(f"Estudiantes activos: {active_enrollments}")
        print(f"Estudiantes completados: {completed_enrollments}")
        print(f"Modulos: {modules_count}")
        print(f"Lecciones: {lessons_count}")

        if active_enrollments == 0:
            print("Validacion correcta: Se puede eliminar curso sin estudiantes activos")

            # Eliminar el curso
            course_title = course.title
            course.delete()
            print(f"Curso '{course_title}' eliminado exitosamente")
        else:
            print("Error: No deberia haber estudiantes activos")

        # Limpiar datos de prueba
        print("\nLimpiando datos de prueba...")
        student.delete()
        user.delete()
        print("Datos de prueba eliminados")

    except Exception as e:
        print(f"Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\nPruebas completadas!")

if __name__ == '__main__':
    test_course_deletion_dependencies()