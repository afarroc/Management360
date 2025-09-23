#!/usr/bin/env python
"""
Script para verificar el procesamiento de un elemento "exercise" con negritas
y contenido específico proporcionado por el usuario.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import render_structured_content

def test_exercise_element_with_bold():
    """Prueba del elemento exercise con negritas y contenido específico"""

    print("=" * 100)
    print("PRUEBA: ELEMENTO EXERCISE CON NEGRITAS Y CONTENIDO ESPECÍFICO")
    print("=" * 100)

    # Elemento JSON con el contenido proporcionado por el usuario
    structured_content = [
        {
            "type": "exercise",
            "content": "**Ejercicio Interactivo: Identifica Variables vs Constantes**\n\nAnaliza las siguientes expresiones algebraicas y determina cuáles son variables y cuáles son constantes:\n\n1. En la expresión `3x + 5`, ¿qué representa `x` y qué representa `3`?\n2. En `y = 2z + 7`, identifica las variables y las constantes.\n3. ¿Cuál es la diferencia entre una variable y una constante?\n\n**Instrucciones**: Escribe tu respuesta para cada pregunta y explica tu razonamiento."
        }
    ]

    print("ELEMENTO JSON COMPLETO:")
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

    # Verificar que las negritas NO se procesan (comportamiento correcto para exercise)
    print(f"\n2. PROCESAMIENTO DE NEGRITAS:")
    has_strong = '<strong>' in rendered_html
    has_em = '<em>' in rendered_html
    print(f"   Negritas procesadas (<strong>): {has_strong}")
    print(f"   Itálicas procesadas (<em>): {has_em}")

    if not has_strong and not has_em:
        print("   SUCCESS: Negritas NO procesadas (comportamiento correcto para exercise)")
    else:
        print("   WARNING: Negritas procesadas (no esperado para exercise)")

    # Verificar contenido específico
    print(f"\n3. CONTENIDO ESPECÍFICO:")
    expected_phrases = [
        "**Ejercicio Interactivo: Identifica Variables vs Constantes**",  # Negritas literales
        "Analiza las siguientes expresiones algebraicas",
        "3x + 5",
        "y = 2z + 7",
        "diferencia entre una variable y una constante",
        "**Instrucciones**",  # Negritas literales
        "Escribe tu respuesta"
    ]

    for phrase in expected_phrases:
        found = phrase in rendered_html
        status = "SUCCESS" if found else "ERROR"
        print(f"   {status}: '{phrase[:50]}...' encontrado")

    # Verificar que el texto con negritas se mantiene literal
    print(f"\n4. NEGRITAS LITERALES:")
    bold_text_1 = "**Ejercicio Interactivo: Identifica Variables vs Constantes**"
    bold_text_2 = "**Instrucciones**"

    bold_1_found = bold_text_1 in rendered_html
    bold_2_found = bold_text_2 in rendered_html

    print(f"   '**Ejercicio Interactivo...**' literal: {bold_1_found}")
    print(f"   '**Instrucciones**' literal: {bold_2_found}")

    if bold_1_found and bold_2_found:
        print("   SUCCESS: Negritas mantenidas como texto literal")
    else:
        print("   ERROR: Negritas no encontradas como texto literal")

    # Verificar saltos de línea
    print(f"\n5. SALTOS DE LÍNEA:")
    content_p = rendered_html.split('<p class="lesson-exercise-content">')[1].split('</p>')[0]
    line_breaks = content_p.count('\n')
    print(f"   Saltos de línea en contenido: {line_breaks}")

    # Verificar párrafos implícitos (líneas vacías)
    empty_lines = content_p.count('\n\n')
    print(f"   Párrafos separados (\\n\\n): {empty_lines}")

    if line_breaks >= 6 and empty_lines >= 2:
        print("   SUCCESS: Saltos de línea correctamente preservados")
    else:
        print("   WARNING: Saltos de línea insuficientes")

    # Verificar estructura completa
    print(f"\n6. ESTRUCTURA COMPLETA:")
    structure_checks = [
        has_container,  # Contenedor principal
        has_header,  # Header presente
        has_icon,  # Icono presente
        has_title,  # Título presente
        has_content,  # Contenido presente
        not has_strong,  # Negritas NO procesadas
        not has_em,  # Itálicas NO procesadas
        bold_1_found,  # Negritas literales presentes
        bold_2_found,  # Negritas literales presentes
        line_breaks >= 6,  # Saltos de línea preservados
        "3x + 5" in rendered_html,  # Contenido específico
        "y = 2z + 7" in rendered_html,  # Contenido específico
    ]

    total_checks = len(structure_checks)
    passed_checks = sum(structure_checks)

    print(f"   Total de verificaciones: {total_checks}")
    print(f"   Verificaciones exitosas: {passed_checks}")
    print(f"   Tasa de éxito: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")

    # Resumen final
    print(f"\n" + "=" * 100)
    print("RESULTADO FINAL:")
    print("=" * 100)

    if passed_checks == total_checks:
        print("SUCCESS: TODOS LOS CRITERIOS CUMPLIDOS")
        print("El elemento exercise con negritas funciona perfectamente")
    else:
        print(f"ERROR: {total_checks - passed_checks} CRITERIOS FALLARON")
        print("Hay problemas con el procesamiento del elemento exercise con negritas")

    # Mostrar resumen específico
    print(f"\n" + "=" * 100)
    print("RESUMEN ESPECÍFICO:")
    print("=" * 100)

    print("ELEMENTO PROCESADO:")
    print("- Type: exercise")
    print(f"- Content: {len(element['content'])} caracteres")
    print("- Icono: bi-pencil-square (lápiz)")
    print("- Color: text-success (verde)")
    print("- Título: 'Ejercicio Práctico'")
    print("- Contenido: Texto plano CON negritas literales")
    print(f"- Saltos de línea: {line_breaks}")
    print(f"- Párrafos separados: {empty_lines}")

    if passed_checks == total_checks:
        print("\nCONFIRMACION: El elemento exercise con negritas funciona correctamente")
        print("- Estructura HTML completa y semántica")
        print("- Negritas mantenidas como texto literal (no procesadas)")
        print("- Saltos de línea preservados")
        print("- Contenido específico correctamente incluido")
    else:
        print("\nPROBLEMAS DETECTADOS:")
        if has_strong:
            print("- Negritas procesadas cuando no deberían")
        if not bold_1_found:
            print("- Negritas literales faltantes")
        if line_breaks < 6:
            print("- Saltos de línea insuficientes")

    print("=" * 100)

if __name__ == '__main__':
    test_exercise_element_with_bold()