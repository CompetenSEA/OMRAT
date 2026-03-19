"""ASGI config for OMRAT Django project."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omrat_web.settings')

application = get_asgi_application()
