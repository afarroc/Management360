#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import django
import sys

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import Lesson
from courses.templatetags.lesson_tags import render_structured_content
from django.template import Template, Context

def test_contentblock_rendering():
    """Prueba el renderizado del ContentBlock id=25 en la lección"""

    try:
        # Obtener la lección creada
        lesson = Lesson.objects.get(slug='prueba-contentblock-anuncio')
        print(f"Lección encontrada: {lesson.title} (ID: {lesson.id})")

        # Renderizar el contenido estructurado
        print("\n=== Renderizando Contenido Estructurado ===")
        rendered_html = render_structured_content(lesson.structured_content)

        # Guardar el HTML renderizado en un archivo para inspección
        with open('rendered_contentblock_25.html', 'w', encoding='utf-8') as f:
            f.write(f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prueba Renderizado ContentBlock 25</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <style>
        body {{ padding: 20px; }}
        .lesson-content-block-container {{
            border: 2px solid #007bff;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            background-color: #f8f9fa;
        }}
        .lesson-content-block-header {{
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Prueba de Renderizado: ContentBlock ID 25</h1>
        <p><strong>Lección:</strong> {lesson.title}</p>
        <p><strong>Slug:</strong> {lesson.slug}</p>
        <p><strong>Autor:</strong> {lesson.author.username}</p>

        <div class="rendered-content">
            {rendered_html}
        </div>
    </div>
</body>
</html>
""")

        print("HTML renderizado guardado en: rendered_contentblock_25.html")

        # Mostrar información sobre los elementos renderizados
        print(f"\nContenido estructurado tiene {len(lesson.structured_content)} elementos:")
        for i, element in enumerate(lesson.structured_content):
            element_type = element.get('type', 'unknown')
            title = element.get('title', '')
            print(f"  {i+1}. Tipo: {element_type}, Título: {title}")

            if element_type == 'content_block':
                block_id = element.get('content')
                print(f"      ContentBlock ID: {block_id}")

        # Verificar si el ContentBlock se renderizó correctamente
        if 'lesson-content-block-container' in rendered_html:
            print("\n[OK] ContentBlock container encontrado en el HTML renderizado")
        else:
            print("\n[ERROR] ContentBlock container NO encontrado en el HTML renderizado")

        # Verificar elementos específicos del anuncio
        ad_indicators = ['🚀', 'banner', 'anuncio', 'premium', 'descuento']
        found_indicators = [indicator for indicator in ad_indicators if indicator in rendered_html]
        if found_indicators:
            print(f"[OK] Elementos de anuncio encontrados: {found_indicators}")
        else:
            print("[WARNING] No se encontraron elementos específicos de anuncio")

        return rendered_html

    except Lesson.DoesNotExist:
        print("Error: Lección 'prueba-contentblock-anuncio' no encontrada")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_contentblock_rendering()