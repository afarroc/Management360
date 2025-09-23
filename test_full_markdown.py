#!/usr/bin/env python
"""
Script para probar el procesamiento completo de Markdown
en el contenido estructurado de lecciones.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import process_markdown

def test_full_markdown():
    """Prueba completa del procesamiento Markdown"""

    print("=" * 80)
    print("PRUEBA COMPLETA DE PROCESAMIENTO MARKDOWN")
    print("=" * 80)

    # Crear elementos de prueba con diferentes formatos Markdown
    test_cases = [
        {
            'name': 'Negrita básica',
            'markdown': 'Este es un **texto en negrita** dentro de un párrafo normal.',
            'expected_contains': ['<strong>texto en negrita</strong>']
        },
        {
            'name': 'Itálica básica',
            'markdown': 'Este es un *texto en itálica* dentro de un párrafo normal.',
            'expected_contains': ['<em>texto en itálica</em>']
        },
        {
            'name': 'Código inline',
            'markdown': 'Usa la función `print()` para mostrar texto en Python.',
            'expected_contains': ['<code>print()</code>']
        },
        {
            'name': 'Enlaces',
            'markdown': 'Visita [Google](https://google.com) para buscar información.',
            'expected_contains': ['<a href="https://google.com" target="_blank">Google</a>']
        },
        {
            'name': 'Encabezados',
            'markdown': '''# Título Principal
## Subtítulo
### Sub-subtítulo''',
            'expected_contains': ['<h1>Título Principal</h1>', '<h2>Subtítulo</h2>', '<h3>Sub-subtítulo</h3>']
        },
        {
            'name': 'Lista no ordenada',
            'markdown': '''Frutas favoritas:
- Manzana
- Banana
- Naranja''',
            'expected_contains': ['<ul>', '<li>Manzana</li>', '<li>Banana</li>', '<li>Naranja</li>', '</ul>']
        },
        {
            'name': 'Lista con simbolo ?',
            'markdown': '''Aplicaciones del álgebra:
? **Finanzas**: Cálculos de intereses
? **Ingeniería**: Modelado matemático
? **Ciencias**: Análisis de datos''',
            'expected_contains': [
                '<ul>',
                '<li><strong>Finanzas</strong>: Cálculos de intereses</li>',
                '<li><strong>Ingeniería</strong>: Modelado matemático</li>',
                '<li><strong>Ciencias</strong>: Análisis de datos</li>',
                '</ul>'
            ]
        },
        {
            'name': 'Lista ordenada',
            'markdown': '''Pasos para cocinar:
1. Lavar los ingredientes
2. Cortar las verduras
3. Cocinar a fuego medio''',
            'expected_contains': ['<ol>', '<li>Lavar los ingredientes</li>', '<li>Cortar las verduras</li>', '<li>Cocinar a fuego medio</li>', '</ol>']
        },
        {
            'name': 'Código en bloque',
            'markdown': '''```python
def hello_world():
    print("Hello, World!")
    return True
```''',
            'expected_contains': ['<pre><code class="language-python">', 'def hello_world():', '</code></pre>']
        },
        {
            'name': 'Línea horizontal',
            'markdown': 'Contenido antes\n\n---\n\nContenido después',
            'expected_contains': ['<hr>']
        },
        {
            'name': 'Combinación compleja',
            'markdown': '''# Guía de **Python** Básico

## Introducción *importante*

Para empezar, instala Python desde [python.org](https://python.org).

### Código de ejemplo

```python
# Este es un comentario
def suma(a, b):
    return a + b

resultado = suma(3, 5)
print(f"El resultado es: {resultado}")
```

### Características principales:
- **Fácil de aprender**
- *Sintaxis clara*
- `Gran comunidad`
- [Documentación completa](https://docs.python.org)

---

¡Empieza tu viaje con Python hoy!''',
            'expected_contains': [
                '<h1>Guía de <strong>Python</strong> Básico</h1>',
                '<h2>Introducción <em>importante</em></h2>',
                '<h3>Código de ejemplo</h3>',
                '<a href="https://python.org" target="_blank">python.org</a>',
                '<pre><code class="language-python">',
                '<strong>Fácil de aprender</strong>',
                '<em>Sintaxis clara</em>',
                '<code>Gran comunidad</code>',
                '<a href="https://docs.python.org" target="_blank">Documentación completa</a>',
                '<hr>'
            ]
        }
    ]

    print("Probando procesamiento de diferentes formatos Markdown...")
    print()

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 60)

        # Mostrar entrada
        print("Entrada Markdown:")
        print(f"  {test_case['markdown']}")
        print()

        # Procesar
        try:
            html_output = process_markdown(test_case['markdown'])
            print("Salida HTML:")
            print(f"  {html_output}")
            print()

            # Verificar expectativas
            success = True
            for expected in test_case['expected_contains']:
                if expected not in html_output:
                    print(f"  ERROR: FALTA {expected}")
                    success = False
                else:
                    print(f"  SUCCESS: ENCONTRADO {expected}")

            if success:
                print("  SUCCESS: TEST EXITOSO")
            else:
                print("  ERROR: TEST FALLIDO")
                all_passed = False

        except Exception as e:
            print(f"  ERROR durante procesamiento: {e}")
            all_passed = False

        print()

    # Resumen final
    print("=" * 80)
    if all_passed:
        print("SUCCESS: TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print("El procesamiento completo de Markdown esta funcionando correctamente.")
    else:
        print("ERROR: ALGUNOS TESTS FALLARON")
        print("Revisa los errores arriba y ajusta la implementacion.")

    print("=" * 80)

    # Mostrar estadísticas
    print("\n📊 ESTADÍSTICAS DE FORMATOS SOPORTADOS:")
    print("✅ Negrita: **texto** → <strong>texto</strong>")
    print("✅ Itálica: *texto* → <em>texto</em>")
    print("✅ Código inline: `código` → <code>código</code>")
    print("✅ Enlaces: [texto](url) → <a href=\"url\">texto</a>")
    print("✅ Encabezados: # ## ### → <h1> <h2> <h3>")
    print("✅ Listas no ordenadas: - item → <ul><li>item</li></ul>")
    print("✅ Listas ordenadas: 1. 2. 3. → <ol><li>item</li></ol>")
    print("✅ Código en bloque: ```código``` → <pre><code>código</code></pre>")
    print("✅ Líneas horizontales: --- → <hr>")
    print("✅ Conversión a párrafos automáticos")

if __name__ == '__main__':
    test_full_markdown()