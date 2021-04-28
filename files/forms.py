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

class FileEditForm(forms.Form):
    contents = forms.CharField()
    def __init__(self, *args, **kwargs):
        edit_file = kwargs.pop('edit_file', ())
        super().__init__(*args, **kwargs)
        self.fields['contents'] = forms.CharField(widget=forms.Textarea, required=False,
                initial=edit_file.contents)

class NewFileForm(forms.Form):
    name = forms.CharField(required=True)

class NewDirForm(forms.Form):
    name = forms.CharField(required=True)
