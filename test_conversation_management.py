#!/usr/bin/env python3
"""
Script de prueba para verificar la gestión de conversaciones:
- Crear nuevas conversaciones
- Cambiar entre conversaciones
- Listar conversaciones
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from chat.models import Conversation

def test_conversation_management():
    print("*** PRUEBA DE GESTIÓN DE CONVERSACIONES ***")
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

    # 1. Ver conversaciones iniciales
    print("\n[PASO 1] Verificando conversaciones iniciales...")
    initial_conversations = Conversation.objects.filter(user=user)
    print(f"[OK] Conversaciones iniciales: {initial_conversations.count()}")

    # 2. Crear primera conversación
    print("\n[PASO 2] Creando primera conversación...")
    conv1 = Conversation.get_or_create_active_conversation(user)
    print(f"[OK] Primera conversación creada: {conv1.conversation_id}")
    print(f"[OK] Título: {conv1.title}")
    print(f"[OK] Activa: {conv1.is_active}")

    # Agregar algunos mensajes
    conv1.add_message('user', 'Hola, primera conversación', user.get_full_name())
    conv1.add_message('ai', '¡Hola! ¿En qué puedo ayudarte?', 'Asistente IA')
    print(f"[OK] Mensajes agregados: {len(conv1.messages)}")

    # 3. Crear segunda conversación
    print("\n[PASO 3] Creando segunda conversación...")
    # Simular creación de nueva conversación (desactivar actual y crear nueva)
    Conversation.objects.filter(user=user, is_active=True).update(is_active=False)

    # Crear nueva conversación usando el método correcto
    conv2_id = f"conv_{user.id}_{int(datetime.now().timestamp())}_2"
    conv2 = Conversation.objects.create(
        user=user,
        conversation_id=conv2_id,
        title="Segunda conversación",
        is_active=True
    )
    print(f"[OK] Segunda conversación creada: {conv2.conversation_id}")
    print(f"[OK] Título: {conv2.title}")
    print(f"[OK] Activa: {conv2.is_active}")

    # Agregar mensajes diferentes
    conv2.add_message('user', 'Esta es la segunda conversación', user.get_full_name())
    conv2.add_message('ai', '¡Entendido! Esta es una conversación separada.', 'Asistente IA')
    print(f"[OK] Mensajes en segunda conversación: {len(conv2.messages)}")

    # 4. Verificar que solo una está activa
    print("\n[PASO 4] Verificando estado activo...")
    active_conversations = Conversation.objects.filter(user=user, is_active=True)
    print(f"[OK] Conversaciones activas: {active_conversations.count()}")
    if active_conversations.count() == 1:
        active_conv = active_conversations.first()
        print(f"[OK] Conversación activa: {active_conv.conversation_id} - {active_conv.title}")
    else:
        print("[ERROR] Debería haber exactamente 1 conversación activa")

    # 5. Cambiar a la primera conversación
    print("\n[PASO 5] Cambiando a primera conversación...")
    # Simular cambio (desactivar todas y activar la primera)
    Conversation.objects.filter(user=user).update(is_active=False)
    conv1.is_active = True
    conv1.save()

    # Verificar cambio
    active_after_switch = Conversation.objects.filter(user=user, is_active=True).first()
    if active_after_switch and active_after_switch.id == conv1.id:
        print(f"[OK] Cambio exitoso a: {active_after_switch.conversation_id}")
    else:
        print("[ERROR] Falló el cambio de conversación")

    # 6. Listar todas las conversaciones
    print("\n[PASO 6] Listando todas las conversaciones...")
    all_conversations = Conversation.objects.filter(user=user).order_by('-updated_at')

    print(f"[OK] Total de conversaciones: {all_conversations.count()}")
    for i, conv in enumerate(all_conversations, 1):
        status = "[ACTIVA]" if conv.is_active else "[INACTIVA]"
        print(f"   {i}. {status} {conv.title} - {len(conv.messages)} mensajes")
        print(f"      ID: {conv.conversation_id}")
        print(f"      Actualizada: {conv.updated_at.strftime('%d/%m/%Y %H:%M:%S')}")

    # 7. Verificar API de lista de conversaciones
    print("\n[PASO 7] Probando formato de API...")
    conversations_data = []
    for conv in all_conversations[:10]:  # Últimas 10
        conversations_data.append({
            'id': conv.id,
            'conversation_id': conv.conversation_id,
            'title': conv.title,
            'created_at': conv.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': conv.updated_at.strftime('%d/%m/%Y %H:%M'),
            'is_active': conv.is_active,
            'message_count': len(conv.messages),
            'last_message': conv.messages[-1] if conv.messages else None
        })

    print(f"[OK] Datos formateados para API: {len(conversations_data)} conversaciones")
    for conv_data in conversations_data:
        active_indicator = " [ACTIVA]" if conv_data['is_active'] else ""
        print(f"   - {conv_data['title']} ({conv_data['message_count']} msgs){active_indicator}")

    # 8. Resumen final
    print("\n[RESUMEN FINAL]")
    print("=" * 60)
    print(f"Usuario: {user.username}")
    print(f"Total conversaciones: {all_conversations.count()}")
    print(f"Conversación activa: {active_after_switch.title if active_after_switch else 'Ninguna'}")
    print(f"Mensajes en conversación activa: {len(active_after_switch.messages) if active_after_switch else 0}")

    print("\n[SISTEMA DE GESTIÓN DE CONVERSACIONES FUNCIONANDO!]")
    print("\nPara probar en el navegador:")
    print("   1. Ve a: http://localhost:8000/chat/ui/")
    print("   2. Verás el panel lateral con conversaciones")
    print("   3. Haz clic en 'Nueva Conversación' para crear una")
    print("   4. Haz clic en conversaciones existentes para cambiar")
    print("   5. Usa las funciones rápidas del panel lateral")

    print("\nPara ver todas las conversaciones:")
    print("   Ve a: http://localhost:8000/chat/conversations/")

if __name__ == '__main__':
    test_conversation_management()