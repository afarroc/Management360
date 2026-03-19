#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from bitacora.models import BitacoraEntry

def verify_blocks():
    try:
        entry = BitacoraEntry.objects.get(id=3)
        print(f'Entrada: {entry.titulo}')
        print(f'Bloques estructurados: {len(entry.structured_content)}')

        for i, block in enumerate(entry.structured_content):
            print(f'{i+1}. {block["title"]} - {block["content_type"]}')

        # Verificar que se renderiza
        rendered = entry.render_structured_content()
        has_content = len(rendered.strip()) > 0
        print(f'Contenido renderizado: {"SI" if has_content else "NO"}')
        print(f'Longitud renderizado: {len(rendered)} caracteres')

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    verify_blocks()