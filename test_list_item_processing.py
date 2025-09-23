#!/usr/bin/env python
"""
Script para verificar cómo se procesan los items individuales de una lista
y detectar el problema del salto de línea entre viñeta y contenido.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import process_markdown

def test_list_item_processing():
    """Prueba específica del procesamiento de items de lista"""

    print("=" * 80)
    print("PRUEBA: PROCESAMIENTO DE ITEMS DE LISTA")
    print("=" * 80)

    # Items de lista del ejemplo del usuario
    test_items = [
        "**Finanzas y Economía**: Calcular intereses, presupuestos, inversiones y análisis de costos",
        "**Ingeniería y Tecnología**: Diseño de estructuras, programación, algoritmos y modelado matemático",
        "**Ciencias**: Física, química, biología - modelar fenómenos naturales y experimentos",
        "**Medicina**: Dosificación de medicamentos, análisis estadístico de tratamientos",
        "**Arquitectura**: Cálculos estructurales, diseño de espacios, proporciones",
        "**Cocina**: Recetas, conversiones de medidas, planificación de menús",
        "**Deportes**: Estadísticas, probabilidades, optimización de rendimiento",
        "**Navegación GPS**: Cálculos de rutas, coordenadas, distancias"
    ]

    print("Procesando cada item de lista individualmente...")
    print()

    for i, item in enumerate(test_items, 1):
        print(f"Item {i}:")
        print(f"  Original: {repr(item)}")

        # Procesar con elementos inline (como hace el template tag actualizado)
        from courses.templatetags.lesson_tags import process_inline_elements
        processed = process_inline_elements(item)
        print(f"  Procesado: {repr(processed)}")

        # Verificar si tiene saltos de línea
        if '\n' in processed:
            print(f"  ERROR: CONTIENE SALTO DE LINEA: {repr(processed)}")
        else:
            print("  SUCCESS: Sin saltos de linea")

        # Verificar negritas
        if '<strong>' in processed and '</strong>' in processed:
            print("  SUCCESS: Negritas procesadas correctamente")
        else:
            print("  ERROR: Negritas no procesadas")

        # Verificar que no tenga etiquetas de párrafo
        if '<p>' in processed or '</p>' in processed:
            print(f"  ERROR: CONTIENE ETIQUETAS P: {repr(processed)}")
        else:
            print("  SUCCESS: Sin etiquetas de parrafo")

        print()

    # Verificar cómo se vería en el HTML final
    print("=" * 80)
    print("SIMULACION DEL HTML FINAL:")
    print("=" * 80)

    for i, item in enumerate(test_items[:3], 1):  # Solo primeros 3 para ejemplo
        from courses.templatetags.lesson_tags import process_inline_elements
        processed = process_inline_elements(item)
        html_item = f'<li class="lesson-list-item"><span class="list-bullet">*</span> {processed}</li>'
        print(f"Item {i} HTML:")
        print(f"  {html_item}")
        print()

    # Verificar si hay saltos de línea problemáticos
    print("=" * 80)
    print("ANÁLISIS DE SALTOS DE LÍNEA:")
    print("=" * 80)

    problematic_items = []
    for i, item in enumerate(test_items, 1):
        from courses.templatetags.lesson_tags import process_inline_elements
        processed = process_inline_elements(item)
        html_item = f'<li class="lesson-list-item"><span class="list-bullet">*</span> {processed}</li>'

        # Buscar patrón problemático: </span> seguido de \n
        if '</span> \n' in html_item or '</span>\n' in html_item:
            print(f"ERROR: Item {i} TIENE SALTO DE LINEA PROBLEMATICO:")
            print(f"   {repr(html_item)}")
            problematic_items.append(i)
        else:
            print(f"SUCCESS: Item {i} OK")

    print()
    if problematic_items:
        print(f"ERROR: ENCONTRADOS {len(problematic_items)} ITEMS CON SALTOS DE LINEA PROBLEMATICOS")
        print("Items problematicos:", problematic_items)
    else:
        print("SUCCESS: NINGUN ITEM TIENE SALTOS DE LINEA PROBLEMATICOS")

    print("\n" + "=" * 80)
    print("RECOMENDACIONES:")
    print("=" * 80)

    if problematic_items:
        print("1. Revisar la funcion process_markdown para evitar saltos de linea innecesarios")
        print("2. Asegurar que el procesamiento inline no agregue \\n")
        print("3. Verificar que los items se procesen como texto continuo")
    else:
        print("1. El procesamiento de items esta correcto")
        print("2. No hay saltos de linea problematicos entre viñeta y contenido")
        print("3. Los items se renderizan correctamente")

    print("=" * 80)

if __name__ == '__main__':
    test_list_item_processing()