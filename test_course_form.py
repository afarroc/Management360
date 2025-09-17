#!/usr/bin/env python3
"""
Script de prueba para crear un curso usando el formulario CourseForm
"""

import os
import sys
import django
from pathlib import Path
from io import BytesIO

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.core.files.base import ContentFile
from courses.models import Course, CourseCategory
from courses.forms import CourseForm
from django.contrib.auth.models import User

def test_course_form():
    # Crear una imagen PNG válida usando PIL si está disponible, o usar datos predefinidos
    try:
        from PIL import Image
        import io

        # Crear una imagen simple con PIL
        img = Image.new('RGB', (10, 10), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        png_data = buffer.getvalue()
        print("Imagen creada con PIL")
    except ImportError:
        # Usar datos de imagen PNG válidos predefinidos
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x0a\x00\x00\x00\x0a\x08\x02\x00\x00\x00\xb4\xea\xe4\xa4\x00\x00\x00\x19IDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        print("Usando imagen PNG predefinida")

    print("Probando creación de curso con formulario...")

    try:
        # Usar usuario existente con CV
        try:
            user = User.objects.get(username='su')  # Usuario existente
            print("Usando usuario existente: su")
        except User.DoesNotExist:
            # Crear usuario básico si no existe
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User'
            )
            print("Usuario de prueba creado")

        # Verificar que tenga perfil CV
        if not hasattr(user, 'cv'):
            print("Error: El usuario no tiene perfil CV. Necesitas crear uno manualmente.")
            return None

        # Obtener o crear categoría
        category, created = CourseCategory.objects.get_or_create(
            name='Prueba',
            defaults={'description': 'Categoría de prueba'}
        )

        # Crear datos del formulario con nombre único
        import time
        timestamp = str(int(time.time()))
        form_data = {
            'title': f'Curso de Prueba con Formulario {timestamp}',
            'category': category.id,
            'level': 'beginner',
            'description': 'Descripción del curso de prueba',
            'short_description': 'Curso de prueba',
            'price': 99.99,
            'duration_hours': 10,
            'is_published': False,
            'is_featured': False
        }

        # Crear archivo de imagen
        thumbnail_file = ContentFile(png_data, name='test_thumbnail.png')
        form_files = {
            'thumbnail': thumbnail_file
        }

        print("Creando formulario con datos...")
        form = CourseForm(data=form_data, files=form_files, user=user)

        print(f"¿Formulario válido?: {form.is_valid()}")
        if not form.is_valid():
            print("Errores del formulario:")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
            return None

        print("Guardando curso...")
        course = form.save(commit=False)
        course.tutor = user
        course.save()

        print(f"Curso creado exitosamente: {course.title}")
        print(f"Thumbnail: {course.thumbnail}")
        print(f"Thumbnail URL: {course.thumbnail.url}")

        # Verificar que el archivo existe en el storage
        from django.core.files.storage import default_storage
        if default_storage.exists(course.thumbnail.name):
            print("✓ Thumbnail existe en el servidor remoto")
        else:
            print("✗ Error: Thumbnail no existe en el servidor")

        return course

    except Exception as e:
        print(f"Error al crear curso: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    test_course_form()