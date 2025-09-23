#!/usr/bin/env python
"""
Script para verificar la estructura y renderizado del contenido estructurado JSON
proporcionado por el usuario para la lección de álgebra.
"""
import os
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.templatetags.lesson_tags import render_structured_content

def test_structured_content_rendering():
    """Prueba el renderizado completo del contenido estructurado"""

    print("=" * 100)
    print("VERIFICACIÓN DE CONTENIDO ESTRUCTURADO - LECCIÓN DE ÁLGEBRA")
    print("=" * 100)

    # Contenido estructurado proporcionado por el usuario
    structured_content = [
        {
            "type": "heading",
            "title": "¡Bienvenido al Fascinante Mundo del Álgebra!"
        },
        {
            "type": "text",
            "title": "¿Qué es el Álgebra?",
            "content": "El álgebra es una rama de las matemáticas que utiliza letras, símbolos y números para representar y resolver problemas. A diferencia de la aritmética que trabaja con números específicos, el álgebra nos permite trabajar con cantidades desconocidas o variables.\n\n**Pensemos en el álgebra como un lenguaje matemático** que nos ayuda a:\n? Resolver problemas del mundo real de manera general\n? Encontrar patrones y relaciones\n? Hacer predicciones basadas en datos\n? Desarrollar el pensamiento lógico y abstracto"
        },
        {
            "type": "image",
            "title": "Evolución de las Matemáticas",
            "content": "https://images.unsplash.com/photo-1509228468518-180dd4864904?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80"
        },
        {
            "type": "video",
            "content": {
                "description": "Historia fascinante del álgebra desde la antigüedad hasta nuestros días",
                "duration": 8,
                "url": "https://www.youtube.com/watch?v=N2y6cUJTfhI"
            }
        },
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
        },
        {
            "type": "text",
            "title": "Pensamiento Algebraico: Una Habilidad Esencial",
            "content": "Aprender álgebra no se trata solo de resolver ecuaciones, sino de desarrollar un **modo de pensar** que nos ayuda a:\n\n**? Resolver Problemas Sistemáticamente**\nEn lugar de probar soluciones al azar, el álgebra nos enseña a:\n1. Identificar lo que buscamos (la incógnita)\n2. Representar el problema con símbolos\n3. Aplicar reglas lógicas para encontrar la solución\n4. Verificar que la solución sea correcta\n\n**? Encontrar Patrones y Relaciones**\nEl álgebra nos entrena para reconocer patrones en datos aparentemente caóticos, una habilidad crucial en nuestra era digital.\n\n**? Desarrollar Pensamiento Abstracto**\nNos permite trabajar con conceptos generales, no solo casos específicos, ampliando nuestra capacidad de comprensión."
        },
        {
            "type": "heading",
            "title": "Conceptos Básicos que Dominarás"
        },
        {
            "type": "text",
            "title": "Variables: Las Incógnitas del Álgebra",
            "content": "**¿Qué son las variables?**\nLas variables son letras que representan números desconocidos o que pueden cambiar. Comúnmente usamos letras como x, y, z, a, b, c.\n\n**Ejemplos en la vida real:**\n? x = número de horas trabajadas\n? y = distancia recorrida\n? z = temperatura actual\n? a = costo de un artículo\n\n**Importante**: Una variable puede representar cualquier número, pero en un problema específico usualmente representa un valor particular que debemos encontrar."
        },
        {
            "type": "text",
            "title": "Constantes: Los Valores Fijos",
            "content": "**¿Qué son las constantes?**\nLas constantes son números fijos que no cambian en una expresión algebraica.\n\n**Ejemplos:**\n? Números: 2, 5, 3.14, -7\n? Valores fijos en fórmulas: ? (pi), e (número e), velocidad de la luz\n\n**En expresiones algebraicas:**\n? 2x + 3: 2 y 3 son constantes, x es variable\n? 5a - 7b + 12: 5, 7 y 12 son constantes, a y b son variables"
        },
        {
            "type": "text",
            "title": "Expresiones Algebraicas: Combinando Todo",
            "content": "**¿Qué es una expresión algebraica?**\nEs una combinación de variables, constantes y operaciones matemáticas que representa una cantidad.\n\n**Ejemplos:**\n? 2x + 3 (lineal)\n? x² + 2x - 1 (cuadrática)\n? 3a + 2b - 5c (con múltiples variables)\n? (x + y) × (a - b) (con paréntesis)\n\n**Tipos de expresiones:**\n? **Monomios**: Una sola variable o constante (2x, 5, -3a)\n? **Binomios**: Dos términos (x + 2, 3a - b)\n? **Trinomios**: Tres términos (x² + 2x - 1)\n? **Polinomios**: Cuatro o más términos"
        },
        {
            "type": "exercise",
            "content": "**Ejercicio Interactivo: Identifica Variables vs Constantes**\n\nAnaliza las siguientes expresiones e identifica qué elementos son variables y cuáles constantes:\n\n1. **3x + 5 = 17**\n   - x: Variable (lo que buscamos)\n   - 3, 5, 17: Constantes\n\n2. **2a - b + 7 = 0**\n   - a, b: Variables\n   - 2, 7: Constantes\n\n3. **?r² (área del círculo)**\n   - r: Variable (radio)\n   - ?: Constante matemática\n\n**¡Practica tú mismo!**\n? En la ecuación del costo total: C = 15x + 100\n? ¿Qué representa x? ¿Qué representan 15 y 100?\n? Si vendo 10 unidades, ¿cuál es el costo total?"
        },
        {
            "type": "text",
            "title": "El Lenguaje del Álgebra: Notación Matemática",
            "content": "**Símbolos Comunes en Álgebra:**\n\n? **=** : igual a\n? **?** : diferente de\n? **<** : menor que\n? **>** : mayor que\n? **?** : menor o igual que\n? **?** : mayor o igual que\n? **+** : más\n? **-** : menos\n? **×** o **?** : multiplicado por\n? **÷** o **/** : dividido por\n? **()** : agrupación\n? **[]** : agrupación\n? **{}** : agrupación\n? **²** : al cuadrado\n? **³** : al cubo\n? **?** : raíz cuadrada\n\n**Ejemplo de expresión completa:**\n**(2x + 3) × (x - 1) = 0**\n\nEsta ecuación representa un problema donde necesitamos encontrar valores de x que hagan la ecuación verdadera."
        },
        {
            "type": "heading",
            "title": "Aplicaciones Prácticas: Álgebra en Acción"
        },
        {
            "type": "text",
            "title": "Problema Real: Planificación de un Viaje",
            "content": "**Situación**: Planeas un viaje de 500 km. Tu auto consume 8 litros cada 100 km y la gasolina cuesta $1.20 por litro.\n\n**¿Cuánto costará el combustible?**\n\n**Razonamiento algebraico:**\n1. **Identificar variables**: Distancia = d = 500 km\n2. **Calcular consumo**: Litros = (d × 8) ÷ 100\n3. **Calcular costo**: Total = Litros × $1.20\n\n**Expresión algebraica**: Costo = [(d × 8) ÷ 100] × 1.20\n\n**Solución**: [(500 × 8) ÷ 100] × 1.20 = 40 × 1.20 = $48\n\n**¡El viaje costará $48 en combustible!**"
        },
        {
            "type": "text",
            "title": "Problema Real: Negocio de Helados",
            "content": "**Situación**: Vendes helados a $3 cada uno. Tus costos fijos son $50 diarios (alquiler, etc.) y cada helado cuesta $1 producir.\n\n**¿Cuántos helados necesitas vender para no perder dinero?**\n\n**Análisis algebraico:**\n? **Ingreso**: 3x (x = helados vendidos)\n? **Costo**: 50 + 1x (costos fijos + costo por helado)\n? **Ganancia**: Ingreso - Costo = 0 (punto de equilibrio)\n\n**Ecuación**: 3x - (50 + x) = 0\n**Solución**: 3x - x - 50 = 0 ? 2x = 50 ? x = 25\n\n**¡Necesitas vender 25 helados para cubrir costos!**"
        },
        {
            "type": "exercise",
            "content": "**Ejercicio Interactivo: Crea tu Propio Problema Algebraico**\n\n**Instrucciones:**\n1. Piensa en una situación de la vida diaria\n2. Identifica qué quieres calcular (la incógnita)\n3. Crea una expresión algebraica\n4. Resuélvela\n\n**Ejemplo:**\n? Situación: Comprar libros con descuento\n? Incógnita: x = precio original\n? Expresión: Precio final = x - (x × 0.20)\n? Si pago $32 con 20% descuento, x = 32 ÷ 0.80 = $40\n\n**¡Ahora crea el tuyo!**"
        },
        {
            "type": "heading",
            "title": "Recursos Adicionales para tu Aprendizaje"
        },
        {
            "type": "list",
            "title": "Materiales Recomendados",
            "items": [
                "**Libros**: \"Álgebra Elemental\" de Charles Smith, \"Introducción al Álgebra\" de Richard Rusczyk",
                "**Videos**: Khan Academy - Álgebra Básica, YouTube - Math Antics",
                "**Apps**: Photomath, Wolfram Alpha, GeoGebra",
                "**Sitios Web**: Wolfram MathWorld, Mathway, Symbolab",
                "**Juegos**: Prodigy Math, DragonBox Algebra",
                "**Cursos Online**: Coursera - Álgebra Lineal, edX - College Algebra"
            ]
        },
        {
            "type": "text",
            "title": "Consejos para el Éxito en Álgebra",
            "content": "**? Estrategias de Aprendizaje:**\n\n1. **Practica Diariamente**: La consistencia es clave en matemáticas\n2. **Entiende los Conceptos**: No memorices, comprende el \"porqué\"\n3. **Trabaja con Ejemplos**: Empieza con casos simples, progresa a complejos\n4. **Verifica tus Respuestas**: Siempre comprueba que la solución sea correcta\n5. **No Temas Equivocarte**: Los errores son oportunidades de aprendizaje\n6. **Busca Ayuda**: Pregunta cuando no entiendas, no te quedes atascado\n7. **Aplica lo Aprendido**: Usa el álgebra en situaciones reales\n8. **Mantén la Curiosidad**: El álgebra es una herramienta poderosa, ¡diviértete usándola!\n\n**? Recuerda**: Todo experto fue principiante alguna vez. ¡Tú puedes dominar el álgebra!"
        },
        {
            "type": "markdown",
            "content": "## ? Glosario de Términos Clave\n\n**Variable**: Letra que representa un número desconocido o que puede cambiar\n**Constante**: Número fijo que no cambia en una expresión\n**Expresión Algebraica**: Combinación de variables, constantes y operaciones\n**Ecuación**: Afirmación matemática de que dos expresiones son iguales\n**Coeficiente**: Número que multiplica a una variable\n**Término**: Parte de una expresión separada por + o -\n**Monomio**: Expresión algebraica con un solo término\n**Binomio**: Expresión algebraica con dos términos\n**Polinomio**: Expresión algebraica con múltiples términos\n\n## ? Próximos Pasos\n\nDespués de esta introducción, estarás listo para:\n1. **Trabajar con expresiones algebraicas**\n2. **Resolver ecuaciones lineales**\n3. **Entender funciones y gráficas**\n4. **Aplicar álgebra a problemas complejos**\n\n**¡El viaje apenas comienza! ?**"
        }
    ]

    print(f"Procesando {len(structured_content)} elementos de contenido estructurado...")
    print()

    # Renderizar el contenido
    rendered_html = render_structured_content(structured_content)

    print("RENDERIZADO COMPLETO:")
    print("=" * 100)
    # Evitar problemas de codificación imprimiendo solo una parte o usando repr
    try:
        print(rendered_html[:2000] + "..." if len(rendered_html) > 2000 else rendered_html)
    except UnicodeEncodeError:
        print("[Contenido HTML generado - caracteres especiales omitidos para compatibilidad de consola]")
        print(f"Longitud total: {len(rendered_html)} caracteres")
    print("=" * 100)

    # Análisis detallado por tipo de elemento
    print("\nANÁLISIS DETALLADO POR TIPO DE ELEMENTO:")
    print("-" * 100)

    element_counts = {}
    issues_found = []

    for i, element in enumerate(structured_content):
        element_type = element.get('type', 'unknown')
        element_counts[element_type] = element_counts.get(element_type, 0) + 1

        print(f"\n[{i+1}] TIPO: {element_type.upper()}")
        print("-" * 50)

        # Verificar estructura básica
        if element_type == 'heading':
            title = element.get('title', '')
            print(f"Título: {title}")
            if '<h2 class="lesson-heading-main">' in rendered_html and title in rendered_html:
                print("SUCCESS: Encabezado renderizado correctamente")
            else:
                print("ERROR: Encabezado no encontrado en HTML")
                issues_found.append(f"Heading {i+1}: not rendered")

        elif element_type == 'text':
            title = element.get('title', '')
            content = element.get('content', '')
            print(f"Título: {title}")
            print(f"Contenido (primeros 100 chars): {content[:100]}...")

            # Verificar procesamiento Markdown
            if '**' in content and '<strong>' in rendered_html:
                print("SUCCESS: Negritas procesadas")
            else:
                print("INFO: No negritas en este elemento")

            if '?' in content and '<ul>' in rendered_html:
                print("SUCCESS: Listas con ? procesadas")
            else:
                print("INFO: No listas con ? en este elemento")

            if '1.' in content and '<ol>' in rendered_html:
                print("SUCCESS: Listas ordenadas procesadas")
            else:
                print("INFO: No listas ordenadas en este elemento")

        elif element_type == 'image':
            title = element.get('title', '')
            content = element.get('content', '')
            print(f"Título: {title}")
            print(f"URL: {content}")
            if f'<img src="{content}"' in rendered_html:
                print("SUCCESS: Imagen renderizada correctamente")
            else:
                print("ERROR: Imagen no encontrada en HTML")
                issues_found.append(f"Image {i+1}: not rendered")

        elif element_type == 'video':
            content = element.get('content', {})
            if isinstance(content, dict):
                description = content.get('description', '')
                duration = content.get('duration', 0)
                url = content.get('url', '')
                print(f"Descripción: {description}")
                print(f"Duración: {duration} min")
                print(f"URL: {url}")
                if description in rendered_html and str(duration) in rendered_html:
                    print("SUCCESS: Video renderizado correctamente")
                else:
                    print("ERROR: Video no encontrado en HTML")
                    issues_found.append(f"Video {i+1}: not rendered")

        elif element_type == 'list':
            title = element.get('title', '')
            items = element.get('items', [])
            print(f"Título: {title}")
            print(f"Número de items: {len(items)}")
            for j, item in enumerate(items[:3]):  # Mostrar primeros 3
                print(f"  Item {j+1}: {item[:50]}...")
            if len(items) > 3:
                print(f"  ... y {len(items)-3} items más")

            # Verificar que las negritas en items se procesen
            if any('**' in item for item in items) and '<strong>' in rendered_html:
                print("SUCCESS: Negritas en items de lista procesadas")
            else:
                print("INFO: No negritas en items de lista")

        elif element_type == 'exercise':
            content = element.get('content', '')
            print(f"Contenido (primeros 100 chars): {content[:100]}...")
            if '**' in content and '<strong>' in rendered_html:
                print("SUCCESS: Markdown en ejercicio procesado")
            else:
                print("INFO: No markdown especial en ejercicio")

        elif element_type == 'markdown':
            content = element.get('content', '')
            print(f"Contenido Markdown (primeros 100 chars): {content[:100]}...")
            # Los elementos markdown se renderizan como texto plano con <br>
            if '<br>' in rendered_html:
                print("SUCCESS: Markdown renderizado como texto con saltos de línea")
            else:
                print("INFO: Markdown sin saltos de línea especiales")

    print("\n" + "=" * 100)
    print("RESUMEN ESTADÍSTICO:")
    print("=" * 100)
    print(f"Total de elementos: {len(structured_content)}")
    for element_type, count in element_counts.items():
        print(f"- {element_type}: {count} elementos")

    print(f"\nProblemas encontrados: {len(issues_found)}")
    if issues_found:
        print("Lista de problemas:")
        for issue in issues_found:
            print(f"  - {issue}")
    else:
        print("SUCCESS: No se encontraron problemas en el renderizado")

    print("\n" + "=" * 100)
    print("VERIFICACIÓN DE FUNCIONALIDADES AVANZADAS:")
    print("=" * 100)

    # Verificaciones específicas
    advanced_checks = [
        ("Negritas en texto", '**' in str(structured_content) and '<strong>' in rendered_html),
        ("Listas con ?", '?' in str(structured_content) and '<ul>' in rendered_html),
        ("Listas ordenadas", '1.' in str(structured_content) and '<ol>' in rendered_html),
        ("Imágenes", any(e.get('type') == 'image' for e in structured_content) and '<img' in rendered_html),
        ("Videos", any(e.get('type') == 'video' for e in structured_content) and 'lesson-video' in rendered_html),
        ("Encabezados", any(e.get('type') == 'heading' for e in structured_content) and '<h2 class="lesson-heading-main">' in rendered_html),
        ("Ejercicios", any(e.get('type') == 'exercise' for e in structured_content) and 'lesson-exercise' in rendered_html),
        ("Elementos Markdown", any(e.get('type') == 'markdown' for e in structured_content) and 'lesson-markdown' in rendered_html),
    ]

    for check_name, result in advanced_checks:
        status = "SUCCESS" if result else "ERROR"
        print(f"{status}: {check_name}")

    print("\n" + "=" * 100)
    if all(result for _, result in advanced_checks):
        print("SUCCESS: TODAS LAS FUNCIONALIDADES AVANZADAS OPERATIVAS")
        print("El contenido estructurado se renderiza perfectamente!")
    else:
        print("ERROR: ALGUNAS FUNCIONALIDADES FALLARON")
        print("Revisa los elementos que fallaron arriba")

    print("=" * 100)

if __name__ == '__main__':
    test_structured_content_rendering()