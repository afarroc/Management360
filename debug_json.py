#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from bitacora.models import BitacoraEntry

def debug_json_block():
    try:
        entry = BitacoraEntry.objects.get(id=3)

        print("=== DEBUG JSON BLOCK ===")
        print(f"Entrada: {entry.titulo}")

        for i, block in enumerate(entry.structured_content):
            print(f"\n--- Bloque {i+1}: {block.get('title', 'Sin titulo')} ---")
            print(f"Tipo: {block.get('content_type', 'Sin tipo')}")
            print(f"ID: {block.get('id', 'Sin ID')}")

            content = block.get('content', '')
            print(f"Contenido (tipo): {type(content)}")
            print(f"Contenido (longitud): {len(str(content))}")

            if block['content_type'] == 'json':
                print("=== CONTENIDO JSON ===")
                try:
                    # Intentar parsear como JSON
                    import json
                    if isinstance(content, str):
                        parsed = json.loads(content)
                        print(f"JSON parseado correctamente: {type(parsed)}")
                        print(f"Contenido: {parsed}")
                    else:
                        print(f"Contenido ya es {type(content)}: {content}")
                except json.JSONDecodeError as e:
                    print(f"ERROR parseando JSON: {e}")
                    print(f"Contenido raw: {repr(content)}")
                except Exception as e:
                    print(f"ERROR general: {e}")

            # Intentar renderizar este bloque específico
            try:
                rendered = entry.render_content_block(block)
                print(f"Renderizado exitoso: {len(rendered)} caracteres")
                print(f"Preview: {rendered[:200]}...")
            except Exception as e:
                print(f"ERROR en renderizado: {e}")

    except Exception as e:
        print(f"ERROR general: {e}")

if __name__ == '__main__':
    debug_json_block()