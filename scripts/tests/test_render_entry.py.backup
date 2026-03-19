#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from bitacora.views import BitacoraDetailView
from bitacora.models import BitacoraEntry

def test_entry_rendering():
    """Probar que una entrada con contenido estructurado se renderiza correctamente"""

    # Crear usuario de prueba si no existe
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )

    # Buscar la entrada creada anteriormente (ID 6)
    try:
        entry = BitacoraEntry.objects.get(id=6, autor=user)
        print(f"Entrada encontrada: {entry.titulo}")
        print(f"Tiene {len(entry.structured_content)} componentes estructurados")
    except BitacoraEntry.DoesNotExist:
        print("Entrada no encontrada, buscando cualquier entrada con contenido estructurado...")
        entries_with_structured = BitacoraEntry.objects.filter(structured_content__isnull=False).exclude(structured_content=[])
        if entries_with_structured.exists():
            entry = entries_with_structured.first()
            print(f"Entrada encontrada: {entry.titulo} (ID: {entry.id})")
            print(f"Tiene {len(entry.structured_content)} componentes estructurados")
        else:
            print("No se encontraron entradas con contenido estructurado")
            return

    # Crear una request simulada
    factory = RequestFactory()
    request = factory.get(f'/bitacora/{entry.id}/')
    request.user = user

    # Crear la vista y obtener el contexto
    view = BitacoraDetailView()
    view.request = request
    view.object = entry

    context = view.get_context_data()

    # Verificar el contexto
    print("\n=== CONTEXTO DE LA VISTA ===")
    print(f"Entry: {context['entry'].titulo}")
    print(f"Rendered structured content: {len(context.get('rendered_structured_content', []))} bloques")

    # Verificar que el contenido renderizado existe
    rendered_blocks = context.get('rendered_structured_content', [])
    if rendered_blocks:
        print("\n=== BLOQUES RENDERIZADOS ===")
        for i, block in enumerate(rendered_blocks, 1):
            print(f"Bloque {i}:")
            print(f"  - Título: {block.get('title', 'Sin título')}")
            print(f"  - Tipo: {block.get('type', 'Desconocido')}")
            print(f"  - Rendered content length: {len(block.get('rendered_content', ''))} caracteres")

            # Mostrar preview del contenido renderizado (primeros 200 chars)
            rendered = block.get('rendered_content', '')
            if rendered:
                preview = rendered[:200] + "..." if len(rendered) > 200 else rendered
                print(f"  - Preview: {preview.replace(chr(10), ' ').replace(chr(13), ' ')}")
            print()

        # Verificar que contiene elementos HTML esperados
        all_rendered = ''.join([block.get('rendered_content', '') for block in rendered_blocks])
        checks = [
            ('ad-banner', 'Banner publicitario'),
            ('ad-card', 'Tarjeta publicitaria'),
            ('bg-primary', 'Estilos Bootstrap'),
            ('btn', 'Botones'),
            ('PREMIUM', 'Texto del banner'),
            ('Ejercicios', 'Texto de la card'),
        ]

        print("=== VERIFICACIONES HTML ===")
        for check, description in checks:
            found = check in all_rendered
            status = "[OK]" if found else "[FAIL]"
            print(f"{status} {description}: {'Encontrado' if found else 'No encontrado'}")

        success = any(check in all_rendered for check, _ in checks)
        print(f"\n[{'OK' if success else 'ERROR'}] Los componentes JSON se renderizan correctamente como HTML")

    else:
        print("ERROR: No se encontraron bloques renderizados")

if __name__ == '__main__':
    test_entry_rendering()