import datetime as dt

from django import forms
from models import RunningPackage
    
class PartialRunningPackageForm(forms.ModelForm):
    class Meta:
        model = RunningPackage
        fields = ('settings', 'timeslot', 'area', 'host')

class CreatePackageForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255, 
                               widget=forms.PasswordInput(render_value=False))
    package = forms.CharField(max_length=255)
    area = forms.CharField(max_length=255)
    host = forms.CharField(max_length=255)
    timeslot = forms.DateTimeField()
    force = forms.BooleanField(required=False)
