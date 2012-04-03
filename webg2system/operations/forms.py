import datetime as dt

from django import forms
    
class CreatePackageForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255, 
                               widget=forms.PasswordInput(render_value=False))
    package = forms.CharField(max_length=255)
    area = forms.CharField(max_length=255)
    timeslot = forms.DateTimeField()
    force = forms.BooleanField(required=False)
    extra = forms.CharField(
                max_length=255, 
                required=False, 
                help_text='Extra keyword arguments for the task. They ' \
                          'should be given in JSON object format.'
            )
