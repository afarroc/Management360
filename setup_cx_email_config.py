#!/usr/bin/env python
"""
Script para configurar el procesamiento de correos CX
Ejecutar con: python setup_cx_email_config.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.management import execute_from_command_line


def create_system_user():
    """Crear usuario sistema para procesamiento de correos CX"""
    try:
        user = User.objects.get(username='system')
        print("Usuario 'system' ya existe")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='system',
            email='system@local',
            first_name='Sistema',
            last_name='CX',
            is_staff=False,
            is_active=False  # Usuario no interactivo
        )
        print("Usuario 'system' creado exitosamente")
    return user


def show_env_config():
    """Mostrar configuración necesaria para variables de entorno"""
    print("\n" + "="*60)
    print("CONFIGURACIÓN DE VARIABLES DE ENTORNO NECESARIA")
    print("="*60)

    config_vars = {
        'EMAIL_RECEPTION_ENABLED': 'True',
        'EMAIL_IMAP_HOST': 'imap.gmail.com',
        'EMAIL_IMAP_PORT': '993',
        'EMAIL_IMAP_USER': 'tu-correo@gmail.com',
        'EMAIL_IMAP_PASSWORD': 'tu-app-password',
        'EMAIL_CX_FOLDER': 'INBOX/CX',
        'EMAIL_CHECK_INTERVAL': '300',
        'CX_EMAIL_DOMAINS': '@cliente.com,@support.com',
        'CX_KEYWORDS': 'cambio de plan,modificar plan,actualizar plan,solicitud,queja,reclamo'
    }

    print("Agrega estas variables a tu archivo .env:")
    print()
    for key, value in config_vars.items():
        print(f"{key}={value}")

    print("\n" + "="*60)
    print("INSTRUCCIONES PARA GMAIL")
    print("="*60)
    print("1. Activa la verificación en 2 pasos en tu cuenta Gmail")
    print("2. Genera una 'Contraseña de aplicación' en:")
    print("   https://myaccount.google.com/apppasswords")
    print("3. Usa esa contraseña (sin espacios) en EMAIL_IMAP_PASSWORD")
    print("4. Crea una etiqueta 'CX' en Gmail para organizar los correos")
    print()


def test_email_connection():
    """Probar conexión IMAP"""
    try:
        from imap_tools import MailBox
        from django.conf import settings

        if not settings.EMAIL_RECEPTION_ENABLED:
            print("AVISO: Email reception is disabled in settings")
            return

        print("Probando conexion IMAP...")
        with MailBox(settings.EMAIL_IMAP_HOST).login(
            settings.EMAIL_IMAP_USER,
            settings.EMAIL_IMAP_PASSWORD
        ) as mailbox:
            # Listar carpetas disponibles
            folders = [f.name for f in mailbox.folder.list()]
            print(f"Conexion exitosa. Carpetas disponibles: {folders}")

            # Verificar carpeta CX
            cx_folder = settings.EMAIL_CX_FOLDER
            if cx_folder in folders:
                print(f"Carpeta CX '{cx_folder}' encontrada")
            else:
                print(f"AVISO: Carpeta CX '{cx_folder}' no encontrada. Se usara INBOX")

    except ImportError:
        print("ERROR: imap-tools no esta instalado. Instala con: pip install imap-tools")
    except Exception as e:
        print(f"ERROR de conexion IMAP: {str(e)}")


def run_initial_test():
    """Ejecutar prueba inicial de procesamiento"""
    print("\n" + "="*60)
    print("EJECUTANDO PRUEBA INICIAL")
    print("="*60)

    try:
        # Ejecutar comando con dry-run
        execute_from_command_line(['manage.py', 'process_cx_emails', '--dry-run', '--max-emails=5'])
    except SystemExit:
        pass  # El comando ejecuta sys.exit(), esto es normal


def main():
    print("CONFIGURACION DE PROCESAMIENTO DE CORREOS CX")
    print("="*60)

    # Crear usuario sistema
    create_system_user()

    # Mostrar configuración
    show_env_config()

    # Probar conexión
    test_email_connection()

    # Ejecutar prueba
    run_initial_test()

    print("\n" + "="*60)
    print("CONFIGURACIÓN COMPLETADA")
    print("="*60)
    print("Para iniciar el procesamiento automático:")
    print("python manage.py schedule_cx_email_processing")
    print()
    print("Para procesar manualmente:")
    print("python manage.py process_cx_emails")
    print()
    print("Para procesar con dry-run (sin crear items):")
    print("python manage.py process_cx_emails --dry-run")


if __name__ == '__main__':
    main()