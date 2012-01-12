import datetime as dt

from piston.handler import BaseHandler
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

    def create(self, request, timeslot, settings, area, host):
        '''
        Create a new Running Package that can subsequently be run.

        Inputs:

            timeslot - A string in the form "YYYYMMDDhhmm"

            settings - The name of the package settings to use

            area - The name of the default area to use

            host - The name of the host where to package is to run
        '''

        ts = dt.datetime.strptime(timeslot, '%Y%m%d%H%M')
        theTimeslot = ts.strftime('%Y-%m-%d %H:%M:%S')
        thePackage = Package.objects.get(name=settings)
        theArea = Area.objects.get(name=area)
        theHost = Host.objects.get(name=host)
        rp = RunningPackage(timeslot=theTimeslot, settings=thePackage, 
                            area=theArea, host=theHost)
        rp.save()
        return rp.pk
