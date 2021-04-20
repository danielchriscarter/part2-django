from django.shortcuts import render
from django.http import HttpResponse
from django.db import connections

#Temporary import
from django.conf import settings

from managedb import models

# Load models from "files" app as well
from files import models as app_models

# Locally created forms
from .forms import *

# Reflection library
import inspect

import os

from pprint import pformat

def index(request):
    # Maybe only allow postgres databases?
    # If we have a form result with a database name
    if request.method == 'POST':
        form = SelectDBForm(request.POST, databases = connections._settings.keys())
        if not form.is_valid():
            # TODO: Improve!
            return HttpResponse(pformat(form.errors))

        # Extract user-submitted database and store it in the user's session
        database = form.cleaned_data['database']
        request.session['database'] = database

        username = os.environ['REMOTE_USER']

        # Needs more thorough testing to make sure it works properly
        settings.DATABASES[database]['USER'] = username.split('@')[0]
        settings.DATABASES[database]['OPTIONS']['ccache_name'] = os.environ['KRB5CCNAME']

        # Enforce admin user (or at least warn?)

        # Step 1
        # Get details of Django models and corresponding database information
        models = dict()
        for (name, model) in inspect.getmembers(app_models, inspect.isclass):
            model_data = dict()
            # Get name of corresponding database table
            model_data['table'] = model._meta.db_table
            # Locate fields of the model (ignoring other class members)
            for (dep_name, dep_model) in inspect.getmembers(model, 
                    lambda x: getattr(x, 'field', None)):
                # Look for a primary_key attribute on the field 
                if getattr(dep_model.field, 'primary_key', False):
                    model_data['primary_key'] = dep_name
            models[name] = model_data

        # Step 2
        # Find candidate tables for storing records
        columns = dict()
        with connections[database].cursor() as cursor:
            for model_data in models.values():
                cursor.execute("""SELECT dst.table_name, dst.column_name
                    FROM information_schema.constraint_column_usage src, information_schema.key_column_usage dst, information_schema.table_constraints constraints
                    WHERE src.constraint_name = constraints.constraint_name
                    AND constraints.constraint_name = dst.constraint_name
                    AND constraints.constraint_type = 'FOREIGN KEY'
                    AND src.table_name = %s
                    AND src.column_name = %s""",
                    [model_data['table'], model_data['primary_key']])
                dependents = dict()
                for (table, foreign_key) in cursor.fetchall():
                    dependents[table] = foreign_key
                # Get details of the table columns, if we don't have them already
                # Note: this doesn't work reliably with tables where the same foreign key appears in more than one column
                for (table, foreign_key) in dependents.items():
                    dependents[table] = foreign_key
                    if table not in columns:
                        # N.B. %% escapes % sign from Django interpolation (here we want to send an actual % sign to SQL server)
                        cursor.execute("""SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name = %s
                            AND data_type LIKE 'character%%'""",
                            [table])
                        # Query results are returned as 1-tuples
                        columns[table] = [x for (x,) in cursor.fetchall()]
                # Save out dependency data
                model_data['dependencies'] = dependents
        # Save this data into the session for later verification
        request.session['models'] = models
        request.session['columns'] = columns

        # Step 3
        # Prepare a form for the user to select appropriate tables
        forms = []
        for (name, model) in models.items():
            if len(model['dependencies']) > 0:
                tables = model['dependencies'].keys()
                forms.append(TableMappingForm(title=name, tables=tables, columns=columns, prefix=name))
        return render(request, 'managedb/table_mapping.html', {'forms': forms, 'columns' : columns})

    # No database name supplied, so we ask the user for one before we can go any further
    else:
        form = SelectDBForm(databases = connections._settings.keys())
        return render(request, 'managedb/index.html', {'form': form})

def setup(request):
    if request.method == 'POST':
        models = request.session['models']
        columns = request.session['columns']
        form_data = dict()

        for (name, model) in models.items():
            if len(model['dependencies']) > 0:
                tables = model['dependencies'].keys()
                form = TableMappingForm(request.POST, tables=tables, columns=columns, prefix=name)
                if form.is_valid():
                    if form.cleaned_data['include']:
                        form_data[name] = form.cleaned_data
                else:
                    # TODO: Improve!
                    # N.B. this stops at the first error
                    return HttpResponse(pformat(form.errors))

        for (model, assignment) in form_data.items():
            source_table = models[model]['table']
            source_column = models[model]['primary_key']
            dest_table = assignment['table']
            dest_column = models[model]['dependencies'][dest_table]
            owner_column = assignment['column']

            with connections[database].cursor() as cursor:
                cursor.execute("""ALTER TABLE %s ENABLE ROW LEVEL SECURITY""",
                        [source_table])
                cursor.execute("""CREATE POLICY %s_view ON %s FOR SELECT
                USING (%s IN (SELECT %s FROM %s WHERE %s = session_user))""",
                        [source_table, source_table, source_column, dest_column, dest_table, owner_column])

        return HttpResponse(pformat(form_data), content_type='text/plain')
    else:
        # Send a proper error here
        return HttpResponse('No form submitted')
