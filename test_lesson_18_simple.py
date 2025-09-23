#!/usr/bin/env python
"""
Script simple para verificar el renderizado de la leccion 18 sin caracteres Unicode.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import Lesson
from courses.templatetags.lesson_tags import render_structured_content
import json

def test_lesson_18_simple():
    """Prueba simple del renderizado de la leccion 18"""

    print("=" * 80)
    print("PRUEBA: RENDERIZADO DE LECCION 18")
    print("=" * 80)

    try:
        # Obtener la leccion 18
        lesson = Lesson.objects.get(id=18)
        print(f"[OK] Leccion encontrada: {lesson.title}")
        print(f"   Tipo: {lesson.lesson_type}")
        print(f"   Modulo: {lesson.module.title}")
        print(f"   Curso: {lesson.module.course.title}")
        print(f"   Tiene contenido estructurado: {bool(lesson.structured_content)}")

        if lesson.structured_content:
            print(f"\n[CONTENT] CONTENIDO ESTRUCTURADO:")
            print("-" * 40)

            try:
                if isinstance(lesson.structured_content, str):
                    structured_data = json.loads(lesson.structured_content)
                else:
                    structured_data = lesson.structured_content

                print(f"Numero de elementos: {len(structured_data)}")

                for i, element in enumerate(structured_data, 1):
                    print(f"\nElemento {i}:")
                    print(f"  Tipo: {element.get('type', 'N/A')}")
                    if element.get('title'):
                        print(f"  Titulo: {element['title'][:50]}...")
                    if element.get('content'):
                        content = str(element['content'])
                        content_preview = content[:100].replace('\n', ' ')
                        print(f"  Contenido: {content_preview}...")
                    if element.get('items'):
                        print(f"  Items: {len(element['items'])} elementos")

                print(f"\n[RENDERING] PROCESANDO CON TEMPLATE TAG:")
                print("-" * 40)

                # Procesar con el template tag
                rendered_html = render_structured_content(lesson.structured_content)
                print("[OK] Template tag ejecutado exitosamente")
                print(f"Longitud del HTML: {len(rendered_html)} caracteres")

                # Analisis basico
                print(f"\n[ANALYSIS] ANALISIS DEL HTML:")
                print("-" * 40)

                # Contar elementos
                containers = rendered_html.count('<div class="lesson-')
                images = rendered_html.count('<img')
                headings = rendered_html.count('<h')
                lists = rendered_html.count('<ul>') + rendered_html.count('<ol>')

                print(f"Contenedores lesson-*: {containers}")
                print(f"Imagenes: {images}")
                print(f"Encabezados: {headings}")
                print(f"Listas: {lists}")

                # Verificar clases especificas
                has_image_container = 'lesson-image-container' in rendered_html
                has_image_class = 'class="lesson-image"' in rendered_html
                has_alt = 'alt=' in rendered_html

                print(f"Tiene lesson-image-container: {has_image_container}")
                print(f"Tiene clase lesson-image: {has_image_class}")
                print(f"Tiene atributos alt: {has_alt}")

                # Mostrar muestra del HTML
                print(f"\n[SAMPLE] MUESTRA DEL HTML (primeros 300 caracteres):")
                print("-" * 40)
                print(rendered_html[:300] + "..." if len(rendered_html) > 300 else rendered_html)

                # Verificar problemas
                print(f"\n[CHECK] VERIFICACION:")
                print("-" * 40)

                problems = []
                open_divs = rendered_html.count('<div')
                close_divs = rendered_html.count('</div>')

                if open_divs != close_divs:
                    problems.append(f"Desbalance de divs: {open_divs} aperturas, {close_divs} cierres")

                if not has_image_container and images > 0:
                    problems.append("Imagenes sin contenedor lesson-image-container")

                if images > 0 and not has_image_class:
                    problems.append("Imagenes sin clase lesson-image")

                if images > 0 and not has_alt:
                    problems.append("Imagenes sin atributo alt")

                if problems:
                    print("PROBLEMAS ENCONTRADOS:")
                    for problem in problems:
                        print(f"  - {problem}")
                else:
                    print("[OK] No se encontraron problemas")

            except Exception as e:
                print(f"[ERROR] Error procesando: {e}")
                import traceback
                traceback.print_exc()

        else:
            print("[WARNING] La leccion no tiene contenido estructurado")

    except Lesson.DoesNotExist:
        print("[ERROR] Leccion 18 no encontrada")
    except Exception as e:
        print(f"[ERROR] Error general: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n" + "=" * 80)
    print("FIN DE LA PRUEBA")
    print("=" * 80)

if __name__ == '__main__':
    test_lesson_18_simple()