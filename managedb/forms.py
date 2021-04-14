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
