#!/usr/bin/env python
"""
Script para verificar específicamente el problema del salto de línea antes de items de lista (\n?)
con el contenido exacto proporcionado por el usuario.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import process_markdown

def test_line_break_before_list():
    """Prueba específica del problema \n? en contenido de texto"""

    print("=" * 100)
    print("PRUEBA ESPECÍFICA: SALTO DE LÍNEA ANTES DE ITEMS DE LISTA (\\n?)")
    print("=" * 100)

    # Contenido exacto del usuario
    content = """El álgebra es una rama de las matemáticas que utiliza letras, símbolos y números para representar y resolver problemas. A diferencia de la aritmética que trabaja con números específicos, el álgebra nos permite trabajar con cantidades desconocidas o variables.

**Pensemos en el álgebra como un lenguaje matemático** que nos ayuda a:
? Resolver problemas del mundo real de manera general
? Encontrar patrones y relaciones
? Hacer predicciones basadas en datos
? Desarrollar el pensamiento lógico y abstracto"""

    print("CONTENIDO ORIGINAL:")
    print("=" * 50)
    print(repr(content))
    print()
    print("CONTENIDO FORMATEADO:")
    print("=" * 50)
    print(content)
    print()

    # Procesar con Markdown
    processed_html = process_markdown(content)

    print("HTML PROCESADO:")
    print("=" * 50)
    print(processed_html)
    print()

    # Análisis específico del problema
    print("ANÁLISIS DEL PROBLEMA \\n?:")
    print("-" * 40)

    # Verificar si hay listas
    has_list = '<ul>' in processed_html and '<li>' in processed_html
    print(f"1. ¿Se creó una lista? {has_list}")

    if has_list:
        print("   SUCCESS: Lista detectada")
        li_count = processed_html.count('<li>')
        print(f"   Items en lista: {li_count}")

        # Mostrar cómo se ve la lista
        import re
        ul_match = re.search(r'<ul>.*?</ul>', processed_html, re.DOTALL)
        if ul_match:
            print("   Lista HTML:")
            print(f"   {ul_match.group(0)}")
    else:
        print("   ERROR: No se creó lista")
        print("   Esto indica que el \\n? no se procesó correctamente")

    # Verificar el contexto antes de la lista
    print("\n2. CONTEXTO ANTES DE LA LISTA:")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('?'):
            print(f"   Línea {i+1} (primer item de lista): {repr(line)}")
            if i > 0:
                print(f"   Línea anterior {i}: {repr(lines[i-1])}")
            break

    # Verificar cómo se ve en el HTML procesado
    print("\n3. ANÁLISIS DEL HTML PROCESADO:")
    html_lines = processed_html.split('\n')
    for i, line in enumerate(html_lines):
        if '<ul>' in line:
            print(f"   Línea HTML {i+1} (inicio lista): {repr(line)}")
            if i > 0:
                print(f"   Línea HTML anterior {i}: {repr(html_lines[i-1])}")
            break

    # Verificar si el párrafo anterior está cerrado correctamente
    print("\n4. VERIFICACIÓN DE CIERRE DE PÁRRAFO:")
    p_end_index = processed_html.find('</p>')
    ul_start_index = processed_html.find('<ul>')

    if p_end_index != -1 and ul_start_index != -1:
        if p_end_index < ul_start_index:
            print("   SUCCESS: Párrafo cerrado antes de lista")
            content_between = processed_html[p_end_index+4:ul_start_index]
            print(f"   Contenido entre </p> y <ul>: {repr(content_between)}")
        else:
            print("   ERROR: Lista aparece antes del cierre de párrafo")
    else:
        print("   INFO: No se encontraron ambas etiquetas")

    # Verificar el texto específico que debería estar en negritas
    print("\n5. VERIFICACIÓN DE NEGRITAS:")
    bold_text = "Pensemos en el álgebra como un lenguaje matemático"
    if f"<strong>{bold_text}</strong>" in processed_html:
        print("   SUCCESS: Negritas aplicadas correctamente")
    else:
        print("   ERROR: Negritas no aplicadas")

    # Mostrar el párrafo que contiene las negritas
    import re
    p_with_bold = re.search(r'<p>.*?<strong>.*?</strong>.*?</p>', processed_html, re.DOTALL)
    if p_with_bold:
        print(f"   Párrafo con negritas: {repr(p_with_bold.group(0))}")

    # Resumen del problema
    print("\n" + "=" * 100)
    print("RESUMEN DEL PROBLEMA:")
    print("=" * 100)

    issues = []

    if not has_list:
        issues.append("La lista no se creó - el \\n? no se procesó como lista")

    if has_list:
        li_count = processed_html.count('<li>')
        if li_count != 4:
            issues.append(f"Número incorrecto de items en lista (esperado: 4, encontrado: {li_count})")

    if not ('<strong>' in processed_html and '</strong>' in processed_html):
        issues.append("Las negritas no se aplicaron")

    if issues:
        print("PROBLEMAS ENCONTRADOS:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
        print("\nCONCLUSION: El procesamiento de \\n? tiene problemas")
    else:
        print("SUCCESS: No se encontraron problemas")
        print("El \\n? se procesa correctamente")

    # Sugerencias de solución
    print("\nSUGERENCIAS DE DEPURACIÓN:")
    print("-" * 40)
    print("1. Revisar la regex de detección de listas en process_markdown")
    print("2. Verificar que \\n? se considere como inicio de lista válido")
    print("3. Comprobar que el procesamiento de párrafos no interfiera")
    print("4. Asegurar que las líneas con ? se procesen como items de lista")

    print("=" * 100)

if __name__ == '__main__':
    test_line_break_before_list()