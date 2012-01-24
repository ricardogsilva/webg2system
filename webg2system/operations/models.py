from django.db import models
from systemsettings.models import Package, Area, Host

from core import g2packages

class RunningPackage(models.Model):
    STATUS_CHOICES = (('running', 'running'),('stopped', 'stopped'))
    timeslot = models.DateTimeField()
    settings = models.ForeignKey(Package)
    area = models.ForeignKey(Area, verbose_name='Default Area', help_text='The name '\
                             '(or regular expression) for the area.')
    host = models.ForeignKey(Host)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, 
                              default='stopped', editable=False)
    force = models.BooleanField(default=False, help_text='Should the package'\
                                ' run even if its outputs are already '\
                                'available?')
    result = models.BooleanField(default=False, editable=False)

    def __unicode__(self):
        #return '%s (%s, %s)' % (self.timeslot, self.settings, self.source)
        return unicode(self.settings)

    def show_timeslot(self):
        return self.timeslot.strftime('%Y-%m-%d %H:%M')
    show_timeslot.short_description = 'Timeslot'

    def show_settings(self):
        return self.settings.package.name
    show_settings.short_description = 'Package'

    def show_area(self):
        return self.area.name
    show_area.short_description = 'Default area'

    def show_host(self):
        return self.host.name
    show_host.short_description = 'Host'

    def _initialize(self):
        '''
        Temporary method to facilitate sharing some code between
        the run() and create_package() methods.
        '''

        packClass = eval('g2packages.%s' % self.settings.codeClass.className)
        pack = packClass(self.settings, self.timeslot, self.area, self.host)
        return pack

    def create_package(self):
        '''
        Temporary method for testing package creation
        '''

        pack = self._initialize()
        return pack

    # TODO
    # Daemonize this method
    def run(self, callback=None):
        '''
        Interfaces with the core packages, calling their public
        delete_outputs(), prepare(), run_main() and clean_up() 
        methods sequentially.
        It MUSTN'T call any other method from the core packages.

        Accepts a callback function that should be used to supply
        progress information to the client code.
        The callback must expect a result in the form of a two-element
        tuple.
        '''

        if callback is None:
            def callback(msg, step):
                pass
        #try:
        self.status = 'running'
        self.save()
        processSteps = 8
        callback('Creating package for processing...', 
                 self.progress(1, processSteps))
        pack = self._initialize()
        callback('Looking for previously available outputs...', 
                 self.progress(2, processSteps))
        outputsAvailable = pack.outputs_available()
        if outputsAvailable:
            if self.force:
                runPackage = True
                callback('Deleting any previously present output files...',
                         self.progress(3, processSteps))
                pack.delete_outputs()
            else:
                runPackage = False
        else:
            runPackage = True
        if runPackage:
            callback('Preparing files...', 
                     self.progress(4, processSteps))
            prepareResult = pack.prepare(callback)
            callback('Running main process...', 
                     self.progress(5, processSteps))
            mainResult = pack.run_main()
            # Will be able to add other error codes later
            if mainResult not in (1,):
                self.result = True
            callback('Cleaning up...', 
                     self.progress(6, processSteps))
            cleanResult = pack.clean_up()
        else:
            callback('Outputs are already available.', 
                     self.progress(7, processSteps))
            self.result = True
        self.status = 'stopped'
        self.save()
        callback('All done!', self.progress(8, processSteps))
        #except:
        #    print('something went wrong')
        #    self.status = 'stopped'
        #    self.result = False
        #    self.save()

    def progress(self, currentStep, totalSteps=100):
        '''
        Return the progress, in percentage.
        '''

        return currentStep * 100 / totalSteps

