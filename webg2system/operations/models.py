import os
import sys
import datetime as dt
import logging
import traceback

from django.db import models
from systemsettings.models import Package, Area

from cloghandler import ConcurrentRotatingFileHandler

from core import g2packages, g2hosts

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

    class Meta:
        ordering = ['-id']

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

    def _initialize(self, logger, callback):
        '''
        Temporary method to facilitate sharing some code between
        the run() and create_package() methods.
        '''

        packClass = eval('g2packages.%s' % self.settings.codeClass.className)
        pack = packClass(self.settings, self.timeslot, self.area, logger=logger)
        return pack

    def create_package(self, log_level=logging.DEBUG, callback=None):
        '''
        Temporary method for testing package creation
        '''

        logger = self._get_logger(log_level)
        pack = self._initialize(logger, callback)
        return pack

    def _get_logger(self, log_level):
        logger = logging.getLogger(__name__)
        hf = g2hosts.HostFactory(log_level)
        host = hf.create_host()
        formatter = logging.Formatter('%(levelname)s %(asctime)s %(module)s ' \
                                      '%(process)s %(message)s')
        log_dir = host.make_dir(self.timeslot.strftime('LOGS/%Y/%m/%d/%H'), relativeTo='data')
        log_file = os.path.join(log_dir, '%s_%s.log' % \
                   (self.settings.name, 
                    self.timeslot.strftime('%Y%m%d%H%M')))
        handler = ConcurrentRotatingFileHandler(log_file, 'a', 512*1024, 3)
        handler.setFormatter(formatter)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        existing_handlers = logger.handlers
        for hdlr in existing_handlers:
            logger.removeHandler(hdlr)
        logger.addHandler(handler)
        logger.addHandler(console_handler)
        logger.setLevel(log_level)
        # reassing the host's logger to ensure it gets the created handler
        # this is because the HostFactory class has a caching mechanism
        # and it will not create new hosts
        host.logger = logger
        for host_name, conn_dict in host.connections.iteritems():
            for proxy_obj in conn_dict.values():
                proxy_obj.host = host
        return logger

    def run(self, callback=None, log_level=logging.DEBUG, *args, **kwargs):
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
                    - move_to_webserver (bool): True
                MetadataGenerator
                    - generate (bool): True
                    - tile (string): None
                    - populateCSW: True
                    - generate_series: False
        '''

        logger = self._get_logger(log_level)
        logger.info('--- Starting execution')
        if callback is None:
            def callback(*args):
                pass
        def log_callbacks(*args):
            callback(*args)
            for arg in args:
                logger.info(arg)
        try:
            self.status = 'running'
            self.result = False
            self.save()
            processSteps = 7
            log_callbacks((self.progress(1, processSteps), 
                          'Creating package for processing...'))
            pack = self._initialize(logger, callback)
            log_callbacks((self.progress(2, processSteps), 
                     'Looking for previously available outputs...'))
            outputsAvailable = pack.outputs_available()
            if outputsAvailable:
                if self.force:
                    runPackage = True
                    log_callbacks((self.progress(3, processSteps), 
                                  'Deleting any previously present output ' \
                                  'files...'))
                    pack.delete_outputs()
                else:
                    special_classes = [
                        g2packages.OWSPreparator,
                        g2packages.QuickLookGenerator,
                        g2packages.MetadataGenerator,
                    ]
                    runPackage = False
                    for cls in special_classes:
                        if isinstance(pack, cls):
                            runPackage = True
            else:
                runPackage = True
            if runPackage:
                log_callbacks((self.progress(4, processSteps), 
                              'Running main process...'))
                mainResult = pack.run_main(callback, *args, **kwargs)
                # Will be able to add other error codes later
                if mainResult:
                    self.result = True
                elif not mainResult or mainResult in (1,):
                    self.result = False
            else:
                log_callbacks((self.progress(6, processSteps),
                              'Outputs are already available.'))
                self.result = True
        except Exception as e:
            log_callbacks('something went wrong. This is the traceback:')
            for line in traceback.format_exception(*sys.exc_info()):
                log_callbacks(line)
            self.result = False
        finally:
            log_callbacks((self.progress(5, processSteps), 
                          'Cleaning up...'))
            cleanResult = pack.clean_up()
            del pack
            self.status = 'stopped'
            self.save()
            log_callbacks((self.progress(7, processSteps), 'All done!'))
            logger.info('--- Finished execution')
        return self.result

    def progress(self, currentStep, totalSteps=100):
        '''
        Return the progress, in percentage.
        '''

        return currentStep * 100 / totalSteps
