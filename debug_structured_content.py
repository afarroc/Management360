#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from bitacora.models import BitacoraEntry

def debug_structured_content():
    """Depurar el contenido estructurado de las entradas"""

    # Buscar entradas con contenido estructurado
    entries = BitacoraEntry.objects.filter(structured_content__isnull=False).exclude(structured_content=[])

    if not entries.exists():
        print("No se encontraron entradas con contenido estructurado")
        return

    for entry in entries:
        print(f"\n=== ENTRADA: {entry.titulo} (ID: {entry.id}) ===")
        print(f"Contenido estructurado: {len(entry.structured_content)} bloques")

        for i, block in enumerate(entry.structured_content, 1):
            print(f"\nBloque {i}:")
            print(f"  Tipo: {type(block)}")
            print(f"  Claves: {list(block.keys()) if isinstance(block, dict) else 'No es dict'}")

            if isinstance(block, dict):
                for key, value in block.items():
                    if key == 'content':
                        print(f"    {key}: {type(value)} - {str(value)[:100]}...")
                    else:
                        print(f"    {key}: {value}")

if __name__ == '__main__':
    debug_structured_content()