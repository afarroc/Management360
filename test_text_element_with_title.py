#!/usr/bin/env python
"""
Script para verificar el procesamiento completo de un elemento "text"
con "title" y "content" incluyendo saltos de línea \n?.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import render_structured_content

def test_text_element_with_title():
    """Prueba completa de elemento text con title y content"""

    print("=" * 100)
    print("PRUEBA: ELEMENTO TEXT COMPLETO CON TITLE Y CONTENT")
    print("=" * 100)

    # Elemento JSON completo como lo proporciona el usuario
    structured_content = [
        {
            "type": "text",
            "title": "¿Qué es el Álgebra?",
            "content": """El álgebra es una rama de las matemáticas que utiliza letras, símbolos y números para representar y resolver problemas. A diferencia de la aritmética que trabaja con números específicos, el álgebra nos permite trabajar con cantidades desconocidas o variables.

**Pensemos en el álgebra como un lenguaje matemático** que nos ayuda a:
? Resolver problemas del mundo real de manera general
? Encontrar patrones y relaciones
? Hacer predicciones basadas en datos
? Desarrollar el pensamiento lógico y abstracto"""
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
    print(f"Title: {element['title']}")
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
    has_container = '<div class="lesson-text-container">' in rendered_html
    has_subheading = '<h4 class="lesson-subheading">' in rendered_html
    has_content = '<div class="lesson-content">' in rendered_html
    print(f"   Contenedor lesson-text-container: {has_container}")
    print(f"   Subheading (h4) presente: {has_subheading}")
    print(f"   Contenedor lesson-content: {has_content}")

    # Verificar título
    print(f"\n2. TÍTULO:")
    title_in_html = element['title'] in rendered_html
    print(f"   Título presente en HTML: {title_in_html}")
    if title_in_html:
        print("   SUCCESS: Título renderizado correctamente")

    # Verificar párrafos
    p_count = rendered_html.count('<p>')
    print(f"\n3. PÁRRAFOS: {p_count}")
    if p_count >= 2:
        print("   SUCCESS: Múltiples párrafos detectados")

    # Verificar listas
    has_ul = '<ul>' in rendered_html
    has_li = '<li>' in rendered_html
    li_count = rendered_html.count('<li>') if has_li else 0
    print(f"\n4. LISTAS:")
    print(f"   Lista no ordenada presente: {has_ul}")
    print(f"   Items de lista presentes: {has_li}")
    print(f"   Número de items: {li_count}")

    if has_ul and has_li and li_count == 4:
        print("   SUCCESS: Lista completa con 4 items")
    else:
        print("   ERROR: Lista incompleta o incorrecta")

    # Verificar negritas
    has_strong = '<strong>' in rendered_html and '</strong>' in rendered_html
    print(f"\n5. NEGRITAS: {has_strong}")
    if has_strong:
        print("   SUCCESS: Negritas procesadas")

    # Verificar contenido específico
    print(f"\n6. CONTENIDO ESPECÍFICO:")
    expected_phrases = [
        "¿Qué es el Álgebra?",  # Título
        "El álgebra es una rama de las matemáticas",  # Primer párrafo
        "Pensemos en el álgebra como un lenguaje matemático",  # Texto con negritas
        "Resolver problemas del mundo real",  # Primer item de lista
        "Encontrar patrones y relaciones",  # Segundo item
        "Hacer predicciones basadas en datos",  # Tercer item
        "Desarrollar el pensamiento lógico"  # Cuarto item
    ]

    for phrase in expected_phrases:
        found = phrase in rendered_html
        status = "SUCCESS" if found else "ERROR"
        print(f"   {status}: '{phrase[:40]}...' encontrado")

    # Verificar específicamente el \n?
    print(f"\n7. VERIFICACIÓN ESPECÍFICA DE \\n?:")
    content_lines = element['content'].split('\n')
    question_lines = [i for i, line in enumerate(content_lines) if line.strip().startswith('?')]

    print(f"   Líneas que empiezan con ?: {question_lines}")
    print(f"   Número de items de lista detectados: {len(question_lines)}")

    if len(question_lines) == 4:
        print("   SUCCESS: Todas las líneas ? detectadas")
    else:
        print(f"   ERROR: Se esperaban 4 líneas ?, se encontraron {len(question_lines)}")

    # Verificar que cada línea ? se convirtió en <li>
    if li_count == len(question_lines):
        print("   SUCCESS: Cada línea ? se convirtió en item de lista")
    else:
        print(f"   ERROR: Desajuste entre líneas ? ({len(question_lines)}) y items HTML ({li_count})")

    # Verificar estructura completa
    print(f"\n8. ESTRUCTURA COMPLETA:")
    structure_checks = [
        has_container,  # Contenedor principal
        has_subheading,  # Título como h4
        has_content,  # Contenedor de contenido
        p_count >= 2,  # Al menos 2 párrafos
        has_ul,  # Lista presente
        has_li,  # Items presentes
        li_count == 4,  # 4 items
        has_strong,  # Negritas presentes
        title_in_html,  # Título presente
        len(question_lines) == 4,  # 4 líneas ?
        li_count == len(question_lines),  # Correspondencia 1:1
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
        print("El elemento text completo con title y content funciona perfectamente")
    else:
        print(f"ERROR: {total_checks - passed_checks} CRITERIOS FALLARON")
        print("Hay problemas con el procesamiento del elemento text")

    # Mostrar resumen específico
    print(f"\n" + "=" * 100)
    print("RESUMEN ESPECÍFICO:")
    print("=" * 100)

    print("ELEMENTO PROCESADO:")
    print("- Type: text")
    print(f"- Title: {element['title']}")
    print(f"- Content: {len(element['content'])} caracteres")
    print(f"- Lineas ?: {len(question_lines)}")
    print(f"- Items HTML: {li_count}")
    print(f"- Parrafos: {p_count}")
    print(f"- Negritas: {'Si' if has_strong else 'No'}")

    if passed_checks == total_checks:
        print("\nCONFIRMACION: El elemento text con title y content funciona perfectamente")
        print("- Titulo renderizado como h4 con clase lesson-subheading")
        print("- Contenido procesado con Markdown completo")
        print("- Saltos de linea \\n? convertidos en lista HTML")
        print("- Estructura HTML completa y semantica")
    else:
        print("\nPROBLEMAS DETECTADOS:")
        if not has_subheading:
            print("- Titulo no renderizado correctamente")
        if not has_ul or li_count != 4:
            print("- Lista no procesada correctamente")
        if not has_strong:
            print("- Negritas no aplicadas")
        if p_count < 2:
            print("- Parrafos no separados correctamente")

    print("=" * 100)

if __name__ == '__main__':
    test_text_element_with_title()