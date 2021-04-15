from django import forms

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
    #table = forms.ChoiceField()
    #column = forms.ChoiceField()
    def __init__(self, *args, **kwargs):
        self.title = kwargs.pop('title', ())
        tables = kwargs.pop('tables', ())
        columns = kwargs.pop('columns', ())
        super().__init__(*args, **kwargs)
        table_choices = [(x,x) for x in tables]
        column_choices = [(x,x) for x in columns]
        self.fields['table'] = forms.ChoiceField(choices=table_choices)
        # This doesn't work yet - need to populate it properly
        self.fields['column'] = forms.ChoiceField(choices=column_choices)
