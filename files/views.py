from django.shortcuts import render
from django.http import HttpResponse
from django.db import connections

#Temporary import
from django.conf import settings

from files import models

from pprint import pformat
import os

def index(request):
    username = os.environ['REMOTE_USER']

    # Needs more thorough testing to make sure it works properly
    settings.DATABASES['data']['USER'] = username.split('@')[0]
    settings.DATABASES['data']['OPTIONS']['ccache_name'] = os.environ['KRB5CCNAME']

    files = models.UserFile.objects.all()
    directories = models.Directory.objects.raw("SELECT * FROM my_dirs;")
    #directories = models.Directory.objects.all()

    context = {"directories": directories, "files" : files, "root_id" : 0, "root_name" :  directories[0].name, "user" : username}

    # N.B. current setup relies on having SELECT access to directories table
    # Try and resolve this (and make the whole output setup tidier)

    #return HttpResponse(os.environ['KRB5CCNAME'])
    return render(request, "files/index.html", context)

