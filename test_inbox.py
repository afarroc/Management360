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

# Verificar si existe el item 99
item = InboxItem.objects.filter(id=99).first()
print('Item 99 existe:', item is not None)
if item:
    print('Título:', item.title)
    print('Asignado a:', item.assigned_to.username if item.assigned_to else None)
    print('Procesado:', item.is_processed)
else:
    # Crear un item de prueba si no existe
    print('Creando item de prueba...')
    user = User.objects.get(id=1)  # su
    item = InboxItem.objects.create(
        title='Item de prueba para delegación',
        description='Este es un item de prueba para testear la funcionalidad de delegación',
        created_by=user,
        gtd_category='pendiente',
        priority='media'
    )
    print(f'Item creado con ID: {item.id}')