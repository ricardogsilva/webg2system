from piston.handler import BaseHandler
from operations.models import RunningPackage

class RunningPackageHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = RunningPackage

    def read(self, request, packId=None):

        base = RunningPackage.objects

        if packId is not None:
            result = base.get(pk=packId)
        else:
            result = base.all()
        return result
