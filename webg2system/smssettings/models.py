import os
import pexpect

from django.db import models
from systemsettings.models import Host
from operations.core.g2hosts import HostFactory
#from operations.core.cdpproxy import CDPProxy

class SMSServer(models.Model):
    alias = models.CharField(max_length=100)
    rpc_num = models.IntegerField()
    host_settings = models.ForeignKey(Host)

    def init_server(self):
        if not hasattr(self, 'connection'):
            self.CDP_PROMPT = 'CDP>'
            self.CDP_COMMANDS = {
                    'login' : 'login %s %s %s',
                    'terminate' : 'terminate -y',
                    'suites' : 'suites',
            }
            self.host = HostFactory().create_host(self.host_settings)
            self.base_path = os.path.join(self.host.dataPath, 'SMS_SERVERS', self.alias)
            self.server_dir = os.path.join(self.base_path, 'SERVER_START_DIR')
            self.suites_dir = os.path.join(self.base_path, 'SUITES')
            self._create_directories()
            self.connection = self._connect_to_cdp()
            server_started = self._start_server()
            if server_started == 0:
                login = self.login()
            else:
                login = 1
            return login

    #FIXME - finish this method
    def list_suites(self):
        '''Return a list with the names of the suites in the server.'''

        out = self._get_cdp_result(self.CDP_COMMANDS['suites'])
        return out

    #def play_suite(self, suite_obj, build_sms_files=True, substitute=False):
    #    '''
    #    Play a suite.

    #    Inputs:

    #        suite_obj - Either the path to the sms definition file defining 
    #            the suite or a Suite instance.

    #        build_sms_files - A boolean indicating if the internal sms
    #            directories and symlinks are to be created. Defaults to True.

    #        substitute - A boolean indicating if the definition file is to be
    #            played even if there is already a suite with the same name
    #            in use in the server. Defaults to False.
    #    '''

    #    if isinstance(suite_obj, Suite):
    #        the_suite = suite_obj
    #    else:
    #        the_suite = Suite(suite_obj)
    #    result = self._play_suite_obj(the_suite)
    #    if result == 0:
    #        if build_sms_files:
    #            built = self._build_sms_files()

    #def _build_sms_files(self, suite_obj):
    #    paths = {'dirs' : [], 'files' : []}
    #    for


    #def _play_suite_obj(self, suite_obj):
    #    '''
    #    Paly a suite in the server from a Suite object.
    #    '''

    #    raise NotImplementedError

    #def cancel_suite(self, suite_name):



    def __unicode__(self):
        return '%s:%s_%s' % (self.alias, self.host_settings.name, self.rpc_num)

    def _create_directories(self):
        for d in (self.server_dir, self.suites_dir):
            self.host.make_dir(d)

    def _delete_directories(self):
        self.init_server()
        for d in (self.server_dir, self.suites_dir):
            self.host.remove_dir(d)

    def login(self):
        out = self._get_cdp_result(self.CDP_COMMANDS['login'] % (self.host.host, 'ricardo', 'pass'))
        result = 0
        for line in out:
            if 'ERR' in line:
                result = 1
        return result

    def _get_cdp_result(self, command):
        self.connection.sendline(command)
        self.connection.expect(self.CDP_PROMPT)
        result = self.connection.before.split('\r\n')
        return result

    def _connect_to_cdp(self):
        os.environ['SMS_PROG'] = str(self.rpc_num)
        c = pexpect.spawn('cdp')
        c.expect(self.CDP_PROMPT)
        return c

    def _start_server(self):
        retcode = self._ping_server()
        if retcode == 0:
            print('the server is already running')
            result = 0
        else:
            print('starting the sms server...')
            os.environ['SMS_PROG'] = str(self.rpc_num)
            result = self.host.start_sms_server(self.server_dir)
        return result

    def _ping_server(self):
        os.environ['SMS_PROG'] = str(self.rpc_num)
        stdout, stderr, retcode = self.host.run_program('smsping %s' % \
                                                        self.host.host)
        return retcode

    def _terminate_server(self):
        '''
        Terminate the SMS server.

        This completely kills the SMS server instance.
        '''

        result = self._get_cdp_result(self.CDP_COMMANDS['terminate'])
        del self.connection
