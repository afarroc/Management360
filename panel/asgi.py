import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panel.settings")
    django_asgi_app = get_asgi_application()

    # Import after Django setup to avoid AppRegistryNotReady
    from chat.routing import websocket_urlpatterns

    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    })
except Exception as e:
    # Log the exception for debugging purposes
    import logging
    logging.error(f"Error in ASGI configuration: {e}")
    raise