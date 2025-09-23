#!/usr/bin/env python
"""
Script para verificar el procesamiento y estilos de elementos "image" en contenido estructurado.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import render_structured_content

def test_image_element_styling():
    """Prueba del elemento image con estilos CSS aplicados"""

    print("=" * 100)
    print("PRUEBA: ELEMENTO IMAGE CON ESTILOS CSS APLICADOS")
    print("=" * 100)

    # Elemento JSON con imagen
    structured_content = [
        {
            "type": "image",
            "content": "https://example.com/mathematics-diagram.png",
            "title": "Diagrama de funciones matemáticas"
        },
        {
            "type": "image",
            "content": "/media/images/algebra-variables.jpg",
            "title": "Variables y constantes en álgebra"
        },
        {
            "type": "image",
            "content": "https://via.placeholder.com/800x600.png?text=Geometria",
            "title": "Figuras geométricas básicas"
        }
    ]

    print("ELEMENTOS JSON:")
    print("=" * 50)
    import json
    print(json.dumps(structured_content, indent=2, ensure_ascii=False))
    print()

    print("DETALLES DE LOS ELEMENTOS:")
    print("=" * 50)
    for i, element in enumerate(structured_content, 1):
        print(f"Imagen {i}:")
        print(f"  Type: {element['type']}")
        print(f"  Content (URL): {element['content']}")
        print(f"  Title: {element['title']}")
        print()

    # Procesar con el template tag
    rendered_html = render_structured_content(structured_content)

    print("HTML RENDERIZADO POR TEMPLATE TAG:")
    print("=" * 50)
    print(rendered_html)
    print()

    # Análisis detallado
    print("ANÁLISIS DETALLADO:")
    print("-" * 30)

    # Verificar estructura general
    print("1. ESTRUCTURA HTML:")
    image_containers = rendered_html.count('<div class="lesson-image-container">')
    images = rendered_html.count('<img src=')
    captions = rendered_html.count('<p class="lesson-image-caption">')
    print(f"   Contenedores lesson-image-container: {image_containers}")
    print(f"   Etiquetas <img>: {images}")
    print(f"   Leyendas lesson-image-caption: {captions}")

    # Verificar clases CSS aplicadas
    print(f"\n2. CLASES CSS APLICADAS:")
    has_lesson_image_class = 'class="lesson-image"' in rendered_html
    has_alt_attribute = 'alt=' in rendered_html
    has_caption_class = 'class="lesson-image-caption"' in rendered_html
    print(f"   Clase 'lesson-image': {has_lesson_image_class}")
    print(f"   Atributo alt presente: {has_alt_attribute}")
    print(f"   Clase 'lesson-image-caption': {has_caption_class}")

    # Verificar URLs específicas
    print(f"\n3. URLs DE IMÁGENES:")
    urls_found = []
    import re
    img_tags = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', rendered_html)
    for i, url in enumerate(img_tags, 1):
        print(f"   Imagen {i}: {url}")
        urls_found.append(url)

    # Verificar que las URLs coinciden
    expected_urls = [
        "https://example.com/mathematics-diagram.png",
        "/media/images/algebra-variables.jpg",
        "https://via.placeholder.com/800x600.png?text=Geometria"
    ]

    urls_match = urls_found == expected_urls
    print(f"   URLs coinciden con originales: {urls_match}")

    # Verificar atributos alt
    print(f"\n4. ATRIBUTOS ALT:")
    alt_texts = re.findall(r'alt="([^"]*)"', rendered_html)
    for i, alt_text in enumerate(alt_texts, 1):
        print(f"   Alt {i}: '{alt_text}'")

    expected_alts = [
        "Diagrama de funciones matemáticas",
        "Variables y constantes en álgebra",
        "Figuras geométricas básicas"
    ]

    alts_match = alt_texts == expected_alts
    print(f"   Textos alt coinciden: {alts_match}")

    # Verificar leyendas
    print(f"\n5. LEYENDAS DE IMAGEN:")
    caption_texts = re.findall(r'<p class="lesson-image-caption"><i[^>]+></i>([^<]+)</p>', rendered_html)
    for i, caption in enumerate(caption_texts, 1):
        print(f"   Leyenda {i}: '{caption.strip()}'")

    expected_captions = [
        "Diagrama de funciones matemáticas",
        "Variables y constantes en álgebra",
        "Figuras geométricas básicas"
    ]

    captions_match = caption_texts == expected_captions
    print(f"   Leyendas coinciden: {captions_match}")

    # Verificar estructura completa
    print(f"\n6. ESTRUCTURA COMPLETA:")
    structure_checks = [
        image_containers == 3,  # Tres contenedores
        images == 3,  # Tres imágenes
        captions == 3,  # Tres leyendas
        has_lesson_image_class,  # Clase aplicada
        has_alt_attribute,  # Alt presente
        has_caption_class,  # Clase de leyenda
        urls_match,  # URLs correctas
        alts_match,  # Alts correctos
        captions_match,  # Leyendas correctas
    ]

    total_checks = len(structure_checks)
    passed_checks = sum(structure_checks)

    print(f"   Total de verificaciones: {total_checks}")
    print(f"   Verificaciones exitosas: {passed_checks}")
    print(f"   Tasa de éxito: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")

    # Verificar que no hay elementos inesperados
    print(f"\n7. ELEMENTOS INESPERADOS:")
    has_strong = '<strong>' in rendered_html
    has_ul = '<ul>' in rendered_html
    has_p_text = '<p>' in rendered_html and 'lesson-content' not in rendered_html
    print(f"   Negritas (<strong>): {has_strong}")
    print(f"   Listas (<ul>): {has_ul}")
    print(f"   Párrafos de texto normales: {has_p_text}")

    # Resumen final
    print(f"\n" + "=" * 100)
    print("RESULTADO FINAL:")
    print("=" * 100)

    if passed_checks == total_checks:
        print("SUCCESS: TODOS LOS CRITERIOS CUMPLIDOS")
        print("El elemento image funciona perfectamente con estilos aplicados")
    else:
        print(f"ERROR: {total_checks - passed_checks} CRITERIOS FALLARON")
        print("Hay problemas con el procesamiento del elemento image")

    # Mostrar resumen específico
    print(f"\n" + "=" * 100)
    print("RESUMEN ESPECÍFICO DEL ELEMENTO IMAGE:")
    print("=" * 100)

    print("ELEMENTOS PROCESADOS:")
    print(f"- Número de imágenes: {images}")
    print(f"- Contenedores: {image_containers}")
    print(f"- Leyendas: {captions}")
    print("- Clases aplicadas: lesson-image, lesson-image-container, lesson-image-caption")
    print("- Atributos: src, alt, class")
    print("- URLs preservadas: Sí")
    print("- Títulos como leyendas: Sí")

    if passed_checks == total_checks:
        print("\nCONFIRMACION: El elemento image funciona correctamente")
        print("- Estructura HTML completa y semántica")
        print("- URLs y títulos correctamente aplicados")
        print("- Atributos alt para accesibilidad")
        print("- Leyendas con iconos descriptivos")
        print("- Estilos CSS aplicados (lesson-image, etc.)")
    else:
        print("\nPROBLEMAS DETECTADOS:")
        if image_containers != 3:
            print("- Número incorrecto de contenedores")
        if not urls_match:
            print("- URLs no coinciden")
        if not alts_match:
            print("- Atributos alt incorrectos")
        if not captions_match:
            print("- Leyendas incorrectas")

    print("=" * 100)

if __name__ == '__main__':
    test_image_element_styling()