from django.conf import settings
from django.http import HttpResponseServerError

import os

class KrbMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):

        # Give an error if the settings file is not correctly set up
        if not hasattr(settings, 'DELEG_DATABASE'):
            return HttpResponseServerError('DELEG_DATABASE must be set in settings.py')
        # Attempt to identify database
        database = settings.DELEG_DATABASE
        if database not in settings.DATABASES:
            return HttpResponseServerError('DELEG_DATABASE option is not a valid database')
        elif settings.DATABASES[database]['ENGINE'] != 'django.db.backends.postgresql':
            return HttpResponseServerError('This permissions framework is only set up to work with a PostgreSQL database')

        # If no problems, set database username for the app to use
        username = os.environ['REMOTE_USER']
        settings.DATABASES[database]['USER'] = username.split('@')[0]

        # Returning None indicates success
        return None

        
