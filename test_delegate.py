#!/usr/bin/env python
import os
import sys

# Añadir el directorio actual al path
sys.path.insert(0, os.getcwd())

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from events.models import InboxItem

# Crear cliente de test con host permitido
client = Client(HTTP_HOST='localhost', enforce_csrf_checks=False)

# Hacer login como superuser
user = User.objects.get(username='su')
client.force_login(user)

print("Usuario autenticado:", user.username)

# Probar acceso a la vista primero
test_response = client.get('/events/inbox/admin/')
print("Acceso a inbox admin - Codigo:", test_response.status_code)

# Verificar el estado inicial del item
item = InboxItem.objects.get(id=99)
print("Estado inicial - Asignado a:", item.assigned_to.username if item.assigned_to else None)

# Usuario destino para delegar (usemos 'arturo' con ID 2)
target_user = User.objects.get(id=2)
print("Delegando a:", target_user.username)

# Hacer la petición POST para delegar usando root bulk actions
response = client.post('/events/root/bulk-actions/', {
    'action': 'delegate',
    'selected_items[]': '99',
    'delegate_user_id': str(target_user.id)
})

print("Codigo de respuesta:", response.status_code)
print("URL de redireccion:", response.get('Location', 'Ninguna'))
print("Contenido de respuesta:", response.content.decode()[:500] + "..." if len(response.content.decode()) > 500 else response.content.decode())

# Verificar el estado final del item
item.refresh_from_db()
print("Estado final - Asignado a:", item.assigned_to.username if item.assigned_to else None)

if item.assigned_to == target_user:
    print("TEST PASADO: Item correctamente delegado")
else:
    print("TEST FALLADO: Item no fue delegado correctamente")