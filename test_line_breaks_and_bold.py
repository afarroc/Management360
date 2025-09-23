#!/usr/bin/env python
"""
Script específico para verificar el manejo de saltos de línea y negritas
en el procesamiento de contenido estructurado.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import process_markdown

def test_line_breaks_and_bold():
    """Prueba específica de saltos de línea y negritas"""

    print("=" * 80)
    print("PRUEBA ESPECÍFICA: SALTOS DE LÍNEA Y NEGRITAS")
    print("=" * 80)

    # Casos de prueba específicos
    test_cases = [
        {
            'name': 'Saltos de línea simples (\\n)',
            'markdown': 'Línea 1\nLínea 2\nLínea 3',
            'expected_contains': ['Línea 1', 'Línea 2', 'Línea 3']
        },
        {
            'name': 'Saltos de línea dobles (\\n\\n) - Párrafos',
            'markdown': 'Párrafo 1\n\nPárrafo 2\n\nPárrafo 3',
            'expected_contains': ['<p>Párrafo 1</p>', '<p>Párrafo 2</p>', '<p>Párrafo 3</p>']
        },
        {
            'name': 'Negritas después de lista',
            'markdown': '? Item 1 de lista\n? Item 2 de lista\n\n**Texto en negrita** después de la lista',
            'expected_contains': ['<ul>', '<li>Item 1 de lista</li>', '<li>Item 2 de lista</li>', '</ul>', '<p><strong>Texto en negrita</strong> después de la lista</p>']
        },
        {
            'name': 'Negritas con salto de línea',
            'markdown': '**Texto en negrita**\ncontinúa en la siguiente línea',
            'expected_contains': ['<p><strong>Texto en negrita</strong> continúa en la siguiente línea</p>']
        },
        {
            'name': 'Lista con negritas y saltos',
            'markdown': '? **Elemento 1**\n? **Elemento 2**\n\nTexto normal después',
            'expected_contains': [
                '<ul>',
                '<li><strong>Elemento 1</strong></li>',
                '<li><strong>Elemento 2</strong></li>',
                '</ul>',
                '<p>Texto normal después</p>'
            ]
        },
        {
            'name': 'Combinación compleja',
            'markdown': '''? **Aplicación 1**: Descripción detallada\n? **Aplicación 2**: Más detalles\n\n## Sección Siguiente\n\n**Texto importante** con *énfasis* y `código`.\n\nOtro párrafo.''',
            'expected_contains': [
                '<li><strong>Aplicación 1</strong>: Descripción detallada</li>',
                '<li><strong>Aplicación 2</strong>: Más detalles</li>',
                '<h2>Sección Siguiente</h2>',
                '<strong>Texto importante</strong>',
                '<em>énfasis</em>',
                '<code>código</code>',
                '<p>Otro párrafo.</p>'
            ]
        }
    ]

    print("Probando casos específicos de saltos de línea y negritas...")
    print()

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 60)

        # Mostrar entrada
        print("Entrada Markdown:")
        print(f"  {repr(test_case['markdown'])}")
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

    # Test específico del contenido del usuario
    print("=" * 80)
    print("TEST ESPECÍFICO DEL CONTENIDO DEL USUARIO")
    print("=" * 80)

    user_content = """? **Finanzas y Economía**: Calcular intereses, presupuestos, inversiones y análisis de costos
? **Ingeniería y Tecnología**: Diseño de estructuras, programación, algoritmos y modelado matemático
? **Ciencias**: Física, química, biología - modelar fenómenos naturales y experimentos
? **Medicina**: Dosificación de medicamentos, análisis estadístico de tratamientos
? **Arquitectura**: Cálculos estructurales, diseño de espacios, proporciones
? **Cocina**: Recetas, conversiones de medidas, planificación de menús
? **Deportes**: Estadísticas, probabilidades, optimización de rendimiento
? **Navegación GPS**: Cálculos de rutas, coordenadas, distancias"""

    print("Contenido de lista del usuario:")
    print(user_content)
    print()

    user_html = process_markdown(user_content)
    print("HTML generado:")
    print(user_html)
    print()

    # Verificaciones específicas
    user_checks = [
        '<ul>' in user_html,
        '</ul>' in user_html,
        user_html.count('<li>') == 8,  # Debería haber 8 items
        '<strong>Finanzas y Economía</strong>' in user_html,
        '<strong>Ingeniería y Tecnología</strong>' in user_html,
        'Calcular intereses, presupuestos, inversiones y análisis de costos' in user_html,
        'Diseño de estructuras, programación, algoritmos y modelado matemático' in user_html
    ]

    print("VERIFICACIONES ESPECÍFICAS:")
    user_check_names = [
        "Contiene <ul>",
        "Contiene </ul>",
        "Tiene exactamente 8 items (<li>)",
        "Negritas en Finanzas funcionan",
        "Negritas en Ingeniería funcionan",
        "Contenido Finanzas presente",
        "Contenido Ingeniería presente"
    ]

    user_success = True
    for check, name in zip(user_checks, user_check_names):
        status = "SUCCESS" if check else "ERROR"
        print(f"  {status}: {name}")
        if not check:
            user_success = False

    print()
    if user_success:
        print("SUCCESS: CONTENIDO DEL USUARIO PROCESADO CORRECTAMENTE")
    else:
        print("ERROR: PROBLEMAS EN EL CONTENIDO DEL USUARIO")
        all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("SUCCESS: TODOS LOS TESTS PASARON")
        print("Los saltos de línea y negritas funcionan correctamente")
    else:
        print("ERROR: ALGUNOS TESTS FALLARON")
        print("Revisa el procesamiento de saltos de línea y negritas")

    print("=" * 80)

if __name__ == '__main__':
    test_line_breaks_and_bold()