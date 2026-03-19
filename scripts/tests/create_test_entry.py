#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
from bitacora.models import BitacoraEntry

def create_test_entry():
    """Crear una entrada de prueba con contenido JSON"""

    # Obtener o crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("Usuario de prueba creado")

    # JSON de ejemplo con componentes publicitarios
    json_content = '''[{'type': 'ad_banner', 'title': '¡Lleva tu Álgebra al Siguiente Nivel!', 'content': {'header': '¿Te está gustando el curso?', 'subheader': 'Descubre todas las ventajas de la versión PREMIUM', 'features': ['💻 **Acceso ilimitado** a todos los módulos y lecciones', '🤖 **Ejercicios personalizados** con inteligencia artificial'], 'offer': '**OFERTA ESPECIAL:** 40% de descuento por tiempo limitado', 'price': {'original': '$99.000', 'discounted': '$59.400', 'period': 'acceso vitalicio'}, 'cta': {'text': '¡QUIERO SER PREMIUM!', 'url': '#premium-upgrade', 'color': 'success'}}}, {'type': 'ad_card', 'title': '¿Necesitas Más Práctica?', 'content': {'header': 'Kit de Ejercicios Premium de Álgebra', 'description': 'Pack exclusivo con 500+ ejercicios resueltos paso a paso', 'highlights': ['✅ **Ejercicios adicionales** para cada lección'], 'price': '$19.900', 'badge': 'MÁS VENDIDO', 'cta': {'text': 'DESCARGAR KIT', 'url': '#exercise-kit'}}}]'''

    # Crear entrada con JSON embebido en el contenido
    entry = BitacoraEntry.objects.create(
        titulo='Entrada de Prueba con Componentes JSON',
        contenido=f'Esta es una entrada de prueba que contiene componentes JSON embebidos.\n\n{json_content}\n\nFin del contenido.',
        autor=user,
        categoria='personal',
        is_public=True
    )

    print(f"Entrada creada: {entry.titulo}")
    print(f"ID: {entry.id}")
    print(f"Contenido tiene {len(entry.contenido)} caracteres")

    # Verificar si el JSON fue extraído
    from bitacora.views import BitacoraCreateView
    view_instance = BitacoraCreateView()
    structured = view_instance.extract_structured_content(entry.contenido)
    print(f"Contenido estructurado extraído: {len(structured)} componentes")

    if structured:
        entry.structured_content = structured
        entry.save()
        print("Contenido estructurado guardado en la entrada")

    return entry

if __name__ == '__main__':
    entry = create_test_entry()
    print(f"\nEntrada creada exitosamente: /bitacora/{entry.id}/")
    print("Visita la URL para ver si los componentes JSON se renderizan correctamente.")