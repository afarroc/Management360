#!/usr/bin/env python
"""
Script para probar específicamente el procesamiento de listas con símbolo ?
en el contenido estructurado de lecciones.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import process_markdown

def test_question_mark_lists():
    """Prueba el procesamiento de listas con símbolo ?"""

    print("=" * 80)
    print("PRUEBA DE LISTAS CON SÍMBOLO ?")
    print("=" * 80)

    # Caso específico del usuario
    test_content = """? **Finanzas y Economía**: Calcular intereses, presupuestos, inversiones y análisis de costos
    ? **Ingeniería y Tecnología**: Diseño de estructuras, programación, algoritmos y modelado matemático
    ? **Ciencias**: Física, química, biología - modelar fenómenos naturales y experimentos
    ? **Medicina**: Dosificación de medicamentos, análisis estadístico de tratamientos
    ? **Arquitectura**: Cálculos estructurales, diseño de espacios, proporciones
    ? **Cocina**: Recetas, conversiones de medidas, planificación de menús
    ? **Deportes**: Estadísticas, probabilidades, optimización de rendimiento
    ? **Navegación GPS**: Cálculos de rutas, coordenadas, distancias"""

    print("Contenido de entrada:")
    print(test_content)
    print("\n" + "=" * 80)

    # Procesar
    result = process_markdown(test_content)

    print("Resultado HTML:")
    print(result)
    print("\n" + "=" * 80)

    # Verificaciones
    checks = [
        '<ul>' in result,
        '</ul>' in result,
        '<li>' in result,
        '</li>' in result,
        '<strong>Finanzas y Economía</strong>' in result,
        '<strong>Ingeniería y Tecnología</strong>' in result,
        'Calcular intereses, presupuestos, inversiones y análisis de costos' in result,
        'Diseño de estructuras, programación, algoritmos y modelado matemático' in result,
        'Física, química, biología - modelar fenómenos naturales y experimentos' in result,
        'Dosificación de medicamentos, análisis estadístico de tratamientos' in result,
        'Cálculos estructurales, diseño de espacios, proporciones' in result,
        'Recetas, conversiones de medidas, planificación de menús' in result,
        'Estadísticas, probabilidades, optimización de rendimiento' in result,
        'Cálculos de rutas, coordenadas, distancias' in result
    ]

    print("VERIFICACIONES:")
    check_names = [
        "Contiene <ul>",
        "Contiene </ul>",
        "Contiene <li>",
        "Contiene </li>",
        "Negrita en Finanzas funciona",
        "Negrita en Ingeniería funciona",
        "Contenido Finanzas presente",
        "Contenido Ingeniería presente",
        "Contenido Ciencias presente",
        "Contenido Medicina presente",
        "Contenido Arquitectura presente",
        "Contenido Cocina presente",
        "Contenido Deportes presente",
        "Contenido GPS presente"
    ]

    all_passed = True
    for i, (check, name) in enumerate(zip(checks, check_names)):
        status = "SUCCESS" if check else "ERROR"
        print(f"  {status}: {name}")
        if not check:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("SUCCESS: TODAS LAS VERIFICACIONES PASARON")
        print("Las listas con simbolo ? funcionan correctamente!")
    else:
        print("ERROR: ALGUNAS VERIFICACIONES FALLARON")
        print("Revisa la implementacion de listas con ?")

    print("=" * 80)

if __name__ == '__main__':
    test_question_mark_lists()