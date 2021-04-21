from django.shortcuts import render

from files import models

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
        subfiles[f.directory_id].append(d)

    # Display directory tree to user
    context = {'directories': subdirs, 'files' : subfiles, 'roots': roots, 'user' : username}
    return render(request, 'files/index.html', context)

