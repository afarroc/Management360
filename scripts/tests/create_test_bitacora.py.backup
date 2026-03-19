#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from bitacora.models import BitacoraEntry, BitacoraAttachment
from events.models import Tag
from django.core.files.base import ContentFile
import requests

def create_test_user():
    """Crear usuario de prueba si no existe"""
    user, created = User.objects.get_or_create(
        username='su',
        defaults={
            'email': 'su@example.com',
            'is_superuser': True,
            'is_staff': True
        }
    )
    if created:
        user.set_password('su')
        user.save()
        print("Usuario 'su' creado")
    else:
        print("Usuario 'su' ya existe")

    return user

def create_test_tags():
    """Crear tags de prueba"""
    from events.models import TagCategory

    # Crear categoría si no existe
    category, _ = TagCategory.objects.get_or_create(
        name='Bitácora',
        defaults={'description': 'Tags para entradas de bitácora'}
    )

    # Crear tags de prueba
    tags = []
    for tag_name in ['reflexión', 'viaje', 'tecnología']:
        tag, created = Tag.objects.get_or_create(
            name=tag_name,
            category=category,
            defaults={'color': '#007bff'}
        )
        tags.append(tag)
        if created:
            print(f"Tag '{tag_name}' creado")

    return tags

def create_test_bitacora_entry(user, tags):
    """Crear entrada de bitácora de prueba con imagen"""

    # Crear entrada de bitácora
    entry = BitacoraEntry.objects.create(
        titulo='Mi Primera Entrada de Bitácora',
        contenido="""
        <h2>Bienvenido a mi bitácora personal</h2>

        <p>Esta es mi primera entrada en la bitácora. Estoy probando todas las funcionalidades del sistema.</p>

        <p><strong>Características que estoy probando:</strong></p>
        <ul>
            <li>Editor TinyMCE con herramientas completas</li>
            <li>Inserción de imágenes</li>
            <li>Sistema de tags y categorías</li>
            <li>Contenido multimedia</li>
        </ul>

        <p>¡Es increíble lo que se puede lograr con esta plataforma!</p>

        <blockquote>
            <p>"La reflexión es la llave del aprendizaje."</p>
        </blockquote>
        """,
        categoria='reflexion',
        autor=user,
        is_public=True,
        mood='contento'
    )

    # Asignar tags
    entry.tags.set(tags)
    print("Entrada de bitacora creada")

    # Crear adjunto de imagen (descargar una imagen de prueba)
    try:
        # URL de una imagen de prueba pequeña
        image_url = "https://picsum.photos/400/300"
        response = requests.get(image_url)

        if response.status_code == 200:
            # Crear adjunto
            attachment = BitacoraAttachment.objects.create(
                entry=entry,
                archivo=ContentFile(response.content, name='imagen_prueba.jpg'),
                tipo='image',
                descripcion='Imagen de prueba para la bitacora'
            )
            print("Adjunto de imagen creado")
        else:
            print("No se pudo descargar la imagen de prueba")

    except Exception as e:
        print(f"Error al crear adjunto: {e}")

    return entry

def verify_creation(entry):
    """Verificar que la entrada se creó correctamente"""
    print("\n" + "="*50)
    print("VERIFICACION DE CREACION")
    print("="*50)

    print(f"Titulo: {entry.titulo}")
    print(f"Autor: {entry.autor.username}")
    print(f"Categoria: {entry.get_categoria_display()}")
    print(f"Estado de animo: {entry.mood}")
    print(f"Publico: {'Si' if entry.is_public else 'No'}")
    print(f"Fecha creacion: {entry.fecha_creacion}")
    print(f"Tags: {', '.join([tag.name for tag in entry.tags.all()])}")

    # Verificar adjuntos
    attachments = entry.attachments.all()
    print(f"Numero de adjuntos: {attachments.count()}")

    for attachment in attachments:
        print(f"  - Tipo: {attachment.get_tipo_display()}")
        print(f"  - Archivo: {attachment.archivo.url}")
        print(f"  - Descripcion: {attachment.descripcion}")

    # Verificar contenido
    content_length = len(entry.contenido)
    print(f"Longitud del contenido: {content_length} caracteres")

    # Verificar que se puede acceder desde la base de datos
    try:
        retrieved_entry = BitacoraEntry.objects.get(id=entry.id)
        print("Entrada recuperable desde la base de datos")
    except BitacoraEntry.DoesNotExist:
        print("Error: Entrada no encontrada en la base de datos")

    print("\n" + "="*50)
    print("VERIFICACION COMPLETADA EXITOSAMENTE")
    print("="*50)

def main():
    print("Creando elementos de prueba para la bitacora...")

    # Crear usuario
    user = create_test_user()

    # Crear tags
    tags = create_test_tags()

    # Crear entrada de bitácora
    entry = create_test_bitacora_entry(user, tags)

    # Verificar creación
    verify_creation(entry)

    print("\nProceso completado exitosamente!")
    print(f"Puedes acceder a la entrada en: /bitacora/{entry.id}/")

if __name__ == '__main__':
    main()