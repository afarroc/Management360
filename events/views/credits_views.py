# events/credits_views.py
# ============================================================================
# VISTAS DE GESTIÓN DE CRÉDITOS
# ============================================================================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..management.utils import add_credits_to_user


# ============================================================================
# VISTA PARA AÑADIR CRÉDITOS
# ============================================================================

@login_required
def add_credits(request):
    """
    Vista para que los usuarios añadan créditos a su cuenta
    """
    if request.method == 'POST':
        amount = request.POST.get('amount')
        
        # Validar que el monto sea un número válido
        try:
            amount = float(amount)
            if amount <= 0:
                return render(request, 'credits/add_credits.html', {
                    'error': 'El monto debe ser un número positivo'
                })
        except (ValueError, TypeError):
            return render(request, 'credits/add_credits.html', {
                'error': 'Por favor, ingresa un monto válido'
            })
        
        # Procesar la adición de créditos
        success, message = add_credits_to_user(request.user, amount)
        
        if success:
            messages.success(request, message)
            return redirect('home')
        else:
            return render(request, 'credits/add_credits.html', {'error': message})

    # GET request - mostrar formulario
    return render(request, 'credits/add_credits.html')