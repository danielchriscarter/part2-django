"""
WSGI config for krbsite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os
import sys

path='/var/www/krbsite'

if path not in sys.path:
    sys.path.append(path)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'krbsite.settings')

_application = get_wsgi_application()

saved_envvars = ['REMOTE_USER', 'KRB5CCNAME']

def application(environ, start_response):
    for var in saved_envvars:
        os.environ[var] = environ.get(var, '')
    return _application(environ, start_response)
