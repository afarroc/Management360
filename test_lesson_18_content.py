#!/usr/bin/env python
"""
Script para extraer y mostrar el contenido renderizado de la leccion 18.
"""
import os
import django
import re

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import Lesson
from courses.templatetags.lesson_tags import render_structured_content

def test_lesson_18_content():
    """Extrae y analiza el contenido de la leccion 18"""

    print("=" * 80)
    print("ANALISIS DEL CONTENIDO DE LA LECCION 18")
    print("=" * 80)

    try:
        # Obtener la leccion 18
        lesson = Lesson.objects.get(id=18)
        print(f"Leccion: {lesson.title}")
        print(f"Tipo: {lesson.lesson_type}")
        print(f"Modulo: {lesson.module.title}")
        print(f"Curso: {lesson.module.course.title}")
        print()

        if lesson.structured_content:
            print("PROCESANDO CONTENIDO ESTRUCTURADO...")
            print("-" * 40)

            # Procesar con el template tag
            rendered_html = render_structured_content(lesson.structured_content)

            print(f"HTML renderizado exitosamente: {len(rendered_html)} caracteres")
            print()

            # Analisis detallado
            print("ANALISIS DE CLASES CSS:")
            print("-" * 30)

            css_classes = [
                'lesson-heading-container',
                'lesson-text-container',
                'lesson-list-container',
                'lesson-image-container',
                'lesson-video-container',
                'lesson-exercise-container',
                'lesson-heading-main',
                'lesson-subheading',
                'lesson-content',
                'lesson-image',
                'lesson-image-caption',
                'lesson-list-title',
                'lesson-list-item',
                'list-bullet'
            ]

            found_classes = {}
            for css_class in css_classes:
                count = rendered_html.count(f'class="{css_class}"')
                if count > 0:
                    found_classes[css_class] = count
                    print(f"[OK] {css_class}: {count}")

            print()
            print("CLASES NO ENCONTRADAS:")
            missing_classes = [cls for cls in css_classes if cls not in found_classes]
            if missing_classes:
                for cls in missing_classes:
                    print(f"[MISSING] {cls}")
            else:
                print("Todas las clases principales encontradas")

            print()
            print("VERIFICACION DE ESTRUCTURA HTML:")
            print("-" * 35)

            # Verificar estructura basica
            checks = {
                'Divs abiertos': rendered_html.count('<div'),
                'Divs cerrados': rendered_html.count('</div>'),
                'Imagenes': rendered_html.count('<img'),
                'Encabezados h2': rendered_html.count('<h2'),
                'Encabezados h4': rendered_html.count('<h4'),
                'Listas ul': rendered_html.count('<ul>'),
                'Items li': rendered_html.count('<li>'),
                'Parrafos p': rendered_html.count('<p>'),
                'Iconos bi': rendered_html.count('bi bi-'),
            }

            for check_name, count in checks.items():
                print(f"{check_name}: {count}")

            # Verificar balance de divs
            divs_open = rendered_html.count('<div')
            divs_close = rendered_html.count('</div>')
            if divs_open == divs_close:
                print(f"[OK] Divs balanceados: {divs_open}")
            else:
                print(f"[ERROR] Desbalance de divs: {divs_open} abiertos, {divs_close} cerrados")

            print()
            print("MUESTRA DEL HTML (limpio, primeros 1000 caracteres):")
            print("-" * 55)

            # Limpiar el HTML para mostrar (remover entidades HTML problemáticas)
            clean_html = re.sub(r'&[a-zA-Z0-9#]+;', '[ENTITY]', rendered_html)
            print(clean_html[:1000] + ("..." if len(clean_html) > 1000 else ""))

            print()
            print("RESUMEN FINAL:")
            print("-" * 15)
            print(f"Total de clases CSS encontradas: {len(found_classes)}")
            print(f"Total de elementos HTML: {sum(checks.values())}")
            print(f"Contenido procesado correctamente: {'SI' if divs_open == divs_close else 'NO'}")

            if found_classes and divs_open == divs_close:
                print("[SUCCESS] El contenido se renderiza correctamente")
            else:
                print("[WARNING] Hay problemas en el renderizado")

        else:
            print("La leccion no tiene contenido estructurado")

    except Lesson.DoesNotExist:
        print("[ERROR] Leccion 18 no encontrada")
    except Exception as e:
        print(f"[ERROR] Error general: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)

if __name__ == '__main__':
    test_lesson_18_content()