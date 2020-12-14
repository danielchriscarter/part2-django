from django.shortcuts import render
from django.http import HttpResponse

#from . import models
from files import models

from pprint import pformat

# Create your views here.

def index(request):
    #return HttpResponse(pformat(dir(models.Model.from_db), indent=4))
    files = models.File.objects.using('data').all()
    #return HttpResponse(pformat(dir(files[0]), indent=4))
    outstr = ""
    for f in files:
        outstr += f.name + " (" + f.directory.name + ")\n"
    return HttpResponse(outstr)
    return HttpResponse("Hello World")
