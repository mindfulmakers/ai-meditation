"""
ASGI config for web project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

from __future__ import annotations

import logging
import os
from importlib import import_module

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

import users.routing
from config.app_packages import get_package_apps

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["ASGI_THREADS"] = "4"

logger = logging.getLogger(__name__)

django_asgi_app = get_asgi_application()

# Collect websocket patterns from enabled sites
all_websocket_patterns = [
    *users.routing.websocket_urlpatterns,
]
for app in get_package_apps():
    try:
        routing_module = import_module(f"{app}.routing")
        if hasattr(routing_module, "websocket_urlpatterns"):
            all_websocket_patterns.extend(routing_module.websocket_urlpatterns)
    except (ImportError, ModuleNotFoundError):
        # logger.debug(f"Failed to import routing module for {app}: {e}")
        pass


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(all_websocket_patterns))
        ),
    }
)
