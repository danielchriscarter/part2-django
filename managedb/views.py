from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.db import connections
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
            # Include the table itself as well as its dependents
            search_tables = list(dependents.keys())
            search_tables.append(model_data['table'])
            for table in search_tables:
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
            owner_cols = columns[model['table']]
            tables = model['dependencies'].keys()
            # Columns output using an approach described at https://adamj.eu/tech/2020/02/18/safely-including-data-for-javascript-in-a-django-template/
            forms.append(TableMappingForm(title=name, owner_cols=owner_cols, tables=tables, columns=columns, prefix=name))
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
                owner_cols = columns[model['table']]
                tables = model['dependencies'].keys()
                form = TableMappingForm(request.POST, owner_cols=owner_cols, tables=tables,
                        columns=columns, prefix=name)
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
            source_owner_column = assignment['owner_field']

            with connections[database].cursor() as cursor:
                # Enable row-level security on the relevant table
                cursor.execute(f"""ALTER TABLE {source_table} ENABLE ROW LEVEL SECURITY""")
                # Only allow users to view files which they have permission to see
                cursor.execute(f"""CREATE POLICY {source_table}_view ON {source_table} FOR SELECT
                USING ({source_column} IN (SELECT {perm_column} FROM {perm_table}
                WHERE {owner_column} = session_user))""")
                # Or where they are the owner (in which case allow editing as well)
                cursor.execute(f"""CREATE POLICY {source_table}_view_owner ON {source_table}
                USING ({source_owner_column} = session_user)""")
                # Insertions to the "main" tables are not restricted, as a USING policy only applies to already-existing records
                # (see https://www.postgresql.org/docs/13/sql-createpolicy.html)
                # Allow all insertions
                cursor.execute(f"""CREATE POLICY {source_table}_insert ON {source_table} FOR INSERT
                WITH CHECK (true);""")

                # Also enable row-level security on the permissions table
                cursor.execute(f"""ALTER TABLE {perm_table} ENABLE ROW LEVEL SECURITY""")
                # Allow all users to view the permissions table
                cursor.execute(f"""CREATE POLICY {perm_table}_view ON {perm_table} FOR SELECT
                USING (true);""")
                # Only allow users to set permissions where they are the owner
                cursor.execute(f"""CREATE POLICY {perm_table}_insert ON {perm_table} FOR INSERT
                WITH CHECK ({perm_column} IN (SELECT {source_column} FROM {source_table}
                WHERE {source_owner_column} = session_user))""")
                # Similarly, only allow the owner to delete permissions
                cursor.execute(f"""CREATE POLICY {perm_table}_delete ON {perm_table} FOR DELETE
                USING ({perm_column} IN (SELECT {source_column} FROM {source_table}
                WHERE {source_owner_column} = session_user))""")

                # Having added these policies, allow all users to use the main table
                cursor.execute(f"""GRANT SELECT, INSERT, UPDATE ON {source_table} TO PUBLIC""")
                # Grant SELECT (unrestricted) and INSERT (restricted using policies above) on the permissions table - do not grant UPDATE
                cursor.execute(f"""GRANT SELECT, INSERT, DELETE ON {perm_table} TO PUBLIC""")
                # Permit access to ID sequences to allow inserting new records with sequential IDs
                # (see https://stackoverflow.com/questions/9325017/error-permission-denied-for-sequence-cities-id-seq-using-postgres)
                cursor.execute("""GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO PUBLIC""")

        # Feed the result back to the user
        return render(request, 'managedb/result.html', {'errors': (len(errstring) > 0), 'errstring': errstring})
    else:
        # GET requests to this page are invalid
        return HttpResponseBadRequest('No form submitted')
