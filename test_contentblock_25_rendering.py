#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import django
import sys

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import Lesson, ContentBlock
from django.contrib.auth.models import User

def create_test_lesson_with_contentblock():
    """Crea una lección de prueba que incluye el ContentBlock id=25"""

    try:
        # Obtener el usuario 'su' (autor del ContentBlock)
        user = User.objects.get(username='su')
        print(f"Usuario encontrado: {user.username}")

        # Verificar que el ContentBlock existe
        content_block = ContentBlock.objects.get(id=25)
        print(f"ContentBlock encontrado: {content_block.title} (ID: {content_block.id})")

        # Crear contenido estructurado que incluye el ContentBlock
        structured_content = [
            {
                "type": "heading",
                "title": "Prueba de Renderizado: ContentBlock Anuncio",
                "content": "Esta lección prueba cómo se renderiza el ContentBlock id=25 que contiene elementos de anuncio."
            },
            {
                "type": "text",
                "title": "Información del ContentBlock",
                "content": f"""
                **Título:** {content_block.title}
                **Tipo:** {content_block.content_type}
                **Autor:** {content_block.author.username}
                **Público:** {content_block.is_public}
                **Uso:** {content_block.usage_count} veces
                """
            },
            {
                "type": "content_block",
                "content": 25  # ID del ContentBlock que contiene los anuncios
            },
            {
                "type": "text",
                "title": "Notas de Prueba",
                "content": """
                Este ContentBlock contiene una lista de elementos de anuncio en formato JSON.
                Debería renderizarse como elementos estructurados de lección.
                """
            }
        ]

        # Crear la lección
        lesson = Lesson.objects.create(
            title="Prueba: Renderizado ContentBlock Anuncio",
            description="Lección de prueba para verificar el renderizado del ContentBlock id=25 con elementos de anuncio",
            author=user,
            slug="prueba-contentblock-anuncio",
            is_published=True,
            structured_content=structured_content
        )

        print("\n=== Lección Creada ===")
        print(f"Título: {lesson.title}")
        print(f"Slug: {lesson.slug}")
        print(f"Autor: {lesson.author.username}")
        print(f"ID: {lesson.id}")
        print(f"Contiene {len(lesson.structured_content)} elementos estructurados")
        print("Incluye ContentBlock ID 25 (Anuncio)")

        # Mostrar la URL para acceder a la lección
        print("\n=== URL de Acceso ===")
        print(f"URL de la lección: /courses/lessons/{lesson.slug}/")

        return lesson

    except User.DoesNotExist:
        print("Error: Usuario 'su' no encontrado")
    except ContentBlock.DoesNotExist:
        print("Error: ContentBlock con ID 25 no encontrado")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_test_lesson_with_contentblock()