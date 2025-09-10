#!/usr/bin/env python
"""
Script para verificar si la tabla CreditAccount existe y funciona correctamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.db import connection
from events.models import CreditAccount
from django.contrib.auth.models import User

def check_creditaccount_table():
    """Verifica si la tabla CreditAccount existe"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM events_creditaccount LIMIT 1")
            result = cursor.fetchone()
            print("Tabla events_creditaccount existe")
            return True
    except Exception as e:
        print(f"Error con tabla events_creditaccount: {e}")
        return False

def check_creditaccount_model():
    """Verifica si el modelo CreditAccount funciona"""
    try:
        count = CreditAccount.objects.count()
        print(f"Modelo CreditAccount funciona - {count} registros")
        return True
    except Exception as e:
        print(f"Error con modelo CreditAccount: {e}")
        return False

def test_creditaccount_creation():
    """Prueba crear un CreditAccount"""
    try:
        # Crear usuario de prueba
        test_user = User.objects.create_user(
            username='test_user_signal',
            email='test@example.com',
            password='testpass123'
        )

        # Verificar si se creó el CreditAccount automáticamente
        credit_account = CreditAccount.objects.filter(user=test_user).first()
        if credit_account:
            print("CreditAccount creado automaticamente por senal")
            # Limpiar
            credit_account.delete()
            test_user.delete()
            return True
        else:
            print("CreditAccount NO se creo automaticamente")
            test_user.delete()
            return False

    except Exception as e:
        print(f"Error al probar creacion de CreditAccount: {e}")
        return False

if __name__ == '__main__':
    print("DIAGNOSTICO DE CREDITACCOUNT")
    print("=" * 40)

    table_ok = check_creditaccount_table()
    model_ok = check_creditaccount_model()
    signal_ok = test_creditaccount_creation()

    print("\n" + "=" * 40)
    if table_ok and model_ok and signal_ok:
        print("TODO FUNCIONA CORRECTAMENTE")
        sys.exit(0)
    else:
        print("HAY PROBLEMAS - REVISAR LOGS")
        sys.exit(1)