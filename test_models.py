#!/usr/bin/env python
"""
Script simple para probar que los modelos funcionan correctamente
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from events.models import Task, Project, InboxItem
from django.contrib.contenttypes.models import ContentType

def test_models():
    print("=== Test: Modelos y GenericForeignKey ===")

    # Verificar que los modelos se importan correctamente
    print("[OK] Modelos importados correctamente")

    # Verificar que Task tiene el GenericRelation
    task_fields = [field.name for field in Task._meta.get_fields()]
    if 'processed_inbox_items' in task_fields:
        print("[OK] Task tiene el campo processed_inbox_items (GenericRelation)")
    else:
        print("[ERROR] Task NO tiene el campo processed_inbox_items")

    # Verificar que Project tiene el GenericRelation
    project_fields = [field.name for field in Project._meta.get_fields()]
    if 'processed_inbox_items' in project_fields:
        print("[OK] Project tiene el campo processed_inbox_items (GenericRelation)")
    else:
        print("[ERROR] Project NO tiene el campo processed_inbox_items")

    # Verificar que InboxItem tiene los campos GenericForeignKey
    inbox_fields = [field.name for field in InboxItem._meta.get_fields()]
    required_fields = ['processed_to_content_type', 'processed_to_object_id', 'processed_to']
    for field in required_fields:
        if field in inbox_fields:
            print(f"[OK] InboxItem tiene el campo {field}")
        else:
            print(f"[ERROR] InboxItem NO tiene el campo {field}")

    # Probar crear objetos
    try:
        from django.contrib.auth.models import User

        # Obtener o crear usuario
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com'}
        )
        if created:
            print("[OK] Usuario de prueba creado")
        else:
            print("[OK] Usuario de prueba ya existe")

        # Crear una tarea
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            host=user,
            assigned_to=user,
            task_status_id=1  # Asumiendo que existe
        )
        print(f"[OK] Task creada: {task.id}")

        # Crear un InboxItem vinculado a la tarea
        inbox_item = InboxItem.objects.create(
            title='Test Inbox Item',
            description='Test Description',
            created_by=user,
            assigned_to=user,
            processed_to=task,
            gtd_category='accionable'
        )
        print(f"[OK] InboxItem creado y vinculado: {inbox_item.id}")

        # Verificar que la relación funciona
        task_refreshed = Task.objects.get(id=task.id)
        related_inbox_items = task_refreshed.processed_inbox_items.all()
        if related_inbox_items.exists():
            print(f"[OK] GenericRelation funciona: {related_inbox_items.count()} items relacionados")
        else:
            print("[ERROR] GenericRelation no funciona")

        # Limpiar
        inbox_item.delete()
        task.delete()
        print("[OK] Limpieza completada")

    except Exception as e:
        print(f"[ERROR] Error al probar modelos: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test completado ===")

if __name__ == '__main__':
    test_models()