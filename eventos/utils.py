# utils.py

from decimal import Decimal
from django.contrib import messages
from .models import CreditAccount

def add_credits_to_user(user, amount):
    if not hasattr(user, 'creditaccount'):
        CreditAccount.objects.create(user=user)
    
    try:
        amount = Decimal(amount)
        user.creditaccount.add_credits(amount)
        return True, f"Monto agregado {amount}"
    except (ValueError, Decimal.InvalidOperation):
        return False, "Monto no válido"
