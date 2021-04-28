from django import forms

class ColumnChoiceField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def validate(self, value):
        # We can't validate this field without knowing the value of the table field, so assume it's valid for now
        pass

# Basic form to identify which database to apply policies to
class SelectDBForm(forms.Form):
    database = forms.ChoiceField()
    def __init__(self, *args, **kwargs):
        # Get list of databases from argument
        databases = kwargs.pop('databases', ())
        super().__init__(*args, **kwargs)
        # Provide pairs of (field, enumeration) values
        db_choices = [(str(x),str(x)) for x in databases]
        # Populate form entries
        self.fields['database'] = forms.ChoiceField(choices=db_choices)

class TableMappingForm(forms.Form):
    include = forms.BooleanField(required=False)
    # Requirements for table and column values are enforced below
    owner_field = forms.ChoiceField(required=False)
    table = forms.ChoiceField(required=False)
    column = ColumnChoiceField(required=False,
            widget=forms.Select(attrs={'class' : 'colselect'}))
    def __init__(self, *args, **kwargs):
        self.title = kwargs.pop('title', ())
        owner_cols = kwargs.pop('owner_cols', ())
        tables = kwargs.pop('tables', ())
        # Save columns for later validation purposes
        self.columns = kwargs.pop('columns', ())
        super().__init__(*args, **kwargs)
        owner_choices = [('', '')] + [(x,x) for x in owner_cols]
        table_choices = [('', '')] + [(x,x) for x in tables]
        self.fields['owner_field'] = forms.ChoiceField(choices=owner_choices, required=False)
        self.fields['table'] = forms.ChoiceField(choices=table_choices, required=False,
                widget=forms.Select(attrs={'onchange' : 'update(this.id);'}))
        # Column selection field is populated in JavaScript

    def clean(self):
        super().clean()
        # If "include" is not specified, rest of the data is ignored
        if self.cleaned_data.get('include'):
            table = self.cleaned_data.get('table')
            column = self.cleaned_data.get('column')
            if table is None or table == '':
                self.add_error('column', 'No table was specified')
            elif column not in self.columns[table]:
                self.add_error('column', 'Specified column name is not in the specified table')
        return self.cleaned_data
