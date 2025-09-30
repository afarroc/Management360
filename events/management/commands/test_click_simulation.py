#!/usr/bin/env python3
"""
Comando de Django para probar la simulación de click
"""
from django.core.management.base import BaseCommand
from django.test import Client, override_settings
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from events.models import Task, InboxItem, TaskStatus, Status


class Command(BaseCommand):
    help = 'Simula el click en Vincular a Tarea Existente sin permisos'

    @override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
    def handle(self, *args, **options):
        self.stdout.write("=== Simulación de Click: Vincular a Tarea Existente ===")

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

            self.stdout.write("[OK] Usuarios creados/verificados")

            # Crear estados si no existen
            task_status, _ = TaskStatus.objects.get_or_create(status_name='To Do')
            event_status, _ = Status.objects.get_or_create(status_name='Created')

            self.stdout.write("[OK] Estados creados/verificados")

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

            self.stdout.write(f"[OK] Tarea existente creada: {existing_task.title} (ID: {existing_task.id})")

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

            self.stdout.write(f"[OK] Inbox item creado: {inbox_item.title} (ID: {inbox_item.id})")
            self.stdout.write(f"   - Creado por: {inbox_item.created_by.username}")
            self.stdout.write(f"   - Asignado a: {inbox_item.assigned_to.username}")

            # Simular el click usando Django test client
            client = Client()

            # Hacer login como user2 (el asignado al inbox)
            login_success = client.login(username='test_user2', password='testpass123')
            if not login_success:
                self.stderr.write("[ERROR] No se pudo hacer login como user2")
                return

            self.stdout.write("[OK] Login exitoso como user2")

            # Simular POST request a process_inbox_item con action 'link_to_task'
            url = f'/events/inbox/process/{inbox_item.id}/'
            post_data = {
                'action': 'link_to_task',
                'task_id': str(existing_task.id)
            }

            self.stdout.write(f"[POST] Enviando request a: {url}")
            self.stdout.write(f"   Datos: {post_data}")

            response = client.post(url, post_data, follow=True)

            self.stdout.write(f"[RESPONSE] Status: {response.status_code}")
            self.stdout.write(f"[RESPONSE] Redirect chain: {[r[0] for r in response.redirect_chain]}")

            # Verificar el resultado
            if response.status_code == 200:
                # Verificar si hay mensajes de error
                messages = list(get_messages(response.wsgi_request))
                error_messages = [str(msg) for msg in messages if msg.level_tag == 'error']

                if error_messages:
                    self.stdout.write("[SUCCESS] ¡Prueba PASADA! Se mostró mensaje de error esperado:")
                    for msg in error_messages:
                        self.stdout.write(f"   [ERROR] {msg}")
                else:
                    self.stderr.write("[FAIL] Prueba FALLIDA: No se mostró mensaje de error")

                # Verificar que el inbox item NO fue procesado
                inbox_item.refresh_from_db()
                if not inbox_item.is_processed:
                    self.stdout.write("[OK] Correcto: El inbox item no fue marcado como procesado")
                else:
                    self.stderr.write("[ERROR] El inbox item fue marcado como procesado incorrectamente")

            else:
                self.stderr.write(f"[ERROR] HTTP Error: {response.status_code}")

            # Limpiar datos de prueba
            self.stdout.write("\n[LIMPIANDO] Limpiando datos de prueba...")
            try:
                inbox_item.delete()
                existing_task.delete()
                self.stdout.write("[OK] Datos de prueba eliminados")
            except Exception as e:
                self.stdout.write(f"[WARN] Error al limpiar datos: {e}")

        except Exception as e:
            self.stderr.write(f"[ERROR] Error durante la simulacion: {e}")
            import traceback
            traceback.print_exc()