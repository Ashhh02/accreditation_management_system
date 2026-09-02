"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

Serves both regular HTTP requests and WebSocket connections. WebSockets are
authenticated with Django's session/authentication middleware (AuthMiddlewareStack)
so the consumers can rely on ``scope['user']`` being an authenticated User.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

import core.routing
import resources.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Pre-load the Django app registry before any consumer runs.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                core.routing.websocket_urlpatterns
                + resources.routing.websocket_urlpatterns
            )
        )
    ),
})