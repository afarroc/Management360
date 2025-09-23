#!/usr/bin/env python
"""
Script para crear una lección independiente con contenido estructurado
"""
import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import Lesson, ContentBlock
from django.contrib.auth.models import User
import json

def create_standalone_lesson():
    """Crear una lección independiente con contenido estructurado"""

    print("=== CREANDO LECCIÓN INDEPENDIENTE ===")

    # Verificar usuarios con CV
    users_with_cv = User.objects.filter(cv__isnull=False)
    print(f"Usuarios con CV encontrados: {users_with_cv.count()}")

    if not users_with_cv.exists():
        print("❌ No hay usuarios con CV. No se puede crear la lección.")
        return False

    # Usar el primer usuario con CV
    author = users_with_cv.first()
    print(f"📝 Usando autor: {author.username} ({author.get_full_name()})")

    # Obtener algunos bloques de contenido existentes
    content_blocks = ContentBlock.objects.filter(is_public=True)[:3]  # Obtener 3 bloques públicos

    # Contenido estructurado completo con elementos de lección y bloques de contenido
    structured_content = [
        {
            "type": "heading",
            "title": "Introducción a la Programación en Python",
            "content": "Aprende los fundamentos de la programación con uno de los lenguajes más populares del mundo"
        },
        {
            "type": "text",
            "title": "¿Por qué Python?",
            "content": """Python es un lenguaje de programación de alto nivel, interpretado y de propósito general.

**Ventajas principales:**
- Fácil de aprender y usar
- Gran comunidad de desarrolladores
- Amplia biblioteca de módulos
- Multiplataforma

*Características destacadas:*
- Sintaxis clara y legible
- Tipado dinámico
- Gestión automática de memoria
- Soporte para programación orientada a objetos"""
        },
        {
            "type": "content_block",
            "content": content_blocks[0].id if content_blocks else None
        },
        {
            "type": "list",
            "title": "Conceptos que aprenderás",
            "items": [
                "Variables y tipos de datos básicos",
                "Estructuras de control (if, for, while)",
                "Funciones y módulos",
                "Programación orientada a objetos",
                "Manejo de archivos",
                "Bibliotecas estándar más importantes"
            ]
        },
        {
            "type": "image",
            "title": "Logo oficial de Python",
            "content": "https://www.python.org/static/community_logos/python-logo.png"
        },
        {
            "type": "content_block",
            "content": content_blocks[1].id if len(content_blocks) > 1 else None
        },
        {
            "type": "text",
            "title": "Primeros pasos",
            "content": """Para comenzar con Python, necesitarás:

1. Instalar Python desde el sitio oficial
2. Configurar tu entorno de desarrollo
3. Aprender la sintaxis básica
4. Practicar con ejercicios simples

**Recuerda:** La práctica constante es la clave del éxito en programación.

> "El código es como el humor. Cuando tienes que explicarlo, es malo." - Cory House"""
        },
        {
            "type": "content_block",
            "content": content_blocks[2].id if len(content_blocks) > 2 else None
        },
        {
            "type": "file",
            "title": "Guía de instalación de Python",
            "content": "/media/files/python-installation-guide.pdf"
        }
    ]

    try:
        # Crear la lección independiente
        lesson = Lesson.objects.create(
            title="Python con ContentBlocks",
            author=author,
            lesson_type="text",
            content="Esta es una lección independiente completa sobre programación en Python con contenido estructurado, ejemplos prácticos, recursos adicionales y bloques de contenido reutilizables.",
            structured_content=structured_content,
            duration_minutes=45,
            order=1,
            is_free=True,
            is_published=True,
            description="Lección completa sobre los fundamentos de Python con contenido estructurado, ejemplos prácticos, recursos adicionales y bloques de contenido reutilizables."
        )

        print("✅ Lección creada exitosamente!")
        print(f"   📚 Título: {lesson.title}")
        print(f"   👤 Autor: {lesson.author.username}")
        print(f"   🆔 ID: {lesson.id}")
        print(f"   🔗 Slug: {lesson.slug}")
        print(f"   ⏱️ Duración: {lesson.duration_minutes} minutos")
        print(f"   📋 Elementos estructurados: {len(lesson.structured_content)}")
        print(f"   🌐 URL: /courses/lessons/{lesson.slug}/")
        print(f"   📅 Creada: {lesson.created_at.strftime('%d/%m/%Y %H:%M')}")

        # Verificar que se guardó correctamente
        standalone_lessons = Lesson.objects.filter(module__isnull=True)
        print(f"\\n📊 Total de lecciones independientes: {standalone_lessons.count()}")

        return True

    except Exception as e:
        print(f"❌ Error al crear la lección: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_content_rendering():
    """Probar que el contenido estructurado se renderice correctamente"""
    print("\\n=== PROBANDO RENDERIZADO DE CONTENIDO ===")

    try:
        from courses.templatetags.lesson_tags import render_structured_content

        # Obtener la lección que acabamos de crear
        lesson = Lesson.objects.filter(module__isnull=True).latest('created_at')

        print(f"🔍 Probando renderizado de: {lesson.title}")

        # Renderizar el contenido
        rendered_html = render_structured_content(lesson.structured_content)

        if rendered_html:
            print("✅ Renderizado exitoso!")
            print(f"   📄 Longitud del HTML: {len(rendered_html)} caracteres")

            # Verificar que contiene elementos esperados
            checks = [
                ('heading', 'lesson-heading-container' in rendered_html),
                ('text', 'lesson-text-container' in rendered_html),
                ('list', 'lesson-list-container' in rendered_html),
                ('image', 'lesson-image-container' in rendered_html),
                ('file', 'lesson-file' in rendered_html)
            ]

            print("   📋 Elementos encontrados:")
            for element_type, found in checks:
                status = "✅" if found else "❌"
                print(f"      {status} {element_type}")

            return True
        else:
            print("❌ Error: No se generó HTML")
            return False

    except Exception as e:
        print(f"❌ Error en el renderizado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando creación de lección independiente...")

    # Crear la lección
    success = create_standalone_lesson()

    if success:
        # Probar el renderizado
        test_content_rendering()

        print("\\n🎉 ¡Proceso completado exitosamente!")
        print("📖 La lección independiente está lista y se puede acceder en:")
        lesson = Lesson.objects.filter(module__isnull=True).latest('created_at')
        print(f"   http://localhost:8000/courses/lessons/{lesson.slug}/")
    else:
        print("\\n💥 Error en el proceso. Revisa los mensajes anteriores.")
        sys.exit(1)