#!/usr/bin/env python
"""
Script para probar el procesamiento de saltos de línea y caracteres especiales
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import process_markdown

def test_line_breaks():
    """Prueba el procesamiento de saltos de línea y caracteres especiales"""

    test_cases = [
        # Caso 1: Texto normal con saltos de línea
        {
            'name': 'Texto normal con saltos de línea',
            'input': 'Esta es la primera línea.\nEsta es la segunda línea.\nEsta es la tercera línea.'
        },

        # Caso 2: Texto con párrafos separados
        {
            'name': 'Párrafos separados',
            'input': 'Primer párrafo con algo de texto.\n\nSegundo párrafo con más contenido.\n\nTercer párrafo final.'
        },

        # Caso 3: Lista con ?
        {
            'name': 'Lista con interrogaciones',
            'input': '? Primera pregunta\n? Segunda pregunta\n? Tercera pregunta'
        },

        # Caso 4: Lista mixta
        {
            'name': 'Lista mixta - y ?',
            'input': '- Primer item\n? Segunda pregunta\n- Tercer item\n? Cuarta pregunta'
        },

        # Caso 5: Texto con ? en medio
        {
            'name': 'Texto con ? en medio',
            'input': '¿Qué es el álgebra?\n\nEl álgebra es una rama de las matemáticas.\n\n¿Para qué sirve?\n\nSirve para resolver problemas.'
        },

        # Caso 6: Markdown con saltos de línea
        {
            'name': 'Markdown con saltos',
            'input': '# Título Principal\n\nEste es un párrafo.\n\n## Subtítulo\n\nOtro párrafo aquí.\n\n- Item 1\n- Item 2\n\n**Texto en negrita**'
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"PRUEBA {i}: {test_case['name']}")
        print('='*60)

        input_text = test_case['input']
        print("ENTRADA:")
        print(repr(input_text))  # Mostrar representación para ver saltos de línea
        print("\nENTRADA (visible):")
        print(input_text)
        print()

        try:
            result = process_markdown(input_text)
            print("SALIDA HTML:")
            print(result)
            print()

            # Verificar elementos HTML generados
            checks = {
                '<p>': 'Párrafos',
                '<h1>': 'Encabezado H1',
                '<h2>': 'Encabezado H2',
                '<ul>': 'Lista no ordenada',
                '<ol>': 'Lista ordenada',
                '<strong>': 'Negrita',
                '<br>': 'Saltos de línea'
            }

            print("ELEMENTOS HTML ENCONTRADOS:")
            for tag, description in checks.items():
                count = result.count(tag)
                if count > 0:
                    print(f"  ✓ {description}: {count} vez(es)")
            print()

        except Exception as e:
            print(f"ERROR: {e}")
            print()

if __name__ == "__main__":
    test_line_breaks()