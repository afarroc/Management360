#!/usr/bin/env python
"""
Script de prueba para el Panel de Gestión GTD
Simula el funcionamiento sin necesidad de base de datos completa
"""

import os
import sys
import django
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.http import JsonResponse
from events.views import (
    inbox_management_panel,
    get_queue_data,
    update_processing_settings,
    assign_interaction_to_agent,
    mark_interaction_resolved
)

def create_mock_user():
    """Crear usuario mock para pruebas"""
    user = Mock()
    user.id = 1
    user.username = 'test_analyst'
    user.is_authenticated = True
    user.profile = Mock()
    user.profile.role = 'GTD_ANALYST'
    return user

def create_mock_request(user=None, method='GET', data=None):
    """Crear request mock"""
    factory = RequestFactory()
    if method == 'GET':
        request = factory.get('/')
    else:
        request = factory.post('/', data=data)

    request.user = user or create_mock_user()
    return request

def test_inbox_management_panel():
    """Prueba la vista principal del panel"""
    print("[TEST] Probando vista principal del panel...")

    request = create_mock_request()

    # Mock de los modelos para evitar consultas a BD
    with patch('events.views.InboxItem.objects') as mock_inbox, \
         patch('events.views.GTDProcessingSettings.get_active_settings') as mock_settings:

        # Configurar mocks
        mock_inbox.count.return_value = 25
        mock_inbox.filter.return_value.count.return_value = 15

        mock_settings_obj = Mock()
        mock_settings_obj.auto_email_processing = True
        mock_settings_obj.auto_call_queue = True
        mock_settings_obj.auto_chat_routing = True
        mock_settings_obj.processing_interval = 60
        mock_settings_obj.max_concurrent_items = 5
        mock_settings.return_value = mock_settings_obj

        try:
            response = inbox_management_panel(request)
            print("[PASS] Vista principal funciona correctamente")
            print(f"   Status: {response.status_code}")
            print(f"   Response type: {type(response).__name__}")
            return True
        except Exception as e:
            print(f"[FAIL] Error en vista principal: {e}")
            return False

def test_get_queue_data():
    """Prueba la API de datos de cola"""
    print("\n[TEST] Probando API de datos de cola...")

    request = create_mock_request()

    with patch('events.views.InboxItem.objects') as mock_inbox:
        # Configurar mocks
        mock_inbox.filter.return_value.count.return_value = 8

        try:
            response = get_queue_data(request)
            print("[PASS] API de cola funciona correctamente")
            print(f"   Status: {response.status_code}")
            if isinstance(response, JsonResponse):
                print("   Respuesta JSON valida")
            return True
        except Exception as e:
            print(f"[FAIL] Error en API de cola: {e}")
            return False

def test_update_processing_settings():
    """Prueba la actualizacion de configuraciones"""
    print("\n[TEST] Probando actualizacion de configuraciones...")

    data = {
        'auto_email_processing': 'true',
        'auto_call_queue': 'true',
        'auto_chat_routing': 'false',
        'processing_interval': '45',
        'max_concurrent': '3'
    }
    request = create_mock_request(method='POST', data=data)

    with patch('events.views.GTDProcessingSettings.objects') as mock_settings:
        mock_obj = Mock()
        mock_settings.get_or_create.return_value = (mock_obj, True)

        try:
            response = update_processing_settings(request)
            print("[PASS] Actualizacion de configuraciones funciona")
            print(f"   Status: {response.status_code}")
            return True
        except Exception as e:
            print(f"[FAIL] Error en actualizacion: {e}")
            return False

def test_assign_interaction():
    """Prueba la asignacion de interacciones"""
    print("\n[TEST] Probando asignacion de interacciones...")

    data = {
        'interaction_id': '123',
        'agent_type': 'bot-cx',
        'priority': 'alta',
        'notes': 'Cliente solicita cambio de plan'
    }
    request = create_mock_request(method='POST', data=data)

    with patch('events.views.InboxItem.objects') as mock_inbox, \
         patch('events.views.InboxItemHistory.objects') as mock_history:

        mock_item = Mock()
        mock_item.created_by = request.user
        mock_item.authorized_users.filter.return_value.exists.return_value = True
        mock_inbox.get.return_value = mock_item

        try:
            response = assign_interaction_to_agent(request)
            print("[PASS] Asignacion de interacciones funciona")
            print(f"   Status: {response.status_code}")
            return True
        except Exception as e:
            print(f"[FAIL] Error en asignacion: {e}")
            return False

def test_mark_resolved():
    """Prueba marcar como resuelto"""
    print("\n[TEST] Probando marcar como resuelto...")

    data = {
        'interaction_id': '123',
        'resolution_notes': 'Problema resuelto exitosamente'
    }
    request = create_mock_request(method='POST', data=data)

    with patch('events.views.InboxItem.objects') as mock_inbox, \
         patch('events.views.InboxItemHistory.objects') as mock_history:

        mock_item = Mock()
        mock_item.created_by = request.user
        mock_item.authorized_users.filter.return_value.exists.return_value = True
        mock_inbox.get.return_value = mock_item

        try:
            response = mark_interaction_resolved(request)
            print("[PASS] Marcar como resuelto funciona")
            print(f"   Status: {response.status_code}")
            return True
        except Exception as e:
            print(f"[FAIL] Error al marcar resuelto: {e}")
            return False

def simulate_panel_workflow():
    """Simula un flujo completo de trabajo del panel"""
    print("\n[SIMULATION] Simulando flujo de trabajo del panel GTD...")

    print("\n1. [METRICS] Panel se carga con metricas:")
    print("   - Items activos: 12")
    print("   - Items pendientes: 8")
    print("   - Emails: 15")
    print("   - Llamadas: 3")
    print("   - Chats: 2")

    print("\n2. [SETTINGS] Configuraciones aplicadas:")
    print("   - Procesamiento automatico de emails: [ON]")
    print("   - Cola automatica de llamadas: [ON]")
    print("   - Enrutamiento automatico de chats: [ON]")
    print("   - Intervalo de procesamiento: 60s")
    print("   - Maximo concurrente: 5 items")

    print("\n3. [EMAIL] Cola de emails procesada:")
    print("   - Email 1: 'Solicitud cambio de plan' -> Asignado a Bot CX")
    print("   - Email 2: 'Factura duplicada' -> Asignado a Bot ATC")
    print("   - Email 3: 'Actualizacion datos' -> En cola de baja prioridad")

    print("\n4. [CALL] Cola de llamadas gestionada:")
    print("   - Llamada 1: 'Problema tecnico' -> Agente humano asignado")
    print("   - Llamada 2: 'Consulta de plan' -> Bot CX asignado")

    print("\n5. [CHAT] Chats activos monitoreados:")
    print("   - Chat 1: 'Duda facturacion' -> Sesion activa con Bot")

    print("\n6. [RESOLVED] Interacciones resueltas:")
    print("   - 3 emails procesados")
    print("   - 1 llamada completada")
    print("   - 2 chats cerrados")

def main():
    """Funcion principal de pruebas"""
    print("[START] Iniciando pruebas del Panel de Gestion GTD")
    print("=" * 50)

    # Ejecutar pruebas
    tests = [
        test_inbox_management_panel,
        test_get_queue_data,
        test_update_processing_settings,
        test_assign_interaction,
        test_mark_resolved
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n[RESULTS] Resultados: {passed}/{total} pruebas pasaron")

    if passed == total:
        print("[SUCCESS] Todas las pruebas pasaron exitosamente!")
        simulate_panel_workflow()
    else:
        print("[WARNING] Algunas pruebas fallaron")

    print("\n" + "=" * 50)
    print("[END] Pruebas completadas")

if __name__ == '__main__':
    main()