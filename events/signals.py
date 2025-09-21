from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Task, InboxItem, TaskStatus

@receiver(post_save, sender=Task)
def create_inbox_item_for_task(sender, instance, created, **kwargs):
    """
    Señal para crear automáticamente un item en el inbox GTD cuando se crea una tarea
    """
    if created:  # Solo cuando se crea una nueva tarea
        try:
            # Verificar que el usuario existe
            if instance.host:
                # NO crear item en inbox si la tarea viene del procesamiento del inbox
                # Verificar si existe algún InboxItem que apunte a esta tarea (ya procesado)
                existing_processed_inbox_item = InboxItem.objects.filter(
                    created_by=instance.host,
                    processed_to=instance
                ).exists()

                if existing_processed_inbox_item:
                    print(f"No se crea item en inbox para tarea '{instance.title}' - viene del procesamiento del inbox")
                    return

                # Verificar si hay InboxItems no procesados con título similar (para evitar duplicados por condición de carrera)
                # Esto detecta cuando una tarea se está creando desde el procesamiento del inbox
                similar_unprocessed_inbox_items = InboxItem.objects.filter(
                    created_by=instance.host,
                    is_processed=False,
                    title__icontains=instance.title[:50]  # Comparar primeros 50 caracteres del título
                )

                if similar_unprocessed_inbox_items.exists():
                    print(f"No se crea item en inbox para tarea '{instance.title}' - detectado InboxItem no procesado similar")
                    return

                # Crear el item en el inbox GTD
                inbox_item = InboxItem.objects.create(
                    title=f"Tarea creada: {instance.title}",
                    description=f"Se ha creado una nueva tarea: {instance.description or 'Sin descripción'}",
                    created_by=instance.host,
                    is_processed=False
                )

                # Agregar etiquetas relevantes basadas en el estado de la tarea
                if instance.important:
                    # Buscar etiqueta de prioridad alta
                    try:
                        priority_tag = instance.host.tag_set.filter(
                            name__icontains='alta'
                        ).first()
                        if priority_tag:
                            inbox_item.tags.add(priority_tag)
                    except:
                        pass

                # Agregar etiqueta GTD para indicar que viene de una tarea
                try:
                    gtd_tag = instance.host.tag_set.filter(
                        name__icontains='gtd'
                    ).first()
                    if not gtd_tag:
                        # Si no existe, buscar cualquier etiqueta relacionada con tareas
                        gtd_tag = instance.host.tag_set.filter(
                            name__icontains='tarea'
                        ).first()

                    if gtd_tag:
                        inbox_item.tags.add(gtd_tag)
                except:
                    pass

                print(f"Inbox item creado automáticamente para tarea: {instance.title}")

        except Exception as e:
            print(f"Error al crear inbox item para tarea {instance.title}: {e}")