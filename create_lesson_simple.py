#!/usr/bin/env python
"""
Script para crear una lección independiente con contenido estructurado
"""
import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import Lesson
from django.contrib.auth.models import User

def create_standalone_lesson():
    """Crear una lección independiente con contenido estructurado"""

    print("=== CREANDO LECCION INDEPENDIENTE ===")

    # Verificar usuarios con CV
    users_with_cv = User.objects.filter(cv__isnull=False)
    print(f"Usuarios con CV encontrados: {users_with_cv.count()}")

    if not users_with_cv.exists():
        print("No hay usuarios con CV. No se puede crear la leccion.")
        return False

    # Usar el primer usuario con CV
    author = users_with_cv.first()
    print(f"Usando autor: {author.username} ({author.get_full_name()})")

    # Contenido estructurado completo
    structured_content = [
        {
            "type": "heading",
            "title": "Introduccion a la Programacion en Python",
            "content": "Aprende los fundamentos de la programacion con uno de los lenguajes mas populares del mundo"
        },
        {
            "type": "text",
            "title": "Por que Python?",
            "content": """Python es un lenguaje de programacion de alto nivel, interpretado y de proposito general.

Ventajas principales:
- Facil de aprender y usar
- Gran comunidad de desarrolladores
- Amplia biblioteca de modulos
- Multiplataforma

Caracteristicas destacadas:
- Sintaxis clara y legible
- Tipado dinamico
- Gestion automatica de memoria
- Soporte para programacion orientada a objetos"""
        },
        {
            "type": "list",
            "title": "Conceptos que aprenderas",
            "items": [
                "Variables y tipos de datos basicos",
                "Estructuras de control (if, for, while)",
                "Funciones y modulos",
                "Programacion orientada a objetos",
                "Manejo de archivos",
                "Bibliotecas estandar mas importantes"
            ]
        },
        {
            "type": "image",
            "title": "Logo oficial de Python",
            "content": "https://www.python.org/static/community_logos/python-logo.png"
        },
        {
            "type": "text",
            "title": "Primeros pasos",
            "content": """Para comenzar con Python, necesitaras:

1. Instalar Python desde el sitio oficial
2. Configurar tu entorno de desarrollo
3. Aprender la sintaxis basica
4. Practicar con ejercicios simples

Recuerda: La practica constante es la clave del exito en programacion."""
        },
        {
            "type": "file",
            "title": "Guia de instalacion de Python",
            "content": "/media/files/python-installation-guide.pdf"
        }
    ]

    try:
        # Crear la lección independiente
        lesson = Lesson.objects.create(
            title="Introduccion a Python - Leccion Completa",
            author=author,
            lesson_type="text",
            content="Esta es una leccion independiente completa sobre programacion en Python con contenido estructurado, ejemplos practicos y recursos adicionales.",
            structured_content=structured_content,
            duration_minutes=45,
            order=1,
            is_free=True,
            is_published=True,
            description="Leccion completa sobre los fundamentos de Python con contenido estructurado, ejemplos practicos y recursos adicionales."
        )

        print("Leccion creada exitosamente!")
        print(f"   Titulo: {lesson.title}")
        print(f"   Autor: {lesson.author.username}")
        print(f"   ID: {lesson.id}")
        print(f"   Slug: {lesson.slug}")
        print(f"   Duracion: {lesson.duration_minutes} minutos")
        print(f"   Elementos estructurados: {len(lesson.structured_content)}")
        print(f"   URL: /courses/lessons/{lesson.slug}/")
        print(f"   Creada: {lesson.created_at.strftime('%d/%m/%Y %H:%M')}")

        # Verificar que se guardó correctamente
        standalone_lessons = Lesson.objects.filter(module__isnull=True)
        print(f"Total de lecciones independientes: {standalone_lessons.count()}")

        return True

    except Exception as e:
        print(f"Error al crear la leccion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Iniciando creacion de leccion independiente...")

    success = create_standalone_lesson()

    if success:
        print("\n¡Proceso completado exitosamente!")
        print("La leccion independiente esta lista y se puede acceder en:")
        lesson = Lesson.objects.filter(module__isnull=True).latest('created_at')
        print(f"   http://localhost:8000/courses/lessons/{lesson.slug}/")
    else:
        print("\nError en el proceso. Revisa los mensajes anteriores.")
        sys.exit(1)