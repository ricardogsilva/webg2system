import os
import pexpect

from django.db import models
from systemsettings.models import Host
from operations.core.g2hosts import HostFactory

import pyparsing as pp

class SMSStatus(models.Model):
    status = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'SMS status'
        verbose_name_plural = 'SMS statuses'

    def __unicode__(self):
        return self.status

class Root(models.Model):
    _name = models.CharField(max_length=100)
    status = models.ForeignKey(SMSStatus)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name


class Suite(Root):
    families = models.ManyToManyField('Family')

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @staticmethod
    def from_def(def_file):
        fh = open(def_file, 'r')
        grammar = Suite.suite_grammar()
        p = grammar.parseString(fh.read())
        s = Suite(name=p[1], status=SMSStatus.objects.get(status='unknown'))
        s.save()
        var_list = [i for i in p if i[0] == 'edit']
        fam_list = [i for i in p if i[0] == 'family']
        s._parse_variables_def(var_list)
        s._parse_families_def(fam_list)
        s.save()
        return p, s

    @staticmethod
    def suite_grammar():
        quote = pp.Word('"\'', exact=1).suppress()
        colon = pp.Literal(':').suppress()
        l_paren = pp.Literal('(').suppress()
        r_paren = pp.Literal(')').suppress()
        sms_node_path = pp.Word('./_' + pp.alphanums)
        identifier = pp.Word(pp.alphas, pp.alphanums + '_')
        var_value = pp.Word(pp.alphanums) | (quote + \
                pp.Combine(pp.OneOrMore(pp.Word(pp.alphanums)), adjacent=False, 
                           joinString=' ') + quote)
        sms_var = pp.Group(pp.Keyword('edit') + identifier + var_value)
        sms_label = pp.Group(pp.Keyword('label') + identifier + var_value)
        sms_meter = pp.Group(pp.Keyword('meter') + identifier + pp.Word(pp.nums) * 3)
        sms_limit = pp.Group(pp.Keyword('limit') + identifier + pp.Word(pp.nums))
        sms_in_limit = pp.Group(pp.Keyword('inlimit') + sms_node_path + colon + identifier)
        sms_trigger = pp.Group(pp.Keyword('trigger') + pp.restOfLine)
        sms_repeat = pp.Group(pp.Keyword('repeat') + identifier + pp.Word(pp.nums) * 2)
        sms_task = pp.Group(
            pp.Keyword('task') + \
            identifier + \
            pp.ZeroOrMore(
                sms_trigger ^ sms_in_limit ^ sms_label ^ sms_meter ^ sms_var
            )
        ) + pp.Optional(pp.Keyword('endtask').suppress())
        sms_family = pp.Forward()
        sms_family << pp.Group(
            pp.Keyword('family') + identifier + pp.ZeroOrMore(
                sms_in_limit ^ sms_limit ^ sms_trigger ^ sms_var ^ sms_task ^ sms_family ^ sms_repeat
            )
        ) + pp.Keyword('endfamily').suppress()
        sms_suite = pp.Keyword('suite') + identifier + \
                    pp.ZeroOrMore(sms_var ^ sms_family) + \
                    pp.Keyword('endsuite').suppress()
        return sms_suite

    def _parse_variables_def(self, var_list):
        for i in var_list:
            v = SuiteVariable(suite=self, name=i[1], value=i[2])
            v.save()

    def _parse_families_def(self, fam_list):
        for i in fam_list:
            #f = Family(name=i[1], status=status)
            f = Family.from_def(i)
            f.save()
            self.families.add(f)
            


class Node(Root):
    _path = models.CharField(max_length=255, editable=False)
    _family = models.ForeignKey(
        'Family', null=True, blank=True,
        related_name='%(app_label)s_%(class)s_families', 
    )

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        self._path = ''.join(self.path.rpartition('/')[0:2] + (name,))

    @property
    def family(self):
        return self._family

    @family.setter
    def family(self, family):
        self._family = family
        if family is not None:
            self._path = '/'.join((family.path, self.name))
        else:
            self._path = self._name

    def save(self):
        self.name = self.name
        self.family = self.family
        super(Node, self).save()

    class Meta:
        abstract = True

class Family(Node):

    class Meta:
        verbose_name_plural = 'Families'

    @staticmethod
    def from_def(parse_obj):
        status = SMSStatus.objects.get(status='unknown')
        f = Family(name=parse_obj[1], status=status)
        f.save()
        var_list = [i for i in parse_obj if i[0] == 'edit']
        fam_list = [i for i in parse_obj if i[0] == 'family']
        task_list = [i for i in parse_obj if i[0] == 'task']
        f._parse_variables_def(var_list)
        f._parse_families_def(fam_list)
        f.save()
        return f

    def _parse_variables_def(self, var_list):
        for i in var_list:
            v = FamilyVariable(family=self, name=i[1], value=i[2])
            v.save()

    def _parse_families_def(self, fam_list):
        for i in fam_list:
            f = Family.from_def(i)
            f.save()
            self.smssettings_family_families.add(f)

    def _parse_tasks_def(self, task_list):
        for i in task_list:
            t = Task.from_def(i)
            t.save()
            self.task_set.add(t)
            

class Task(Node):
    family = models.ForeignKey(Family, null=True, blank=True)

    @staticmethod
    def from_def(parse_obj):
        status = SMSStatus.objects.get(status='unknown')
        t = Task(name=parse_obj[1], status=status)
        t.save()
        var_list = [i for i in parse_obj if i[0] == 'edit']
        t._parse_variables_def(var_list)
        t.save()
        return t


class Variable(models.Model):
    name = models.CharField(max_length=20)
    value = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

class SuiteVariable(Variable):
    suite = models.ForeignKey(Suite)

class FamilyVariable(Variable):
    family = models.ForeignKey(Family)

class TaskVariable(Variable):
    task = models.ForeignKey(Task)

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
