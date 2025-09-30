#!/usr/bin/env python
import os
import sys

# Añadir el directorio actual al path
sys.path.insert(0, os.getcwd())

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')

import django
django.setup()

from events.models import InboxItem
from django.contrib.auth.models import User

print('Verificando item 110...')
item = InboxItem.objects.filter(id=110).first()
if item:
    print('Item 110 existe:')
    print(f'  - Titulo: {item.title}')
    print(f'  - Descripcion: {item.description}')
    print(f'  - Creado por: {item.created_by.username if item.created_by else None}')
    print(f'  - Asignado a: {item.assigned_to.username if item.assigned_to else None}')
    print(f'  - Categoria GTD: {item.gtd_category}')
    print(f'  - Prioridad: {item.priority}')
    print(f'  - Procesado: {item.is_processed}')
    print(f'  - Fecha creacion: {item.created_at}')
else:
    print('Item 110 no existe')
    print('Creando item de prueba...')
    test_item = InboxItem.objects.create(
        title='Item de prueba 110',
        description='Descripcion de prueba para item 110',
        created_by=User.objects.get(username='su'),
        gtd_category='pendiente',
        priority='media'
    )
    print(f'Item creado con ID: {test_item.id}')

print(f'\nTotal de items en inbox: {InboxItem.objects.count()}')
print(f'Usuarios disponibles: {list(User.objects.values_list("username", flat=True))}')