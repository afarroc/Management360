#!/usr/bin/env python
"""
Script para probar el renderizado de la lección creada con ContentBlock integrado
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

def test_lesson_rendering():
    """Prueba el renderizado de la lección con ContentBlock integrado"""

    try:
        # Buscar la lección por título
        lesson = Lesson.objects.filter(title="Lección Demo: ContentBlock Integrado").first()

        if not lesson:
            print("Error: Lección no encontrada")
            return

        print(f"Lección encontrada: {lesson.title}")
        print(f"ID: {lesson.id}, Slug: {lesson.slug}")
        print(f"Autor: {lesson.author.username}")
        print(f"Contenido estructurado: {len(lesson.structured_content)} elementos")
        print()

        # Mostrar los elementos estructurados
        print("Elementos estructurados:")
        for i, element in enumerate(lesson.structured_content, 1):
            element_type = element.get('type', 'unknown')
            title = element.get('title', 'Sin título')
            content = element.get('content', '')

            print(f"  {i}. Tipo: {element_type}")
            print(f"     Título: {title}")
            if element_type == 'content_block':
                print(f"     ContentBlock ID: {content}")
            elif len(str(content)) < 100:
                print(f"     Contenido: {content}")
            else:
                print(f"     Contenido: {str(content)[:100]}...")
            print()

        # Probar el renderizado
        print("Probando renderizado...")
        rendered_html = render_structured_content(lesson.structured_content)

        print(f"[OK] Renderizado exitoso: {len(rendered_html)} caracteres de HTML")
        print()

        # Verificar que contiene el ContentBlock
        if 'Bloque: Ejercicio' in rendered_html:
            print("[OK] ContentBlock correctamente integrado en el HTML renderizado")
        else:
            print("[ERROR] ContentBlock no encontrado en el HTML renderizado")

        # Mostrar una parte del HTML generado
        print("\nVista previa del HTML generado (primeros 500 caracteres):")
        print("-" * 60)
        print(rendered_html[:500] + "..." if len(rendered_html) > 500 else rendered_html)
        print("-" * 60)

        print(f"\nURL de la lección: http://127.0.0.1:8000/courses/lessons/{lesson.slug}/")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_lesson_rendering()