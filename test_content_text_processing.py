#!/usr/bin/env python
"""
Script para verificar el procesamiento de saltos de línea en elementos de tipo "text"
con el contenido específico proporcionado por el usuario.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import process_markdown

def test_content_text_processing():
    """Prueba específica del procesamiento de contenido de texto con saltos de línea"""

    print("=" * 100)
    print("PRUEBA: PROCESAMIENTO DE CONTENIDO TEXTO CON SALTOS DE LÍNEA")
    print("=" * 100)

    # Contenido específico proporcionado por el usuario
    content_text = """El álgebra es una rama de las matemáticas que utiliza letras, símbolos y números para representar y resolver problemas. A diferencia de la aritmética que trabaja con números específicos, el álgebra nos permite trabajar con cantidades desconocidas o variables.

**Pensemos en el álgebra como un lenguaje matemático** que nos ayuda a:
? Resolver problemas del mundo real de manera general
? Encontrar patrones y relaciones
? Hacer predicciones basadas en datos
? Desarrollar el pensamiento lógico y abstracto"""

    print("Contenido original:")
    print("=" * 50)
    print(repr(content_text))
    print()
    print("Contenido formateado para lectura:")
    print("=" * 50)
    print(content_text)
    print()

    # Procesar con Markdown
    processed_html = process_markdown(content_text)

    print("HTML PROCESADO:")
    print("=" * 50)
    print(processed_html)
    print()

    # Análisis detallado
    print("ANÁLISIS DETALLADO:")
    print("-" * 30)

    # Verificar párrafos
    p_count = processed_html.count('<p>')
    print(f"1. PÁRRAFOS ENCONTRADOS: {p_count}")
    if p_count >= 2:
        print("   SUCCESS: Múltiples párrafos detectados correctamente")
    else:
        print("   INFO: Número de párrafos menor al esperado")

    # Mostrar contenido de párrafos
    import re
    para_matches = re.findall(r'<p>(.*?)</p>', processed_html, re.DOTALL)
    for i, para in enumerate(para_matches, 1):
        clean_para = para.replace('<strong>', '').replace('</strong>', '').strip()
        print(f"   Párrafo {i}: {clean_para[:80]}{'...' if len(clean_para) > 80 else ''}")
    print()

    # Verificar negritas
    print("2. NEGRITAS:")
    if '<strong>' in processed_html and '</strong>' in processed_html:
        print("   SUCCESS: Negritas procesadas correctamente")
        # Extraer el texto en negritas
        import re
        bold_matches = re.findall(r'<strong>(.*?)</strong>', processed_html)
        for match in bold_matches:
            print(f"   Texto en negrita: '{match}'")
    else:
        print("   ERROR: Negritas no procesadas")
    print()

    # Verificar listas
    print("3. LISTAS:")
    if '<ul>' in processed_html and '<li>' in processed_html:
        print("   SUCCESS: Lista no ordenada creada")
        li_count = processed_html.count('<li>')
        print(f"   Items en lista: {li_count}")

        # Extraer items de lista
        import re
        li_matches = re.findall(r'<li>(.*?)</li>', processed_html)
        for i, item in enumerate(li_matches, 1):
            print(f"   Item {i}: {item}")
    else:
        print("   ERROR: Lista no creada")
    print()

    # Verificar saltos de línea
    print("4. SALTOS DE LÍNEA:")
    lines = processed_html.split('\n')
    print(f"   Total de líneas en HTML: {len(lines)}")

    # Verificar que los párrafos estén separados correctamente
    if '<p>' in processed_html and '</p>' in processed_html:
        print("   SUCCESS: Párrafos correctamente separados")
    else:
        print("   ERROR: Párrafos no separados correctamente")
    print()

    # Verificar estructura general
    print("5. ESTRUCTURA GENERAL:")
    checks = [
        ('<p>', 'Inicio de párrafo'),
        ('</p>', 'Fin de párrafo'),
        ('<ul>', 'Inicio de lista'),
        ('</ul>', 'Fin de lista'),
        ('<strong>', 'Inicio de negrita'),
        ('</strong>', 'Fin de negrita'),
    ]

    for tag, description in checks:
        if tag in processed_html:
            print(f"   SUCCESS: {description} presente")
        else:
            print(f"   ERROR: {description} faltante")
    print()

    # Verificar contenido específico
    print("6. CONTENIDO ESPECÍFICO:")
    expected_texts = [
        "El álgebra es una rama de las matemáticas",
        "Pensemos en el álgebra como un lenguaje matemático",
        "Resolver problemas del mundo real",
        "Encontrar patrones y relaciones",
        "Hacer predicciones basadas en datos",
        "Desarrollar el pensamiento lógico"
    ]

    for text in expected_texts:
        if text in processed_html:
            print(f"   SUCCESS: Contenido encontrado: '{text[:50]}...'")
        else:
            print(f"   ERROR: Contenido faltante: '{text[:50]}...'")
    print()

    # Simulación de cómo se vería en el template
    print("7. SIMULACIÓN EN TEMPLATE:")
    print("=" * 30)
    template_simulation = f"""
<div class="lesson-text-container">
  <div class="lesson-content">
    {processed_html}
  </div>
</div>
"""
    print(template_simulation)

    # Resumen final
    print("\n" + "=" * 100)
    print("RESUMEN FINAL:")
    print("=" * 100)

    success_count = 0
    total_checks = 0

    # Checks básicos
    basic_checks = [
        p_count >= 2,  # Al menos 2 párrafos
        '<strong>' in processed_html,
        '<ul>' in processed_html,
        '<li>' in processed_html,
        'El álgebra es una rama' in processed_html,
        'Pensemos en el álgebra' in processed_html,
    ]

    total_checks += len(basic_checks)
    success_count += sum(basic_checks)

    print(f"Total de verificaciones: {total_checks}")
    print(f"Verificaciones exitosas: {success_count}")
    print(f"Tasa de éxito: {success_count}/{total_checks} ({success_count/total_checks*100:.1f}%)")

    if success_count == total_checks:
        print("\nSUCCESS: TODAS LAS VERIFICACIONES PASARON")
        print("El contenido de texto con saltos de línea se procesa correctamente!")
    else:
        print(f"\nERROR: {total_checks - success_count} VERIFICACIONES FALLARON")
        print("Revisa el procesamiento de saltos de línea en contenido de texto")

    print("=" * 100)

if __name__ == '__main__':
    test_content_text_processing()