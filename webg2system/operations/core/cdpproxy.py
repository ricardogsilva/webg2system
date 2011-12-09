#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A module to serve as a proxy between CDP and Python.
"""

import re
from pexpect import spawn
import xml.etree.ElementTree as etree

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
