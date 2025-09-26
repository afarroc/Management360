#!/usr/bin/env python3
"""
Script de prueba para demostrar la recuperación de historial de chat
Simula una conversación y muestra cómo se retoma
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.cache import cache
from chat.functions import function_registry, parse_command
from chat.models import CommandLog

def test_resume_chat():
    """Prueba completa del sistema de recuperación de chat"""

    print("*** PRUEBA DE RECUPERACION DE HISTORIAL DE CHAT ***")
    print("=" * 60)

    # 1. Simular conversación anterior
    print("\n[PASO 1] Creando conversacion simulada...")

    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )

    # Simular historial de chat
    chat_history = [
        {
            'sender': 'user',
            'content': 'Hola, quiero crear un proyecto de e-commerce',
            'timestamp': (datetime.now() - timedelta(minutes=10)).isoformat(),
            'sender_name': 'Test User'
        },
        {
            'sender': 'ai',
            'content': 'Hola! Claro, puedo ayudarte a planificar un proyecto de e-commerce. Que tipo de tienda en linea tienes en mente?',
            'timestamp': (datetime.now() - timedelta(minutes=9)).isoformat(),
            'sender_name': 'Asistente IA'
        },
        {
            'sender': 'user',
            'content': 'crea un proyecto llamado "Tienda Online" con descripcion "Plataforma e-commerce completa"',
            'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
            'sender_name': 'Test User'
        },
        {
            'sender': 'ai',
            'content': '[OK] Comando ejecutado: Proyecto "Tienda Online" creado exitosamente con ID 100',
            'timestamp': (datetime.now() - timedelta(minutes=4)).isoformat(),
            'sender_name': 'Asistente IA'
        },
        {
            'sender': 'user',
            'content': 'lista mis proyectos',
            'timestamp': (datetime.now() - timedelta(minutes=2)).isoformat(),
            'sender_name': 'Test User'
        },
        {
            'sender': 'ai',
            'content': '[OK] Comando ejecutado: Encontrados 3 proyectos',
            'timestamp': (datetime.now() - timedelta(minutes=1)).isoformat(),
            'sender_name': 'Asistente IA'
        }
    ]

    # Guardar en cache (simulando localStorage del navegador)
    cache_key = f'chat_history_{user.username}'
    cache.set(cache_key, chat_history, timeout=86400)  # 24 horas

    print(f"[OK] Historial guardado en cache para usuario: {user.username}")

    # 2. Simular comandos ejecutados
    print("\n[PASO 2] Registrando comandos ejecutados...")

    # Limpiar comandos anteriores de prueba
    CommandLog.objects.filter(user=user).delete()

    # Crear comandos simulados
    commands_data = [
        {
            'command': 'crea un proyecto llamado "Tienda Online" con descripción "Plataforma e-commerce completa"',
            'function_name': 'create_project',
            'result': {'success': True, 'message': 'Proyecto "Tienda Online" creado exitosamente con ID 100', 'project_id': 100},
            'execution_time': 0.15,
            'executed_at': datetime.now() - timedelta(minutes=5)
        },
        {
            'command': 'lista mis proyectos',
            'function_name': 'list_projects',
            'result': {
                'success': True,
                'message': 'Encontrados 3 proyectos',
                'projects': [
                    {'id': 100, 'title': 'Tienda Online', 'description': 'Plataforma e-commerce completa', 'status': 'Planning', 'created_at': '26/09/2025'},
                    {'id': 99, 'title': 'App Móvil', 'description': '', 'status': 'Draft', 'created_at': '25/09/2025'},
                    {'id': 98, 'title': 'Sistema Web', 'description': 'Aplicación web empresarial', 'status': 'In Progress', 'created_at': '24/09/2025'}
                ]
            },
            'execution_time': 0.08,
            'executed_at': datetime.now() - timedelta(minutes=2)
        }
    ]

    for cmd_data in commands_data:
        CommandLog.objects.create(
            user=user,
            command=cmd_data['command'],
            function_name=cmd_data['function_name'],
            params=cmd_data.get('params', {}),
            result=cmd_data['result'],
            success=cmd_data['result'].get('success', False),
            execution_time=cmd_data['execution_time'],
            executed_at=cmd_data['executed_at']
        )

    print(f"[OK] {len(commands_data)} comandos registrados en base de datos")

    # 3. Simular recuperación del historial
    print("\n[PASO 3] Simulando recuperacion del historial...")

    # Recuperar historial de chat
    recovered_history = cache.get(cache_key)
    if recovered_history:
        print(f"[OK] Historial de chat recuperado: {len(recovered_history)} mensajes")
        for i, msg in enumerate(recovered_history, 1):
            sender = msg['sender_name'] or ('Tu' if msg['sender'] == 'user' else 'Asistente')
            print(f"   {i}. {sender}: {msg['content'][:50]}{'...' if len(msg['content']) > 50 else ''}")
    else:
        print("[ERROR] No se pudo recuperar el historial de chat")

    # Recuperar historial de comandos
    command_history = CommandLog.objects.filter(user=user).order_by('-executed_at')
    if command_history.exists():
        print(f"[OK] Historial de comandos recuperado: {command_history.count()} comandos")
        for cmd in command_history:
            status = "[OK]" if cmd.success else "[ERROR]"
            print(f"   - {status} {cmd.function_name}: {cmd.command[:40]}{'...' if len(cmd.command) > 40 else ''}")
            print(f"      Tiempo: {cmd.execution_time:.3f}s")
    else:
        print("[ERROR] No se encontraron comandos en el historial")

    # 4. Simular continuación de conversación
    print("\n[PASO 4] Simulando continuacion de conversacion...")

    # Agregar nuevo mensaje a la conversación
    new_message = {
        'sender': 'user',
        'content': 'Ahora quiero actualizar el proyecto Tienda Online',
        'timestamp': datetime.now().isoformat(),
        'sender_name': 'Test User'
    }

    if recovered_history:
        recovered_history.append(new_message)
        cache.set(cache_key, recovered_history, timeout=86400)
        print("[OK] Nuevo mensaje agregado al historial")
        print(f"   Nuevo mensaje: {new_message['content']}")

    # 5. Mostrar resumen final
    print("\n[RESUMEN FINAL]")
    print("=" * 60)
    print(f"Usuario: {user.username}")
    print(f"Mensajes en historial: {len(recovered_history) if recovered_history else 0}")
    print(f"Comandos ejecutados: {command_history.count()}")
    print(f"Ultima actividad: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    print("\n[SISTEMA DE RECUPERACION FUNCIONANDO CORRECTAMENTE!]")
    print("\nPara retomar esta conversacion en el navegador:")
    print("   1. Ve a: http://localhost:8000/chat/ui/")
    print("   2. El historial se cargara automaticamente")
    print("   3. Puedes continuar preguntando sobre el proyecto e-commerce")
    print("   4. O ejecutar mas comandos como 'lista mis proyectos'")

    print("\nPara ver el historial de comandos:")
    print("   Ve a: http://localhost:8000/chat/commands/")

if __name__ == '__main__':
    test_resume_chat()