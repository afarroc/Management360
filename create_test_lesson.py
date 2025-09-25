#!/usr/bin/env python
"""
Script para crear una lección de prueba con contenido estructurado que incluye un ContentBlock
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

from courses.models import Lesson, ContentBlock
from django.contrib.auth.models import User

def create_test_lesson():
    """Crea una lección de prueba con contenido estructurado que incluye un ContentBlock"""

    try:
        # Obtener el usuario 'su' (autor del ContentBlock)
        user = User.objects.get(username='su')
        print(f"Usuario encontrado: {user.username}")

        # Verificar que el ContentBlock existe
        content_block = ContentBlock.objects.get(id=22)
        print(f"ContentBlock encontrado: {content_block.title} (ID: {content_block.id})")

        # Crear contenido estructurado que incluye el ContentBlock
        structured_content = [
            {
                "type": "heading",
                "title": "Lección Demo: ContentBlock Integrado",
                "content": "Esta lección demuestra cómo integrar diferentes tipos de contenido, incluyendo bloques reutilizables."
            },
            {
                "type": "text",
                "title": "Introducción a la Lección",
                "content": """
                Esta es una **lección de prueba** que combina diferentes tipos de contenido estructurado:

                - Texto con formato Markdown
                - Elementos interactivos
                - **Bloques de contenido reutilizable**

                A continuación verás un ejemplo práctico de cómo se integra un ContentBlock en una lección.
                """
            },
            {
                "type": "list",
                "title": "Elementos que se van a demostrar",
                "items": [
                    "Texto con formato Markdown completo",
                    "Listas estructuradas",
                    "Integración de ContentBlocks reutilizables",
                    "Elementos interactivos y multimedia"
                ]
            },
            {
                "type": "content_block",
                "content": 22  # ID del ContentBlock que contiene el ejercicio
            },
            {
                "type": "text",
                "title": "Conclusión",
                "content": """
                Has completado la lección de prueba. Esta demostración muestra cómo el sistema de **contenido estructurado** permite:

                1. **Reutilización**: Los ContentBlocks pueden usarse en múltiples lecciones
                2. **Flexibilidad**: Diferentes tipos de contenido en una sola lección
                3. **Mantenimiento**: Actualizar un ContentBlock afecta a todas las lecciones que lo usan

                ¡El sistema funciona correctamente! ✅
                """
            }
        ]

        # Crear la lección independiente
        lesson = Lesson.objects.create(
            title="Lección Demo: ContentBlock Integrado",
            description="Lección de demostración que integra contenido estructurado con bloques reutilizables",
            author=user,
            lesson_type="text",
            structured_content=structured_content,
            is_published=True,
            duration_minutes=15
        )

        print(f"Lección creada exitosamente: {lesson.title}")
        print(f"Slug: {lesson.slug}")
        print(f"ID: {lesson.id}")
        print(f"URL: http://127.0.0.1:8000/courses/lessons/{lesson.slug}/")

        # Verificar que el contenido estructurado se guardó correctamente
        print(f"Contenido estructurado guardado: {len(lesson.structured_content)} elementos")

        # Probar el renderizado
        from courses.templatetags.lesson_tags import render_structured_content
        rendered_html = render_structured_content(lesson.structured_content)
        print(f"Renderizado exitoso: {len(rendered_html)} caracteres de HTML generado")

        # Mostrar información de los elementos
        for i, element in enumerate(lesson.structured_content):
            element_type = element.get('type', 'unknown')
            title = element.get('title', 'Sin título')
            print(f"  Elemento {i+1}: {element_type} - {title}")

        return lesson

    except User.DoesNotExist:
        print("Error: Usuario 'su' no encontrado")
    except ContentBlock.DoesNotExist:
        print("Error: ContentBlock con ID 22 no encontrado")
    except Exception as e:
        print(f"Error al crear la lección: {e}")

if __name__ == "__main__":
    lesson = create_test_lesson()
    if lesson:
        print("\n" + "="*60)
        print("LECCIÓN CREADA EXITOSAMENTE")
        print("="*60)
        print(f"Título: {lesson.title}")
        print(f"URL: http://127.0.0.1:8000/courses/lessons/{lesson.slug}/")
        print(f"Contiene {len(lesson.structured_content)} elementos estructurados")
        print("Incluye ContentBlock ID 22 (Ejercicio)")
        print("="*60)