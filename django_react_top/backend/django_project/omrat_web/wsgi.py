"""WSGI config for OMRAT Django project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omrat_web.settings')

application = get_wsgi_application()
