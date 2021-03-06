#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A module to serve as a proxy between CDP and Python.
"""

import getpass
import g2hosts

import re
from pexpect import spawn, ExceptionPexpect
import xml.etree.ElementTree as etree

import pygraphviz as pgv
from uuid import uuid1

class CDPGetError(Exception):
    pass


class SMSNode(object):
    IDS = [0]

    def __init__(self, name):
        self.name = name
        self.id = self.IDS[-1] + 1
        self.IDS.append(self.id)

    def __repr__(self):
        return '%s_%s' % (self.id, self.name)


class Suite(SMSNode):

    def __init__(self, name):
        super(Suite, self).__init__(name)
        self.variables = dict()
        self.families = []


class Family(SMSNode):

    def __init__(self, name, parent=None):
        super(Family, self).__init__(name)
        self.parent = parent
        self.variables = dict()
        self.families = []
        self.tasks = []


class Task(SMSNode):

    def __init__(self, name, parent=None):
        super(Task, self).__init__(name)
        self.parent = parent
        self.variables = dict()


class SuiteGraph(pgv.AGraph):

    def __init__(self, suite, name=None, strict=True, directed=False, **kwargs):
        self.suite = suite
        if name is None:
            name = suite.name
        super(SuiteGraph, self).__init__(name=name, strict=strict, 
                                         directed=directed, **kwargs)
        self.add_node(suite)
        for f in suite.families:
            self._add_family(f)

    def _add_family(self, family):
        self.add_node(family, color='red')
        self.add_edge(family.parent, family, color='blue')
        for fam in family.families:
            self._add_family(fam)
        for task in family.tasks:
            self._add_task(task)

    def _add_task(self, task):
        self.add_node(task)
        self.add_edge(task.parent, task)


class NewCDPProxy(object):
    '''
    Connect to CDP and run commands.
    '''

    host = None
    _connection = None
    _cdp_prompt = 'CDP>'

    def __init__(self, cdp_host='localhost', rpc_num=314156, 
                 user=None, password=None):
        hf = g2hosts.HostFactory()
        self.host = hf.create_host()
        self.rpc_num = rpc_num
        self.cdp_host = cdp_host
        if user is None:
            self.user = getpass.getuser()
        if password is None:
            self.password = 'dummy'
        #self.connected = self._connect()
        self.connected = self._connect()

    def _connect(self):
        result = False
        if self._connect_to_cdp():
            result = self._login_to_sms(self.rpc_num, self.cdp_host, self.user,
                                        self.password)
        return result

    def _connect_to_cdp(self):
        result = False
        if self._connection is not None:
            # already connected
            result = True
        else:
            try:
                print('About to connect to CDP')
                self.connection = spawn('cdp')
                self.connection.expect(self._cdp_prompt)
                result = True
            except ExceptionPexpect as err:
                print(err)
        return result

    def _login_to_sms(self, rpc_num, cdp_host, user, password):
        result = False
        cmd = 'set SMS_PROG %i; login %s %s %s' % (rpc_num, cdp_host,
                                                   user, password)
        output = self._get_result(cmd)
        if 'logged into' in output[1]:
            #connection successful
            result = True
        else:
            errorMsg = "Couldn't login to the SMS server."
            errorMsg += " CDP's response was:\n%s" % output
            print(errorMsg)
        return result

    def _get_result(self, command):
        self.connection.sendline(command)
        self.connection.expect(self._cdp_prompt)
        result = self.connection.before.split('\r\n')
        return result

    def list_suites(self):
        out = self._get_result('suites')
        defined_suites = out[2].split()
        return defined_suites

    def node_info(self, node_path):
        if node_path.startswith('/'):
            node_path = node_path[1:]
        node_path = '/'.join(('//%s' % self.cdp_host, node_path))
        out = self._get_result('info -v %s' % node_path)
        node_variables = self._parse_node_variables(out)
        return node_variables

    def _parse_node_variables(self, raw_output):
        result = dict()
        count = 0
        variable_definitions = False
        while count < len(raw_output):
            line = raw_output[count].strip()
            if line == '':
                pass
            elif line.startswith('Variables'):
                variable_definitions = True
                pass
            else:
                if variable_definitions:
                    line = re.sub(r'^\((?P<rest>.*)\s*\)\s*\[.*\]$', r'\g<rest>', line)
                    line = re.sub(r'^(?P<rest>.*)\s*\[.*\]$', r'\g<rest>', line)
                    var_name, var_value = line.split('=', 1)
                    result[var_name.strip()] = var_value.strip()
            count += 1
        return result

    def find_nodes(self, node_regexp, suite=None, families=[]):
        '''
        Find nodes whose name matches the input regular expression.

        Inputs:

            node_regexp - a regular expression defining the name of the
                          node to find.

            suite - the suite where the node is to be searched. If None
                    (the default) the node will be searched in all the
                    currently defined suites.

            families - a list of families where the node is to be searched.

        Returns:

        A list with all the nodes whose name matches the input regular
        expression.
        '''

        out = self._get_result('find -v %s' % node_regexp)
        result = out[1:]
        if suite is not None:
            result = [n for n in result if '/%s' % suite in n]
        if len(families) > 0:
            for f in families:
                result = [n for n in result if '%s' % f in n]
        return result

    def get_definition(self, suite):
        result = []
        try:
            self._update_definition()
            out = self._get_result('show')
            in_suite = False
            count = 0
            while count < len(out):
                line = out[count]
                if 'suite %s' % suite in line:
                    in_suite = True
                elif 'endsuite' in line:
                    result.append(line)
                    in_suite = False
                if in_suite:
                    result.append(line)
                count += 1
        except CDPGetError as err:
            print(err)
        return result

    def _update_definition(self):
        out = self._get_result('get')
        result = False
        if 'Got it' in out[1]:
            result = True
        else:
            raise CDPGetError
        return result

    #FIXME - finish this method
    def parse_definition(self, suite):
        definition = self.get_definition(suite)
        current = None
        result = None
        for line in definition:
            words = line.split()
            first_word = words[0]
            if first_word == 'suite':
                current = Suite(words[1])
                result = current
            elif first_word == 'defstatus':
                current.defstatus = words[1]
            elif first_word == 'edit':
                current.variables[words[1]] = words[2]
            elif first_word == 'family':
                fam = Family(words[1], parent=current)
                current.families.append(fam)
                current = fam
            elif first_word == 'endfamily':
                if isinstance(current, Family):
                    current = current.parent
                else:
                    current = current.parent.parent
            elif first_word == 'task':
                if isinstance(current, Family):
                    t = Task(words[1], parent=current)
                    current.tasks.append(t)
                    current = t
                else:
                    parent = current.parent
                    t = Task(words[1], parent=parent)
                    parent.tasks.append(t)
                    current = t
            elif first_word == 'endtask':
                current = current.parent
            else:
                pass
        return result


class CDPProxy(object):
    '''
    Connect to CDP and run commands.
    '''

    connection = None
    serverStructure = None
    tagMap = dict()
    taskPaths = None
    cdpPrompt = 'CDP>'

    def __init__(self, CDPAlias):
        self.alias = CDPAlias
        self._get_tag_mapping()
        self._update_server_definition()

    def _act_upon_nodes(self, pathList, cdpAction):
        '''
        Perform 'cdpAction' command upon the nodes in 'pathList'.

        See the 'cancel_nodes' method for an example.

        Inputs:

            pathList - A list of node paths to act upon.

            cdpAction - A string with a cdp command that accepts a node path
                as argument.
        '''

        cdpCommands = ['%s %s' % (cdpAction, p) for p in pathList]
        self.run_commands(cdpCommands)

    def _connect(self):
        if self.connection is not None and not self.connection.closed:
            #print('Already connected')
            pass
        else:
            print('About to connect')
            self.connection = spawn('cdp')
            self.connection.expect(self.cdpPrompt)
            logInOutput = self._get_result(self.alias)
            if 'logged into' in logInOutput[1]:
                #connection successful
                pass
            else:
                errorMsg = "Couldn't login to the SMS server."
                errorMsg += " CDP's response was:\n%s" % logInOutput
                raise IOError, errorMsg

    def _find_related_nodes(self, infoList, relation):
        '''
        Return a list with the paths of the nodes that are mentioned in
        the 'infoList' argument.

        Inputs:

            infoList - A list of strings containing the information on a node,
                as reported by CDP's 'info -v' function

            relation - A string with a pattern that signals the beginning of 
                the paths to filter from the infoList
        '''

        pathRE = re.compile(r'(/\w*)+')
        relatedPaths = []
        relatedLine = False
        for line in infoList:
            if relation in line:
                relatedLine = True
            else:
                pathSearch = pathRE.search(line)
                if relatedLine:
                    if pathSearch is not None:
                        # strangely, CDP returns the same path twice when 
                        # asked for dependencies or dependants, so we check
                        # for duplicate paths before appending
                        pathToAdd = pathSearch.group()
                        if pathToAdd not in relatedPaths:
                            relatedPaths.append(pathToAdd)
                    else:
                        relatedLine = False
        return relatedPaths

    def _find_node_variables(self, infoList):
        '''
        Return a dictionary with the variables defined in the node.

        Inputs:

            infoList - A list of strings containing the information on a node,
                as reported by CDP's 'info -v' function
        '''

        varEndRe = re.compile(r'\[(.*)\]$')
        varLine = False
        variables = {
                'nodeVariables' : dict(),
                'otherVariables' : dict()
                }
        for line in infoList:
            if 'Variables' in line:
                varLine = True
            else:
                varNodeSearch = varEndRe.search(line)
                if varLine:
                    if varNodeSearch is not None:
                        if varNodeSearch.group(1) == '':
                            varType = variables['nodeVariables']
                        else:
                            varType = variables['otherVariables']
                        varEnd = varNodeSearch.group()
                        varName, varValue = [p.strip() for p in \
                                line.replace(varEnd, '').split('=')]
                        varType[varName] = varValue
                    else:
                        varLine = False
        return variables

    def _get_result(self, command):
        self.connection.sendline(command)
        self.connection.expect(self.cdpPrompt)
        result = self.connection.before.split('\r\n')
        return result

    def _get_task_paths(self, startingNodes, pathName='/', pathNames=None):
        '''
        Return a list with the absolute paths of all the 'task' nodes that
        exist under the 'startingNodes' argument.

        This is a recursive function. This function should not be called by
        external client code, unless it knows what it is doing!

        Inputs:

            startingNodes - An Etree NodeList

            pathName - A temporary variable used in the recursion cycle.
                It should not be overriden.

            pathNames - A temporary variable used in the recursion cycle.
                It should not be overriden.

        Returns:

            A list of strings with the full paths to every 'task' node defined
            below the 'startingNodes' argument.
        '''

        if pathNames is None:
            pathNames = []
        for nodeEl in startingNodes:
            nodeType = self.tagMap.get(nodeEl.tag)
            if nodeType in ('suite', 'family', 'task', 'repeat'):
                nodeName = nodeEl.find('n').text
                if nodeType == 'repeat':
                    pathNames.append(pathName[:-1] + ':' + nodeName)
                elif nodeType == 'task':
                    pathNames.append(pathName + nodeName)
                else:
                    self._get_task_paths(nodeEl.getchildren(), 
                                         pathName + nodeName + '/', 
                                         pathNames)
        return pathNames

    def _get_all_task_paths(self):
        '''
        Update the class variable 'taskPaths' with a list of the full paths 
        of every 'task' defined in the sms server.
        '''

        self.taskPaths = self._get_task_paths(self.serverStructure)

    def _get_server_structure(self):
        '''
        Update the class variable 'serverStructure' with an Etree object with
        the xml description of the suites defined.
        '''

        results = self.run_commands(['get', 'xml'])
        self.serverStructure = etree.fromstring(''.join(results[1]))

    def _update_server_definition(self):
        self._get_server_structure()
        self._get_all_task_paths()

    def _get_tag_mapping(self):
        '''
        Populate self.tagMap with the correct values.

        Read CDP's help page on the 'xml' command for more details.
        '''

        mapList = self.run_commands(['xml -h'])[0]
        for item in mapList:
            parts = item.split()
            self.tagMap[parts[1]] = parts[0]
        # this tag explanation is missing from CDP's 'xml -h' command
        self.tagMap['n'] = 'name'

    def run_commands(self, commandList):
        '''
        Run the desired CDP commands.

        Inputs:

            commandList - A list of strings with the CDP commands to run
        '''

        self._connect()
        bigResult = []
        for cmd in commandList:
            # the first line of output is the command that was run
            # and the last line is just blank, that's why they are being 
            # removed
            result = self._get_result(cmd)[1:-1]
            bigResult.append(result)
        return bigResult

    def find_paths(self, regexp):
        '''
        Return the full paths to all the nodes whose path matches 'regexp'.

        Inputs:

            regexp - A regular expression to filter paths.

        Examples:

            - find the families named 'postProcessing':
                    
                    find_paths(r'.*postProcessing')

            - find the families named 'postProcessing' that exist in the 
            'daily' family:

                    find_paths(r'.*/daily.*postProcessing')

            find the tasks that exist inside the 'postProcessing' family
            for the '22h00m' family:

                    find_paths(r'.*22.*postProcessing.*')
        '''

        reRegExp = re.compile(regexp)
        matchedTasks = []
        for tp in self.taskPaths:
            reObj = reRegExp.search(tp)
            if reObj is not None:
                matchedTasks.append(reObj.group())
        matchedFamilies = set(matchedTasks)
        return matchedFamilies

    def cancel_nodes(self, regexp):
        '''
        Cancel the nodes whose paths match the 'regexp' argument.

        The nodes to cancel can be 'task' or 'family' nodes.

        Inputs:

            regexp - a string with a regular expression to filter paths.
        '''

        pathsToCancel = self.find_paths(regexp)
        result = self._act_upon_nodes(pathsToCancel, 'cancel -yf')
        self._update_server_definition()
        return result

    def find_all_related_paths(self, regexp, dependencies, dependants):
        relatedPaths = list(self.find_paths(regexp))
        extraPaths = []
        if dependencies or dependants:
            for path in relatedPaths:
                nodeInfo = self.node_info(path)
                if dependencies:
                    extraPaths += nodeInfo['dependencies']
                if dependants:
                    extraPaths += nodeInfo['dependants']
        allRelatedPaths = relatedPaths + extraPaths
        return allRelatedPaths
        
    def keep_nodes(self, regexp, dependencies=False, dependants=False):
        '''
        Filter the node paths defined in the server and keep only the ones
        that match the 'regexp' argument.

        Inputs:

            regexp - A string with a regular expression to filter paths.

            dependencies - A boolean indicating if the dependencies of the
                nodes that match the 'regexp' argument should also be kept.

            dependants - A boolean indicating if the dependants of the
                nodes that match the 'regexp' argument should also be kept.
        '''

        pathsToKeep = self.find_all_related_paths(regexp, dependencies, 
                                                  dependants)
        removables = []
        for path in pathsToKeep:
            removables.append(self.find_removable_paths(path))
        processed = []
        pathsToCancel = []
        # iterate through each sublist inside the 'removables' list
        while len(removables) != 0:
            listToProcess = removables.pop()
            for candidate in listToProcess:
                removes = [False] * (len(removables) + len(processed))
                # compare the candidate with the other paths
                for i, otherList in enumerate(removables):
                    for item in otherList:
                        if item in candidate:
                            # this candidate can be removed according to the 
                            # current otherList
                            removes[i] = True
                for i, anotherList in enumerate(processed):
                    for item in anotherList:
                        if item in candidate:
                            removes[len(removables) + i] = True
                if False not in removes and candidate not in pathsToCancel:
                    # can remove this candidate
                    pathsToCancel.append(candidate)
            processed.append(listToProcess)
        result = self._act_upon_nodes(pathsToCancel, 'cancel -yf')
        self._update_server_definition()
        return result

    def find_removable_paths(self, path):
        '''
        Find the paths that can be removed from the server tree.

        This method will sort out the paths that can be removed from
        the suite according to a given path that is to be kept. The
        removable paths are aggregated according to their minimum common
        family.

        Example:

            - For the server tree composed of the following nodes:

            a             | a command of self.find_removable_paths('/a/b/c/d')
             |_b          | will yield the result:
             |  |_c       |         
             |     |_d    |         /a/b/c/e
             |     |_e    |         /a/b/c/f
             |     |_f    |         /a/g
             |_g          |         /a/m
             |  |_h       |         
             |  |_i       |         
             |  |_j       |         
             |     |_k    |         
             |     |_l    |         
             |_m          |         
                |_n       |         
                |_o       |         

        Inputs:

            path - The path to keep

        Returns:

            A list of paths that can be removed from the server.
        '''

        candidates = []
        currentPath = path
        while currentPath != '':
            siblings = self.get_siblings(currentPath)
            if len(siblings) != 0:
                candidates += siblings
            currentPath = currentPath.rpartition('/')[0]
        return candidates

    def get_parent(self, path):
        '''
        Return a string with the path of the parent of 'path'.
        '''

        return path.rpartition('/')[0]

    def get_children(self, path):
        '''
        Return a list of paths with the children of 'path'.
        '''

        children = []
        reObj = re.compile(r'^(%s/\w+)/*' % path)
        for path in self.taskPaths:
            rePath = reObj.search(path)
            if rePath is not None:
                child = rePath.group(1)
                if child not in children:
                    children.append(child)
        return children

    def get_siblings(self, path):
        '''
        Return a list with the siblings of 'path'.
        '''

        parent = self.get_parent(path)
        children = self.get_children(parent)
        siblings = [p for p in children if p != path]
        return siblings

    def node_info(self, path):
        '''
        Return a dictionary with (most) of the variables and their values.

        Inputs:

            path - A string specifying the full path of the node
        '''

        rawVars = self.run_commands(['info -v %s' % path])[0]
        nodeInfo = dict()
        daStartLine = 'Nodes triggered by this node'
        diStartLine = 'Nodes that trigger this node'
        nodeInfo['dependants'] = self._find_related_nodes(rawVars, daStartLine)
        nodeInfo['dependencies'] = self._find_related_nodes(rawVars, diStartLine)
        nodeInfo['variables'] = self._find_node_variables(rawVars)
        return nodeInfo

    def play_file(self, filePath):
        '''
        Play a definition file.

        Inputs:

            filePath - The full path to the definition file.
        '''

        self.run_commands(['play %s' % filePath])
        self._update_server_definition()
