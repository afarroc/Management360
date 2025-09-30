#!/usr/bin/env python3
"""
Simulación de click para probar la opción 'Vincular a Tarea Existente'
en el panel de control inbox cuando el inbox es asignado por otro usuario
"""
import os
import sys
import django
import requests
from django.test import Client
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from events.models import Task, InboxItem, TaskStatus, Status


def simulate_click_test():
    """
    Simula el click en 'Vincular a Tarea Existente' sin permisos
    """
    print("=== Simulación de Click: Vincular a Tarea Existente ===")

    # Crear datos de prueba directamente en la base de datos real
    try:
        # Crear usuarios si no existen
        user1, created1 = User.objects.get_or_create(
            username='test_user1',
            defaults={
                'email': 'user1@test.com',
                'first_name': 'Usuario',
                'last_name': 'Uno'
            }
        )
        if created1:
            user1.set_password('testpass123')
            user1.save()

        user2, created2 = User.objects.get_or_create(
            username='test_user2',
            defaults={
                'email': 'user2@test.com',
                'first_name': 'Usuario',
                'last_name': 'Dos'
            }
        )
        if created2:
            user2.set_password('testpass123')
            user2.save()

        user3, created3 = User.objects.get_or_create(
            username='test_user3',
            defaults={
                'email': 'user3@test.com',
                'first_name': 'Usuario',
                'last_name': 'Tres'
            }
        )
        if created3:
            user3.set_password('testpass123')
            user3.save()

        print("✅ Usuarios creados/verificados")

        # Crear estados si no existen
        task_status, _ = TaskStatus.objects.get_or_create(status_name='To Do')
        event_status, _ = Status.objects.get_or_create(status_name='Created')

        print("✅ Estados creados/verificados")

        # Crear tarea existente propiedad de user3
        existing_task, created_task = Task.objects.get_or_create(
            title='Tarea existente de user3 para prueba',
            defaults={
                'description': 'Esta tarea pertenece a user3 y no debe ser accesible por user2',
                'host': user3,
                'assigned_to': user3,
                'task_status': task_status,
                'ticket_price': 0.07
            }
        )

        print(f"✅ Tarea existente creada: {existing_task.title} (ID: {existing_task.id})")

        # Crear inbox item creado por user1 y asignado a user2
        inbox_item, created_inbox = InboxItem.objects.get_or_create(
            title='Inbox item asignado para prueba de permisos',
            defaults={
                'description': 'Este inbox fue creado por user1 pero asignado a user2',
                'created_by': user1,
                'assigned_to': user2,
                'is_processed': False,
                'gtd_category': 'accionable',
                'priority': 'media'
            }
        )

        print(f"✅ Inbox item creado: {inbox_item.title} (ID: {inbox_item.id})")
        print(f"   - Creado por: {inbox_item.created_by.username}")
        print(f"   - Asignado a: {inbox_item.assigned_to.username}")

        # Simular el click usando Django test client
        client = Client()

        # Hacer login como user2 (el asignado al inbox)
        login_success = client.login(username='test_user2', password='testpass123')
        if not login_success:
            print("❌ Error: No se pudo hacer login como user2")
            return False

        print("✅ Login exitoso como user2")

        # Simular POST request a process_inbox_item con action 'link_to_task'
        url = f'/events/process_inbox_item/{inbox_item.id}/'
        post_data = {
            'action': 'link_to_task',
            'task_id': str(existing_task.id)
        }

        print(f"🚀 Enviando POST request a: {url}")
        print(f"   Datos: {post_data}")

        response = client.post(url, post_data, follow=True)

        print(f"📡 Response status: {response.status_code}")
        print(f"📡 Response redirect chain: {[r[0] for r in response.redirect_chain]}")

        # Verificar el resultado
        if response.status_code == 200:
            # Verificar si hay mensajes de error
            messages = list(get_messages(response.wsgi_request))
            error_messages = [str(msg) for msg in messages if msg.level_tag == 'error']

            if error_messages:
                print("✅ ¡Prueba PASADA! Se mostró mensaje de error esperado:")
                for msg in error_messages:
                    print(f"   ❌ {msg}")
            else:
                print("❌ Prueba FALLIDA: No se mostró mensaje de error")

            # Verificar que el inbox item NO fue procesado
            inbox_item.refresh_from_db()
            if not inbox_item.is_processed:
                print("✅ Correcto: El inbox item no fue marcado como procesado")
            else:
                print("❌ Error: El inbox item fue marcado como procesado incorrectamente")

        else:
            print(f"❌ Error HTTP: {response.status_code}")

        # Limpiar datos de prueba
        print("\n🧹 Limpiando datos de prueba...")
        try:
            inbox_item.delete()
            existing_task.delete()
            print("✅ Datos de prueba eliminados")
        except Exception as e:
            print(f"⚠️  Error al limpiar datos: {e}")

        return True

    except Exception as e:
        print(f"❌ Error durante la simulación: {e}")
        import traceback
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"❌ Error durante la simulación: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Iniciando simulación de click para 'Vincular a Tarea Existente'")
    print("=" * 60)

    success = simulate_click_test()

    print("\n" + "=" * 60)
    if success:
        print("🎉 Simulación completada exitosamente")
    else:
        print("❌ Simulación fallida")
        sys.exit(1)