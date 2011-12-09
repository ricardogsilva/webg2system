#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

import subprocess
import re
import os.path
from xml.dom import minidom
import xml.etree.ElementTree as etree

import utilities as utils
from decorators import log_calls

class G2SuiteParser(object):
    """
    Parse a SMS suite
    """

    @log_calls
    def __init__(self, suiteName, cdpAlias):
        self.suiteName = suiteName
        self.cdpAlias = cdpAlias
        cdpCommand = 'cdp -c "%s;get;show -x /%s"' % (self.cdpAlias, self.suiteName)
        newProcess = subprocess.Popen(cdpCommand, shell=True,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
        stdoutData, stderrData = newProcess.communicate()
        stdoutList = [line for line in stdoutData.split("\n")if not line.startswith("#")]
        outputList = []
        for index, line in enumerate(stdoutList):
            line = line.strip()
            if 1 < index < (len(stdoutList) - 2):
                newLine = self._fix_xml_errors(line)
                if newLine:
                    outputList.append(newLine)
        #print("outputList:\n%s" % outputList)
        self.suiteXML = minidom.parseString('\n'.join(outputList))
        self.suiteNode = self.suiteXML.getElementsByTagName('suite')[0]
        self.suiteETree = etree.fromstring(self.suiteNode.toxml()) 

        # this snippet was taken from effbot's element tree documentation[0]
        # it overcomes Etree's lack of methods for dealing with an element's
        # parent.
        # [0] - http://effbot.org/zone/element.htm#accessing-parents 
        self.parentMap = dict((c, p) for p in self.suiteETree.getiterator() for c in p)

    @log_calls
    def get_nodes_data(self, rootNode):
        """
        Returns: A set of tuples, containing the unique information on each 
                 task
        """

        taskNodes = rootNode.getElementsByTagName('task')
        nodesInfo = set()
        for nodeElement in taskNodes:
            nodeName = nodeElement.getAttribute("name")
            variableElements = nodeElement.getElementsByTagName("variable")
            nodeVersion = None
            nodeMode = None
            nodeArea = None
            if len(variableElements) >= 4:
                nodeVersion = variableElements[0].getAttribute("value")
                nodeMode = variableElements[1].getAttribute("value")
                nodeArea = variableElements[2].getAttribute("value")
                nodeDBPackage = variableElements[3].getAttribute("value")
            elif len(variableElements) < 4:
                nodeDBPackage = variableElements[0].getAttribute("value")
            nodesInfo.add((nodeName, nodeMode, nodeArea, nodeDBPackage)) 
        return nodesInfo

    @log_calls
    def get_nodes_data_with_path(self, rootNode):
        """
        Returns: A set of tuples, containing the unique information on each 
                 task
        """

        taskNodes = rootNode.getElementsByTagName('task')
        nodesInfo = set()
        for nodeElement in taskNodes:
            nodePath = self.reconstruct_node_path(nodeElement)
            nodeName = nodeElement.getAttribute("name")
            variableElements = nodeElement.getElementsByTagName("variable")
            nodeVersion = None
            nodeMode = None
            nodeArea = None
            if len(variableElements) >= 4:
                nodeVersion = variableElements[0].getAttribute("value")
                nodeMode = variableElements[1].getAttribute("value")
                nodeArea = variableElements[2].getAttribute("value")
                nodeDBPackage = variableElements[3].getAttribute("value")
            elif len(variableElements) < 4:
                nodeDBPackage = variableElements[0].getAttribute("value")
            nodesInfo.add((nodeName, nodeMode, nodeArea, nodeDBPackage, nodePath)) 
        return nodesInfo

    @log_calls
    def get_nodes_with_repeat(self, rootNode, repeatName='YMD'):
        familyNodes = rootNode.getElementsByTagName("family")
        nodesWithRepeat = []
        for familyNode in familyNodes:
            familyName = familyNode.getAttribute("name")
            hourlyFamilyREObj = re.search(r"[0-9]{2}h00m", familyName)
            if hourlyFamilyREObj is not None:
                # a hack to see if this family really defines a repeat object
                # we are searching for text elements because SMS outputs badly
                # formatted XML...
                # nodeType == 3 is a textNode
                textElements = [n.nodeValue for n in familyNode.childNodes if n.nodeType == 3] 
                for text in textElements:
                    if re.search(r"repeat.*%s" % (repeatName), text) is not None: # found a repeat
                        nodesWithRepeat.append(familyNode)
        return nodesWithRepeat

    @log_calls
    def reconstruct_node_path(self, node):
        path = ""
        while node.parentNode is not None:
            name = node.getAttribute("name")
            path = name + "/" + path
            node = node.parentNode
        return path[:-1]

    @log_calls
    def reconstruct_node_path_et(self, element):
        "reconstruct a node's path using the element tree module."

        path = ""
        while element is not None:
            parent = self.parentMap.get(element)
            name = element.get("name")
            path = name + "/" + path
            element = parent
        return path[:-1]

    @log_calls
    def _fix_xml_errors(self, line):
        """
        Fix the various XML errors that can potentially exist
        """

        newLine = line
        if line.startswith("<") and not line.endswith(">"):
            newLine += " />"
        if line.startswith("<time"):
            splitLine = newLine.split()
            newLine = "%s value=%s" % (splitLine[0], " ".join(splitLine[1:]))
            #newLine = None
        if line.startswith("limit"):
            newLine = "<" + newLine
        if line.startswith("inlimit"):
            elements = newLine.split()
            newLine = "<%s name='%s' />" % (elements[0], elements[1])
        if line.startswith("clock"):
            removeComments = line.split("#")[0]
            sections = removeComments.split()
            newLine = "<%s name='%s' />" % (sections[0], sections[1])
        if line.find("&") != -1:
            newLine = newLine.replace("&", "&amp;")
        if line.count(">") > 1:
            sections = newLine.split(">")
            newLine = ""
            for section in sections:
                newLine += section + "&gt;"
            newLine = newLine[:-4] + ">"
        newLine = self._fix_unquoted_attributes(newLine)
        if line.startswith("<variable name='SMS"):
            newLine = None
        if line.startswith("<defstatus"):
            newLine = None
        return newLine

    @log_calls
    def _fix_unquoted_attributes(self, line):
        if line.startswith("<") and line.endswith("/>"):
            newLine = "<" + self._add_quotes2(line[1:-2]) + "/>"
        elif line.startswith("<") and line.endswith(">"):
            newLine = "<" + self._add_quotes2(line[1:-1]) + ">"
        else:
            newLine = line
        return newLine

    @log_calls
    def _add_quotes(self, line):
        newLine = line.replace("'", "")
        newLine = newLine.replace('"', "")
        tokenList = newLine.split("=")
        if len(tokenList) > 1:
            newLine = tokenList[0]
            for token in tokenList[1:]:
                spaceList = token.split()
                if len(spaceList) == 2:
                    newLine += "='" + " ".join(spaceList[:-1]) + "' "
                    newLine += spaceList[-1]
                elif len(spaceList) > 2:
                    newLine += "='" + " ".join(spaceList) + "'"
                else:
                    newLine += "='" + spaceList[0] + "'"
        else:
            newLine = line
        return newLine

    @log_calls
    def _add_quotes2(self, line):
        newLine = line.replace("'", "")
        newLine = newLine.replace('"', "")
        tokenList = newLine.split("=")
        if len(tokenList) > 1:
            newLine = tokenList[0]
            for token in tokenList[1:-1]:
                spaceList = token.split()
                newLine += "='" + " ".join(spaceList[:-1]) + "' "
                newLine += spaceList[-1]
            newLine += "='" + tokenList[-1] + "'"
        else:
            newLine = line
        return newLine

    @log_calls
    def traverse_nodes(self, nodeList, pathName='', pathNames=[], 
                       pathNodeName='', pathNodeNames=[]):
        """
        Get the paths that represent the suite's family hierarchy.

        Inputs: nodeList - a list of XML nodes
                pathName - A temporary string that is used internally to create
                           each branch's hierarchy
                pathNames - A temporary list of strings that is used internally
                            to create each branch's hierarchy
                pathNodeName - A temporary string that is used internally to
                               create each branch's hierarchy, but using the
                               name of ech node
                pathNodeNames - A temporary list of strings that is used 
                                internally to create each branch's hierarchy
                                using the name of each node
                                

        Returns: A tuple with two lists of strings. The first list specifies
        the paths and the second list specifies the node names (to be used for
        searching the XML object) specifying all the paths that are defined
        by the suite's definition.

        This function recursively traverses the XML node hierarchy of the suite's
        definition and returns lists with the various paths.
        """

        for node in nodeList:
            nType = node.nodeName
            if nType in ('suite', 'family', 'task'):
                nName = node.getAttribute("name")
                if nType == 'family':
                    self.traverse_nodes(node.childNodes, pathName + nName + '/',
                                        pathNames, pathNodeName + nType + '/',
                                        pathNodeNames)
                else:
                    pathNames.append(pathName + nName)
                    pathNodeNames.append(pathNodeName + nType)

        return pathNames, pathNodeNames

    @log_calls
    def get_symlink_matches(self):
        """
        Get the ...

        Returns: A dictionary with the names of the python scripts that have
                 code as keys, and the SMS 'PACKAGE' variable that matches
                 each script.
        """

        makeFamily = [f for f in self.suiteETree.getchildren() if 
                      f.get('name') == 'make'][0]
        matchList = [(v.get('name'), v.get('value')) 
                     for v in makeFamily.findall('variable')]
        matches = dict()
        for scriptName, packageNamesString in matchList:
            matches[scriptName] = packageNamesString.split()
        return matches

    @log_calls
    def get_task_package(self, namesPath, nodesPath):
        taskName = os.path.basename(namesPath)
        taskElement = [e for e in self.suiteETree.findall('./%s' % nodesPath) 
                      if e.get('name') == taskName][0]
        #taskPackage = [v.get('value') for v in taskElement.getchildren() 
        #              if v.get('name') == 'PACKAGE'][0]
        #return taskPackage
        taskPackageList = [v.get('value') for v in taskElement.getchildren()
                          if v.get('name') == 'PACKAGE']
        if taskPackageList:
            return taskPackageList[0]

    @log_calls
    def get_node_data(self, node):
        """
        Return the variables associated with the input node.
        
        Inputs:
            node - An ElementTree element. It can be either a task node or
                   a family node.

        Returns: A dictionary with the variables associated with the node, as
                 defined in the suite's definition file.
        """


        nodeName = node.get("name")
        variables = node.findall("variable")
        if len(variables) > 0:
            for el in node.findall("variable"):
                #attribName = utils.underscore_to_camelcase(el.attrib["name"])
                exec("%s = '%s'" % \
                     (utils.underscore_to_camelcase(el.attrib["name"]), 
                      el.attrib["value"]))
            # the del command deletes variables from memory
            del el
        del variables, node, self
        # the locals() function returns a dictionary with all the variables 
        # defined in the current scope
        return locals()

    @log_calls
    def find_nodes_to_keep(self, taskName=None, algorithmMode=None, area=None,
                           hours=[], parentFamily=None, useRegExp=False):
        """
        Return a list of node paths that match the input criteria.

        Inputs:
            taskName - A string specifying the name of the task, as defined in
                       the suite's definition file. It can be used together
                       with the 'useRegExp' input.
            algorithmMode - A string specifying the mode of the algorithm
                            to be searched for, as defined in the suite's
                            definition file.
            area - A string specifying the name of the area to search for,
                   as defined in the suite's definition file.
            hour - A list specifying a range of hours to be searched
            parentFamily - A string specifying the name of one family which
                           is the parent of the nodes to keep
            useRegExp - A boolean specifying if the 'taskName' and 
                        'parentFamily' inputs should be treated as regular
                        expressions.
        """

        nodesToKeep = []
        for el in self.suiteETree.findall(".//task"):
            taskNameTest = utils._word_search_test(el.get("name"), taskName, 
                                                  useRegExp)
            if taskNameTest:
                nodeVars = self.get_node_data(el)
                if (nodeVars.get("algorithmMode") == algorithmMode or \
                    algorithmMode is None) and (nodeVars.get("area") == area \
                    or area is None):
                        nodePath = self.reconstruct_node_path_et(el)
                        hourToCompare = None
                        nodeHour = re.search(r'[0-9]{2}h[0-9]{2}m', nodePath)
                        if nodeHour is not None:
                            hourToCompare = int(nodeHour.group()[:2])
                        hourTest = (len(hours) == 0) or (hourToCompare in hours)
                        familyTest = utils._word_search_test(nodePath, 
                                                            parentFamily, 
                                                            useRegExp)
                        if hourTest and familyTest:
                            nodesToKeep.append(nodePath)
        return nodesToKeep

    @log_calls
    def get_element_from_path(self, nodePath):
        """
        Return an ETree element object from an input sms suite path.
        """

        allPaths, allNodes = self.traverse_nodes(self.suiteNode.childNodes)
        try:
            nodeName = [n for p, n in zip(allPaths, allNodes) if p in nodePath][0]
            element = [el for el in self.suiteETree.findall(nodeName) if \
                       self.reconstruct_node_path_et(el) == nodePath][0]
        except IndexError:
            element = None
        return element

    @log_calls
    def find_dependencies(self, nodePath, triggerRule="queued"):
        """
        Return a list of nodePaths that need to be complete before the
        input nodePath can be run.
        """

        #cdpCommand = 'cdp -c "%s;info /%s"' % (self.cdpAlias, nodePath)
        #newProcess = subprocess.Popen(cdpCommand, shell=True,
        #                              stdin=subprocess.PIPE,
        #                              stdout=subprocess.PIPE, 
        #                              stderr=subprocess.PIPE)
        #stdoutData, stderrData = newProcess.communicate()
        #stdoutList = [line for line in stdoutData.split("\n")if not line.startswith("#")]
        cdpCommand = 'info /%s' % nodePath
        stdoutList, stderrList, retCode = utils.run_cdp_command(self.cdpAlias,
                                                                cdpCommand)
        triggers = []
        triggerLine = False
        for line in stdoutList:
            if not triggerLine:
                if line.startswith("Nodes that trigger this node"):
                    triggerLine = True
            else:
                if line.startswith("Goodbye"):
                    triggerLine = False
                else:
                    triggerExp, triggerStatus = line.split()
                    triggerStatus = triggerStatus[1:-1] # removing the square brackets
                    triggers.append((triggerExp, triggerStatus))
        return [tExp for tExp, tRule in triggers if tRule == triggerRule]

    @log_calls
    def find_dependants(self, nodePath):
        """
        Return a list of nodePaths that need to be complete before the
        input nodePath can be run.

        This method scans the dependants of the task as well as the dependants
        of all the families that the task lies in. It is therefore a bit slow.
        """

        pathList = nodePath.split("/")
        allDependants = []
        while len(pathList) > 1:
            nodePath = "/".join(pathList)
            cdpCommand = 'cdp -c "%s;info /%s"' % (self.cdpAlias, nodePath)
            newProcess = subprocess.Popen(cdpCommand, shell=True,
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE)
            stdoutData, stderrData = newProcess.communicate()
            stdoutList = [line for line in stdoutData.split("\n")if not line.startswith("#")]
            triggers = []
            triggerLine = False
            for line in stdoutList:
                if not triggerLine:
                    if line.startswith("Nodes triggered by this node"):
                        triggerLine = True
                else:
                    if line.startswith("Nodes that trigger this node") or \
                       line.startswith("Goodbye"):
                        triggerLine = False
                    else:
                        triggerExp = line.strip()
                        triggers.append(triggerExp)
            allDependants += triggers
            pathList.pop()
        return allDependants

    @log_calls
    def traverse(self, nodePath, relation, accumDeps=None):
        relationMap = {
                "dependencies" : self.find_dependencies,
                "dependants" : self.find_dependants}
        if accumDeps is None:
            accumDeps = []
        related = relationMap.get(relation)(nodePath)
        for rel in related:
            if rel not in accumDeps:
                accumDeps.append(rel)
            accumDeps = self.traverse(nodePath=rel, relation=relation, 
                                      accumDeps=accumDeps)
        return accumDeps

    @log_calls
    def generate(self, nodePath, withDependencies=False, withDependants=False,
                 withDependantsDependencies=False):
        """
        Sort all the objects that need to be generated.

        Inputs:

            nodePath - A string with the sms path of the node

            withDependencies - A boolean indicating if the dependencies
                                  of 'obj' are to be generated as well.

            withDependants - A boolean indicating if the objects that are
                             dependant of 'obj' are to be generated as well.

            withDependantsDependencies - A boolean indicating if the objects
                                         that are dependencies of the 'obj's
                                         dependants are to be generated as well.

        Returns: A list of objects that are to be generated.

        Examples:
            
            Let's suppose we habe the following objects and dependencies:

            LRIT2HDF5_g2 -> REF_g2 -> SA_g2 -> |CMa_g2 -> |DSSF_g2
                                |___________-> |          |
                                |______________________-> |
            
            - self.generate_object('CMa_g2') -> generate only the 'CMa_g2' object.

                result: ['CMa_g2']

            - self.generate_object('CMa_g2', True) -> generate the 'CMa_g2' and all 
                                                      its dependencies

                result: ['CMa_g2', 'REF_g2', 'LRIT2HDF5_g2', 'SA_g2']

            - self.generate_object('CMa_g2', False, True) -> generate the 'CMa_g2'
                                                             and all its dependants

                result: ['CMa_g2', 'DSSF_g2']

            - self.generate_object('CMa_g2', False, True, True) -> generate the 
                                                                   'CMa_g2', all its
                                                                   dependants and all
                                                                   the dependencies
                                                                   needed by the
                                                                   dependants.

                result: []

            - self.generate_object('CMa_g2', True, True, True) -> generate the 
                                                                  'CMa_g2', all its
                                                                  dependencies, all
                                                                  its dependants and
                                                                  all the dependencies
                                                                  needed by the 
                                                                  dependents.

                result: []

        """

        toGenerate = [nodePath]
        if withDependants:
            toGenerate += self.traverse(nodePath, "dependants")
        if withDependencies:
            directDependencies = self.traverse(nodePath, "dependencies")
            toGenerate += directDependencies
            if withDependantsDependencies:
                allDependencies = self.sort_all_dependencies(nodePath)
                toGenerate += allDependencies
        generateSet = set(toGenerate)
        return list(generateSet)

    @log_calls
    def sort_all_dependencies(self, nodePath):
        allDependencies = []
        directDependencies = self.traverse(nodePath, "dependencies")
        allDependencies += directDependencies
        otherDependencies = []
        dependants = self.traverse(nodePath, "dependants")
        for dependant in dependants:
            secondaryDependencies = self.traverse(nodePath, "dependencies")
            for dep in secondaryDependencies:
                if dep not in directDependencies + dependants and \
                   dep not in otherDependencies:
                    otherDependencies.append(dep)
        allDependencies += otherDependencies
        return allDependencies

    @log_calls
    def cancel_nodes(self, nodePaths=None, statuses=("unknwon",), recursive=False):
        """
        Cancel the nodes whose status match the input 'statuses'.

        Inputs:
            nodePaths - A list of strings specifying the nodes to be canceled.
            statuses - An iterable of strings with the full names of the
                     statuses that are to be used as a match for finding nodes
                     to cancel.
            recursive - A boolean specifying if the cancel operation is to be
                        extended to each node's parent families.
        """

        if nodePaths is None:
            nodePaths = self.traverse_nodes(self.suiteNode.childNodes)[0]
        for nodePath in nodePaths:
            path = "/%s" % nodePath
            pathStatus = self.get_node_status(path)
            if pathStatus in statuses:
                self.cancel_node(path)
            if recursive:
                path = path.rpartition("/")[0]
                while path != "":
                    pathStatus = self.get_node_status(path)
                    if pathStatus in statuses:
                        self.cancel_node(path)
                    path = path.rpartition("/")[0]

    @log_calls
    def cancel_node(self, nodePath):
        """
        Run an external CDP command to cancel the node.

        Inputs:
            nodePath - A string specifying the CDP path to the node.

        Returns: the return code of the external CDP process.
        """

        cdpCancelCommand = 'cancel -yf %s' % nodePath
        stdoutList, stderrList, returnCode = utils.run_cdp_command(
                self.cdpAlias, cdpCancelCommand)
        return returnCode

    @log_calls
    def get_node_status(self, nodePath):
        """
        Run an external CDP command to get the status of a node.

        Inputs:
            nodePath - A string specifying the CDP path to the node.

        Returns: The status of the input nodePath, or None.
        """

        cdpStatusCommand = 'status -m full %s' % nodePath
        stdoutList = utils.run_cdp_command(self.cdpAlias, cdpStatusCommand)[0]
        statusLine = stdoutList[2]
        foundStatus = re.search(r"[[{][a-z]+ *[]}]", statusLine)
        if foundStatus is not None:
            pathStatus = foundStatus.group()[1:-1].strip()
        else:
            pathStatus = None
        return pathStatus
