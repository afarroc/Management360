# views.py
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from .forms import PasswordForm
from .generators import PasswordGenerator

def generate_password(request):
    # Inicializamos el generador y el formulario
    generator = PasswordGenerator()
    form = PasswordForm(request.POST or None)
    
    # Contexto base con el formulario y el generador
    context = {
        'form': form,
        'generator': generator,
        'generated_password': None,
        'pattern_used': None,
        'pattern_name': None
    }
    
    if request.method == 'POST' and form.is_valid():
        pattern_type = form.cleaned_data['pattern_type']
        custom_pattern = form.cleaned_data['custom_pattern'].strip()
        include_accents = form.cleaned_data['include_accents']
        
        try:
            # Obtenemos el patrón a usar (predefinido o personalizado)
            if pattern_type == 'custom':
                pattern = custom_pattern
                pattern_name = 'Personalizado'
            else:
                # Para patrones predefinidos, obtenemos el patrón base
                pattern_data = generator.PREDEFINED_PATTERNS[pattern_type]
                pattern = pattern_data['pattern']
                pattern_name = pattern_data['description']
            
            # Aplicamos acentos si está marcada la opción
            if include_accents:
                pattern = apply_accents_to_pattern(pattern)
            
            # Generamos la contraseña
            password = generator.generate(pattern)
            
            # Actualizamos el contexto con los resultados
            context.update({
                'generated_password': password,
                'pattern_used': pattern,
                'pattern_name': pattern_name
            })
            
            messages.success(request, '¡Contraseña generada con éxito!')
            
        except ValueError as e:
            messages.error(request, f'Error en el patrón: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error al generar la contraseña: {str(e)}')
            # Para debug en desarrollo - quitar en producción
            if settings.DEBUG:
                import traceback
                traceback.print_exc()
    
    return render(request, 'passgen/generar.html', context)

def apply_accents_to_pattern(pattern):
    """Aplica acentos a los componentes alfabéticos de un patrón"""
    pattern_parts = []
    for part in pattern.split('|'):
        part = part.strip()
        if part.startswith(('a:', 'A:')):
            parts = part.split(':')
            if len(parts) == 2:  # a:3 → a:3:1
                part = f"{parts[0]}:{parts[1]}:1"
            elif len(parts) == 3:  # a:3:0 → a:3:1
                part = f"{parts[0]}:{parts[1]}:1"
        pattern_parts.append(part)
    return '|'.join(pattern_parts)

def password_help(request):
    generator = PasswordGenerator()
    
    # Obtenemos todos los datos de contexto del generador
    context = generator.get_context_data()
    
    # Añadimos información adicional para el modal
    context.update({
        'modal_title': 'Ayuda para Generación de Contraseñas',
        'pattern_categories': [
            ('Básicas', ['basic', 'pin', 'phrase']),
            ('Avanzadas', ['strong', 'secure']),
            ('Especiales', ['accented', 'date_based'])
        ]
    })
    
    return render(request, 'passgen/info.html', context)
