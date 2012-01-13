import datetime as dt

from operations.forms import PartialRunningPackageForm

from piston.handler import BaseHandler
from piston.utils import validate

from operations.models import RunningPackage
from systemsettings.models import Package, Area, Host

class RunningPackageHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    model = RunningPackage

    def read(self, request, packId=None):

        base = RunningPackage.objects

        if packId is not None:
            result = base.get(pk=packId)
        else:
            result = base.all()
        return result

    # FIXME
    # not implemented or tested fully yet.
    @validate(PartialRunningPackageForm, 'POST')
    def run_task(self, request, timeslot, settings, area, host):
        '''
        Create a new Running Package and run it.

        Inputs:

            timeslot - A string in the form "YYYYMMDDhhmm"

            settings - The name of the package settings to use

            area - The name of the default area to use

            host - The name of the host where to package is to run

        Returns:

            The RunningPackage's id.
        '''

        theTimeslot = request.form.cleaned_data['timeslot']
        thePackage = request.form.cleaned_data['package']
        theArea = request.form.cleaned_data['area']
        theHost = request.form.cleaned_data['host']
        rp = RunningPackage(timeslot=theTimeslot, settings=thePackage, 
                            area=theArea, host=theHost)
        rp.save()
        return rp.pk
