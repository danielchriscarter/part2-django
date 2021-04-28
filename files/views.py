from django.http import HttpResponseBadRequest
from django.shortcuts import render

from files import models
from files.utils import traverse
from files.forms import *

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
        # Load in the file that was requested
        f = models.File.objects.get(id=file_id)
    except File.DoesNotExist:
        raise Http404("Non-existent file ID provided")

    # Get the list of currently permitted users
    users = [p.owner for p in f.permission_set.all()]

    # If a permission change has been requested
    if request.method == 'POST':
        # Load and validate form data
        update_perm_form = PermissionUpdateForm(request.POST, users = users)
        if update_perm_form.is_valid():
            # Deal with updating permissions
            if update_perm_form.cleaned_data['add']:
                # Add new user to permission list
                new_user = models.Permission(file = f, owner = update_perm_form.cleaned_data['add'])
                new_user.save()
            for removed_user in update_perm_form.cleaned_data['remove']:
                # Remove user from permission list
                permission = models.Permission.objects.filter(file = f, owner = removed_user)
                permission.delete()
        else:
            return HttpResponseBadRequest('Invalid permission update request')
        # Refresh the list of users, and display to the user as normal
        users = [p.owner for p in f.permission_set.all()]

    # Create a form to allow the user to update permissions
    perm_form = PermissionUpdateForm(users = users)
    return render(request, 'files/fileview.html', {'file': f, 'perm_form': perm_form})

# Conceptually similar to fileview, but using different tables
def dirview(request, dir_id):
    try:
        # Load in the directory that was requested
        d = models.Directory.objects.get(id=dir_id)
    except Directory.DoesNotExist:
        raise Http404("Non-existent directory ID provided")

    # Get the list of currently permitted users
    users = [p.owner for p in d.directory_permission_set.all()]

    # If a permission change has been requested
    if request.method == 'POST':
        # Load and validate form data
        update_perm_form = PermissionUpdateForm(request.POST, users = users)
        if update_perm_form.is_valid():
            # Deal with updating permissions
            if update_perm_form.cleaned_data['add']:
                # Add new user to permission list
                new_user = models.Directory_Permission(directory = d, owner = update_perm_form.cleaned_data['add'])
                new_user.save()
            for removed_user in update_perm_form.cleaned_data['remove']:
                # Remove user from permission list
                permission = models.Permission.objects.filter(directory = d, owner = removed_user)
                permission.delete()
        else:
            return HttpResponseBadRequest('Invalid permission update request')
        # Refresh the list of users, and display to the user as normal
        users = [p.owner for p in d.directory_permission_set.all()]

    # Create a form to allow the user to update permissions
    perm_form = PermissionUpdateForm(users = users)
    return render(request, 'files/dirview.html', {'directory': d, 'perm_form': perm_form})

def fileedit(request, file_id):
    try:
        # Load in the file that was requested
        f = models.File.objects.get(id=file_id)
    except File.DoesNotExist:
        raise Http404("Non-existent file ID provided")

    if request.method == 'POST':
        # Load and validate form data
        edit_form = FileEditForm(request.POST, edit_file = f)
        if edit_form.is_valid():
            # Update file contents
            f.contents = edit_form.cleaned_data['contents']
            f.save()
            # Redirect user back to file viewing page
            return fileview(request, file_id)
        else:
            return HttpResponseBadRequest('Invalid file contents update request')

    # If we weren't sent an update POST, show the editing interface
    edit_form = FileEditForm(edit_file = f)
    return render(request, 'files/fileedit.html', {'file' : f, 'form' : edit_form})

def newfile(request, dir_id):
    try:
        # Load in the containing directory that was requested
        d = models.Directory.objects.get(id=dir_id)
    except Directory.DoesNotExist:
        raise Http404("Non-existent directory ID provided")
 
    if request.method == 'POST':
        # Load and validate form data
        file_form = NewFileForm(request.POST)
        if file_form.is_valid():
            username = os.environ['REMOTE_USER']
            # Create a new file
            new_file = models.File(name = file_form.cleaned_data['name'], directory = d, contents='', owner=username)
            new_file.save()
            #new_perm = models.Permission(file = new_file, owner = username)
            #new_perm.save()
            # Redirect user to editing interface, to add content to the file
            return fileedit(request, new_file.id)
        else:
            return HttpResponseBadRequest('Containing directory does not exist')

    # If we weren't sent a POST, get the name of the file from the user
    file_form = NewFileForm()
    return render(request, 'files/create.html', {'type' : 'file', 'form' : file_form, 'dir' : d})

def newdir(request, dir_id):
    try:
        # Load in the containing directory that was requested
        d = models.Directory.objects.get(id=dir_id)
    except Directory.DoesNotExist:
        raise Http404("Non-existent directory ID provided")

    if request.method == 'POST':
        # Load and validate form data
        dir_form = NewDirForm(request.POST)
        if dir_form.is_valid():
            username = os.environ['REMOTE_USER']
            # Create a new directory
            new_dir = models.Directory(name = file_form.cleaned_data['name'], parent = d, owner=username)
            new_dir.save()
            # Redirect user to directory management page
            return dirview(request, new_dir.id)
        else:
            return HttpResponseBadRequest('Containing directory does not exist')

    # If we weren't sent a POST, get the name of the file from the user
    file_form = NewFileForm()
    return render(request, 'files/create.html', {'type' : 'directory', 'form' : file_form, 'dir' : d})
