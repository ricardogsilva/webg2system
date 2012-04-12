import os
import sys
import datetime as dt

from django.db import models
from systemsettings.models import Package, Area

from core import g2packages, rpdaemon

class RunningPackage(models.Model):
    STATUS_CHOICES = (('running', 'running'),('stopped', 'stopped'))
    timeslot = models.DateTimeField()
    settings = models.ForeignKey(Package)
    area = models.ForeignKey(Area, verbose_name='Default Area', help_text='The name '\
                             '(or regular expression) for the area.')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, 
                              default='stopped', editable=False)
    force = models.BooleanField(default=False, help_text='Should the package'\
                                ' run even if its outputs are already '\
                                'available?')
    result = models.BooleanField(default=False, editable=False)
    timestamp = models.DateTimeField(editable=False)

    def __unicode__(self):
        return unicode(self.settings)

    def save(self):
        '''
        Provide a chance to update the timestamp field.

        This method overrides Django's own save() method in order
        to update the 'timestamp' field, which is not editable and
        cannot have a default value assigned.
        '''

        self.timestamp = dt.datetime.utcnow()
        super(RunningPackage, self).save()

    def show_timeslot(self):
        return self.timeslot.strftime('%Y-%m-%d %H:%M')
    show_timeslot.short_description = 'Timeslot'

    def show_timestamp(self):
        return self.timestamp.strftime('%Y-%m-%d %H:%M')
    show_timestamp.short_description = 'Timestamp'

    def show_settings(self):
        return self.settings.package.name
    show_settings.short_description = 'Package'

    def show_area(self):
        return self.area.name
    show_area.short_description = 'Default area'

    def _initialize(self):
        '''
        Temporary method to facilitate sharing some code between
        the run() and create_package() methods.
        '''

        packClass = eval('g2packages.%s' % self.settings.codeClass.className)
        pack = packClass(self.settings, self.timeslot, self.area)
        return pack

    def create_package(self):
        '''
        Temporary method for testing package creation
        '''

        pack = self._initialize()
        return pack

    def daemonize(self):
        daemon = rpdaemon.RPDaemon(self, '/tmp/rpdaemon.pid', 'RPDaemon')
        r, w = os.pipe() # file descriptors
        pid = os.fork()
        if pid: # this is the parent process
            os.close(w)
        else: # this is the child process
            os.close(r)
            daemon._start()
            #sys.exit(0)
        print('Aqui')

    def run(self, callback=None, *args, **kwargs):
        '''
        Interfaces with the core packages, calling their public
        delete_outputs(), run_main() and clean_up() methods sequentially.
        It MUSTN'T call any other method from the core packages.

        Accepts a callback function that should be used to supply
        progress information to the client code. The callback function
        is expected to accept a variable number of inputs, as if they were
        a sequence of messages.
        Example callback function:

            def callback(*args):
                for arg in args:
                    print(arg)

        Also accepts other arguments and keyword arguments that get passed
        to the packages' 'run_main()' method. Available choices are:

            Package:
                Outra
                    - sleepSecs (int): 5
                    - sleepSteps (int): 3
                OWSPreparator 
                    - generate (bool): True
                    - update (string): None
                QuickLookGenerator
                    - tile (string): None
                MetadataGenerator
                    - generate (bool): True
                    - tile (string): None
                    - populateCSW: True
        '''

        if callback is None:
            def callback(*args):
                pass
        #try:
        self.status = 'running'
        self.result = False
        self.save()
        processSteps = 7
        callback((self.progress(1, processSteps), 
                 'Creating package for processing...'))
        pack = self._initialize()
        callback((self.progress(2, processSteps), 
                 'Looking for previously available outputs...'))
        outputsAvailable = pack.outputs_available()
        if outputsAvailable:
            if self.force:
                runPackage = True
                callback((self.progress(3, processSteps), 
                         'Deleting any previously present output files...'))
                pack.delete_outputs()
            else:
                runPackage = False
        else:
            runPackage = True
        if runPackage:
            callback((self.progress(4, processSteps), 
                     'Running main process...'))
            print('kwargs: %s' % kwargs)
            mainResult = pack.run_main(callback, *args, **kwargs)
            # Will be able to add other error codes later
            if mainResult not in (1,):
                self.result = True
            else:
                self.result = False
            callback((self.progress(5, processSteps), 'Cleaning up...'))
            cleanResult = pack.clean_up()
        else:
            callback((self.progress(6, processSteps),
                     'Outputs are already available.'))
            self.result = True
        self.status = 'stopped'
        self.save()
        callback((self.progress(7, processSteps), 'All done!'))
        #except:
        #    print('something went wrong')
        #    self.status = 'stopped'
        #    self.result = False
        #    self.save()
        return self.result

    def progress(self, currentStep, totalSteps=100):
        '''
        Return the progress, in percentage.
        '''

        return currentStep * 100 / totalSteps
