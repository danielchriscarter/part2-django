from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
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
    # Show an information page
    return render(request, 'managedb/index.html', {'database': settings.DELEG_DATABASE})

def select(request):
    database = settings.DELEG_DATABASE

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
            # Columns output using an approach described at https://adamj.eu/tech/2020/02/18/safely-including-data-for-javascript-in-a-django-template/
            forms.append(TableMappingForm(title=name, tables=tables, columns=columns, prefix=name))
    return render(request, 'managedb/table_mapping.html', {'forms': forms, 'columns' : columns, 'database': database})


def setup(request):
    if request.method == 'POST':
        database = settings.DELEG_DATABASE
        models = request.session['models']
        columns = request.session['columns']
        form_data = dict()
        errstring = ''

        for (name, model) in models.items():
            if len(model['dependencies']) > 0:
                tables = model['dependencies'].keys()
                form = TableMappingForm(request.POST, tables=tables, columns=columns, prefix=name)
                if form.is_valid():
                    if form.cleaned_data['include']:
                        form_data[name] = form.cleaned_data
                else:
                    # Form data had an error in it - log it and go on to the next table
                    errstring += (pformat(form.errors) + '\n\n')
                    continue

        for (model, assignment) in form_data.items():
            source_table = models[model]['table']
            source_column = models[model]['primary_key']
            perm_table = assignment['table']
            perm_column = models[model]['dependencies'][perm_table]
            owner_column = assignment['column']

            with connections[database].cursor() as cursor:
                # Enable row-level security on the relevant table
                cursor.execute("""ALTER TABLE %s ENABLE ROW LEVEL SECURITY"""
                        % (source_table))
                # Only allow users to view and edit files which they have permission to see
                cursor.execute("""CREATE POLICY %s_view ON %s
                USING (%s IN (SELECT %s FROM %s WHERE %s = session_user))"""
                        % (source_table, source_table, source_column, perm_column, perm_table, owner_column))
                # Insertions to the "main" tables are not restricted, as a USING policy only applies to already-existing records
                # (see https://www.postgresql.org/docs/13/sql-createpolicy.html)
                # Allow all insertions
                cursor.execute("""CREATE POLICY %s_insert ON %s FOR INSERT
                WITH CHECK (true);"""
                        % (source_table, source_table))

                # Also enable row-level security on the permissions table
                cursor.execute("""ALTER TABLE %s ENABLE ROW LEVEL SECURITY"""
                        % (perm_table))
                # Allow all users to view the permissions table
                cursor.execute("""CREATE POLICY %s_view ON %s FOR SELECT
                USING (true);"""
                        % (perm_table, perm_table))
                # Only allow users to set permissions where they already have access to that file
                cursor.execute("""CREATE POLICY %s_insert ON %s FOR INSERT
                WITH CHECK (%s IN (SELECT %s FROM %s WHERE %s = session_user))"""
                        % (perm_table, perm_table, perm_column, perm_column, perm_table, owner_column))
                # Special case (to allow for new files) - a file with no current users can have a permission created for it
                cursor.execute("""CREATE POLICY %s_insert_empty ON %s FOR INSERT
                WITH CHECK (%s NOT IN (SELECT %s FROM %s))"""
                        % (perm_table, perm_table, perm_column, perm_column, perm_table))

                # Having added these policies, allow all users to use the main table
                cursor.execute("""GRANT SELECT, INSERT, UPDATE ON %s TO PUBLIC"""
                        % (source_table))
                # Grant SELECT (unrestricted) and INSERT (restricted using policies above) on the permissions table - do not grant UPDATE
                cursor.execute("""GRANT SELECT, INSERT ON %s TO PUBLIC"""
                        % (perm_table))

        # Feed the result back to the user
        return render(request, 'managedb/result.html', {'errors': (len(errstring) > 0), 'errstring': errstring})
    else:
        # GET requests to this page are invalid
        return HttpResponseBadRequest('No form submitted')
