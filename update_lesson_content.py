#!/usr/bin/env python
"""
Script para actualizar el contenido de la lección "Introducción al Álgebra"
con material completo y estético.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import Lesson

def update_lesson_content():
    """Actualizar la lección con contenido completo y estético"""

    # Obtener la lección
    lesson = Lesson.objects.get(id=18)

    # Crear contenido estructurado completo y estético
    structured_content = [
        {
            'type': 'heading',
            'title': '¡Bienvenido al Fascinante Mundo del Álgebra!'
        },
        {
            'type': 'text',
            'title': '¿Qué es el Álgebra?',
            'content': '''El álgebra es una rama de las matemáticas que utiliza letras, símbolos y números para representar y resolver problemas. A diferencia de la aritmética que trabaja con números específicos, el álgebra nos permite trabajar con cantidades desconocidas o variables.

**Pensemos en el álgebra como un lenguaje matemático** que nos ayuda a:
• Resolver problemas del mundo real de manera general
• Encontrar patrones y relaciones
• Hacer predicciones basadas en datos
• Desarrollar el pensamiento lógico y abstracto'''
        },
        {
            'type': 'image',
            'title': 'Evolución de las Matemáticas',
            'content': 'https://images.unsplash.com/photo-1509228468518-180dd4864904?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
        },
        {
            'type': 'text',
            'title': 'Un Viaje a Través del Tiempo: Historia del Álgebra',
            'content': '''El álgebra tiene raíces antiguas que se remontan a la civilización babilónica alrededor del 2000 a.C., donde se resolvían ecuaciones lineales en tablillas de arcilla.

**Hitos importantes:**
• **Siglo IX**: El matemático persa Al-Juarismi escribe "El Compendio de Cálculo por Restauración y Comparación", dando origen al término "álgebra"
• **Siglo XVI**: François Viète introduce el uso sistemático de letras para representar cantidades variables
• **Siglo XVII**: René Descartes combina álgebra y geometría, creando la geometría analítica
• **Siglo XIX**: Se desarrolla el álgebra abstracta y lineal'''
        },
        {
            'type': 'video',
            'content': {
                'description': 'Historia fascinante del álgebra desde la antigüedad hasta nuestros días',
                'duration': 8,
                'url': 'https://www.youtube.com/watch?v=N2y6cUJTfhI'
            }
        },
        {
            'type': 'heading',
            'title': '¿Por qué es Importante el Álgebra en la Vida Diaria?'
        },
        {
            'type': 'list',
            'title': 'Aplicaciones Prácticas del Álgebra',
            'items': [
                '**Finanzas y Economía**: Calcular intereses, presupuestos, inversiones y análisis de costos',
                '**Ingeniería y Tecnología**: Diseño de estructuras, programación, algoritmos y modelado matemático',
                '**Ciencias**: Física, química, biología - modelar fenómenos naturales y experimentos',
                '**Medicina**: Dosificación de medicamentos, análisis estadístico de tratamientos',
                '**Arquitectura**: Cálculos estructurales, diseño de espacios, proporciones',
                '**Cocina**: Recetas, conversiones de medidas, planificación de menús',
                '**Deportes**: Estadísticas, probabilidades, optimización de rendimiento',
                '**Navegación GPS**: Cálculos de rutas, coordenadas, distancias'
            ]
        },
        {
            'type': 'text',
            'title': 'Pensamiento Algebraico: Una Habilidad Esencial',
            'content': '''Aprender álgebra no se trata solo de resolver ecuaciones, sino de desarrollar un **modo de pensar** que nos ayuda a:

**💡 Resolver Problemas Sistemáticamente**
En lugar de probar soluciones al azar, el álgebra nos enseña a:
1. Identificar lo que buscamos (la incógnita)
2. Representar el problema con símbolos
3. Aplicar reglas lógicas para encontrar la solución
4. Verificar que la solución sea correcta

**🔍 Encontrar Patrones y Relaciones**
El álgebra nos entrena para reconocer patrones en datos aparentemente caóticos, una habilidad crucial en nuestra era digital.

**🚀 Desarrollar Pensamiento Abstracto**
Nos permite trabajar con conceptos generales, no solo casos específicos, ampliando nuestra capacidad de comprensión.'''
        },
        {
            'type': 'heading',
            'title': 'Conceptos Básicos que Dominarás'
        },
        {
            'type': 'text',
            'title': 'Variables: Las Incógnitas del Álgebra',
            'content': '''**¿Qué son las variables?**
Las variables son letras que representan números desconocidos o que pueden cambiar. Comúnmente usamos letras como x, y, z, a, b, c.

**Ejemplos en la vida real:**
• x = número de horas trabajadas
• y = distancia recorrida
• z = temperatura actual
• a = costo de un artículo

**Importante**: Una variable puede representar cualquier número, pero en un problema específico usualmente representa un valor particular que debemos encontrar.'''
        },
        {
            'type': 'text',
            'title': 'Constantes: Los Valores Fijos',
            'content': '''**¿Qué son las constantes?**
Las constantes son números fijos que no cambian en una expresión algebraica.

**Ejemplos:**
• Números: 2, 5, 3.14, -7
• Valores fijos en fórmulas: π (pi), e (número e), velocidad de la luz

**En expresiones algebraicas:**
• 2x + 3: 2 y 3 son constantes, x es variable
• 5a - 7b + 12: 5, 7 y 12 son constantes, a y b son variables'''
        },
        {
            'type': 'text',
            'title': 'Expresiones Algebraicas: Combinando Todo',
            'content': '''**¿Qué es una expresión algebraica?**
Es una combinación de variables, constantes y operaciones matemáticas que representa una cantidad.

**Ejemplos:**
• 2x + 3 (lineal)
• x² + 2x - 1 (cuadrática)
• 3a + 2b - 5c (con múltiples variables)
• (x + y) × (a - b) (con paréntesis)

**Tipos de expresiones:**
• **Monomios**: Una sola variable o constante (2x, 5, -3a)
• **Binomios**: Dos términos (x + 2, 3a - b)
• **Trinomios**: Tres términos (x² + 2x - 1)
• **Polinomios**: Cuatro o más términos'''
        },
        {
            'type': 'exercise',
            'content': '''**Ejercicio Interactivo: Identifica Variables vs Constantes**

Analiza las siguientes expresiones e identifica qué elementos son variables y cuáles constantes:

1. **3x + 5 = 17**
   - x: Variable (lo que buscamos)
   - 3, 5, 17: Constantes

2. **2a - b + 7 = 0**
   - a, b: Variables
   - 2, 7: Constantes

3. **πr² (área del círculo)**
   - r: Variable (radio)
   - π: Constante matemática

**¡Practica tú mismo!**
• En la ecuación del costo total: C = 15x + 100
• ¿Qué representa x? ¿Qué representan 15 y 100?
• Si vendo 10 unidades, ¿cuál es el costo total?'''
        },
        {
            'type': 'text',
            'title': 'El Lenguaje del Álgebra: Notación Matemática',
            'content': '''**Símbolos Comunes en Álgebra:**

• **=** : igual a
• **≠** : diferente de
• **<** : menor que
• **>** : mayor que
• **≤** : menor o igual que
• **≥** : mayor o igual que
• **+** : más
• **-** : menos
• **×** o **⋅** : multiplicado por
• **÷** o **/** : dividido por
• **()** : agrupación
• **[]** : agrupación
• **{}** : agrupación
• **²** : al cuadrado
• **³** : al cubo
• **√** : raíz cuadrada

**Ejemplo de expresión completa:**
**(2x + 3) × (x - 1) = 0**

Esta ecuación representa un problema donde necesitamos encontrar valores de x que hagan la ecuación verdadera.'''
        },
        {
            'type': 'heading',
            'title': 'Aplicaciones Prácticas: Álgebra en Acción'
        },
        {
            'type': 'text',
            'title': 'Problema Real: Planificación de un Viaje',
            'content': '''**Situación**: Planeas un viaje de 500 km. Tu auto consume 8 litros cada 100 km y la gasolina cuesta $1.20 por litro.

**¿Cuánto costará el combustible?**

**Razonamiento algebraico:**
1. **Identificar variables**: Distancia = d = 500 km
2. **Calcular consumo**: Litros = (d × 8) ÷ 100
3. **Calcular costo**: Total = Litros × $1.20

**Expresión algebraica**: Costo = [(d × 8) ÷ 100] × 1.20

**Solución**: [(500 × 8) ÷ 100] × 1.20 = 40 × 1.20 = $48

**¡El viaje costará $48 en combustible!**'''
        },
        {
            'type': 'text',
            'title': 'Problema Real: Negocio de Helados',
            'content': '''**Situación**: Vendes helados a $3 cada uno. Tus costos fijos son $50 diarios (alquiler, etc.) y cada helado cuesta $1 producir.

**¿Cuántos helados necesitas vender para no perder dinero?**

**Análisis algebraico:**
• **Ingreso**: 3x (x = helados vendidos)
• **Costo**: 50 + 1x (costos fijos + costo por helado)
• **Ganancia**: Ingreso - Costo = 0 (punto de equilibrio)

**Ecuación**: 3x - (50 + x) = 0
**Solución**: 3x - x - 50 = 0 → 2x = 50 → x = 25

**¡Necesitas vender 25 helados para cubrir costos!**'''
        },
        {
            'type': 'exercise',
            'content': '''**Ejercicio Interactivo: Crea tu Propio Problema Algebraico**

**Instrucciones:**
1. Piensa en una situación de la vida diaria
2. Identifica qué quieres calcular (la incógnita)
3. Crea una expresión algebraica
4. Resuélvela

**Ejemplo:**
• Situación: Comprar libros con descuento
• Incógnita: x = precio original
• Expresión: Precio final = x - (x × 0.20)
• Si pago $32 con 20% descuento, x = 32 ÷ 0.80 = $40

**¡Ahora crea el tuyo!**'''
        },
        {
            'type': 'heading',
            'title': 'Recursos Adicionales para tu Aprendizaje'
        },
        {
            'type': 'list',
            'title': 'Materiales Recomendados',
            'items': [
                '**Libros**: "Álgebra Elemental" de Charles Smith, "Introducción al Álgebra" de Richard Rusczyk',
                '**Videos**: Khan Academy - Álgebra Básica, YouTube - Math Antics',
                '**Apps**: Photomath, Wolfram Alpha, GeoGebra',
                '**Sitios Web**: Wolfram MathWorld, Mathway, Symbolab',
                '**Juegos**: Prodigy Math, DragonBox Algebra',
                '**Cursos Online**: Coursera - Álgebra Lineal, edX - College Algebra'
            ]
        },
        {
            'type': 'text',
            'title': 'Consejos para el Éxito en Álgebra',
            'content': '''**🎯 Estrategias de Aprendizaje:**

1. **Practica Diariamente**: La consistencia es clave en matemáticas
2. **Entiende los Conceptos**: No memorices, comprende el "porqué"
3. **Trabaja con Ejemplos**: Empieza con casos simples, progresa a complejos
4. **Verifica tus Respuestas**: Siempre comprueba que la solución sea correcta
5. **No Temas Equivocarte**: Los errores son oportunidades de aprendizaje
6. **Busca Ayuda**: Pregunta cuando no entiendas, no te quedes atascado
7. **Aplica lo Aprendido**: Usa el álgebra en situaciones reales
8. **Mantén la Curiosidad**: El álgebra es una herramienta poderosa, ¡diviértete usándola!

**💪 Recuerda**: Todo experto fue principiante alguna vez. ¡Tú puedes dominar el álgebra!'''
        },
        {
            'type': 'markdown',
            'content': '''## 📚 Glosario de Términos Clave

**Variable**: Letra que representa un número desconocido o que puede cambiar
**Constante**: Número fijo que no cambia en una expresión
**Expresión Algebraica**: Combinación de variables, constantes y operaciones
**Ecuación**: Afirmación matemática de que dos expresiones son iguales
**Coeficiente**: Número que multiplica a una variable
**Término**: Parte de una expresión separada por + o -
**Monomio**: Expresión algebraica con un solo término
**Binomio**: Expresión algebraica con dos términos
**Polinomio**: Expresión algebraica con múltiples términos

## 🎯 Próximos Pasos

Después de esta introducción, estarás listo para:
1. **Trabajar con expresiones algebraicas**
2. **Resolver ecuaciones lineales**
3. **Entender funciones y gráficas**
4. **Aplicar álgebra a problemas complejos**

**¡El viaje apenas comienza! 🚀**'''
        }
    ]

    # Actualizar la lección
    lesson.structured_content = structured_content
    lesson.duration_minutes = 25  # Aumentar duración por contenido más rico
    lesson.save()

    print('SUCCESS: Leccion actualizada exitosamente con contenido completo y estetico')
    print(f'Titulo: {lesson.title}')
    print(f'Duracion: {lesson.duration_minutes} minutos')
    print(f'Elementos de contenido: {len(structured_content)}')

if __name__ == '__main__':
    update_lesson_content()