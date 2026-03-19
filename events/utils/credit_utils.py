"""
Utilidades para gestión de créditos y transacciones
Centraliza toda la lógica relacionada con créditos
"""

from decimal import Decimal, InvalidOperation
from django.contrib.auth import get_user_model

User = get_user_model()
from ..models import CreditAccount
import logging

logger = logging.getLogger(__name__)


def ensure_credit_account(user):
    """
    Asegura que el usuario tenga una cuenta de créditos
    
    Args:
        user (User): Instancia de usuario
        
    Returns:
        CreditAccount: Cuenta de créditos del usuario
    """
    if not hasattr(user, 'creditaccount'):
        logger.info(f"Creating credit account for user {user.username}")
        return CreditAccount.objects.create(user=user)
    
    return user.creditaccount


def add_credits_to_user(user, amount):
    """
    Agrega créditos a la cuenta de un usuario
    
    Args:
        user (User): Instancia de usuario
        amount (str|Decimal): Monto a agregar
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        credit_account = ensure_credit_account(user)
        amount_decimal = Decimal(str(amount))
        
        credit_account.add_credits(amount_decimal)
        
        logger.info(f"Added {amount_decimal} credits to user {user.username}")
        return True, f"Monto agregado: {amount_decimal}"
        
    except (ValueError, InvalidOperation) as e:
        logger.error(f"Invalid credit amount '{amount}': {e}")
        return False, "Monto no válido"
        
    except Exception as e:
        logger.exception(f"Error adding credits to user {user.username}: {e}")
        return False, f"Error al agregar créditos: {str(e)}"


def get_credit_balance(user):
    """
    Obtiene el balance de créditos del usuario
    
    Args:
        user (User): Instancia de usuario
        
    Returns:
        Decimal: Balance de créditos
    """
    credit_account = ensure_credit_account(user)
    return credit_account.balance


def deduct_credits(user, amount, description=""):
    """
    Deduce créditos de la cuenta de un usuario
    
    Args:
        user (User): Instancia de usuario
        amount (Decimal): Monto a deducir
        description (str): Descripción de la transacción
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        credit_account = ensure_credit_account(user)
        amount_decimal = Decimal(str(amount))
        
        if credit_account.balance < amount_decimal:
            return False, "Saldo insuficiente"
        
        # Método a implementar en CreditAccount
        credit_account.deduct_credits(amount_decimal, description)
        
        logger.info(f"Deducted {amount_decimal} credits from user {user.username}")
        return True, f"Créditos deducidos: {amount_decimal}"
        
    except Exception as e:
        logger.exception(f"Error deducting credits from user {user.username}: {e}")
        return False, f"Error al deducir créditos: {str(e)}"


def format_currency(amount, currency="$"):
    """
    Formatea un monto como moneda
    
    Args:
        amount (Decimal): Monto a formatear
        currency (str): Símbolo de moneda
        
    Returns:
        str: Monto formateado
    """
    try:
        return f"{currency}{float(amount):,.2f}"
    except:
        return f"{currency}0.00"