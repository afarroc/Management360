#!/usr/bin/env python
"""
Script para probar el preview de ContentBlocks con contenido JSON estructurado
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import ContentBlock
from courses.templatetags.lesson_tags import get_structured_content, render_structured_content

def test_content_block_preview():
    """Probar el preview de un ContentBlock con contenido JSON"""

    print("=== Probando Preview de ContentBlock ===\n")

    # Eliminar ContentBlock existente si existe
    try:
        existing_block = ContentBlock.objects.get(slug='ejercicio')
        print(f"[INFO] Eliminando ContentBlock existente: {existing_block.title}")
        existing_block.delete()
    except ContentBlock.DoesNotExist:
        pass

    # Crear un ContentBlock de prueba
    print("[INFO] Creando nuevo ContentBlock con contenido JSON estructurado...")

    # Obtener o crear usuario de prueba
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print("[OK] Usuario de prueba creado")

    # Crear ContentBlock con contenido JSON estructurado más complejo
    block = ContentBlock.objects.create(
        title='Ejercicio Completo de Programación',
        slug='ejercicio',
        description='Un ejercicio completo con múltiples elementos estructurados',
        content_type='json',
        author=user,
        category='Programación',
        tags='programación, ejercicio, completo, python',
        is_public=True,
        json_content=[
            {
                'type': 'heading',
                'level': 1,
                'title': 'Ejercicio: Variables y Operaciones Matemáticas'
            },
            {
                'type': 'text',
                'content': 'En este ejercicio aprenderás a trabajar con variables y operaciones matemáticas básicas en Python.'
            },
            {
                'type': 'list',
                'ordered': True,
                'items': [
                    'Declara variables para almacenar datos',
                    'Realiza operaciones aritméticas',
                    'Muestra resultados formateados',
                    'Trabaja con diferentes tipos de datos'
                ]
            },
            {
                'type': 'heading',
                'level': 2,
                'title': 'Instrucciones'
            },
            {
                'type': 'text',
                'content': 'Crea un programa que calcule el área de un círculo y realice varias operaciones matemáticas.'
            },
            {
                'type': 'code',
                'language': 'python',
                'code': 'PI = 3.14159\nradio = float(input("Ingresa el radio: "))\narea = PI * radio ** 2\nprint(f"Area: {area:.2f}")'
            },
            {
                'type': 'exercise',
                'title': 'Ejercicio Práctico',
                'description': 'Implementa el código anterior y añade operaciones adicionales',
                'difficulty': 'beginner',
                'estimated_time': 20
            }
        ]
    )
    print(f"[OK] ContentBlock creado: {block.title}")

    # Mostrar información del ContentBlock
    print(f"\n[INFO] Información del ContentBlock:")
    print(f"   Título: {block.title}")
    print(f"   Tipo: {block.content_type}")
    print(f"   Slug: {block.slug}")
    print(f"   Autor: {block.author.username}")
    print(f"   Público: {block.is_public}")
    print(f"   Categoría: {block.category}")
    print(f"   Etiquetas: {block.tags}")

    # Probar el filtro get_structured_content
    print(f"\n[TEST] Probando filtro get_structured_content...")
    try:
        structured_content = get_structured_content(block)
        print(f"[OK] Filtro ejecutado exitosamente")
        print(f"   Tipo de retorno: {type(structured_content)}")
        print(f"   Número de elementos: {len(structured_content)}")

        for i, element in enumerate(structured_content):
            print(f"   Elemento {i+1}: {element.get('type', 'unknown')} - {element.get('title', 'sin título')}")

    except Exception as e:
        print(f"[ERROR] Error en get_structured_content: {e}")
        return

    # Probar el filtro render_structured_content
    print(f"\n[TEST] Probando filtro render_structured_content...")
    try:
        rendered_html = render_structured_content(structured_content)
        print(f"[OK] Renderizado exitoso")
        print(f"   Longitud del HTML: {len(rendered_html)} caracteres")

        # Mostrar información sobre el HTML generado
        print(f"   Contiene HTML valido: {'<' in rendered_html and '>' in rendered_html}")

        # Buscar elementos específicos
        if '<div' in rendered_html:
            print(f"   Contiene elementos div: SI")
        if '<p' in rendered_html:
            print(f"   Contiene parrafos: SI")
        if '<h' in rendered_html:
            print(f"   Contiene encabezados: SI")

    except Exception as e:
        print(f"[ERROR] Error en render_structured_content: {e}")
        import traceback
        traceback.print_exc()

    # Verificar que el ContentBlock tenga el contenido esperado
    print(f"\n[INFO] Contenido JSON del ContentBlock:")
    if block.json_content:
        import json
        try:
            json_str = json.dumps(block.json_content, indent=2, ensure_ascii=False)
            print(f"   JSON valido: SI")
            print(f"   Longitud del JSON: {len(json_str)} caracteres")
            # Mostrar primeras líneas sin caracteres especiales
            lines = json_str.split('\n')[:5]
            for line in lines:
                print(f"   {line}")
            if len(json_str.split('\n')) > 5:
                print("   ...")
        except:
            print("   Error al procesar JSON")
    else:
        print("   No hay contenido JSON")

    print(f"\n[SUCCESS] Prueba completada exitosamente!")
    print(f"\n[INFO] Para ver el preview completo, visita:")
    print(f"   http://192.168.18.47:5000/courses/content/{block.slug}/preview/")

if __name__ == '__main__':
    test_content_block_preview()