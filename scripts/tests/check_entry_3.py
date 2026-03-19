#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from bitacora.models import BitacoraEntry

def check_entry_3():
    try:
        entry = BitacoraEntry.objects.get(id=3)
        print('=== ENTRADA ENCONTRADA ===')
        print(f'ID: {entry.id}')
        print(f'Titulo: {entry.titulo}')
        print(f'Autor: {entry.autor.username}')
        print(f'Categoria: {entry.get_categoria_display()}')
        print(f'Contenido principal: {entry.contenido[:100]}...' if len(entry.contenido) > 100 else f'Contenido principal: {entry.contenido}')

        print(f'\nContenido estructurado: {entry.structured_content}')
        print(f'Longitud del contenido estructurado: {len(entry.structured_content) if entry.structured_content else 0}')

        if entry.structured_content:
            print('\n=== BLOQUES ESTRUCTURADOS ===')
            for i, block in enumerate(entry.structured_content):
                print(f'Bloque {i+1}:')
                print(f'  - Titulo: {block.get("title", "Sin titulo")}')
                print(f'  - Tipo: {block.get("content_type", "Sin tipo")}')
                print(f'  - ID: {block.get("id", "Sin ID")}')
                print(f'  - Insertado: {block.get("inserted_at", "Sin fecha")}')
                content_preview = block.get("content", "")[:100] + "..." if len(block.get("content", "")) > 100 else block.get("content", "")
                print(f'  - Contenido: {content_preview}')
                print()

        # Verificar si tiene adjuntos
        attachments = entry.attachments.all()
        print(f'Adjuntos: {attachments.count()}')
        for attachment in attachments:
            print(f'  - {attachment.tipo}: {attachment.archivo.url}')

        print('\n=== RENDERIZADO ===')
        rendered = entry.render_structured_content()
        print(f'Contenido renderizado: {rendered[:200]}...' if len(rendered) > 200 else f'Contenido renderizado: {rendered}')

    except BitacoraEntry.DoesNotExist:
        print('ERROR: Entrada con ID 3 no existe')
        # Listar todas las entradas disponibles
        all_entries = BitacoraEntry.objects.all()
        print(f'Entradas disponibles: {all_entries.count()}')
        for entry in all_entries:
            print(f'  - ID {entry.id}: {entry.titulo}')
    except Exception as e:
        print(f'ERROR: {e}')

if __name__ == '__main__':
    check_entry_3()