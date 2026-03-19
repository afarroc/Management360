#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from bitacora.models import BitacoraEntry
from courses.models import ContentBlock
from django.utils import timezone

def add_content_blocks_to_entry_3():
    try:
        # Obtener la entrada
        entry = BitacoraEntry.objects.get(id=3)
        print(f'Entrada encontrada: {entry.titulo}')

        # Obtener algunos bloques de contenido disponibles
        content_blocks = ContentBlock.objects.filter(is_public=True)[:3]  # Tomar los primeros 3 públicos

        if not content_blocks:
            print('No hay bloques de contenido publicos disponibles. Creando uno de prueba...')
            # Crear un bloque de contenido de prueba
            test_block = ContentBlock.objects.create(
                title='Bloque de Prueba',
                slug='bloque-prueba',
                description='Bloque de contenido para pruebas',
                content_type='html',
                html_content='<div class="alert alert-success"><h4>Contenido de Prueba</h4><p>Este es un bloque de contenido de prueba insertado en la bitacora.</p></div>',
                author=entry.autor,
                is_public=True
            )
            content_blocks = [test_block]

        # Agregar bloques al contenido estructurado de la entrada
        structured_content = entry.get_structured_content_blocks()

        for block in content_blocks:
            structured_content.append({
                'id': block.id,
                'type': 'content_block',
                'title': block.title,
                'content_type': block.content_type,
                'content': block.get_content(),
                'inserted_at': timezone.now().isoformat(),
            })
            print(f'Agregado bloque: {block.title} ({block.content_type})')

        # Guardar la entrada
        entry.structured_content = structured_content
        entry.save()

        print(f'\nContenido estructurado actualizado. Total de bloques: {len(structured_content)}')

        # Verificar el renderizado
        rendered = entry.render_structured_content()
        print(f'\nContenido renderizado (primeros 300 caracteres):')
        print(rendered[:300] + '...' if len(rendered) > 300 else rendered)

    except BitacoraEntry.DoesNotExist:
        print('ERROR: Entrada con ID 3 no existe')
    except Exception as e:
        print(f'ERROR: {e}')

if __name__ == '__main__':
    add_content_blocks_to_entry_3()