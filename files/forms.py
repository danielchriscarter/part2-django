from django import forms

class PermissionUpdateForm(forms.Form):
    remove = forms.MultipleChoiceField()
    add = forms.CharField(required=False, label='Grant access to')
    def __init__(self, *args, **kwargs):
        users = kwargs.pop('users', ())
        user_choices = [(u,u) for u in users]
        super().__init__(*args, **kwargs)
        self.fields['remove'] = forms.MultipleChoiceField(choices=user_choices,
                widget=forms.CheckboxSelectMultiple, required=False)
