from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect

from files import models
from files.utils import traverse, username
from files.forms import *

from collections import defaultdict

def index(request):
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

    # Display a search box
    search_form = SearchForm()

    # Display directory tree to user
    return render(request, 'files/index.html', {'directories': dirlist, 'user': username(), 'search_form' : search_form})

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
    # Check whether current user is the owner
    # (N.B. not for security purposes - this just avoids showing the user options which will only produce SQL errors)
    is_owner = (username() == f.owner)
    return render(request, 'files/fileview.html', {'file': f, 'perm_form': perm_form, 'owner' : is_owner})

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
                permission = models.Directory_Permission.objects.filter(directory = d, owner = removed_user)
                permission.delete()
        else:
            return HttpResponseBadRequest('Invalid permission update request')
        # Refresh the list of users, and display to the user as normal
        users = [p.owner for p in d.directory_permission_set.all()]

    # Create a form to allow the user to update permissions
    perm_form = PermissionUpdateForm(users = users)
    # Check whether current user is the owner
    is_owner = (username() == d.owner)
    return render(request, 'files/dirview.html', {'directory': d, 'perm_form': perm_form, 'owner' : is_owner})

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
            return redirect('files:file', file_id = file_id)
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
            # Create a new file
            new_file = models.File(name = file_form.cleaned_data['name'], directory = d, contents='', owner=username())
            new_file.save()
            # Redirect user to editing interface, to add content to the file
            return redirect('files:file', file_id = new_file.id)
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
            # Create a new directory
            new_dir = models.Directory(name = dir_form.cleaned_data['name'], parent = d, owner=username())
            new_dir.save()
            # Redirect user to directory management page
            return redirect('files:directory', dir_id = new_dir.id)
        else:
            return HttpResponseBadRequest('Containing directory does not exist')

    # If we weren't sent a POST, get the name of the file from the user
    file_form = NewDirForm()
    return render(request, 'files/create.html', {'type' : 'directory', 'form' : file_form, 'dir' : d})

# Similar to newdir, but uses a different form since there's no parent directory
def newdir_root(request):
    if request.method == 'POST':
        # Load and validate form data
        dir_form = NewDirForm(request.POST)
        if dir_form.is_valid():
            # Create a new directory
            new_dir = models.Directory(name = dir_form.cleaned_data['name'], parent = None, owner=username())
            new_dir.save()
            # Redirect user to directory management page
            return redirect('files:directory', dir_id = new_dir.id)
        else:
            return HttpResponseBadRequest('Containing directory does not exist')

    # If we weren't sent a POST, get the name of the file from the user
    file_form = NewDirForm()
    return render(request, 'files/rootdir.html', {'type' : 'directory', 'form' : file_form})

def search(request):
    if request.method == 'POST':
        # Load in search term from user
        search_form = SearchForm(request.POST)
        if search_form.is_valid():
            # Extract search term from page
            term = search_form.cleaned_data['term']
            # Get database table name to search in
            table = models.File._meta.db_table
            # Deliberate SQL injection vulnerability
            query = "SELECT * FROM " + table + " WHERE CONTENTS LIKE '%%" + term + "%%'"
            results = models.File.objects.raw(query)
            return render(request, 'files/search.html', {'term' : term, 'results' : results})
        else:
            return HttpResponseBadRequest('Error in processing search request')

    # This page only accepts POST requests - redirect back to the homepage (which has a search box) otherwise
    return redirect('files:index')
