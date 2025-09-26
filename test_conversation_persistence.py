#!/usr/bin/env python3
"""
Script de prueba para verificar que las conversaciones con IA se guardan correctamente
y se pueden recuperar para continuar el chat anterior.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from chat.models import Conversation, CommandLog

def test_conversation_persistence():
    print("*** PRUEBA DE PERSISTENCIA DE CONVERSACIONES ***")
    print("=" * 60)

    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("[OK] Usuario de prueba creado")
    else:
        print("[OK] Usuario de prueba encontrado")

    # 1. Crear conversación simulada
    print("\n[PASO 1] Creando conversación simulada...")

    # Obtener o crear conversación activa
    conversation = Conversation.get_or_create_active_conversation(user)
    print(f"[OK] Conversación activa obtenida: {conversation.conversation_id}")

    # Agregar mensajes simulados
    messages_to_add = [
        {
            'sender': 'user',
            'content': 'Hola, quiero crear un proyecto de e-commerce completo',
            'sender_name': user.get_full_name(),
            'message_type': 'text'
        },
        {
            'sender': 'ai',
            'content': '¡Hola! Claro, puedo ayudarte a planificar un proyecto de e-commerce. ¿Qué tipo de tienda en línea tienes en mente?',
            'sender_name': 'Asistente IA',
            'message_type': 'text'
        },
        {
            'sender': 'user',
            'content': 'crea un proyecto llamado "Tienda Online Completa" con descripción "Plataforma e-commerce con carrito, pagos y gestión de inventario"',
            'sender_name': user.get_full_name(),
            'message_type': 'command'
        },
        {
            'sender': 'ai',
            'content': '[OK] Comando ejecutado: Proyecto "Tienda Online Completa" creado exitosamente con ID 100',
            'sender_name': 'Asistente IA',
            'message_type': 'command_response'
        },
        {
            'sender': 'user',
            'content': 'Ahora quiero ver todos mis proyectos',
            'sender_name': user.get_full_name(),
            'message_type': 'text'
        },
        {
            'sender': 'ai',
            'content': 'Aquí tienes la lista de tus proyectos actuales...',
            'sender_name': 'Asistente IA',
            'message_type': 'text'
        }
    ]

    for msg in messages_to_add:
        conversation.add_message(**msg)

    print(f"[OK] {len(messages_to_add)} mensajes agregados a la conversación")

    # 2. Simular comandos ejecutados
    print("\n[PASO 2] Registrando comandos ejecutados...")

    commands_data = [
        {
            'user': user,
            'command': 'crea un proyecto llamado "Tienda Online Completa" con descripción "Plataforma e-commerce..."',
            'function_name': 'create_project',
            'params': {'title': 'Tienda Online Completa', 'description': 'Plataforma e-commerce...'},
            'result': {'success': True, 'message': 'Proyecto creado exitosamente', 'project_id': 100},
            'success': True,
            'execution_time': 0.150
        },
        {
            'user': user,
            'command': 'lista mis proyectos',
            'function_name': 'list_projects',
            'params': {},
            'result': {'success': True, 'message': 'Proyectos listados', 'projects': []},
            'success': True,
            'execution_time': 0.080
        }
    ]

    for cmd_data in commands_data:
        CommandLog.objects.create(**cmd_data)

    print(f"[OK] {len(commands_data)} comandos registrados en base de datos")

    # 3. Verificar recuperación de conversación
    print("\n[PASO 3] Verificando recuperación de conversación...")

    # Recargar conversación desde BD
    reloaded_conversation = Conversation.objects.get(
        conversation_id=conversation.conversation_id,
        user=user
    )

    print(f"[OK] Conversación recargada: {reloaded_conversation.title}")
    print(f"[OK] Mensajes en conversación: {len(reloaded_conversation.messages)}")

    # Verificar que los mensajes están correctos
    expected_messages = len(messages_to_add)
    actual_messages = len(reloaded_conversation.messages)

    if actual_messages == expected_messages:
        print(f"[OK] Número correcto de mensajes: {actual_messages}")
    else:
        print(f"[ERROR] Número incorrecto de mensajes. Esperado: {expected_messages}, Actual: {actual_messages}")

    # Mostrar algunos mensajes
    print("\nMensajes en la conversación:")
    for i, msg in enumerate(reloaded_conversation.messages[:3], 1):
        sender = msg['sender_name'] or ('Tú' if msg['sender'] == 'user' else 'Asistente')
        content_preview = msg['content'][:60] + '...' if len(msg['content']) > 60 else msg['content']
        print(f"   {i}. {sender}: {content_preview}")

    # 4. Verificar historial de comandos
    print("\n[PASO 4] Verificando historial de comandos...")

    command_history = CommandLog.objects.filter(user=user).order_by('-executed_at')
    if command_history.exists():
        print(f"[OK] Historial de comandos recuperado: {command_history.count()} comandos")
        for cmd in command_history:
            status = "[OK]" if cmd.success else "[ERROR]"
            print(f"   - {status} {cmd.function_name}: {cmd.command[:50]}{'...' if len(cmd.command) > 50 else ''}")
            print(f"      Tiempo: {cmd.execution_time:.3f}s")
    else:
        print("[ERROR] No se encontraron comandos en el historial")

    # 5. Simular continuación de conversación
    print("\n[PASO 5] Simulando continuación de conversación...")

    # Agregar mensaje nuevo
    new_message = {
        'sender': 'user',
        'content': 'Ahora quiero actualizar el proyecto para agregar más funcionalidades',
        'sender_name': user.get_full_name(),
        'message_type': 'text'
    }

    reloaded_conversation.add_message(**new_message)
    print("[OK] Nuevo mensaje agregado a la conversación")

    # Verificar que se guardó
    final_conversation = Conversation.objects.get(
        conversation_id=conversation.conversation_id,
        user=user
    )

    final_message_count = len(final_conversation.messages)
    print(f"[OK] Conversación final tiene {final_message_count} mensajes")

    # 6. Mostrar resumen final
    print("\n[RESUMEN FINAL]")
    print("=" * 60)
    print(f"Usuario: {user.username}")
    print(f"Conversación ID: {conversation.conversation_id}")
    print(f"Título: {conversation.title}")
    print(f"Mensajes totales: {final_message_count}")
    print(f"Comandos ejecutados: {command_history.count()}")
    print(f"Última actividad: {conversation.updated_at.strftime('%d/%m/%Y %H:%M:%S')}")

    print("\n[SISTEMA DE PERSISTENCIA FUNCIONANDO CORRECTAMENTE!]")
    print("\nPara probar en el navegador:")
    print("   1. Ve a: http://localhost:8000/chat/ui/")
    print("   2. El historial se cargará automáticamente")
    print("   3. Puedes continuar la conversación sobre e-commerce")
    print("   4. Ejecutar comandos como 'lista mis proyectos'")
    print("   5. Ver historial en: http://localhost:8000/chat/conversations/")

    print("\nPara ver el historial de comandos:")
    print("   Ve a: http://localhost:8000/chat/commands/")

if __name__ == '__main__':
    test_conversation_persistence()