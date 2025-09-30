from events.models import InboxItem
from django.contrib.auth.models import User
from django.test import Client

# Obtener datos
inbox_item = InboxItem.objects.first()
if inbox_item:
    print(f'Inbox item encontrado: ID={inbox_item.id}, Title={inbox_item.title}')
    print(f'Description: {inbox_item.description}')
    print(f'Created by: {inbox_item.created_by.username}')
    print(f'GTD Category: {inbox_item.gtd_category}')
    print(f'Priority: {inbox_item.priority}')
    print(f'Is processed: {inbox_item.is_processed}')
else:
    print('No hay items en el inbox')

# Probar vista
client = Client()
admin_user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first() or User.objects.first()
if admin_user:
    client.force_login(admin_user)
    if inbox_item:
        response = client.get(f'/events/inbox/admin/{inbox_item.id}/')
        print(f'Status code: {response.status_code}')
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if inbox_item.title in content:
                print('SUCCESS: Título encontrado en respuesta')
            else:
                print('ERROR: Título NO encontrado en respuesta')
        else:
            print(f'ERROR: Status {response.status_code}')
    else:
        print('No hay item para probar')
else:
    print('No hay usuario para probar')