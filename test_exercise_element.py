#!/usr/bin/env python
"""
Script para verificar el procesamiento del tipo "exercise" en contenido estructurado.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import render_structured_content

def test_exercise_element():
    """Prueba del elemento exercise en contenido estructurado"""

    print("=" * 100)
    print("PRUEBA: ELEMENTO EXERCISE EN CONTENIDO ESTRUCTURADO")
    print("=" * 100)

    # Elemento JSON de tipo exercise
    structured_content = [
        {
            "type": "exercise",
            "content": "Resuelve los siguientes problemas de álgebra básica:\n\n1. Simplifica la expresión: 2x + 3x - 5x\n2. Resuelve la ecuación: 2(x + 3) = 10\n3. Factoriza: x² - 9\n\n**Pista**: Recuerda las propiedades de los números reales y las reglas de los exponentes."
        }
    ]

    print("ELEMENTO JSON:")
    print("=" * 50)
    import json
    print(json.dumps(structured_content, indent=2, ensure_ascii=False))
    print()

    print("DETALLES DEL ELEMENTO:")
    print("=" * 50)
    element = structured_content[0]
    print(f"Type: {element['type']}")
    print(f"Content length: {len(element['content'])} characters")
    print()

    print("CONTENT FORMATEADO:")
    print("=" * 50)
    print(element['content'])
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
    has_container = '<div class="lesson-exercise-container">' in rendered_html
    has_header = '<div class="lesson-exercise-header">' in rendered_html
    has_icon = '<i class="bi bi-pencil-square text-success me-2"></i>' in rendered_html
    has_title = '<span class="exercise-title">Ejercicio Práctico</span>' in rendered_html
    has_content = '<p class="lesson-exercise-content">' in rendered_html
    print(f"   Contenedor lesson-exercise-container: {has_container}")
    print(f"   Header lesson-exercise-header: {has_header}")
    print(f"   Icono bi-pencil-square: {has_icon}")
    print(f"   Título 'Ejercicio Práctico': {has_title}")
    print(f"   Contenido lesson-exercise-content: {has_content}")

    # Verificar contenido específico
    print(f"\n2. CONTENIDO ESPECÍFICO:")
    expected_phrases = [
        "Resuelve los siguientes problemas",
        "2x + 3x - 5x",
        "2(x + 3) = 10",
        "x² - 9",
        "Pista",
        "propiedades de los números reales"
    ]

    for phrase in expected_phrases:
        found = phrase in rendered_html
        status = "SUCCESS" if found else "ERROR"
        print(f"   {status}: '{phrase[:40]}...' encontrado")

    # Verificar que el contenido se mantiene sin procesar Markdown
    print(f"\n3. PROCESAMIENTO DE CONTENIDO:")
    has_strong = '<strong>' in rendered_html
    has_ul = '<ul>' in rendered_html
    has_li = '<li>' in rendered_html
    print(f"   Negritas procesadas: {has_strong}")
    print(f"   Lista HTML generada: {has_ul}")
    print(f"   Items de lista: {has_li}")

    if not has_strong and not has_ul and not has_li:
        print("   SUCCESS: Contenido NO procesado como Markdown (comportamiento correcto)")
    else:
        print("   WARNING: Contenido procesado como Markdown (puede no ser deseado)")

    # Verificar estructura completa
    print(f"\n4. ESTRUCTURA COMPLETA:")
    structure_checks = [
        has_container,  # Contenedor principal
        has_header,  # Header presente
        has_icon,  # Icono presente
        has_title,  # Título presente
        has_content,  # Contenido presente
        "Resuelve los siguientes problemas" in rendered_html,  # Contenido específico
        "2x + 3x - 5x" in rendered_html,  # Ejemplo matemático
        "Pista" in rendered_html,  # Texto de pista
    ]

    total_checks = len(structure_checks)
    passed_checks = sum(structure_checks)

    print(f"   Total de verificaciones: {total_checks}")
    print(f"   Verificaciones exitosas: {passed_checks}")
    print(f"   Tasa de éxito: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")

    # Verificar que el contenido se muestra como texto plano
    print(f"\n5. CONTENIDO COMO TEXTO PLANO:")
    content_p = rendered_html.split('<p class="lesson-exercise-content">')[1].split('</p>')[0]
    print(f"   Contenido extraído: {repr(content_p)}")

    # Verificar saltos de línea
    line_breaks = content_p.count('\n')
    print(f"   Saltos de línea en contenido: {line_breaks}")

    if line_breaks > 0:
        print("   SUCCESS: Saltos de línea preservados")
    else:
        print("   WARNING: Saltos de línea no preservados")

    # Resumen final
    print(f"\n" + "=" * 100)
    print("RESULTADO FINAL:")
    print("=" * 100)

    if passed_checks == total_checks:
        print("SUCCESS: TODOS LOS CRITERIOS CUMPLIDOS")
        print("El elemento exercise funciona perfectamente")
    else:
        print(f"ERROR: {total_checks - passed_checks} CRITERIOS FALLARON")
        print("Hay problemas con el procesamiento del elemento exercise")

    # Mostrar resumen específico
    print(f"\n" + "=" * 100)
    print("RESUMEN ESPECÍFICO DEL ELEMENTO EXERCISE:")
    print("=" * 100)

    print("ELEMENTO PROCESADO:")
    print("- Type: exercise")
    print(f"- Content: {len(element['content'])} caracteres")
    print("- Icono: bi-pencil-square (lápiz)")
    print("- Color: text-success (verde)")
    print("- Título: 'Ejercicio Práctico'")
    print("- Contenido: Texto plano sin procesar Markdown")

    if passed_checks == total_checks:
        print("\nCONFIRMACION: El elemento exercise funciona correctamente")
        print("- Estructura HTML completa y semántica")
        print("- Contenido mostrado como texto plano")
        print("- Saltos de línea preservados")
        print("- Icono y título apropiados para ejercicios")
    else:
        print("\nPROBLEMAS DETECTADOS:")
        if not has_container:
            print("- Contenedor principal faltante")
        if not has_icon:
            print("- Icono faltante")
        if not has_title:
            print("- Título faltante")
        if "Resuelve los siguientes problemas" not in rendered_html:
            print("- Contenido específico faltante")

    print("=" * 100)

if __name__ == '__main__':
    test_exercise_element()