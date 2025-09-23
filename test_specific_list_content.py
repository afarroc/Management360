#!/usr/bin/env python
"""
Script específico para probar el contenido JSON exacto proporcionado por el usuario
para verificar el renderizado de listas con elementos de texto formateado.
"""
import os
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import render_structured_content

def test_specific_list_content():
    """Prueba específica del contenido JSON proporcionado por el usuario"""

    print("=" * 100)
    print("PRUEBA ESPECÍFICA: CONTENIDO LIST CON ELEMENTOS FORMATEADOS")
    print("=" * 100)

    # Contenido JSON exacto proporcionado por el usuario
    structured_content = [
        {
            "type": "heading",
            "title": "¿Por qué es Importante el Álgebra en la Vida Diaria?"
        },
        {
            "type": "list",
            "title": "Aplicaciones Prácticas del Álgebra",
            "items": [
                "**Finanzas y Economía**: Calcular intereses, presupuestos, inversiones y análisis de costos",
                "**Ingeniería y Tecnología**: Diseño de estructuras, programación, algoritmos y modelado matemático",
                "**Ciencias**: Física, química, biología - modelar fenómenos naturales y experimentos",
                "**Medicina**: Dosificación de medicamentos, análisis estadístico de tratamientos",
                "**Arquitectura**: Cálculos estructurales, diseño de espacios, proporciones",
                "**Cocina**: Recetas, conversiones de medidas, planificación de menús",
                "**Deportes**: Estadísticas, probabilidades, optimización de rendimiento",
                "**Navegación GPS**: Cálculos de rutas, coordenadas, distancias"
            ]
        }
    ]

    print("Contenido JSON a probar:")
    print(json.dumps(structured_content, indent=2, ensure_ascii=False))
    print()

    # Renderizar el contenido
    rendered_html = render_structured_content(structured_content)

    print("HTML RENDERIZADO:")
    print("=" * 100)
    # Evitar problemas de codificación imprimiendo solo una parte o usando repr
    try:
        print(rendered_html[:2000] + "..." if len(rendered_html) > 2000 else rendered_html)
    except UnicodeEncodeError:
        print("[Contenido HTML generado - caracteres especiales omitidos para compatibilidad de consola]")
        print(f"Longitud total: {len(rendered_html)} caracteres")
    print("=" * 100)

    # Análisis detallado
    print("\nANÁLISIS DETALLADO:")
    print("-" * 50)

    # Verificar el encabezado
    print("1. ENCABEZADO:")
    if '<h2 class="lesson-heading-main">' in rendered_html and '¿Por qué es Importante el Álgebra en la Vida Diaria?' in rendered_html:
        print("   SUCCESS: Encabezado renderizado correctamente")
    else:
        print("   ERROR: Encabezado no encontrado")

    # Verificar el título de la lista
    print("\n2. TITULO DE LA LISTA:")
    if 'Aplicaciones Prácticas del Álgebra' in rendered_html:
        print("   SUCCESS: Titulo de lista renderizado correctamente")
    else:
        print("   ERROR: Titulo de lista no encontrado")

    # Verificar la estructura de la lista
    print("\n3. ESTRUCTURA DE LA LISTA:")
    checks = [
        ('<ul class="lesson-list">', 'Lista no ordenada inicia'),
        ('</ul>', 'Lista no ordenada termina'),
        ('<li class="lesson-list-item">', 'Items de lista presentes'),
        ('</li>', 'Items de lista cerrados'),
    ]

    for tag, description in checks:
        if tag in rendered_html:
            print(f"   SUCCESS: {description}")
        else:
            print(f"   ERROR: {description} - FALTA {tag}")

    # Contar items de lista
    li_count = rendered_html.count('<li class="lesson-list-item">')
    print(f"\n4. CONTEO DE ITEMS:")
    print(f"   - Items encontrados: {li_count}")
    if li_count == 8:
        print("   SUCCESS: Numero correcto de items (8)")
    else:
        print(f"   ERROR: Numero incorrecto de items (esperado: 8, encontrado: {li_count})")

    # Verificar negritas en cada item
    print("\n5. NEGRITAS EN ITEMS:")
    expected_bold_texts = [
        "Finanzas y Economía",
        "Ingeniería y Tecnología",
        "Ciencias",
        "Medicina",
        "Arquitectura",
        "Cocina",
        "Deportes",
        "Navegación GPS"
    ]

    for bold_text in expected_bold_texts:
        if f'<strong>{bold_text}</strong>' in rendered_html:
            print(f"   SUCCESS: Negrita encontrada: {bold_text}")
        else:
            print(f"   ERROR: Negrita faltante: {bold_text}")

    # Verificar contenido completo de items
    print("\n6. CONTENIDO COMPLETO DE ITEMS:")
    expected_contents = [
        "Calcular intereses, presupuestos, inversiones y análisis de costos",
        "Diseño de estructuras, programación, algoritmos y modelado matemático",
        "Física, química, biología - modelar fenómenos naturales y experimentos",
        "Dosificación de medicamentos, análisis estadístico de tratamientos",
        "Cálculos estructurales, diseño de espacios, proporciones",
        "Recetas, conversiones de medidas, planificación de menús",
        "Estadísticas, probabilidades, optimización de rendimiento",
        "Cálculos de rutas, coordenadas, distancias"
    ]

    for content in expected_contents:
        if content in rendered_html:
            print(f"   SUCCESS: Contenido encontrado: {content[:50]}...")
        else:
            print(f"   ERROR: Contenido faltante: {content[:50]}...")

    # Verificar formato visual
    print("\n7. FORMATO VISUAL:")
    visual_checks = [
        ('class="lesson-list-container"', "Contenedor de lista"),
        ('class="lesson-list-title"', "Titulo de lista con clase"),
        ('class="lesson-list"', "Lista con clase"),
        ('class="list-bullet"', "Vinetas de lista"),
    ]

    for selector, description in visual_checks:
        if selector in rendered_html:
            print(f"   SUCCESS: {description} presente")
        else:
            print(f"   ERROR: {description} faltante")

    # Mostrar un item de ejemplo completo
    print("\n8. EJEMPLO DE ITEM COMPLETO:")
    # Verificar que al menos un item tenga la estructura correcta con negrita
    if ('<li class="lesson-list-item">' in rendered_html and
        '<span class="list-bullet">' in rendered_html and
        '<strong>Finanzas y Economía</strong>' in rendered_html and
        'Calcular intereses, presupuestos' in rendered_html):
        print("   SUCCESS: Item de ejemplo renderizado correctamente con estructura completa")
    else:
        print("   ERROR: Item de ejemplo no encontrado o estructura incorrecta")

    # Resumen final
    print("\n" + "=" * 100)
    print("RESUMEN FINAL:")
    print("=" * 100)

    # Contar éxitos y errores
    success_count = 0
    total_checks = 0

    # Checks básicos
    basic_checks = [
        '<h2 class="lesson-heading-main">' in rendered_html,
        '<h4>Aplicaciones Prácticas del Álgebra</h4>' in rendered_html,
        '<ul>' in rendered_html,
        '</ul>' in rendered_html,
        li_count == 8,
    ]

    total_checks += len(basic_checks)
    success_count += sum(basic_checks)

    # Checks de negritas
    bold_checks = [f'<strong>{text}</strong>' in rendered_html for text in expected_bold_texts]
    total_checks += len(bold_checks)
    success_count += sum(bold_checks)

    # Checks de contenido
    content_checks = [content in rendered_html for content in expected_contents]
    total_checks += len(content_checks)
    success_count += sum(content_checks)

    # Checks visuales
    visual_check_results = [selector in rendered_html for selector, _ in visual_checks]
    total_checks += len(visual_check_results)
    success_count += sum(visual_check_results)

    print(f"Total de verificaciones: {total_checks}")
    print(f"Verificaciones exitosas: {success_count}")
    print(f"Tasa de éxito: {success_count}/{total_checks} ({success_count/total_checks*100:.1f}%)")

    if success_count == total_checks:
        print("\nSUCCESS: TODAS LAS VERIFICACIONES PASARON")
        print("El contenido de lista con elementos formateados funciona perfectamente!")
    else:
        print(f"\nERROR: {total_checks - success_count} VERIFICACIONES FALLARON")
        print("Revisa los elementos que fallaron arriba")

    print("=" * 100)

if __name__ == '__main__':
    test_specific_list_content()