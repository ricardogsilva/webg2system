import os
import pexpect
import re
import datetime as dt

from django.db import models
from systemsettings.models import Host
from operations.core.g2hosts import HostFactory

import pyparsing as pp

class Suite(models.Model):
    name = models.CharField(max_length=255, unique=True)
    sms_representation = models.TextField()

    def get_suite_obj(self):
        '''
        Return a SuiteObj instance from this object's sms representation.
        '''

        s = SuiteObj.from_sms_definition(self.sms_representation)
        return s


    def import_suite_obj(self, suite_obj):
        '''
        Import the input suite_obj and update this object's sms representation.
        '''

        self.sms_representation = suite_obj.cdp_definition()


class SMSGenericNode(object):
    sms_type = ''
    _name = ''
    _path = ''
    variables = dict()
    defstatus = 'queued'
    status = 'unknown'
    _parent = None

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        oldPath = self.path.rpartition('/')
        self._path = '/'.join((oldPath[0], self.name))

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if self.sms_type != 'suite':
            self._parent = parent
        else:
            raise Exception
        if parent is None:
            self._path = self.name
        else:
            if parent.sms_type == 'suite':
                self._path = parent.path + self.name
            else:
                self._path = '/'.join((self.parent.path, self.name))

    def __init__(self, name, variables=None, defstatus=None):
        self.name = name
        if variables is None:
            self.variables = dict()
        else:
            self.variables = variables
        if defstatus is not None:
            self.defstatus = defstatus

    def __repr__(self):
        return '%s(%s)' % (self.sms_type, self.name)

    def cdp_definition(self, indent_order=0):
        output = '%s%s %s\n' % ('\t'*indent_order, self.sms_type, self.name)
        output += self._start_cdp_definition(indent_order)
        output += self._specific_cdp_definition(indent_order+1)
        output += self._end_cdp_definition(indent_order)
        return output

    def _start_cdp_definition(self, indent_order=0):
        output = ''
        if self.defstatus != 'queued':
            output += '%sdefstatus %s\n' % ('\t' * (indent_order + 1), 
                                            self.defstatus)
        for k, v in self.variables.iteritems():
            output += '%sedit %s "%s"\n' % ('\t'*(indent_order+1), k, v)
        return output

    def _end_cdp_definition(self, indent_order=0):
        output = '%send%s\n' % ('\t'*indent_order, self.sms_type)
        return output

    def _specific_cdp_definition(self, indent_order=0):
        return ''

    def get_suite(self):
        if self.parent is None:
            if self.sms_type == 'suite':
                result = self
            else:
                result = None
        elif self.parent.sms_type == 'suite':
            result = self.parent
        else:
            result = self.parent.get_suite()
        return result

    def get_node(self, path):
        '''
        Return the node with the defined path.

        Paths can be given in an absolute or relative way.

        Inputs:

            path - a path to another node on the suite
        '''

        if path.startswith('/'):
            base_node = self.get_suite()
            node = base_node.get_node(path[1:])
        else:
            base_node = self.parent
            if base_node is None:
                base_node = self.get_suite()
            path_list = path.split('/')
            rel_path_list = []
            for token in path_list:
                if token != '':
                    if token == '..':
                        base_node = base_node.parent
                    else:
                        rel_path_list.append(token)
            rel_path = '/'.join(rel_path_list)
            node = None
            if base_node is not None:
                node = base_node._node_from_path(rel_path)
        return node


class SuiteObj(SMSGenericNode):
    sms_type = 'suite'
    _families = []
    _limits = []

    @property
    def families(self):
        return self._families

    @property
    def limits(self):
        return self._limits

    @staticmethod
    def from_sms_definition(def_string):
        '''Return a new SuiteObj by parsing the input def_string.'''

        grammar = SuiteObj.suite_grammar()
        p = grammar.parseString(def_string)
        the_variables = dict()
        the_defstatus = 'queued'
        the_clock = 'hybrid'
        the_families = []
        the_limits = []
        for item in p[2:]:
            the_type = item[0]
            if the_type == 'edit':
                the_variables[item[1]] = item[2]
            elif the_type == 'defstatus':
                the_defstatus = item[1]
            elif the_type == 'clock':
                the_clock = item[1]
            elif the_type == 'limit':
                the_limits.append(Limit(item[1], item[2]))
            elif the_type == 'family':
                the_families.append(FamilyObj.from_parse_obj(item))
        s = SuiteObj(p[1], the_variables, the_defstatus, the_families, 
                     the_limits, the_clock)
        for f in s.families:
            f._parse_triggers()
            f._parse_in_limits()
        return s, p

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
        sms_comment = pp.Word('#') + pp.Optional(pp.restOfLine)
        sms_var = pp.Group(pp.Keyword('edit') + identifier + var_value)
        sms_label = pp.Group(pp.Keyword('label') + identifier + var_value)
        sms_meter = pp.Group(pp.Keyword('meter') + identifier + pp.Word(pp.nums) * 3)
        sms_limit = pp.Group(pp.Keyword('limit') + identifier + pp.Word(pp.nums))
        sms_in_limit = pp.Group(pp.Keyword('inlimit') + sms_node_path + colon + identifier)
        sms_trigger = pp.Group(pp.Keyword('trigger') + pp.restOfLine)
        sms_repeat = pp.Group(pp.Keyword('repeat') + pp.Keyword('date') + identifier + pp.Word(pp.nums) * 2)
        sms_defstatus = pp.Group(pp.Keyword('defstatus') + (pp.Keyword('suspended') ^ \
                        pp.Keyword('complete') ^ pp.Keyword('queued')))
        sms_clock = pp.Group(pp.Keyword('clock') + pp.Keyword('hybrid') + pp.Word(pp.nums))
        sms_task = pp.Group(
            pp.Keyword('task') + \
            identifier + \
            pp.ZeroOrMore(
                sms_defstatus ^ sms_trigger ^ sms_in_limit ^ sms_label ^ sms_meter ^ sms_var
            )
        ) + pp.Optional(pp.Keyword('endtask').suppress())
        sms_family = pp.Forward()
        sms_family << pp.Group(
            pp.Keyword('family') + identifier + pp.ZeroOrMore(
                sms_defstatus ^ sms_in_limit ^ sms_limit ^ sms_trigger ^ sms_var ^ sms_task ^ sms_family ^ sms_repeat
            )
        ) + pp.Keyword('endfamily').suppress()
        sms_suite = pp.Keyword('suite') + identifier + \
                    pp.ZeroOrMore(sms_clock ^ sms_limit ^ sms_defstatus ^ sms_var ^ sms_family) + \
                    pp.Keyword('endsuite').suppress()
        sms_suite.ignore(sms_comment)
        return sms_suite

    def __init__(self, name, variables=None, defstatus=None, families=None, 
                 limits=None, clock=None):
        super(SuiteObj, self).__init__(name, variables, defstatus)
        self._path = '/'
        self.clock = clock
        self._families = []
        self._limits = []
        if families is not None:
            for f in families:
                self.add_family(f)
        if limits is not None:
            for li in limits:
                self.add_limit(li)

    def add_family(self, f):
        self._families.append(f)
        f.parent = self

    def remove_family(self, f):
        self._families.remove(f)
        f.parent = None

    def add_limit(self, li):
        self._limits.append(li)
        li.parent = self

    def remove_limit(self, li):
        self._limits.remove(li)
        li.parent = None

    def _start_cdp_definition(self, indent_order=0):
        output = '%sclock %s\n' % ('\t' * (indent_order + 1), self.clock)
        output += super(SuiteObj, self)._start_cdp_definition(indent_order)
        return output

    def _specific_cdp_definition(self, indent_order=0):
        output = ''
        for li in self.limits:
            output += li.cdp_definition(indent_order)
        for n in self.families:
            output += n.cdp_definition(indent_order)
        return output

    def _node_from_path(self, path):
        if path == '' or path == '.':
            node = self
        else:
            path_list = path.split('/')
            node_list = self.families
            possible_node = None
            for n in node_list:
                if n.name == path_list[0]:
                    new_path = '/'.join(path_list[1:])
                    possible_node = n._node_from_path(new_path)
            node = possible_node
        return node


class SMSTriggerNode(SMSGenericNode):
    trigger = ''
    in_limits = []

    def __init__(self, name, variables=None, defstatus=None, trigger=None, 
                 in_limits=None):
        super(SMSTriggerNode, self).__init__(name, variables, defstatus)
        if trigger is not None:
            self.trigger = trigger
        if in_limits is not None:
            self.in_limits = in_limits

    def _parse_trigger(self):
        if isinstance(self.trigger, str):
            new_exp = ''
            nodes = []
            path_obj = re.compile(r'(\(*)([\w\d./=]*)(\)*)')
            for tok in self.trigger.split():
                re_obj = path_obj.search(tok)
                for i in re_obj.groups():
                    if i == '':
                        pass
                    elif ('(' in i) or (')' in i):
                        new_exp += i
                    elif i in ('complete', 'unknown'):
                        new_exp += ' "%s" ' % i
                    elif i in ('AND', 'OR'):
                        new_exp += ' %s ' % i.lower()
                    elif i in ('==',):
                        new_exp += ' %s ' % i
                    else:
                        new_exp += ' "%s" '
                        nodes.append(self.get_node(i))
            self.trigger = new_exp, nodes

    def _parse_in_limits(self):
        new_inlimits = []
        for item in self.in_limits:
            #print('item: %s' % item)
            if isinstance(item, tuple):
                node = self.get_suite().get_node(item[0])
                lim_name = item[1]
                for lim in node.limits:
                    if lim_name == lim.name:
                        lim.members.append(self)
                        new_inlimits.append(lim)
            else:
                new_inlimits.append(item)
        self.in_limits = new_inlimits

    def evaluate_trigger(self):
        exp, nodes = self.trigger
        if exp == '':
            result = True
        else:
            result = eval(exp % tuple([n.status for n in nodes]))
        return result

    def _specific_cdp_definition(self, indent_order=0):
        output = ''
        for in_lim in self.in_limits:
            output += '%sinlimit %s\n' % ('\t' * indent_order, in_lim.path)
        trig_text, trig_nodes = self.trigger
        if trig_text != '':
            trigger = trig_text % tuple([t.path for t in trig_nodes])
            output += '%strigger %s\n' % ('\t' * indent_order, trigger)
        return output


class FamilyObj(SMSTriggerNode):
    sms_type = 'family'
    repeat = None
    _families = []
    _tasks = []
    _limits = []

    @property
    def families(self):
        return self._families

    @property
    def tasks(self):
        return self._tasks

    @property
    def limits(self):
        return self._limits

    @staticmethod
    def from_parse_obj(parse_obj):
        name = parse_obj[1]
        the_variables = dict()
        the_defstatus = 'queued'
        the_trigger = ''
        the_families = []
        the_tasks = []
        the_limits = []
        the_in_limits = []
        the_repeat = None
        for item in parse_obj[2:]:
            the_type = item[0]
            if the_type == 'repeat':
                #the_repeat = ' '.join([i for i in item[2:]]) # for now the repeat is just a string
                the_repeat = RepeatFactory.create(item)
            elif the_type == 'edit':
                the_variables[item[1]] = item[2]
            elif the_type == 'defstatus':
                the_defstatus = item[1]
            elif the_type == 'trigger':
                the_trigger = item[1]
            elif the_type == 'family':
                f = FamilyObj.from_parse_obj(item)
                the_families.append(f)
            elif the_type == 'task':
                t = TaskObj.from_parse_obj(item)
                the_tasks.append(t)
            elif the_type == 'limit':
                the_limits.append(Limit(item[1], int(item[2])))
            elif the_type == 'inlimit':
                the_in_limits.append((item[1], item[2]))
        f = FamilyObj(name=name, variables=the_variables, 
                      defstatus=the_defstatus, trigger=the_trigger,
                      repeat=the_repeat, families=the_families,
                      tasks=the_tasks, limits=the_limits, 
                      in_limits=the_in_limits)
        return f

    def __init__(self, name, variables=None, defstatus=None, trigger=None,
                 in_limits=None, repeat=None, families=None, tasks=None, 
                 limits=None):
        super(FamilyObj, self).__init__(name, variables, defstatus, trigger,
                                        in_limits)
        self._families = []
        self._tasks = []
        self._limits = []
        if families is not None:
            for f in families:
                self.add_family(f)
        if tasks is not None:
            for t in tasks:
                self.add_task(t)
        if limits is not None:
            for li in limits:
                self.add_limit(li)
        if repeat is not None:
            self.repeat = repeat

    def _parse_triggers(self):
        self._parse_trigger()
        for t in self.tasks:
            t._parse_trigger()
        for f in self.families:
            f._parse_triggers()

    def _parse_in_limits(self):
        super(FamilyObj, self)._parse_in_limits()
        for t in self.tasks:
            t._parse_in_limits()
        for f in self.families:
            f._parse_in_limits()

    def add_family(self, f):
        self._families.append(f)
        f.parent = self

    def remove_family(self, f):
        self._families.remove(f)
        f.parent = None

    def add_task(self, t):
        self._tasks.append(t)
        t.parent = self

    def remove_task(self, t):
        self._tasks.remove(t)
        t.parent = None

    def add_limit(self, li):
        self._limits.append(li)
        li.parent = self

    def remove_limit(self, li):
        self._limits.remove(li)
        li.parent = None

    def _node_from_path(self, path):
        if path == '' or path == '.':
            node = self
        else:
            path_list = path.split('/')
            node_list = self.tasks + self.families
            possible_node = None
            for n in node_list:
                if n.name == path_list[0]:
                    new_path = '/'.join(path_list[1:])
                    possible_node = n._node_from_path(new_path)
            node = possible_node
        return node

    def _start_cdp_definition(self, indent_order=0):
        output = ''
        if self.repeat is not None:
            output += self.repeat.cdp_definition(indent_order + 1)
        output += super(FamilyObj, self)._start_cdp_definition(indent_order)
        return output

    def _specific_cdp_definition(self, indent_order=0):
        output = super(FamilyObj, self)._specific_cdp_definition(indent_order)
        for li in self.limits:
            output += li.cdp_definition(indent_order)
        for n in self.families:
            output += n.cdp_definition(indent_order)
        for t in self.tasks:
            output += t.cdp_definition(indent_order)
        return output


class TaskObj(SMSTriggerNode):
    sms_type = 'task'

    def __init__(self, name, variables=None, defstatus=None, trigger=None,
                 in_limits=None):
        super(TaskObj, self).__init__(name, variables, defstatus, trigger,
                                      in_limits)

    @staticmethod
    def from_parse_obj(parse_obj):
        name = parse_obj[1]
        the_variables = dict()
        the_trigger = ''
        the_defstatus = 'queued'
        the_in_limits = []
        for item in parse_obj[2:]:
            the_type = item[0]
            if the_type == 'edit':
                the_variables[item[1]] = item[2]
            elif the_type == 'trigger':
                the_trigger = item[1]
            elif the_type == 'defstatus':
                the_defstatus = item[1]
            elif the_type == 'inlimit':
                the_in_limits.append((item[1], item[2]))
        t = TaskObj(name= name, variables=the_variables, 
                    defstatus=the_defstatus, trigger=the_trigger, 
                    in_limits=the_in_limits)
        return t

    def _node_from_path(self, path):
        node = None
        if path == self.path or path == '':
            node = self
        return node


class Limit(object):
    sms_type = 'limit'
    name = ''
    num_tasks = 0
    members = []
    parent = None

    @property
    def path(self):
        return ':'.join((self.parent.path, self.name))

    def __init__(self, name, num_tasks, parent=None, members=None):
        self.name = name
        self.num_tasks = num_tasks
        if parent is not None:
            self.parent = parent
        if members is None:
            self.members = []
        else:
            self.members = members

    def __repr__(self):
        return '%s(%s)' % (self.sms_type, self.name)

    def cdp_definition(self, indent_order=0):
        output = '%slimit %s %s\n' % ('\t' * (indent_order), 
                                      self.name, self.num_tasks)
        return output


class RepeatFactory(object):

    @staticmethod
    def create(parse_obj):
        r = None
        if parse_obj[1] == 'date':
            if len(parse_obj) <= 5:
                delta = 0
            else:
                delta = parse_obj[5]
            r = DateRepeat(name=parse_obj[2], start_ymd=parse_obj[3], 
                           end_ymd=parse_obj[4], delta=delta)
        return r

class GenericRepeat(object):
    sms_type = 'repeat'
    name = ''

    def __init__(self, name=None):
        if name is not None:
            self.name = name

    def __repr__(self):
        return '%s(%s)' % (self.sms_type, self.name)


class DateRepeat(GenericRepeat):

    def __init__(self, name, start_ymd, end_ymd, delta=None):
        super(DateRepeat, self).__init__(name)
        self.start_ymd = dt.date(int(start_ymd[0:4]), 
                                 int(start_ymd[4:6]), 
                                 int(start_ymd[6:8]))
        self.end_ymd = dt.date(int(end_ymd[0:4]), 
                               int(end_ymd[4:6]), 
                               int(end_ymd[6:8]))
        if delta is None:
            delta = 0
        self.delta = dt.timedelta(days=delta)

    def cdp_definition(self, indent_order=0):
        output = '%srepeat date %s %s %s %s\n' % \
                ('\t' * (indent_order), 
                 self.name, 
                 self.start_ymd.strftime('%Y%m%d'),
                 self.end_ymd.strftime('%Y%m%d'),
                 self.delta.days)
        return output


# TODO
# - Implement methods to retrieve a node given an absolute or
#   a relative path
#class SMSStatus(models.Model):
#    status = models.CharField(max_length=50)
#
#    class Meta:
#        verbose_name = 'SMS status'
#        verbose_name_plural = 'SMS statuses'
#
#    def __unicode__(self):
#        return self.status
#
#class Root(models.Model):
#    _name = models.CharField(max_length=100)
#    status = models.ForeignKey(SMSStatus)
#
#    class Meta:
#        abstract = True
#
#    def __unicode__(self):
#        return self.name
#
#    def cdp_definition(self, indent_order=0):
#        output = '%s%s %s\n' % ('\t'*indent_order, 
#                                self.__class__.__name__.lower(), 
#                                self.name)
#        output += self._start_cdp_definition(indent_order)
#        output += self._specific_cdp_definition(indent_order+1)
#        output += self._end_cdp_definition(indent_order)
#        return output
#
#    def _start_cdp_definition(self, indent_order=0):
#        return ''
#
#    def _end_cdp_definition(self, indent_order=0):
#        output = '%send%s\n' % ('\t'*indent_order, 
#                                self.__class__.__name__.lower())
#        return output
#
#    def _specific_cdp_definition(self, indent_order=0):
#        return ''
#
#
#class Suite(Root):
#
#    @property
#    def name(self):
#        return self._name
#
#    @name.setter
#    def name(self, name):
#        self._name = name
#
#    @staticmethod
#    def from_def(def_file):
#        fh = open(def_file, 'r')
#        grammar = Suite.suite_grammar()
#        p = grammar.parseString(fh.read())
#        s = Suite(name=p[1], status=SMSStatus.objects.get(status='unknown'))
#        s.save()
#        var_list = [i for i in p if i[0] == 'edit']
#        fam_list = [i for i in p if i[0] == 'family']
#        s._parse_variables_def(var_list)
#        s._parse_families_def(fam_list)
#        s.save()
#        return p, s
#
#    @staticmethod
#    def suite_grammar():
#        quote = pp.Word('"\'', exact=1).suppress()
#        colon = pp.Literal(':').suppress()
#        l_paren = pp.Literal('(').suppress()
#        r_paren = pp.Literal(')').suppress()
#        sms_node_path = pp.Word('./_' + pp.alphanums)
#        identifier = pp.Word(pp.alphas, pp.alphanums + '_')
#        var_value = pp.Word(pp.alphanums) | (quote + \
#                pp.Combine(pp.OneOrMore(pp.Word(pp.alphanums)), adjacent=False, 
#                           joinString=' ') + quote)
#        sms_comment = pp.Word('#') + pp.Optional(pp.restOfLine)
#        sms_var = pp.Group(pp.Keyword('edit') + identifier + var_value)
#        sms_label = pp.Group(pp.Keyword('label') + identifier + var_value)
#        sms_meter = pp.Group(pp.Keyword('meter') + identifier + pp.Word(pp.nums) * 3)
#        sms_limit = pp.Group(pp.Keyword('limit') + identifier + pp.Word(pp.nums))
#        sms_in_limit = pp.Group(pp.Keyword('inlimit') + sms_node_path + colon + identifier)
#        sms_trigger = pp.Group(pp.Keyword('trigger') + pp.restOfLine)
#        sms_repeat = pp.Group(pp.Keyword('repeat') + pp.Keyword('date') + identifier + pp.Word(pp.nums) * 2)
#        sms_defstatus = pp.Group(pp.Keyword('defstatus') + (pp.Keyword('suspended') ^ \
#                        pp.Keyword('complete') ^ pp.Keyword('queued')))
#        sms_clock = pp.Group(pp.Keyword('clock') + pp.Keyword('hybrid') + pp.Word(pp.nums))
#        sms_task = pp.Group(
#            pp.Keyword('task') + \
#            identifier + \
#            pp.ZeroOrMore(
#                sms_defstatus ^ sms_trigger ^ sms_in_limit ^ sms_label ^ sms_meter ^ sms_var
#            )
#        ) + pp.Optional(pp.Keyword('endtask').suppress())
#        sms_family = pp.Forward()
#        sms_family << pp.Group(
#            pp.Keyword('family') + identifier + pp.ZeroOrMore(
#                sms_defstatus ^ sms_in_limit ^ sms_limit ^ sms_trigger ^ sms_var ^ sms_task ^ sms_family ^ sms_repeat
#            )
#        ) + pp.Keyword('endfamily').suppress()
#        sms_suite = pp.Keyword('suite') + identifier + \
#                    pp.ZeroOrMore(sms_clock ^ sms_defstatus ^ sms_var ^ sms_family) + \
#                    pp.Keyword('endsuite').suppress()
#        sms_suite.ignore(sms_comment)
#        return sms_suite
#
#    def _parse_variables_def(self, var_list):
#        for i in var_list:
#            v = SuiteVariable(suite=self, name=i[1], value=i[2])
#            v.save()
#
#    def _parse_families_def(self, fam_list):
#        for i in fam_list:
#            f = Family.from_def(i, parent=self)
#            f.save()
#
#    def _start_cdp_definition(self, indent_order=0):
#        output = ''
#        for var in self.suitevariable_set.all():
#            output += '%sedit %s "%s"\n' % ('\t'*(indent_order+1), 
#                                            var.name, var.value)
#        return output
#
#    def _specific_cdp_definition(self, indent_order=0):
#        output = ''
#        for f in self.family_set.all():
#            output += f.cdp_definition(indent_order)
#        return output
#
#
#class Node(Root):
#    _path = models.CharField(max_length=255, editable=False)
#    _family = models.ForeignKey(
#        'Family', null=True, blank=True,
#        related_name='%(app_label)s_%(class)s_families', 
#    )
#
#    @property
#    def path(self):
#        return self._path
#
#    @property
#    def name(self):
#        return self._name
#
#    @name.setter
#    def name(self, name):
#        self._name = name
#        self._path = ''.join(self.path.rpartition('/')[0:2] + (name,))
#
#    @property
#    def family(self):
#        return self._family
#
#    @family.setter
#    def family(self, family):
#        self._family = family
#        if family is not None:
#            self._path = '/'.join((family.path, self.name))
#        else:
#            if self.suite is None:
#                self._path = self.name
#            else:
#                self._path = '/' + self.name
#
#    def save(self):
#        self.name = self.name
#        self.family = self.family
#        super(Node, self).save()
#
#    class Meta:
#        abstract = True
#
#    def _specific_cdp_definition(self, indent_order=0):
#        return ''
#
#
#class Family(Node):
#    repeat = models.ForeignKey('Repeat', null=True, blank=True)
#    _suite = models.ForeignKey(Suite, null=True, blank=True)
#
#    @property
#    def suite(self):
#        if self._suite is None and self.family is not None:
#            result = self.family.suite
#        else:
#            result = self._suite
#        return result
#
#    @suite.setter
#    def suite(self, suite):
#        self._suite = suite
#
#    class Meta:
#        verbose_name_plural = 'Families'
#
#    @staticmethod
#    def from_def(parse_obj, parent=None):
#        status = SMSStatus.objects.get(status='unknown')
#        if parent is not None:
#            if isinstance(parent, Family):
#                f = Family(name=parse_obj[1], status=status, family=parent)
#            elif isinstance(parent, Suite):
#                f = Family(name=parse_obj[1], status=status, suite=parent)
#        else:
#            f = Family(name=parse_obj[1], status=status)
#        f.save()
#        var_list = [i for i in parse_obj if i[0] == 'edit']
#        fam_list = [i for i in parse_obj if i[0] == 'family']
#        task_list = [i for i in parse_obj if i[0] == 'task']
#        f._parse_variables_def(var_list)
#        f._parse_repeat_def(parse_obj)
#        f._parse_families_def(fam_list)
#        f._parse_tasks_def(task_list)
#        f.save()
#        return f
#
#    def _parse_variables_def(self, var_list):
#        for i in var_list:
#            v = FamilyVariable(family=self, name=i[1], value=i[2])
#            v.save()
#
#    def _parse_families_def(self, fam_list):
#        for i in fam_list:
#            f = Family.from_def(i, parent=self)
#
#    def _parse_repeat_def(self, parse_obj):
#        try:
#            r = [i for i in parse_obj if i[0] == 'repeat'][0]
#            repeat = {'type' : r[1], 'name' : r[2], 'start' : r[3], 'end' : r[4]}
#            existent = Repeat.objects.filter(repeat_type=repeat['type'],
#                                             name=repeat['name'], 
#                                             start=repeat['start'],
#                                             end=repeat['end'])
#            if len(existent) > 0:
#                the_repeat = existent[0]
#            else:
#                the_repeat = Repeat(repeat_type=repeat['type'], 
#                                    name=repeat['name'],
#                                    start=repeat['start'],
#                                    end=repeat['end'])
#                the_repeat.save()
#            self.repeat = the_repeat
#        except IndexError:
#            # this family doesn't define a repeat
#            pass
#
#    def _parse_tasks_def(self, task_list):
#        for i in task_list:
#            t = Task.from_def(i, family=self)
#            
#    def _start_cdp_definition(self, indent_order=0):
#        output = ''
#        for var in self.familyvariable_set.all():
#            output += '%sedit %s "%s"\n' % ('\t'*(indent_order+1), 
#                                            var.name, var.value)
#        return output
#
#    def _specific_cdp_definition(self, indent_order=0):
#        output = ''
#        if self.repeat is not None:
#            output += self.repeat.cdp_definition(indent_order)
#        for f in self.smssettings_family_families.all():
#            output += f.cdp_definition(indent_order)
#        for t in self.smssettings_task_families.all():
#            output += t.cdp_definition(indent_order)
#        return output
#
#
#
#class Task(Node):
#
#    @staticmethod
#    def from_def(parse_obj, family=None):
#        status = SMSStatus.objects.get(status='unknown')
#        if isinstance(family, Family):
#            t = Task(name=parse_obj[1], status=status, family=family)
#        else:
#            t = Task(name=parse_obj[1], status=status)
#        t.save()
#        var_list = [i for i in parse_obj if i[0] == 'edit']
#        t._parse_variables_def(var_list)
#        t.save()
#        return t
#
#    def _parse_variables_def(self, var_list):
#        for i in var_list:
#            v = TaskVariable(task=self, name=i[1], value=i[2])
#            v.save()
#
#    def _start_cdp_definition(self, indent_order=0):
#        output = ''
#        for var in self.taskvariable_set.all():
#            output += '%sedit %s "%s"\n' % ('\t'*(indent_order+1), 
#                                            var.name, var.value)
#        return output
#    def _specific_cdp_definition(self, indent_order=0):
#        output = ''
#        #exp, nodes = self.trigger
#        #if exp != '':
#        #    trig = exp % tuple([n.path for n in nodes])
#        #    output += '%strigger %s\n' % ('\t' * indent_order, trig)
#        return output
#
#
#
#class Variable(models.Model):
#    name = models.CharField(max_length=20)
#    value = models.CharField(max_length=255)
#
#    class Meta:
#        abstract = True
#
#    def __unicode__(self):
#        return '%s: %s' % (self.name, self.value)
#
#class SuiteVariable(Variable):
#    suite = models.ForeignKey(Suite)
#
#class FamilyVariable(Variable):
#    family = models.ForeignKey(Family)
#
#class TaskVariable(Variable):
#    task = models.ForeignKey(Task)
#
#class Repeat(models.Model):
#    name = models.CharField(max_length=50)
#    repeat_type = models.CharField(max_length=50)
#    start = models.CharField(max_length=255)
#    end = models.CharField(max_length=255)
#
#    def __unicode__(self):
#        return self.name
#
#    def cdp_definition(self, indent_order=0):
#        output = '%srepeat %s %s %s %s\n' % ('\t'*indent_order, 
#                                             self.repeat_type, self.name, 
#                                             self.start, self.end)
#        return output
#

class SMSServer(models.Model):
    alias = models.CharField(max_length=100)
    rpc_num = models.IntegerField()
    host_settings = models.ForeignKey(Host)

    @staticmethod
    def get_server(alias):
        '''
        Get the server object and initialize it in one go
        '''

        s = SMSServer.objects.get(alias=alias)
        login_result = s._init_server()
        return s, login_result

    def _init_server(self):
        if not hasattr(self, 'connection'):
            self.CDP_PROMPT = 'CDP>'
            self.CDP_COMMANDS = {
                    'login' : 'login %s %s %s',
                    'terminate' : 'terminate -y',
                    'suites' : 'suites',
                    'update' : 'get',
                    'get_suite' : 'show',
            }
            self.host = HostFactory().create_host(self.host_settings)
            self.base_path = os.path.join(self.host.dataPath, 'SMS_SERVERS', self.alias)
            self.server_dir = os.path.join(self.base_path, 'SERVER_START_DIR')
            self.suites_dir = os.path.join(self.base_path, 'SUITES')
            self.connection = self._connect_to_cdp()
            server_started = self._start_server()
            if server_started == 0:
                login = self.login()
            else:
                login = 1
            return login

    def list_suites(self):
        '''Return a list with the names of the suites in the server.'''

        out = self._get_cdp_result(self.CDP_COMMANDS['suites'])
        suites = out[4].split()
        return suites

    def _get_suite_definition(self, suite_name):
        '''Return a string with the CDP commands that defined a suite.'''

        update = self._get_cdp_result(self.CDP_COMMANDS['update'])
        out = self._get_cdp_result(self.CDP_COMMANDS['get_suite'])
        suite_def = ''
        suite_started = False
        for line in out:
            if line.startswith('suite') and suite_name in line:
                suite_started = True
            if suite_started:
                suite_def += line + '\n'
            if suite_started and line.startswith('endsuite'):
                break
        return suite_def

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
            self._create_directories()
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
