#!/usr/bin/env python
"""
Script para crear datos de prueba para el Panel de Gestión GTD
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth.models import User
from events.models import InboxItem, GTDProcessingSettings

def create_test_data():
    """Crear datos de prueba para el panel GTD"""

    print("Creando datos de prueba para el Panel de Gestión GTD...")

    # Obtener el usuario admin
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("Usuario admin no encontrado. Creando...")
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    # Crear configuraciones de procesamiento GTD
    settings, created = GTDProcessingSettings.objects.get_or_create(
        created_by=admin_user,
        defaults={
            'is_active': True,
            'auto_email_processing': True,
            'auto_call_queue': True,
            'auto_chat_routing': True,
            'processing_interval': 60,
            'max_concurrent_items': 5,
            'email_batch_size': 10,
            'call_queue_timeout': 30,
            'chat_response_timeout': 300,
            'enable_bot_cx': True,
            'enable_bot_atc': True,
            'enable_human_agents': True,
        }
    )

    if created:
        print("Configuraciones GTD creadas")
    else:
        print("Configuraciones GTD ya existen")

    # Crear InboxItems de prueba
    inbox_items_data = [
        {
            'title': 'Solicitud cambio de plan internet',
            'description': 'Cliente solicita cambiar de plan básico a premium. Necesita más velocidad.',
            'gtd_category': 'accionable',
            'action_type': 'delegar',
            'priority': 'alta',
            'context': '@telefono',
        },
        {
            'title': 'Factura duplicada mes anterior',
            'description': 'Cliente recibió dos facturas del mismo mes. Solicita aclaración.',
            'gtd_category': 'accionable',
            'action_type': 'hacer',
            'priority': 'media',
            'context': '@email',
        },
        {
            'title': 'Problema técnico con conexión',
            'description': 'Cliente reporta cortes intermitentes en la conexión.',
            'gtd_category': 'accionable',
            'action_type': 'delegar',
            'priority': 'alta',
            'context': '@telefono',
        },
        {
            'title': 'Actualización de datos personales',
            'description': 'Cliente quiere cambiar dirección de facturación.',
            'gtd_category': 'accionable',
            'action_type': 'hacer',
            'priority': 'baja',
            'context': '@email',
        },
        {
            'title': 'Consulta sobre promociones',
            'description': 'Cliente pregunta sobre descuentos disponibles.',
            'gtd_category': 'accionable',
            'action_type': 'hacer',
            'priority': 'media',
            'context': '@chat',
        },
        {
            'title': 'Reclamo por servicio lento',
            'description': 'Cliente insatisfecho con velocidad de internet.',
            'gtd_category': 'accionable',
            'action_type': 'delegar',
            'priority': 'alta',
            'context': '@telefono',
        },
        {
            'title': 'Cancelación de servicio',
            'description': 'Cliente quiere cancelar su plan actual.',
            'gtd_category': 'accionable',
            'action_type': 'delegar',
            'priority': 'alta',
            'context': '@telefono',
        },
        {
            'title': 'Duda sobre instalación',
            'description': 'Cliente pregunta sobre proceso de instalación.',
            'gtd_category': 'accionable',
            'action_type': 'hacer',
            'priority': 'baja',
            'context': '@chat',
        },
        {
            'title': 'Solicitud de reembolso',
            'description': 'Cliente pagó doble y solicita devolución.',
            'gtd_category': 'accionable',
            'action_type': 'delegar',
            'priority': 'alta',
            'context': '@email',
        },
        {
            'title': 'Actualización de equipo',
            'description': 'Cliente necesita modem nuevo.',
            'gtd_category': 'accionable',
            'action_type': 'delegar',
            'priority': 'media',
            'context': '@telefono',
        },
        {
            'title': 'Artículo sobre productividad',
            'description': 'Interesante artículo sobre técnicas GTD que encontré.',
            'gtd_category': 'no_accionable',
            'action_type': 'archivar',
            'priority': 'baja',
            'context': '@lectura',
        },
        {
            'title': 'Idea para mejorar el servicio',
            'description': 'Pensar en implementar chatbots para soporte.',
            'gtd_category': 'pendiente',
            'action_type': '',
            'priority': 'media',
            'context': '@ideas',
        },
    ]

    created_count = 0
    for item_data in inbox_items_data:
        # Verificar si ya existe
        if not InboxItem.objects.filter(
            title=item_data['title'],
            created_by=admin_user
        ).exists():
            InboxItem.objects.create(
                title=item_data['title'],
                description=item_data['description'],
                created_by=admin_user,
                gtd_category=item_data['gtd_category'],
                action_type=item_data['action_type'] if item_data['action_type'] else None,
                priority=item_data['priority'],
                context=item_data['context'],
                is_public=True,
            )
            created_count += 1

    print(f"Creados {created_count} items de inbox de prueba")

    # Mostrar resumen
    total_items = InboxItem.objects.filter(created_by=admin_user).count()
    processed_items = InboxItem.objects.filter(created_by=admin_user, is_processed=True).count()
    unprocessed_items = total_items - processed_items

    print("\nResumen de datos creados:")
    print(f"- Total de items en inbox: {total_items}")
    print(f"- Items procesados: {processed_items}")
    print(f"- Items sin procesar: {unprocessed_items}")
    print(f"- Configuraciones GTD: {'Creadas' if created else 'Ya existian'}")

    print("\nDatos de prueba creados exitosamente!")
    print("Ahora puedes acceder al panel en: http://localhost:8000/events/inbox/management/")

if __name__ == '__main__':
    create_test_data()