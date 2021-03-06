import os
import sys
import subprocess
import datetime as dt
import logging
import logging.handlers
import traceback

from django.db import models
import django.contrib.auth.models as am
from systemsettings.models import Package, Area

from core import g2packages, g2hosts

class RunningPackage(models.Model):
    STATUS_CHOICES = (('running', 'running'),('stopped', 'stopped'))
    timeslot = models.DateTimeField()

    settings = models.CharField(max_length=255)
    area = models.CharField(max_length=255, verbose_name='Default area',
                            help_text='The name (or regexp) for the area.')


    status = models.CharField(max_length=50, choices=STATUS_CHOICES, 
                              default='stopped', editable=False)
    force = models.BooleanField(default=False, help_text='Should the package'\
                                ' run even if its outputs are already '\
                                'available?')
    result = models.BooleanField(default=False, editable=False)
    timestamp = models.DateTimeField(editable=False)
    _loggers = dict()

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

    def _initialize(self, logger, callback):
        '''
        Temporary method to facilitate sharing some code between
        the run() and create_package() methods.
        '''

        try:
            settings_obj = Package.objects.get(name=self.settings)
            area_obj = Area.objects.get(name=self.area)
            packClass = eval('g2packages.%s' % settings_obj.code_class.className)
            pack = packClass(settings_obj, self.timeslot, area_obj, logger=logger)
        except (Package.DoesNotExist, Area.DoesNotExist):
            logger.error('Some of the input arguments are invalid: ' \
                         'package or area inexistent.')
            pack = None
        return pack

    def _get_logger(self, log_level):
        if self._loggers.get(__name__) is None:
            logger = logging.getLogger(__name__)
            hf = g2hosts.HostFactory(log_level)
            host = hf.create_host()
            formatter = logging.Formatter('%(levelname)s %(asctime)s %(module)s ' \
                                          '%(process)s %(message)s')
            short_formatter = logging.Formatter('%(levelname)s %(asctime)s ' \
                                                '%(message)s')
            log_dir = host.make_dir(self.timeslot.strftime('LOGS/%Y/%m/%d/%H'),
                                    relativeTo='data')
            log_file = os.path.join(log_dir, '%s_%s.log' % \
                       (self.settings, 
                        self.timeslot.strftime('%Y%m%d%H%M')))
            file_handler = logging.handlers.WatchedFileHandler(log_file, 'a', 
                                                               'UTF-8')
            file_handler.setFormatter(short_formatter)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            mail_host = ('perseus.ipma.pt', 587)
            from_addr = 'ricardo.silva@ipma.pt'
            subject = '%s - g2system error' % (host.name)
            mail_destinations = [u.email for u in am.User.objects.filter(is_staff=True)]
            mail_handler = logging.handlers.SMTPHandler(mail_host, from_addr, 
                                                        mail_destinations, 
                                                        subject,
                                                        credentials=(from_addr,'geo2123'),
                                                        secure=())
            mail_handler.setLevel(logging.ERROR)
            mail_handler.setFormatter(formatter)
            existing_handlers = logger.handlers
            for hdlr in existing_handlers:
                logger.removeHandler(hdlr)
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            logger.addHandler(mail_handler)
            logger.setLevel(log_level)
            # reassing the host's logger to ensure it gets the created handler
            # this is because the HostFactory class has a caching mechanism
            # and it will not create new hosts
            host.logger = logger
            for host_name, conn_dict in host.connections.iteritems():
                for proxy_obj in conn_dict.values():
                    proxy_obj.host = host
            self._loggers[__name__] = logger
        return self._loggers[__name__]

    def run(self, callback=None, log_level=logging.DEBUG, clean_up=True, 
            *args, **kwargs):
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
                    - archive(bool): False
                    - delete_local(bool): True
                MetadataGenerator
                    - generate (bool): True
                    - tile (string): None
                    - populateCSW: True
                    - generate_series: False
                SWIMetadataHandler
                    - send_to_csw: True
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
            if outputsAvailable and len(pack.outputs) > 0:
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
                        g2packages.SWIMetadataHandler,
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
            if clean_up:
                log_callbacks((self.progress(5, processSteps), 
                              'Cleaning up...'))
                cleanResult = pack.clean_up()
            del pack
            log_callbacks((self.progress(6, processSteps),
                          'Deleting hosts...'))
            g2hosts.HostFactory.clear_all_hosts()
            self.status = 'stopped'
            self.save()
            log_callbacks((self.progress(7, processSteps), 'All done!'))
            logger.info('--- Finished execution')
            open_files = self.get_open_fds()
            logger.warning('Open files: %i' % open_files)
        return self.result

    def progress(self, currentStep, totalSteps=100):
        '''
        Return the progress, in percentage.
        '''

        return currentStep * 100 / totalSteps

    def get_open_fds(self):
        pid = os.getpid()
        procs = subprocess.check_output(['lsof', '-w', '-Ff', '-p', str(pid)])
        nprocs = len(
            filter(
                lambda s: s and s[0] == 'f' and s[1:].isdigit(), procs.split('\n')
            )
        )
        return nprocs
