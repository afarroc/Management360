#!/usr/bin/env python
"""
Script para probar específicamente el renderizado de texto en negrita (**)
en el contenido estructurado de lecciones.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import render_structured_content

def test_bold_rendering():
    """Prueba el renderizado de texto en negrita"""

    print("=" * 80)
    print("PRUEBA DE RENDERIZADO DE TEXTO EN NEGRITA (**)")
    print("=" * 80)

    # Crear elementos de prueba con diferentes formatos de negrita
    test_elements = [
        {
            'type': 'text',
            'title': 'Texto con negrita simple',
            'content': 'Este es un **texto en negrita** dentro de un párrafo normal.'
        },
        {
            'type': 'text',
            'title': 'Múltiples negritas',
            'content': 'Aquí tenemos **primera negrita** y luego **segunda negrita** en la misma oración.'
        },
        {
            'type': 'text',
            'title': 'Negrita al inicio',
            'content': '**Texto que comienza en negrita** y continúa normal.'
        },
        {
            'type': 'text',
            'title': 'Negrita al final',
            'content': 'Texto normal que termina con **palabras en negrita**.'
        },
        {
            'type': 'text',
            'title': 'Negrita con puntuación',
            'content': 'La **fórmula matemática** (x + y) = z es muy importante.'
        },
        {
            'type': 'text',
            'title': 'Negrita en lista',
            'content': '''• **Primer elemento** de la lista
• Segundo elemento normal
• **Tercer elemento** destacado'''
        },
        {
            'type': 'text',
            'title': 'Negrita en ejemplo algebraico',
            'content': '''En la ecuación **2x + 3 = 7**, la variable **x** representa el valor desconocido que debemos encontrar.

**Pasos para resolver:**
1. **Restar 3** a ambos lados: 2x = 4
2. **Dividir entre 2**: x = 2

**Resultado:** x = **2**'''
        }
    ]

    print("Probando renderizado de elementos con formato **negrita**...")
    print()

    for i, element in enumerate(test_elements, 1):
        print(f"Elemento {i}: {element['title']}")
        print("-" * 50)

        # Mostrar contenido original
        print("Contenido original:")
        print(f"  {element['content']}")
        print()

        # Renderizar
        try:
            html = render_structured_content([element])
            print("HTML renderizado:")

            # Extraer solo el párrafo de contenido para análisis
            start = html.find('<p class="lesson-content">')
            end = html.find('</p>', start) + 4
            if start != -1 and end != -1:
                content_html = html[start:end]
                print(f"  {content_html}")

                # Verificar si la negrita se convirtió correctamente
                if '<strong>' in content_html or '<b>' in content_html:
                    print("  SUCCESS: Negrita renderizada correctamente")
                elif '**' in content_html:
                    print("  WARNING: Negrita NO convertida (aun tiene **)")

                    # Mostrar qué se debería convertir
                    original_bold = element['content']
                    expected_bold = original_bold.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
                    while '**' in expected_bold:
                        expected_bold = expected_bold.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
                    print(f"  Esperado: {expected_bold}")
                else:
                    print("  ERROR: No se encontro formato de negrita")
            else:
                print("  ERROR: No se encontro el parrafo de contenido")

        except Exception as e:
            print(f"  ERROR durante renderizado: {e}")

        print()

    # Prueba específica del procesamiento Markdown
    print("=" * 80)
    print("ANALISIS DETALLADO DEL PROCESAMIENTO MARKDOWN")
    print("=" * 80)

    test_text = "Este es un **ejemplo de negrita** en el texto."
    print(f"Texto original: {test_text}")

    # Simular el procesamiento actual (solo saltos de línea)
    current_processing = test_text.replace('\n', '<br>')
    print(f"Procesamiento actual: {current_processing}")

    # Procesamiento esperado (con negrita)
    expected_processing = test_text.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
    expected_processing = expected_processing.replace('\n', '<br>')
    print(f"Procesamiento esperado: {expected_processing}")

    print()
    if '**' in current_processing:
        print("🔍 CONCLUSION: El sistema NO convierte ** a <strong>")
        print("💡 RECOMENDACION: Implementar conversión Markdown básica")
    else:
        print("✅ CONCLUSION: El sistema SÍ convierte ** correctamente")

if __name__ == '__main__':
    test_bold_rendering()