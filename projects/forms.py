from django import forms
from projects.models import Project


class ProjectFileForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.all())
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    public = forms.BooleanField(required=False)
