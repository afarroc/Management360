# analyst/signals.py
import logging
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_out
from django.contrib.sessions.models import Session
from django.utils import timezone

logger = logging.getLogger(__name__)

@receiver(user_logged_out)
def cleanup_user_session(sender, request, user, **kwargs):
    """
    Limpia los datos temporales cuando el usuario cierra sesión
    """
    logger.info(f"Limpiando datos de sesión para usuario {user}")
    
    if hasattr(request, 'session'):
        # Eliminar datos de upload
        if 'upload_data' in request.session:
            del request.session['upload_data']
        
        # Limpiar clipboard
        if 'clipboard' in request.session:
            del request.session['clipboard']
        if 'clipboard_keys' in request.session:
            del request.session['clipboard_keys']
        
        request.session.modified = True


def cleanup_expired_sessions():
    """
    Limpia sesiones expiradas periódicamente
    (Esta función puede ser llamada desde un comando de gestión)
    """
    try:
        expired = Session.objects.filter(expire_date__lt=timezone.now()).delete()
        if expired[0] > 0:
            logger.info(f"Limpiadas {expired[0]} sesiones expiradas")
        return expired[0]
    except Exception as e:
        logger.error(f"Error limpiando sesiones expiradas: {str(e)}")
        return 0