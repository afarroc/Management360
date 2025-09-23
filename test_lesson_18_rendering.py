#!/usr/bin/env python
"""
Script para verificar el renderizado específico de la lección 18 y diagnosticar problemas.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import Lesson
from courses.templatetags.lesson_tags import render_structured_content
import json

def test_lesson_18_rendering():
    """Prueba específica del renderizado de la lección 18"""

    print("=" * 100)
    print("PRUEBA: RENDERIZADO ESPECÍFICO DE LECCIÓN 18")
    print("=" * 100)

    try:
        # Obtener la lección 18
        lesson = Lesson.objects.get(id=18)
        print(f"[OK] Leccion encontrada: {lesson.title}")
        print(f"   Tipo: {lesson.lesson_type}")
        print(f"   Modulo: {lesson.module.title}")
        print(f"   Curso: {lesson.module.course.title}")
        print(f"   Tiene contenido estructurado: {bool(lesson.structured_content)}")

        if lesson.structured_content:
            print(f"\n[CONTENT] CONTENIDO ESTRUCTURADO (tipo: {type(lesson.structured_content)}):")
            print("-" * 50)

            # Mostrar el contenido estructurado de manera segura
            try:
                if isinstance(lesson.structured_content, str):
                    structured_data = json.loads(lesson.structured_content)
                else:
                    structured_data = lesson.structured_content

                print(f"Número de elementos: {len(structured_data)}")

                for i, element in enumerate(structured_data, 1):
                    print(f"\nElemento {i}:")
                    print(f"  Tipo: {element.get('type', 'N/A')}")
                    print(f"  Título: {element.get('title', 'N/A')[:50]}...")
                    if element.get('content'):
                        content_preview = element['content'][:100].replace('\n', ' ')
                        print(f"  Contenido: {content_preview}...")
                    if element.get('items'):
                        print(f"  Items: {len(element['items'])} elementos")

            except Exception as e:
                print(f"[ERROR] Error procesando contenido estructurado: {e}")

            print(f"\n[PROCESSING] PROCESANDO CON TEMPLATE TAG:")
            print("-" * 50)

            try:
                # Procesar con el template tag
                rendered_html = render_structured_content(lesson.structured_content)
                print("[OK] Template tag ejecutado exitosamente")
                print(f"Longitud del HTML renderizado: {len(rendered_html)} caracteres")

                # Análisis del HTML renderizado
                print(f"\n[ANALYSIS] ANALISIS DEL HTML RENDERIZADO:")
                print("-" * 50)

                # Contar diferentes tipos de elementos
                element_counts = {
                    'lesson-heading-container': rendered_html.count('<div class="lesson-heading-container">'),
                    'lesson-text-container': rendered_html.count('<div class="lesson-text-container">'),
                    'lesson-list-container': rendered_html.count('<div class="lesson-list-container">'),
                    'lesson-image-container': rendered_html.count('<div class="lesson-image-container">'),
                    'lesson-exercise-container': rendered_html.count('<div class="lesson-exercise-container">'),
                    'lesson-video-container': rendered_html.count('<div class="lesson-video-container">'),
                    'lesson-file': rendered_html.count('<div class="lesson-file">'),
                }

                print("Elementos encontrados:")
                for element_type, count in element_counts.items():
                    if count > 0:
                        print(f"  [OK] {element_type}: {count}")

                # Verificar si hay elementos sin clases esperadas
                if '<div class="' not in rendered_html:
                    print("[WARNING] ADVERTENCIA: No se encontraron clases CSS en el HTML renderizado")

                # Mostrar una muestra del HTML (primeros 500 caracteres)
                print(f"\n[SAMPLE] MUESTRA DEL HTML RENDERIZADO (primeros 500 caracteres):")
                print("-" * 50)
                print(rendered_html[:500] + "..." if len(rendered_html) > 500 else rendered_html)

                # Verificar problemas específicos
                print(f"\n[CHECK] VERIFICACION DE PROBLEMAS:")
                print("-" * 50)

                problems = []

                # Verificar si hay elementos sin cerrar
                open_divs = rendered_html.count('<div')
                close_divs = rendered_html.count('</div>')
                if open_divs != close_divs:
                    problems.append(f"[ERROR] Desbalance de divs: {open_divs} aperturas, {close_divs} cierres")

                # Verificar caracteres especiales
                if '&' in rendered_html and ';' not in rendered_html:
                    problems.append("[WARNING] Posibles entidades HTML sin codificar")

                # Verificar si hay clases CSS esperadas
                expected_classes = ['lesson-heading-container', 'lesson-text-container', 'lesson-image-container']
                found_classes = [cls for cls in expected_classes if f'class="{cls}"' in rendered_html]
                missing_classes = [cls for cls in expected_classes if f'class="{cls}"' not in rendered_html]

                if missing_classes:
                    problems.append(f"[WARNING] Clases CSS faltantes: {missing_classes}")

                if found_classes:
                    print(f"[OK] Clases CSS encontradas: {found_classes}")

                # Verificar imágenes específicamente
                if 'lesson-image-container' in rendered_html:
                    img_tags = rendered_html.count('<img')
                    alt_attrs = rendered_html.count('alt=')
                    print(f"[OK] Imagenes encontradas: {img_tags} (con alt: {alt_attrs})")

                    # Verificar si las imágenes tienen las clases correctas
                    if 'class="lesson-image"' in rendered_html:
                        print("[OK] Imagenes con clase lesson-image aplicada")
                    else:
                        problems.append("[WARNING] Imagenes sin clase lesson-image")

                if not problems:
                    print("[OK] No se encontraron problemas evidentes")
                else:
                    print("Problemas encontrados:")
                    for problem in problems:
                        print(f"  {problem}")

            except Exception as e:
                print(f"[ERROR] Error procesando template tag: {e}")
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

    print(f"\n" + "=" * 100)
    print("FIN DE LA PRUEBA")
    print("=" * 100)

if __name__ == '__main__':
    test_lesson_18_rendering()