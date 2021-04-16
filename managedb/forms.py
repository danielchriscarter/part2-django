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
    # TODO: resolve "required" status where dependent on other fields
    include = forms.BooleanField(required=False)
    table = forms.ChoiceField(required=True)
    column = forms.ChoiceField(required=True,
            widget=forms.Select(attrs={'class' : 'colselect'}))
    def __init__(self, *args, **kwargs):
        self.title = kwargs.pop('title', ())
        tables = kwargs.pop('tables', ())
        super().__init__(*args, **kwargs)
        table_choices = [('', '')] + [(x,x) for x in tables]
        self.fields['table'] = forms.ChoiceField(choices=table_choices,
                widget=forms.Select(attrs={'onchange' : 'update(this.id);'}))
        # Column selection field is populated in JavaScript
