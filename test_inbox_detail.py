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

# Verificar el estado del item después de la delegación
item = InboxItem.objects.get(id=99)
print("Item 99 - Asignado a:", item.assigned_to.username if item.assigned_to else None)
print("Item 99 - Título:", item.title)
print("Item 99 - Categoría GTD:", item.gtd_category)

# Probar acceso a la vista de detalles del item
response = client.get('/events/inbox/admin/99/')
print("Acceso a inbox item detail - Código:", response.status_code)

if response.status_code == 200:
    print("TEST PASADO: Vista de detalles funciona correctamente")
    # Verificar que el contenido contiene información del item
    content = response.content.decode()
    if item.title in content:
        print("TEST PASADO: El título del item aparece en la página")
    else:
        print("TEST FALLADO: El título del item no aparece en la página")
else:
    print("TEST FALLADO: No se pudo acceder a la vista de detalles")
    print("Contenido de respuesta:", response.content.decode()[:500])