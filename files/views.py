from django.shortcuts import render

from files import models
from files.utils import traverse

from collections import defaultdict

import os

def index(request):
    username = os.environ['REMOTE_USER']

    # Get file and directory records from database
    files = models.File.objects.all()
    directories = models.Directory.objects.all()

    # Build up a directory tree
    roots = []
    subdirs = defaultdict(list)
    subfiles = defaultdict(list)

    # Note: "id" is the default name for a model's primary key
    # If a different key is set for the model, this would need to be incorporated here to make the demo application work properly
    for d in directories:
        if d.parent is None:
            roots.append(d)
        else:
            subdirs[d.parent_id].append(d)
    for f in files:
        subfiles[f.directory_id].append(f)

    # Convert into a suitable format for output
    dirlist = []
    for root in roots:
        dirlist.append(traverse(root, subfiles, subdirs))

    # Display directory tree to user
    return render(request, 'files/index.html', {'directories': dirlist, 'user': username})

def fileview(request, file_id):
    try:
        f = models.File.objects.get(id=file_id)
    except File.DoesNotExist:
        raise Http404("Non-existent file ID provided")
    permissions = f.permission_set.all()
    return render(request, 'files/fileview.html', {'file': f, 'permissions': permissions})

def dirview(request, dir_id):
    # Stub
    return None
