import datetime as dt

from django import forms
from operations.models import RunningPackage
from systemsettings.models import Package
    
class PartialRunningPackageForm(forms.ModelForm):
    class Meta:
        model = RunningPackage
        fields = ('settings', 'timeslot', 'area', 'host')