#!/usr/bin/env python
"""
Script para probar el template tag render_structured_content directamente.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import render_structured_content

def test_template_tag():
    """Prueba directa del template tag"""

    print("=" * 60)
    print("PRUEBA DIRECTA DEL TEMPLATE TAG")
    print("=" * 60)

    # Contenido de prueba simple
    test_content = [
        {
            "type": "heading",
            "title": "Test Heading",
            "content": "Test subtitle"
        },
        {
            "type": "text",
            "title": "Test Text",
            "content": "This is a test paragraph."
        },
        {
            "type": "image",
            "content": "https://example.com/test.jpg",
            "title": "Test Image"
        },
        {
            "type": "list",
            "title": "Test List",
            "items": ["Item 1", "Item 2", "Item 3"]
        }
    ]

    print("Contenido de prueba:")
    print(f"- {len(test_content)} elementos")
    print()

    # Probar el template tag
    try:
        result = render_structured_content(test_content)
        print("Template tag ejecutado exitosamente")
        print(f"Longitud del resultado: {len(result)} caracteres")
        print()

        # Verificar elementos clave
        checks = {
            'lesson-heading-container': 'lesson-heading-container' in result,
            'lesson-text-container': 'lesson-text-container' in result,
            'lesson-image-container': 'lesson-image-container' in result,
            'lesson-list-container': 'lesson-list-container' in result,
            'lesson-image': 'class="lesson-image"' in result,
            'lesson-image-caption': 'lesson-image-caption' in result,
            'lesson-list-item': 'lesson-list-item' in result,
            'list-bullet': 'list-bullet' in result,
        }

        print("Verificaciones de elementos:")
        for check_name, passed in checks.items():
            status = "[OK]" if passed else "[FAIL]"
            print(f"  {status} {check_name}")

        print()
        print("Muestra del HTML generado (primeros 500 caracteres):")
        print("-" * 50)
        print(result[:500] + ("..." if len(result) > 500 else ""))

        # Contar elementos HTML
        div_count = result.count('<div')
        close_div_count = result.count('</div>')
        img_count = result.count('<img')
        ul_count = result.count('<ul>')
        li_count = result.count('<li>')

        print()
        print("Conteo de elementos HTML:")
        print(f"- Divs abiertos: {div_count}")
        print(f"- Divs cerrados: {close_div_count}")
        print(f"- Imagenes: {img_count}")
        print(f"- Listas: {ul_count}")
        print(f"- Items de lista: {li_count}")

        # Verificar balance de divs
        if div_count == close_div_count:
            print("[OK] Divs balanceados correctamente")
        else:
            print(f"[ERROR] Desbalance de divs: {div_count} abiertos, {close_div_count} cerrados")

    except Exception as e:
        print(f"[ERROR] Error en template tag: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 60)
    print("FIN DE LA PRUEBA")
    print("=" * 60)

if __name__ == '__main__':
    test_template_tag()