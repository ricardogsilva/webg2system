from django.db import models
from systemsettings.models import Package, Source, Host

import core

class RunningPackage(models.Model):
    STATUS_CHOICES = (('running', 'running'),('stopped', 'stopped'))
    timeslot = models.DateTimeField()
    settings = models.ForeignKey(Package)
    source = models.ForeignKey(Source)
    host = models.ForeignKey(Host)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, 
                              default='stopped')
    result = models.BooleanField(default=False)

    def __unicode__(self):
        #return '%s (%s, %s)' % (self.timeslot, self.settings, self.source)
        return unicode(self.settings)

    def show_timeslot(self):
        return self.timeslot.strftime('%Y-%m-%d %H:%M')
    show_timeslot.short_description = 'Timeslot'

    def show_settings(self):
        return self.settings.package.name
    show_settings.short_description = 'Package'

    def show_source(self):
        return self.source.name
    show_source.short_description = 'Source'

    def show_host(self):
        return self.host.name
    show_host.short_description = 'Host'

    def _initialize(self):
        '''
        Temporary method to facilitate sharing some code between
        the run() and create_package() methods.
        '''

        packClass = eval('core.%s' % self.settings.codeClass.className)
        pack = packClass(self.settings, self.timeslot, self.source, self.host)
        return pack

    def create_package(self):
        '''
        Temporary method for testing package creation
        '''

        pack = self._initialize()
        return pack

    def run(self, callback):
        '''
        Interfaces with the core packages, calling their public
        prepare(), run_main() and clean_up() methods sequentially.
        It MUSTN'T call any other method from the core packages.

        Accepts a callback function that should be used to supply
        progress information to the client code.
        The callback must expect a result in the form of a two-element
        tuple.
        '''

        try:
            self.status = 'running'
            self.save()
            callback('Creating package for processing...', 1)
            pack = self._initialize()
            callback('Preparing files...', 2)
            prepareResult = pack.prepare(callback)
            callback('Running main process...', 3)
            mainResult = pack.run_main()
            callback('Cleaning up...', 4)
            cleanResult = pack.clean_up()
            self.status = 'stopped'
            self.save()
            callback('All done!', 5)
        except:
            self.status = 'stopped'
            self.result = False
            self.save()

