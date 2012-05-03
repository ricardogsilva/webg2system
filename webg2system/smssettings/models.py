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
