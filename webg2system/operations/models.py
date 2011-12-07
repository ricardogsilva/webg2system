from django.db import models
from systemsettings.models import Package, Source, Host

class RunningPackage(models.Model):
    timeslot = models.DateTimeField()
    source = models.ForeignKey(Source)
    package = models.ForeignKey(Package)
    host = models.ForeignKey(Host)

    def __unicode__(self):
        return '%s (%s, %s)' % (self.timeslot, self.package, self.source)

    def prepare(self):
        print('Prepare method called.')
