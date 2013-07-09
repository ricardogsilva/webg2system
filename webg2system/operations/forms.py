import datetime as dt

from django import forms
    
class CreatePackageForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(
        max_length=255,
        widget=forms.PasswordInput(render_value=False)
    )
    package = forms.CharField(max_length=255)
    area = forms.CharField(max_length=255)
    timeslot = forms.DateTimeField(
        input_formats=[
            '%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
            '%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
            '%Y-%m-%d',              # '2006-10-25'
            '%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
            '%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
            '%m/%d/%Y',              # '10/25/2006'
            '%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
            '%m/%d/%y %H:%M',        # '10/25/06 14:30'
            '%m/%d/%y',              # '10/25/06'
            '%Y%m%d%H%M',
            '%Y%m%d%H'
        ],
        help_text='Input format must follow YYYYMMDDHHmm format.'
    )
    force = forms.BooleanField(required=False)
    log_level = forms.CharField(
        max_length=20,
        help_text='Acctepted values are: debug, info, warning, error'
    )
    extra = forms.CharField(
        max_length=255,
        required=False,
        help_text='Extra keyword arguments for the task. They should be ' \
                  'given in JSON object format.'
        )
