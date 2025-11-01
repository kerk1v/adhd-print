"""
ASGI config for adhd_print_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import logging

from django.core.asgi import get_asgi_application

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

logger = logging.getLogger(__name__)


async def application(scope, receive, send):
    """
    Enhanced ASGI application that handles HTTP requests and lifespan events.
    """
    if scope["type"] == "lifespan":
        # Handle lifespan events (startup/shutdown)
        await handle_lifespan(scope, receive, send)
    elif scope["type"] == "http":
        # Handle HTTP requests with Django (including static files)
        await django_asgi_app(scope, receive, send)
    else:
        # Unsupported scope type
        logger.warning(f"Unsupported ASGI scope type: {scope['type']}")
        raise ValueError(f"Unsupported ASGI scope type: {scope['type']}")


async def handle_lifespan(scope, receive, send):
    """
    Handle ASGI lifespan events (startup and shutdown).
    """
    message = await receive()

    if message["type"] == "lifespan.startup":
        logger.info("ASGI application starting up...")
        try:
            # Perform any startup tasks here
            # The background jobs are already started by Django's AppConfig.ready()
            await send({"type": "lifespan.startup.complete"})
        except Exception as e:
            logger.error(f"Error during startup: {e}", exc_info=True)
            await send({"type": "lifespan.startup.failed", "message": str(e)})

    elif message["type"] == "lifespan.shutdown":
        logger.info("ASGI application shutting down...")
        try:
            # Perform any cleanup tasks here
            # Background job scheduler will be shut down by Django's atexit handler
            await send({"type": "lifespan.shutdown.complete"})
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
            await send({"type": "lifespan.shutdown.failed", "message": str(e)})
