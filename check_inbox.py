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

print('Items en inbox:', InboxItem.objects.count())
print('Usuarios:', list(User.objects.values_list('username', flat=True)))
item = InboxItem.objects.filter(id=99).first()
print('Item 99 existe:', item is not None)
if item:
    print('Asignado a:', item.assigned_to)
    print('Título:', item.title)
    print('Categoría GTD:', item.gtd_category)
else:
    print('Creando item de prueba...')
    # Crear un item de prueba
    test_item = InboxItem.objects.create(
        title='Item de prueba para delegación',
        description='Este es un item de prueba para testear la funcionalidad de delegación',
        created_by=User.objects.get(username='su'),
        gtd_category='pendiente',
        priority='media'
    )
    print(f'Item creado con ID: {test_item.id}')