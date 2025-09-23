#!/usr/bin/env python
"""
Script para verificar que los saltos de línea (\n?) funcionen correctamente
en elementos de contenido estructurado de tipo "content" (text).
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import render_structured_content

def test_structured_content_line_breaks():
    """Prueba de saltos de línea en contenido estructurado JSON"""

    print("=" * 100)
    print("PRUEBA: SALTOS DE LÍNEA \\n? EN CONTENIDO ESTRUCTURADO")
    print("=" * 100)

    # JSON con el contenido exacto del usuario (tipo "content" que es "text")
    structured_content = [
        {
            "type": "text",
            "content": """El álgebra es una rama de las matemáticas que utiliza letras, símbolos y números para representar y resolver problemas. A diferencia de la aritmética que trabaja con números específicos, el álgebra nos permite trabajar con cantidades desconocidas o variables.

**Pensemos en el álgebra como un lenguaje matemático** que nos ayuda a:
? Resolver problemas del mundo real de manera general
? Encontrar patrones y relaciones
? Hacer predicciones basadas en datos
? Desarrollar el pensamiento lógico y abstracto"""
        }
    ]

    print("CONTENIDO JSON ESTRUCTURADO:")
    print("=" * 50)
    import json
    print(json.dumps(structured_content, indent=2, ensure_ascii=False))
    print()

    print("CONTENIDO TEXTO EXTRAÍDO:")
    print("=" * 50)
    content_text = structured_content[0]["content"]
    print(repr(content_text))
    print()
    print("CONTENIDO FORMATEADO:")
    print("=" * 50)
    print(content_text)
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
    has_div = '<div class="lesson-text-container">' in rendered_html
    has_content = '<div class="lesson-content">' in rendered_html
    print(f"   Contenedor lesson-text-container: {has_div}")
    print(f"   Contenedor lesson-content: {has_content}")

    # Verificar párrafos
    p_count = rendered_html.count('<p>')
    print(f"\n2. PÁRRAFOS: {p_count}")
    if p_count >= 2:
        print("   SUCCESS: Múltiples párrafos detectados")

    # Verificar listas
    has_ul = '<ul>' in rendered_html
    has_li = '<li>' in rendered_html
    li_count = rendered_html.count('<li>') if has_li else 0
    print(f"\n3. LISTAS:")
    print(f"   Lista no ordenada presente: {has_ul}")
    print(f"   Items de lista presentes: {has_li}")
    print(f"   Número de items: {li_count}")

    if has_ul and has_li and li_count == 4:
        print("   SUCCESS: Lista completa con 4 items")
    else:
        print("   ERROR: Lista incompleta o incorrecta")

    # Verificar negritas
    has_strong = '<strong>' in rendered_html and '</strong>' in rendered_html
    print(f"\n4. NEGRITAS: {has_strong}")
    if has_strong:
        print("   SUCCESS: Negritas procesadas")

    # Verificar contenido específico
    print(f"\n5. CONTENIDO ESPECÍFICO:")
    expected_phrases = [
        "El álgebra es una rama de las matemáticas",
        "Pensemos en el álgebra como un lenguaje matemático",
        "Resolver problemas del mundo real",
        "Encontrar patrones y relaciones",
        "Hacer predicciones basadas en datos",
        "Desarrollar el pensamiento lógico"
    ]

    for phrase in expected_phrases:
        found = phrase in rendered_html
        status = "SUCCESS" if found else "ERROR"
        print(f"   {status}: '{phrase[:40]}...' encontrado")

    # Verificar específicamente el \n?
    print(f"\n6. VERIFICACIÓN ESPECÍFICA DE \\n?:")
    lines = content_text.split('\n')
    question_lines = [i for i, line in enumerate(lines) if line.strip().startswith('?')]

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

    # Mostrar el resultado final
    print(f"\n" + "=" * 100)
    print("RESULTADO FINAL:")
    print("=" * 100)

    success_criteria = [
        has_div,  # Contenedor presente
        has_content,  # Contenido presente
        p_count >= 2,  # Al menos 2 párrafos
        has_ul,  # Lista presente
        has_li,  # Items presentes
        li_count == 4,  # 4 items
        has_strong,  # Negritas presentes
        len(question_lines) == 4,  # 4 líneas ?
        li_count == len(question_lines),  # Correspondencia 1:1
    ]

    total_criteria = len(success_criteria)
    passed_criteria = sum(success_criteria)

    print(f"Total de criterios: {total_criteria}")
    print(f"Criterios cumplidos: {passed_criteria}")
    print(f"Tasa de éxito: {passed_criteria}/{total_criteria} ({passed_criteria/total_criteria*100:.1f}%)")

    if passed_criteria == total_criteria:
        print("\nSUCCESS: TODOS LOS CRITERIOS CUMPLIDOS")
        print("Los saltos de línea \\n? funcionan perfectamente en contenido estructurado")
    else:
        print(f"\nERROR: {total_criteria - passed_criteria} CRITERIOS FALLARON")
        print("Hay problemas con el procesamiento de \\n? en contenido estructurado")

    # Resumen específico
    print(f"\n" + "=" * 100)
    print("RESUMEN ESPECÍFICO DE \\n?:")
    print("=" * 100)

    if li_count == 4 and len(question_lines) == 4:
        print("CONFIRMACION: Los saltos de línea \\n? SI se aplican correctamente")
        print("   - 4 líneas con ? detectadas en el texto original")
        print("   - 4 items <li> generados en el HTML")
        print("   - Procesamiento completo y correcto")
    else:
        print("PROBLEMA: Los saltos de línea \\n? NO se aplican correctamente")
        print(f"   - Líneas ? encontradas: {len(question_lines)} (esperado: 4)")
        print(f"   - Items HTML generados: {li_count} (esperado: 4)")

    print("=" * 100)

if __name__ == '__main__':
    test_structured_content_line_breaks()