from events.models import InboxItem
from django.contrib.auth.models import User
from django.test import Client
import sys

print('=== Iniciando prueba de vista inbox_item_detail_admin ===', file=sys.stderr)

# Obtener item específico
try:
    inbox_item = InboxItem.objects.get(id=99)
    print(f'Item encontrado: ID={inbox_item.id}, Title="{inbox_item.title}"', file=sys.stderr)
except InboxItem.DoesNotExist:
    inbox_item = InboxItem.objects.first()
    if inbox_item:
        print(f'Usando primer item: ID={inbox_item.id}, Title="{inbox_item.title}"', file=sys.stderr)
    else:
        print('ERROR: No hay items en inbox', file=sys.stderr)
        sys.exit(1)

# Probar vista
client = Client()
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.filter(is_staff=True).first()
if not admin_user:
    admin_user = User.objects.first()

if admin_user:
    print(f'Usuario encontrado: {admin_user.username}', file=sys.stderr)
    client.force_login(admin_user)

    response = client.get(f'/events/inbox/admin/{inbox_item.id}/')
    print(f'Status code: {response.status_code}', file=sys.stderr)

    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if inbox_item.title in content:
            print('SUCCESS: Título encontrado en respuesta', file=sys.stderr)
        else:
            print('ERROR: Título NO encontrado', file=sys.stderr)
            print('Contenido (primeros 200 chars):', repr(content[:200]), file=sys.stderr)
    else:
        print(f'ERROR: Status {response.status_code}', file=sys.stderr)
else:
    print('ERROR: No hay usuarios', file=sys.stderr)