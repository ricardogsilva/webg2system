#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

import re
import shutil
import glob
import logging
import os
import subprocess
from xml.dom import minidom
import datetime as dt
from random import randint # for creating unique working dirs

# this package's specific imports
import utilities
from g2item import G2Item
import factories
#from filecreator import file_creator
from g2errors import CorruptedBZipFileError
from g2suiteparser import G2SuiteParser
import packagecreator as pc
from decorators import log_calls

# TODO 
#
# - Test the fetch* methods of FetchData and G2Package. This is mainly testing 
#   of the more general fetch_files() method on the FetchData class.
#
# - Implement a send_files() method to allow sending of arbitrary g2files to 
#   another host. It should be similar in concept to fetch_files().
#   Implement send_inputs() and send_outputs() methods on top of it.
#
# - Implement a delete_files() method to allow deletion of arbitrary g2files 
#   and implement a delete_outputs() on top of it.
#
# - Is a _decompress_files() method really necessary, or should it just call
#   the host's method when needed?
#
# - Is a delete_output_dir() method really necessary? Maybe the package
#   should just call the _delete_directories() when needed...
#
# - Implement the pcfSettings and acfSettings attributes on the G2Package class
#
# - Test the write_pcf() method of the G2Package class

# Package - A generic package class with
#       attributes:
#           - logger
#           - name, 
#           - source, 
#           - timeslot, 
#           - host, 
#           - outputDir
#           - inputs
#           - outputs
#       methods:
#           - add_inputs/remove_inputs, etc
#           - find_inputs/find_outputs
#           - fetch_files
#           - send_files

# FetchData - Inherits from Package and adds:
#       methods:
#           - fetch_inputs/fetch_outputs

# ExternalCodePackage - Inherits from Package and adds:
#       attributes:
#           - workingDir
#           - version
#           - codeName
#           - codeDir
#       methods:
#           - 

class FetchData(G2Item):

    inputs = []
    outputs = []
    optionalInputs = []
    optionalOutputs = []

    #@log_calls
    def __init__(self, name, source, timeslot, host):
        '''
        Inputs:

            name - The package's name.

            source - A G2Source object.

            timeslot - A datetime.datetime object.

            host - A G2Host object.
        '''

        super(FetchData, self).__init__(name, timeslot, source)
        self.host = host
        self.logger = logging.getLogger(self.__class__.__name__)
        packSettings = utilities.get_package_details(self.name)
        self.outputDir = utilities.parse_marked(packSettings['outputDir'], self)
        self.inputs, self.optionalInputs = self._create_files('inputs')
        self.outputs, self.optionalOutputs = self._create_files('outputs')

    #@log_calls
    def add_input(self, g2Input, optional):
        self._act_upon_g2file(g2Input, 'inputs', 'append')
        if optional:
            self._act_upon_g2file(g2Input, 'optionalInputs', 'append')

    #@log_calls
    def remove_input(self, g2Input):
        self._act_upon_g2file(g2Input, 'inputs', 'remove')
        if g2Input in self.optionalInputs:
            self._act_upon_g2file(g2Input, 'optionalInputs', 'remove')

    #@log_calls
    def add_output(self, g2Output, optional):
        self._act_upon_g2file(g2Output, 'outputs', 'append')
        if optional:
            self._act_upon_g2file(g2Output, 'optionalOutputs', 'append')

    #@log_calls
    def remove_output(self, g2Output):
        self._act_upon_g2file(g2Output, 'outputs', 'remove')
        if g2Output in self.optionalOutputs:
            self._act_upon_g2file(g2Output, 'optionalOutputs', 'remove')

    #@log_calls
    def ensure_dirs(self, *dirlist):
        for directory in dirlist:
            if not self.host.is_dir(directory):
                self.host.make_dir(directory)

    #@log_calls
    def _act_upon_g2file(self, g2File, fileRole, action):
        eval('self.%s.%s(g2File)' % (fileRole, action))
        if action == 'append':
            g2File.package = self
        elif action == 'remove':
            g2File.package = None

    #@log_calls
    def _create_files(self, fileRole):
        '''
        Create the default files as defined in the settings file.

        This method creates G2File instances and adds them to this package
        under its 'inputs' or 'outputs' attribute.
        This method is temporary, as it should become useless once this
        app is converted to django (a plan for the future).

        Inputs:

            fileRole - A string which can be either 'inputs' or 'outputs'.
                It specifies what type of files are to be created.
        '''
        
        g2fList = []
        optionalList = []
        filesParamList = utilities.get_package_details(self.name)[fileRole]
        for fileDict in filesParamList:
            self.logger.debug('Creating %s...' % fileDict['name'])
            timeslotsToCreate = self._sort_file_timeslots(fileDict)
            sourcesToCreate = self._sort_file_sources(fileDict)
            for timeslotSTR in timeslotsToCreate:
                for source, area in sourcesToCreate:
                    newFile = factories.create_file(fileDict['name'], 
                                                    timeslotSTR, source, area,
                                                    None)
                    if newFile is not None:
                        g2fList.append(newFile)
                        if fileDict['optional']:
                            optionalList.append(newFile)
                    else:
                        self.logger.error("Couldn't create %s object." \
                                          % fileDict['name'])
        return g2fList, optionalList

    #@log_calls
    def _sort_file_timeslots(self, fileSettings):
        '''
        Returns a list of timeslot strings for the files that are about to be 
        created.
        '''

        timeslots = []
        timeslotAds = fileSettings['timeslotAdjustments']
        if len(timeslotAds) != 0:
            for tsDict in timeslotAds:
                adjustUnit = tsDict['unit'] 
                adjustValue = tsDict['displace'] 
                if adjustUnit == 'minute':
                    delta = dt.timedelta(minutes=adjustValue)
                elif adjustUnit == 'hour':
                    delta = dt.timedelta(hours=adjustValue)
                elif adjustUnit == 'day':
                    delta = dt.timedelta(days=adjustValue)
                else:
                    delta = dt.timedelta()
                newTimeslot = self.timeslot + delta
                timeslots.append(newTimeslot.strftime('%Y%m%d%H%M'))
        else:
            timeslots.append(self.timeslot.strftime('%Y%m%d%H%M'))
        return timeslots

    #@log_calls
    def _sort_file_sources(self, fileSettings):
        '''
        Returns a list of sources for the files that are about to be created.
        '''

        packDetails = utilities.get_package_details(self.name)
        sources = []
        if len(fileSettings['sources']) != 0:
            for sourceTup in fileSettings['sources']:
                source, area = sourceTup
                sources.append((source, area))
        else:
            #apply only one source with defaultSource and defaultArea
            sources.append((modeDetails['defaultSource'], 
                            modeDetails['defaultArea']))
        return sources

    
    #@log_calls
    def find_files(self, g2files, hostName=None, useArchive=None):
        '''
        Inputs:

            g2files - A list of g2file instances

            hostName - A string with the host's name. A value of None (the
                default) will use each file's default host.

            useArchive - A string indicating what kind of file is to be
                searched for in the archives. Accepted values are 'inputs'
                and 'outputs'. A value of None (the default) causes the
                archives not to be searched at all.

        Returns:
            A dictionary with the input g2files as keys and another 
            sub-dictionary as values. This sub-dictionary contais a 'paths' 
            key with a list of strings with full file paths as values and 
            another key 'host', with the name of the host where the files have
            been found as values. If a g2file was not found in any of the given
            hostNames, the corresponding value for its key will be None.
        '''

        result = dict()
        for g2f in g2files:
            self.logger.info('Looking for %s...' % g2f.name)
            result[g2f] = g2f.find(hostName, useArchive)
        return result

    #@log_calls
    def find_inputs(self, hostName=None, useArchive=False):
        '''
        Look for this package's inputs.

        Inputs:

            hostName - A string specifying the name of a host in which to
                search the inputs. A value of None (the default) will use
                each input's default host.

            useArchive - A boolean indicating if the files are to be searched
                for in the archvies, in case they cannot be found in host.

        Returns:

            A dictionary with the package's inputs as keys and
            sub-dictionaries as values. These sub-diciotnaries have
            two keys: 'host' and 'paths' and specify the name of the host
            where the files have been found and the full paths to the files.
        '''

        if useArchive:
            useArchive = 'inputs'
        else:
            useArchive = None
        return self.find_files(self.inputs, hostName, useArchive)

    #@log_calls
    def find_outputs(self, useArchive=False):
        if useArchive:
            useArchive = 'outputs'
        else:
            useArchive = None
        return self.find_files(self.outputs, None, useArchive)

    #@log_calls
    def _get_relative_path(self, fullPath):
        '''Return a path's relative path.'''

        relPath = fullPath.replace(self.host.basePath + os.path.sep, '')
        return relPath

    #@log_calls
    def fetch_files(self, g2files, relTargetDir, hostName=None,
                    useArchive=None, forceCopy=False, decompress=False):
        '''
        Fetch the input g2files from their destination to relTargetDir.

        If a file is on a remote host, it will always be copied to the target
        directory, regardless of its compression state. If a file is on a
        local host and it is compressed it will also always get copied over
        to the target directory, regardless of it being decompressed
        afterwards or not. The decompression of files is always done after 
        copying them to the target directory and can be controlled by the
        'decompress' argument. If a file is on a local host and it is not
        compressed, it may be copied to the target dir or left at its original
        location, depending on the value of the 'forceCopy' argument.

        Inputs:

            g2files - A list of G2File instances specifying the files that
                are to be fetched.

            relTargetDir - The relative (relative to the host) path to the
                directory, where files should be placed if they were
                originally in a compressed form.

            hostName - A string with the names of a G2Host where the files 
                are to be copied from.

            <------
            useArchive - A boolean indicating if the files are to be searched
                for in the archives, in case they cannot be found in host.
                ------->

            forceCopy - A boolean indicating if the files should be copied
                to the target directory even if they are not compressed. The
                default is False.

            decompress - A boolean indicating if the files should be
                decompressed after being copied to the target directory.
                The default is False.

        Returns:
            A dictionary with the input g2files as keys and a sub-dictionary
            as values. This sub-dictionary contains...
        '''

        for g2f in g2files:
            paths = g2f.fetch(relTargetDir, hostName, useArchive=useArchive,
                              forceCopy=forceCopy)
            if decompress:
                relPaths = [self._get_relative_path(p) for p in paths]
                paths = self._decompress_files(relPaths)
            return paths

    #@log_calls
    def _decompress_files(self, pathList):
        '''
        Decompress the files in pathList and return their new path.
        '''

        return self.host.decompress(pathList)

    #@log_calls
    def fetch_inputs(self, hostName=None, useArchive=False):
        self.ensure_dirs(self.outputDir)
        fetchedFiles = self.fetch_files(self.inputs, self.outputDir, hostName,
                                        useArchive, forceCopy=True, 
                                        decompress=False)

    #@log_calls
    def send_outputs(self, relTargetDir, destHost):
        '''
        Copy this package's outputs to another directory at the specified host.

        Inputs

            relTargetDir - The relative path to a destination directory where
                the files will be copied to.

            destHost - A G2Host object.
        '''

        #return self._fetch_files('outputs', relTargetDir)
        raise NotImplementedError

    #@log_calls
    def delete_outputs(self):
        '''
        Delete this package's outputs from their final output directories.

        This method can be overriden by specialized classes in order to
        introduce some filtering mechanism to allow the deleting of only
        a subset of the outputs.
        '''

        absolutePaths = self.find_outputs()
        for absPath in absolutePaths:
            relPath = self._get_relative_path(absPath)
            self.host.delete_file(relPath)

    #@log_calls
    def _delete_directories(self, *leafDirs):
        '''
        Recursively delete leafDirs and any empty parent directories.

        Inputs:

            leafDirs - A list of strings with the relative paths to the
                leaf directories to delete.
        '''

        # not done yet, I guess it is not really recursive
        for leafDir in leafDirs:
            self.host.remove_dir(leafDir)

    #@log_calls
    def delete_output_dir(self):
        return self._delete_directories(self.outputDir)

    #@log_calls
    def package_can_be_processed(self, useArchive=False):
        '''
        Determine if the available files are enough for processing.

        Inputs:

            useArchive - A boolean indicating if the files are to be searched
                for in the archvies, in case they cannot be found in host.

        Returns:

            A boolean indicating if all the required inputs are available for
            further fetching and processing.
        '''

        found = self.find_inputs(useArchive=useArchive)
        result = True
        for g2f, foundDict in found.iteritems():
            self.logger.info('Evaluating %s...' % g2f.name)
            if g2f not in self.optionalInputs:
                # this g2file is mandatory
                self.logger.info('%s is a mandatory file' % g2f.name)
                if foundDict is None:
                    self.logger.info('Couldn\'t find %s' % g2f.name)
                    result = False
        return result



class G2Package(FetchData):
    '''
    ...
    '''

    #@log_calls
    def __init__(self, name, source, timeslot, host):
        super(G2Package, self).__init__(name, source, timeslot, host)
        #self.logger = logging.getLogger(self.__class__.__name__)
        packSettings = utilities.get_package_details(self.name)
        self.version = packSettings.get('version')
        externalCodeSettings = packSettings.get('externalCode')
        self.codeName = externalCodeSettings['codeName']
        self.workingDir = utilities.parse_marked(packSettings['workingDir'], self)
        self.workingDir = os.path.join(self.workingDir, 'wd_%i' % randint(1, 100))
        self.codeDir = utilities.parse_marked(externalCodeSettings['codeDir'], self)
        self.staticOutputDir = utilities.parse_marked(staticOutputDir, self)

    #@log_calls
    def fetch_inputs(self, useArchive=None, forceCopy=False, decompress=False):
        # This method is needed because the base class has no working dir
        # it just copies the files to the output dir
        self.ensure_dirs(self.workingDir)
        return self.fetch_files(self.inputs, self.workingDir, 
                                useArchive=useArchive, forceCopy=forceCopy,
                                decompress=decompress)

    #@log_calls
    def fetch_outputs(self, useArchive=None, forceCopy=False, decompress=False):
        # This method is needed because the base class has no working dir
        # it just copies the files to the output dir
        self.ensure_dirs(self.workingDir)
        return self.fetch_files(self.outputs, self.workingDir, 
                                useArchive=useArchive, forceCopy=forceCopy,
                                decompress=decompress)

    #@log_calls
    def write_pcf(self, paths, g2InputFiles=None, g2OutputFiles=None, 
                  outputDirs=None):
        '''
        Write the Product Configuration File.

        Inputs:

            paths - A list of strings with the full paths to the files
                that are to be written in the Product Configuration File as
                inputs.

            g2InputFiles - A list with g2file objects whose paths are to be 
                written in the PCF. A value of None uses all the paths 
                specified in the 'paths' argument.

            g2OutputFiles - A list with g2file objects whose paths are to be
                written in the PCF. A value of None uses all of the instance's
                outputs.

            outputDir - A string with the relative path (relative to 
                this package's host's basepath) with the output directory to
                be used in the PCF. A value of None (the default) will use
                an 'output' subdirectory inside the package's 'workingDir'.

        Returns:

            The full path to the newly written Product Configuration File.
        '''


        if outputDir is None:
            outputDir = os.path.join(self.workingDir, 'output')
        if g2InputFiles is not None:
            inputPaths = []
            for path in paths:
                for g2f in g2InputFiles:
                    if g2f.is_file(path):
                        inpObj = inp
                        inputPaths.append(path)
                        break
        else:
            inputPaths = paths
        fileContents = '&NAM_ALG_MODES\n'
        fileContents += 'MODE = %s\n/\n' % (self.pcfSettings["mode"]) # the pcfSettings attribute hasn't been defined yet
        fileContents += '&NAM_ALG_INPUT_FILES_PATH\n'
        fileContents += 'YFILEINP=' 
        for path in inputPaths:
            fileContents += "'%s',\n" % path
        fileContents = fileContents[:-2] #trimming the last newline and comma
        fileContents += "\n/\n"
        fileContents += "&NAM_ALG_OUTPUT_FILES_PATH\n"
        fileContents += "YFILEOUT = "
        if g2OutputFiles is None:
            g2OutputFiles = self.outputs
        for out in g2OutputFiles:
            namePattern = out.searchPaterns[0]
            if namePattern.endswith('.*'):
                namePattern = namePattern[:-2]
            fileContents += "'%s',\n" % (os.path.join(self.host.basePath, 
                                         outputDir, namePattern))
        fileContents = fileContents[:-2]
        fileContents += "\n/\n"
        fileContents += "&NAM_STOP_STATUS_RETRIEVAL_FREQ\n"
        fileContents += "YFREQINSECS = %s\n" % (self.pcfSettings["stopStatusRetFreq"])
        fileContents += "/\n"
        pcfRelPath = os.path.join(self.workingDir, 'productConfigurationFile')
        pcfFullPath = self.host.create_file(pcfRelPath, fileContents)
        return pcfFullPath


    
#class G2Package(G2Item):
#    """
#    This class holds the implementation of the fetchData packages and
#    also serves a a general base class for other more specialized tasks.
#    """
#
#    def __init__(self, xmlSettings, timeslot, mode, area, suiteName,
#                 version=None):
#        """
#        Inputs: xmlSettings - An XML Node object containing all the relevant
#                              settings for the package being created. This
#                              XML extract comes from the packageSettings.xml
#                              file.
#                timeslot - A datetime.datetime object that holds the timeslot
#                mode - The specific mode the package is to be run
#                area -
#                suiteName - 
#                version - The version of the package that is to be run
#        """
#
#        G2Item.__init__(self, xmlSettings, timeslot, area)
#        self.logger = logging.getLogger("G2ProcessingLine.G2Package")
#        self.SMSSuite = suiteName
#        self.modeXML = utilities.find_xml_element(xmlSettings.getElementsByTagName("modes")[0], 
#                                              "mode", "name", mode)
#        self.mode = self.modeXML.getAttribute("name")
#        versionListEl = self.modeXML.getElementsByTagName("versions")[0]
#        if not version or version == 'current':
#            for versionEl in versionListEl.getElementsByTagName("version"):
#                if versionEl.getAttribute("status") == "current":
#                    self.version = versionEl.getAttribute("number")
#        else:
#            self.version = version
#        self.codeMainDir = self.parse_path_element(self.modeXML.getElementsByTagName("codeMainDir")[0], self)
#        self.workingDir = self.parse_path_element(self.modeXML.getElementsByTagName("workingDir")[0], self, "data")
#        self.tempOutDir = os.path.join(self.workingDir, "output")
#        outputDirsEl = self.modeXML.getElementsByTagName("outputDirs")[0]
#        self.outputDir = self.parse_path_element(outputDirsEl.getElementsByTagName("outputDir")[0], self, "data")
#        versionXML = utilities.find_xml_element(versionListEl, "version", "number", self.version)
#        self.logger.debug("self.version: %s" % self.version)
#        self.logger.debug("versionXML: %s" % versionXML)
#        self.inputs = self._create_files(versionXML.getElementsByTagName("inputs")[0], "input")
#        self.outputs = self._create_files(versionXML.getElementsByTagName("outputs")[0], "output")
#        #self.clean_up()
#        for dirString in self.workingDir, self.outputDir, self.tempOutDir:
#            if dirString != "":
#                self._create_dir_tree(dirString)
#
#        self.logger.debug("--- PACKAGE SETTINGS ---")
#        self.logger.debug("self.name: %s" % self.name)
#        self.logger.debug("self.modeXML: %s" % self.modeXML)
#        self.logger.debug("self.timeslot: %s" % self.timeslot)
#        self.logger.debug("self.version: %s" % self.version)
#        self.logger.debug("self.codeMainDir: %s" % self.codeMainDir)
#        self.logger.debug("self.workingDir: %s" % self.workingDir)
#        self.logger.debug("self.outputDir: %s" % self.outputDir)
#        self.logger.debug("self.inputs: %s" % [inp.name for inp in self.inputs])
#        self.logger.debug("self.outputs: %s" % [out.name for out in self.outputs])
#        self.logger.debug("------------------------")
#
#    def clean_output_dir(self):
#        """
#        Delete the files inside the outputDir.
#
#        Only the files that are outputs of this package and whose 'frequency'
#        property is 'dynamic' get deleted.
#        """
#
#        self.logger.debug("clean_output_dir method called")
#        allThere, outputDict = self.find_outputs()
#        for outpObj, fileList in outputDict.iteritems():
#            self.logger.debug("output: %s" % outpObj.name)
#            if outpObj.frequency == "dynamic":
#                for filePath in fileList:
#                    self.logger.debug("filepath: %s" % filePath)
#                    self.logger.debug("deleting...")
#                    os.remove(filePath)
#        self.logger.debug("clean_output_dir method exiting")
#
#    def clean_up(self):
#        """
#        Scan the workingDir tree and the outputDir tree and remove all
#        unnecessary files and directories.
#        """
#
#        self.logger.debug("clean_up method called.")
#        self._clean_working_dir()
#        self._remove_empty_dirs()
#        self.logger.debug("clean_up method exiting.")
#
#    def decompress(self, fileDict):
#        """
#        Decompress the files using the external bunzip2 program.
#
#        Returns: a dictionary 
#        """
#
#        self.logger.debug("decompress method called")
#        newFileDict = dict()
#        for fileObj, localFileList in fileDict.iteritems():
#            newFileDict[fileObj] = []
#            for path in localFileList:
#                self.logger.debug("path: %s" % path)
#                if path.endswith(".bz2"):
#                    self.logger.debug("decompressing...")
#                    bunzipCommand = ["bunzip2", "-f", path]
#                    newProcess = subprocess.Popen(bunzipCommand)
#                    result = int(newProcess.wait())
#                    if result == 2:
#                        raise CorruptedBZipFileError(path, fileObj)
#                    else:
#                        newFileDict[fileObj].append(path.replace(".bz2", ""))
#                else:
#                    newFileDict[fileObj].append(path)
#        self.logger.debug("newFileDict: %s" % newFileDict)
#        self.logger.debug("decompress method exiting")
#        return newFileDict
#
#    def fetch_inputs(self, inputLocations):
#        """
#        Get the local paths for all the available inputs.
#
#        Inputs: inputLocations - a dictionary with G2File instances as keys
#                                 and lists to their fullpaths as values, as
#                                 returned by the find_inputs method.
#
#        Returns: a dictionary with G2File instances as keys and their
#        corresponding local path as values.
#
#        The returned dictionary contains only records for the inputs that
#        are available.
#        """
#
#        self.logger.debug("fetch_inputs method called.")
#        okFiles = dict()
#        for inp, pathList in inputLocations.iteritems():
#            self.logger.debug("inp: %s" % inp.name)
#            try:
#                self.logger.debug("fetching %s files..." % inp.name)
#                localPathList = inp.fetch(pathList)
#                #localPathList = []
#                #for path in pathList:
#                #    localPathList.append("%s/%s" % (self.workingDir, os.path.basename(path)))
#                okFiles[inp] = localPathList
#            except:
#                self.logger.debug("something went wrong with the fetching of the %s files" % inp.name)
#        self.logger.debug("okFiles: %s" % okFiles)
#        self.logger.debug("fetch_inputs method exiting.")
#        return okFiles
#        
#    def find_inputs(self):
#        """
#        Search for the inputs at their designated paths.
#
#        Returns: A tuple: A Boolean indicating if all the expected files have
#                 been found; A dictionary with G2File instances as keys and
#                 lists of fullpaths to the corresponding files as values; An
#                 integer specifying how many files have been found.
#        """
#
#        self.logger.debug("find_inputs method called")
#        allPresent = True
#        availableFiles = dict()
#        for inp in self.inputs:
#            self.logger.debug("inp: %s" % inp.name)
#            allInp, availableFiles[inp] = inp.find()
#            if not allInp:
#                allPresent = False
#        totalFiles = 0
#        for fileList in availableFiles.itervalues():
#            totalFiles += len(fileList)
#        self.logger.debug("find_inputs method exiting")
#        return (allPresent, availableFiles, totalFiles)
#
#    def find_outputs(self):
#        """
#        Search for the outputs at their designated paths.
#
#        Returns: A tuple: A Boolean indicating if all the expected files have
#                 been found; A dictionary with G2File instances as keys and 
#                 lists of fullpaths to the corresponding files as values.
#        """
#
#        self.logger.debug("find_outputs method called")
#        allPresent = True
#        availableFiles = dict()
#        for outp in self.outputs:
#            self.logger.debug("outp: %s" % outp.name)
#            allOutp, availableFiles[outp] = outp.find()
#            if not allOutp:
#                allPresent = False
#        self.logger.debug("find_outputs method exiting")
#        return (allPresent, availableFiles)
#
#    def get_inputs(self, inputLocations, tryArchive=False):
#        #FIXME - something must be done about the so called quasi-static files, that
#        # are currently marked as just 'static', which prevents their fetching
#        # from the archive.
#
#        """
#        Get the inputs for this package and decompress them, if needed.
#
#        Inputs: inputLocations - a dictionary with G2File instances as keys
#                                 and lists to their fullpaths as values, as
#                                 returned by the find_inputs method.
#                tryArchive - A boolean. If True, the inputs will be searched
#                             for in the archives and fetched accordingly.
#
#        Returns:
#
#        This method encapsulates the 'fetch_inputs' and 'decompress' methods
#        in a single function, in order to simplify the usage.
#        """
#
#        self.logger.debug("get_inputs method called.")
#        okFiles = self.fetch_inputs(inputLocations)
#        if tryArchive:
#            missingInputs = [k for k, v in okFiles.iteritems() \
#                             if len(v) == 0]
#            self.logger.debug("Couldn't fetch the inputs %s. Trying the archives..." \
#                             % [i.name for i in missingInputs])
#            archiveDict = utilities.find_inputs_in_archive(self)
#            archFetchList = []
#            for inp in missingInputs:
#                if inp.fetchFromArchive:
#                    archiveInp = archiveDict.get(inp)
#                    self.logger.debug("archiveInp: %r" % list(archiveInp))
#                    if archiveInp[0]:
#                        self.logger.info("Found %s in the archive." % inp.name)
#                        archFetchList.append((inp, archiveInp[1], archiveInp[2]))
#                    else:
#                        self.logger.info("Couldn't find %s in the archive." % inp.name)
#                else:
#                    self.logger.info("%s is marked as noArchiveFetch in the xml settings. Skipping...")
#            self.logger.info("archFetchList: %s" % archFetchList)
#            okFiles.update(utilities.fetch_inputs_from_archive(archFetchList))
#        else:
#            okFiles = compressedFiles
#        self.logger.debug("----------")
#        self.logger.debug("okFiles:\n%s" % okFiles)
#        decompressedFiles = self.decompress(okFiles)
#
#            
#
#        self.logger.debug("get_inputs method exiting.")
#        return decompressedFiles
#
#
#    def run(self, fileDict):
#        """
#        Copy the fetched files from the working directory to the final output directory.
#
#        Inputs: fileDict - a dictionary containing G2File instances as keys and lists with
#                           the path of the correspondent files on the workingDir, as
#                           returned by the 'decompress' method
#        Returns: A two element tuple. The first element is an integer, 
#                 indicating the exit status of the operation (zero means 
#                 sucess). The second element is a list with output messages.
#        """
#
#        self.logger.debug("run method called")
#        for fileObj, fileList in fileDict.iteritems():
#            newDateTimeSubDir = fileObj.timeslotDT.strftime("%Y/%m/%d")
#            for file in fileList:
#                self.logger.debug("file: %s" % file)
#                oldDateTimeSubDir = re.search(r"[0-9]{4}/[0-9]{2}/[0-9]{2}", file)
#                if oldDateTimeSubDir:
#                    # to cope with the fact that some input files (LANDSAT RAD, LANDSAT VZA, ...)
#                    # may have a different timeslot than the package's own timeslot
#                    # and the final output directory must take this into account
#                    finalDir = self.outputDir.replace(oldDateTimeSubDir.group(), newDateTimeSubDir)
#                else:
#                    finalDir = self.outputDir
#                self._create_dir_tree(finalDir)
#                fileName = os.path.basename(file).split('.')[0]
#                self.logger.debug("fileName: %s" % fileName)
#                presentFileNames = [name.split('.')[0] for name in os.listdir(finalDir)]
#                self.logger.debug("presentFileNames: %s" % presentFileNames)
#                if fileName not in presentFileNames:
#                    self.logger.debug("moving %s to %s..." % (file, finalDir))
#                    shutil.move(file, finalDir)
#                else:
#                    self.logger.debug("no need to move %s to %s as the file is already present" % (file, finalDir))
#        self._delete_compressed_files(fileDict)
#        self.logger.debug("run method exiting")
#        return 0, [] # there should be a try... block enclosing the move operation
#
#    def _delete_compressed_files(self, fileDict):
#        """
#        For a file that came from the 'local' G2Host, if the file is in the
#        workingDir, it means it is also present in the original dir, but in
#        a compressed format. The fetchData package should delete these files.
#        """
#
#        self.logger.debug("_delete_compressed_files method called")
#        filesToDelete = []
#        for fileObj, fileList in fileDict.iteritems():
#            if fileObj.hosts[0].name == 'local':
#                for filePath in fileList:
#                    dirName, fName = os.path.split(filePath)
#                    if dirName == self.workingDir:
#                        # this file should be deleted from its original searchPath
#                        filesToDelete += [os.path.join(p, fName) + '.bz2' \
#                                for p in fileObj.hosts[0].searchPaths \
#                                if(os.path.isfile(os.path.join(p, fName) + '.bz2'))]
#        self.logger.debug("filesToDelete: %s" % filesToDelete)
#        for filePath in filesToDelete:
#            os.remove(filePath)
#        self.logger.debug("_delete_compressed_files method exiting.")
#
#    def write_config_files(self):
#        """
#        #TODO - Is this method necessary here?
#
#        Write the configuration files needed by the product's algorithm.
#        
#        Returns: a dictionary with keys 'productConfigurationFile' and
#                 'algorithmConfigurationFile' and the respective file
#                 paths as values.
#        """
#
#        self.logger.debug("write_config_files method called.")
#        pass
#        self.logger.debug("write_config_files method exiting.")
#
#    def _clean_working_dir(self):
#        """
#        Delete all files in the workingDir.
#        """
#
#        self.logger.debug("_clean_working_dir method called")
#        for path in glob.glob("%s/*" % self.workingDir):
#            if os.path.isfile(path):
#                os.remove(path)
#            elif os.path.isdir(path):
#                shutil.rmtree(path)
#        #shutil.rmtree(self.workingDir)
#        self.logger.debug("_clean_working_dir method exiting")
#
#    def _create_dir_tree(self, dirString):
#        """
#        Create the directory structure specified by the input string
#
#        Inputs: dirString - a string specifying the directory structure
#                            to create.
#        """
#
#        self.logger.debug("_create_dir_tree method called")
#        self.logger.debug("dirString: %s" % dirString)
#        if not os.path.isdir(dirString):
#            if os.path.isfile(dirString):
#                os.remove(dirString)
#            #os.makedirs(dirString)
#            mkdirCode = subprocess.call(["mkdir", "-p", dirString])
#            if mkdirCode != 0:
#                raise OSError
#        self.logger.debug("_create_dir_tree method exiting")
#        
#    def _create_files(self, filesParentNode, fileRole):
#        """
#        Compares each input defined in the package's xml settings
#        with the each input defined in the inputs's xml settings
#        and finds the xml settings of every input.
#
#        Inputs: inputsParentNode - an xml node that holds all the
#                                   inputs of the package, as returned
#                                   by the getElementsByTagName("inputs")[0]
#                                   function
#                fileRole - a string specifying the role of the G2File instance
#                           in this package. It can either be 'input' or
#                           'output'.
#
#        Returns: A list of G2File instances.
#
#        The matching of inputs' xml settings is done via its 'name' 
#        attribute, so care must be taken that each input has a unique 
#        name.
#        """
#
#        self.logger.debug("_create_files method called")
#        xmlDoc = minidom.parse(self.filesXMLFile)
#        fileList = []
#        for fileElement in filesParentNode.getElementsByTagName(fileRole):
#            for fileEl in xmlDoc.getElementsByTagName("file"):
#                if fileEl.getAttribute("name") == fileElement.getAttribute("name"):
#                    #fileList.append(file_creator(fileEl, self.timeslotDT, self))
#                    areaToCreate = fileElement.getAttribute("area")
#                    if areaToCreate:
#                        area = areaToCreate
#                    else:
#                        area = self.sourceObj.area
#                    optionalFile = fileElement.getAttribute("optional")
#                    if optionalFile.capitalize() == 'True':
#                        optional = True
#                    else:
#                        optional = False
#                    fileList += file_creator(fileEl, area, self.timeslotDT, self, fileRole, optional)
#        self.logger.debug("_create_files method exiting")
#        return fileList
#
#    def _remove_empty_dirs(self, extraDirsToRemove=[]):
#        """
#        Remove any empty directories.
#
#        Inputs: extraDirsToRemove - A list of strings specifying more
#                                    directories to remove, if they are
#                                    empty.
#        """
#
#        self.logger.debug("_remove_empty_dirs method called.")
#        for dirPath in [self.workingDir, self.outputDir] + extraDirsToRemove:
#            self.logger.debug("trying to remove %s" % dirPath)
#            try:
#                os.removedirs(dirPath)
#            except OSError: # the directory doesn't exist
#                pass
#                #self.logger.info("couldn't remove the empty dirs")
#        self.logger.debug("_remove_empty_dirs method exiting.")
#
#    def _sort_g2files(self, fileRole, g2FileNames):
#        """
#        Return a list of G2File instances that correspond to the files
#        that are to be processed.
#        """
#
#        self.logger.debug("_sort_g2files method called.")
#        g2Files = [f for f in self.inputs + self.outputs \
#                   if f.role == fileRole and \
#                   (f.name in g2FileNames or len(g2FileNames) == 0)]
#        self.logger.debug("_sort_g2files method exiting.")
#        return g2Files
#
#    def send(self, hostName, directory, fileRole="output", g2FileNames=[]):
#        """
#        Send this package's files to a directory on another host.
#
#        Inputs:
#            hostName - A string specifying the name of the host, as defined
#                       in the hostsettings.xml file.
#            directory - A string specifying the base directory on the host
#                        where the files are to be placed.
#            fileRole - A string specifying the role of the files to be sent
#                       according to this package. It can be either 'output'
#                       or 'input'.
#            g2FileNames - A list of strings specifying the names of the G2file
#                          instances that should be sent. If passed an empty
#                          list all the files are sent.
#
#        Returns: 0 in case of success and 1 in case something went wrong.
#
#        This method will sort the G2File instances that are to be sent and
#        then call their individual send() methods. 
#        """
#
#        # FIXME
#        # the 'directory' parameter needs to be better specified, maybe
#        # make it similar to each file's directory on the local host
#        self.logger.debug("send method called.")
#        g2Files = self._sort_g2files(fileRole, g2FileNames)
#        resultList = []
#        endResult = 1
#        for g2f in g2Files:
#            resultList.append(g2f.send(hostName, directory))
#        if not False in [i == 0 for i in resultList]:
#            endResult = 0
#        self.logger.debug("send method exiting.")
#        return endResult
#
#    def generate_quickviews(self, fileRole="output", g2FileNames=[]):
#        """
#        ...
#        """
#
#        self.logger.debug("generate_quickviews method called.")
#        g2Files = self._sort_g2files(fileRole, g2FileNames)
#        quickviews = []
#        for g2f in g2Files:
#            self.logger.debug("g2file: %s" % g2f.name)
#            try:
#                quickviews += g2f.generate_quickview()
#            except NotImplementedError:
#                self.logger.debug("Quickview generation is not implemented"
#                                  " for %s objects." \
#                                  % (g2f.__class__.__name__))
#        self.logger.debug("generate_quickviews method exiting.")
#        return quickviews
#
#    def generate_metadata(self, fileRole="output", g2FileNames=[],
#                          outputDir=None):
#        """
#        ...
#        """
#
#        self.logger.debug("generate_metadata method called.")
#        g2Files = self._sort_g2files(fileRole, g2FileNames)
#        metadatas = []
#        for g2f in g2Files:
#            self.logger.debug("g2file: %s" % g2f.name)
#            try:
#                metadatas += g2f.generate_metadata(outputDir)
#            except NotImplementedError:
#                self.logger.debug("Metadata generation is not implemented"
#                                  " for %s objects." \
#                                  % (g2f.__class__.__name__))
#        self.logger.debug("generate_metadata method exiting.")
#        return metadatas
#
#    def __repr__(self):
#        return "%s(name=%r, mode=%r, source=%r, timeslot=%r)" \
#                % (self.__class__.__name__, self.name, self.mode, 
#                   self.sourceObj, self.timeslot)
#
#
#class G2FetchDataDelayPackage(G2Package):
#    """
#    To accomodate for the fact that the LSASAF files are fetched with a delay,
#    - reassign the various time variables and the outputDir: 
#    - delete the directory specified in the old self.outputDir (if it is empty)
#    - create (if necessary) the new self.outputDir directory
#    """
#
#    def __init__(self, xmlSettings, timeslot, mode, area, suiteName,
#                 version=None):
#        """
#        ...
#        """
#
#        self.logger = logging.getLogger("G2ProcessingLine.G2FetchDataDelayPackage")
#        self.logger.debug("__init__method called")
#        G2Package.__init__(self, xmlSettings, timeslot, mode, area, suiteName,
#                           version=None)
#        newTimeslotDT = None
#        for inp in self.inputs:
#            if inp.timeslotDT != self.timeslotDT:
#                # timeslot needs updating, and so does the outputDir
#                newTimeslotDT = inp.timeslotDT
#        if newTimeslotDT:
#            self.logger.debug("Updating the outputDir to account for the delay...")
#            oldTimeslotDT = self.timeslotDT
#            self.update_timeslot_elements(newTimeslotDT)
#            outputDirEl = self.modeXML.getElementsByTagName("outputDirs")[0].getElementsByTagName("outputDir")[0]
#            newOutputDir = self.parse_path_element(outputDirEl, self, "data")
#            self._remove_empty_dirs()
#            self.outputDir = newOutputDir
#            for dirString in (self.workingDir, self.outputDir):
#                self._create_dir_tree(dirString)
#            self.update_timeslot_elements(oldTimeslotDT)
#        self.logger.debug("__init__ method exiting")
#
#
#class G2FetchDataStaticPackage(G2FetchDataDelayPackage):
#    """
#    ...
#    """
#
#    def fetch_inputs(self, availableInputs):
#        """
#        Check if the latest static inputs are already present. If not, fetch them
#
#        Inputs: availableInputs - a dictionary, as returned by the find_inputs method
#        """
#
#        self.logger.debug("fetch_inputs method called")
#        inputsToFetch = dict()
#        okFiles = dict()
#        allOutputs, availableOutputs = self.find_outputs()
#        fileMaps = {
#                "remote lsasaf lon" : "lsasaf lon",
#                "remote lsasaf lat" : "lsasaf lat"
#                }
#        inputFileName = None
#        outputFileName = None
#        for inp, inpFileList in availableInputs.iteritems():
#            self.logger.debug("inp.name: %s" % inp.name)
#            inputFileName = os.path.basename(inpFileList[0].split(".")[0])
#            outputName = fileMaps[inp.name]
#            for outp, outpFileList in availableOutputs.iteritems():
#                if len(outpFileList) > 0:
#                    if outp.name == outputName:
#                        outputFileName = os.path.basename(outpFileList[0].split(".")[0])
#                        self.logger.debug("inputFileName: %s" % inputFileName)
#                        self.logger.debug("outputFileName: %s" % outputFileName)
#                        inputTimeslot = utilities.extract_timeslot(inputFileName)
#                        outputTimeslot = utilities.extract_timeslot(outputFileName)
#                        self.logger.debug("inputTimeslot: %s" % inputTimeslot)
#                        self.logger.debug("outputTimeslot: %s" % outputTimeslot)
#                        if outputTimeslot >= inputTimeslot:
#                            self.logger.debug("There are no new files to fetch. Using the already present files.")
#                            inputsToFetch[outp] = outpFileList
#                        else:
#                            self.logger.debug("Need to fetch this file")
#                            inputsToFetch[inp] = inpFileList
#                else:
#                    self.logger.debug("Need to fetch this file")
#                    inputsToFetch[inp] = inpFileList
#        okFiles = G2Package.fetch_inputs(self, inputsToFetch)
#        self.logger.debug("fetch_inputs method exiting")
#        return okFiles
#
#
#class G2ProcessPackage(G2Package):
#    """
#    This class implements the pre-processing and processing tasks.
#    """
#
#    def __init__(self, xmlSettings, timeslot, mode, area, suiteName,
#                 version=None):
#        G2Package.__init__(self, xmlSettings, timeslot, mode, area, suiteName, 
#                           version)
#        self.logger = logging.getLogger("G2ProcessingLine.G2ProcessPackage")
#        pcfNl = self.modeXML.getElementsByTagName("productConfigurationFile")
#        if pcfNl:
#            self.pcfSettings = {
#                    "mode" : pcfNl[0].getAttribute("mode"),
#                    "stopStatusRetFreq" : pcfNl[0].getAttribute("stopStatusRetFreq")
#                    }
#        acfNl = self.modeXML.getElementsByTagName("algorithmConfigurationFileLocation")
#        if len(acfNl) != 0:
#            self.acfSettings = self.parse_marked_element(acfNl[0], self)
#            self.acfFileName = os.path.basename(self.acfSettings)
#
#    def run(self, configFiles):
#        """
#        Run the external application that pre-processes the data.
#
#        Inputs: configFiles - a dictionary with keys: 
#                        - "AlgorithmConfigurationFile";
#                        - "ProductConfigurationFIle" 
#                        and values:
#                            - a string indicating the path to the Product
#                            Configuration File.
#                            - a string indicating the path to the algorithm
#                            Configuration File.
#
#        Returns: an integer specifying the return code of the external Fortran
#                 pre-processor algorithm.
#        """
#
#        self.logger.debug("run method called")
#        commandList = [
#               "./wrapper_g2.exe", 
#                configFiles["ProductConfigurationFile"], 
#                configFiles["AlgorithmConfigurationFile"]]
#        exitCode, outputLines = self._run_external_algorithm(commandList)
#        if exitCode == 0:
#            #the algorithm ran successfully
#            self._create_dir_tree(self.outputDir)
#            self._move_outputs_to_final_dir()
#        self.logger.debug("run method exiting")
#        return exitCode, outputLines
#
#    def write_config_files(self, okFiles, acfReplaceList=[]):
#        """
#        ...
#        """
#
#        self.logger.debug("write_config_files method called")
#        configFiles = {
#                "ProductConfigurationFile" : self._write_pcf(okFiles),
#                "AlgorithmConfigurationFile" : self._write_acf(acfReplaceList)}
#        self.logger.debug("write_config_files method exiting")
#        return configFiles
#
#    def _change_search_pattern(self, G2File, pattern):
#        """
#        Change the pattern string into a new one.
#
#        Inputs:
#
#        Returns: The default implementation just returns the 'pattern' string
#                 input.
#
#        This method's purpose is to allow the changing of the search pattern
#        that gets written to the Product Configuration File for the special
#        cases when this pattern must be different. The concrete application
#        of this is in the 'G2NGP2Grid' class.
#        """
#
#        self.logger.debug("_change_search_pattern method called.")
#        self.logger.debug("_change_search_pattern method exiting.")
#        return pattern
#
#    def _run_external_algorithm(self, commandList):
#        """
#        ...
#        """
#
#        self.logger.debug("_run_external_algorithm method called.")
#        thisDir = os.getcwd()
#        algVersionDir = "%s/%s_v%s" % (self.codeMainDir, self.name, self.version)
#        self.logger.debug("algVersionDir: %s" % algVersionDir)
#        os.chdir(algVersionDir)
#        self.logger.info("will run %s algorithm version %s" % (self.name, self.version))
#        self.logger.debug("currently on: %s" % os.getcwd())
#        newProcess = subprocess.Popen(commandList, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
#        outputLines = []
#        running = True
#        while running:
#            outputLine = newProcess.stdout.readline().strip()
#            if outputLine:
#                self.logger.info(outputLine)
#                outputLines.append(outputLine)
#            else:
#                running = False
#        newProcess.stdin.close()
#        #result = newProcess.communicate()[0].split("\n")
#        #exitCode = int(newProcess.poll())
#        exitCode = int(newProcess.wait())
#        #for line in result:
#        #    self.logger.info(line)
#        os.chdir(thisDir)
#        self.logger.debug("_run_external_algorithm method exiting.")
#        return exitCode, outputLines[-10:]
#
#    def _write_pcf(self, okFiles):
#        """
#        Write the ProductConfigurationFile for the external algorithm.
#
#        Inputs: okFiles - a dictionary with G2File objects that represent
#                          the available and already prepared inputs for 
#                          the execution of this package as keys, and
#                          lists with the paths to these files as values.
#        
#        Returns: a string indicating the full path to the newly created
#                 file.
#
#        The product configuration file of the pre-processing packages
#        is only a file with a list of the inputs
#        """
#
#        self.logger.debug("_write_pcf method called.")
#        pcfPath = "%s/ProductConfigurationFile" % self.workingDir
#        self.logger.debug("ProductConfigurationFile path: %s" % pcfPath)
#        fileContents = "&NAM_ALG_MODES\n"
#        fileContents += "MODE = %s\n/\n" % (self.pcfSettings["mode"]) 
#        fileContents += "&NAM_ALG_INPUT_FILES_PATH\n"
#        fileContents += "YFILEINP=" 
#        for (inputObj, pathList) in okFiles.iteritems():
#            for path in pathList:
#                fileContents += "'%s',\n" % path
#        fileContents = fileContents[:-2] #trimming the last newline and comma
#        fileContents += "\n/\n"
#        fileContents += "&NAM_ALG_OUTPUT_FILES_PATH\n"
#        fileContents += "YFILEOUT = "
#        for fileObj in self.outputs:
#            if "quickview" not in fileObj.name:
#                namePattern = fileObj.searchPattern
#                if namePattern.endswith("*"):
#                    namePattern = namePattern[:-1] # trimming the last '*' sign
#                    namePattern = self._change_search_pattern(fileObj, namePattern)
#                fileContents += "'%s/%s',\n" % (self.tempOutDir, namePattern)
#        fileContents = fileContents[:-2]
#        fileContents += "\n/\n"
#        fileContents += "&NAM_STOP_STATUS_RETRIEVAL_FREQ\n"
#        fileContents += "YFREQINSECS = %s\n" % (self.pcfSettings["stopStatusRetFreq"])
#        fileContents += "/\n"
#        confFile = open(pcfPath, "w") # this should be wrapped in a try block
#        confFile.write(fileContents)
#        self.logger.debug("_write_pcf method exiting.")
#        return pcfPath
#
#    def _write_acf(self, replaceList):
#        """
#        Create the algorithm configuration file.
#
#        Inputs: replaceList - a list of two-element tuples of strings. 
#                              The first element in the tuple specifies 
#                              an expression that is to be searched for 
#                              in the template Algorithm Configuration File.
#                              The second element provides the alternative
#                              string that is meant to substitute the text.
#
#        Returns: The path to the newly created Algorithm Configuration File
#                 or 'None', if the file cannot be created.
#
#        The Algorithm Configuration File is copied from a fixed template
#        (located in the directory structures of the original external algorithm
#        packages) to the working directory. Any desired modifications to the
#        template, if one desires to alter some parameters at runtime, can be made
#        using the 'replaceList' input argument.
#        """
#
#        self.logger.debug("_write_acf method called")
#        self.logger.debug("replaceList: %s" % replaceList)
#        templateAcf = open(self.acfSettings, 'r')
#        acfPath = "%s/%s" % (self.workingDir, self.acfFileName)
#        fileHandler = open(acfPath, 'w')
#        for line in templateAcf:
#            newLine = line
#            for original, replacement in replaceList:
#                newLine = newLine.replace(original, replacement, 1)
#            fileHandler.write(newLine)
#        self.logger.debug("_write_acf method exiting")
#        return acfPath
#
#    def _move_outputs_to_final_dir(self):
#        """
#        """
#
#        self.logger.debug("_move_outputs_to_final_dir method called.")
#        for outFile in glob.glob(os.path.join(self.tempOutDir, "*")):
#            self.logger.debug("moving %s to %s..." % (outFile, self.outputDir))
#            shutil.move(outFile, self.outputDir)
#        self.logger.debug("_move_outputs_to_final_dir method exiting.")
#
#
#class G2NGP2Grid(G2ProcessPackage):
#    """
#    ...
#    """
#
#    def _change_search_pattern(self, G2File, pattern):
#        """
#        Allow the modification of the real search pattern in to the modified
#        pattern required by this product's Product Configuration File.
#
#        The Product Configuration File of the 'NGP2GRID' external algorithm
#        expects the name pattern of the output tiled files to contain the
#        'area' substring in its name. The external algorithm will replace this
#        substring with the real portion of each tile's name. The real portion
#        includes 'H*_V*', indicating the horizontal and vertical tile
#        coordinates, according to the grid defined by the external algorithm.
#        """
#
#        self.logger.debug("_change_search_pattern method called.")
#        if G2File.name.endswith('tile'):
#            newPattern = pattern.replace('H??V??', 'area')
#        else:
#            newPattern = pattern
#        self.logger.debug("pattern: %s" % pattern)
#        self.logger.debug("newPattern: %s" % newPattern)
#        self.logger.debug("_change_search_pattern method exiting.")
#        return newPattern
#
#
#class G2PreProcessPackage(G2ProcessPackage):
#    """
#    ...
#    """
#
#    def __init__(self, xmlSettings, timeslot, mode, area, suiteName, 
#                 version=None):
#        """
#        ...
#        """
#
#        self.logger = logging.getLogger("G2ProcessingLine.G2PreProcessPackage")
#        self.logger.debug("__init__ method called")
#        G2ProcessPackage.__init__(self, xmlSettings, timeslot, mode, area, suiteName,
#                                  version)
#        outputDirsEl = self.modeXML.getElementsByTagName("outputDirs")[0]
#        self.staticOutputDir = ""
#        staticOutDirList = outputDirsEl.getElementsByTagName("staticOutputDir")
#        if staticOutDirList:
#            self.staticOutputDir = self.parse_path_element(staticOutDirList[0], self, "data")
#            self._create_dir_tree(self.staticOutputDir)
#        self.logger.debug("__init__ method exiting")
#
#    def run(self, configFiles, destination=None):
#        """
#        Return a list with the command to run the pre-processing algorithm.
#        """
#
#        self.logger.debug("run method called")
#        pcfPath = configFiles["ProductConfigurationFile"]
#        numberOfInputs = 0
#        for line in open(pcfPath, 'r'):
#            numberOfInputs += 1
#        if not destination:
#            outputDir = self.tempOutDir
#        else:
#            outputDir = destination
#        commandList = ["./wrapper_g2.exe", self.sourceObj.area, self.staticOutputDir, 
#                outputDir, str(numberOfInputs), pcfPath]
#        self.logger.debug("commandList: %s" % commandList)
#        exitCode, outputLines = self._run_external_algorithm(commandList)
#        if exitCode in (0, 12):
#            #the algorithm ran successfully
#            self._move_outputs_to_final_dir()
#        self.logger.debug("run method exiting")
#        return exitCode, outputLines
#
#    def write_config_files(self, okFiles):
#        """
#        ...
#        """
#
#        self.logger.debug("write_config_files method called")
#        configFiles = {"ProductConfigurationFile" : self._write_pcf(okFiles)}
#        self.logger.debug("write_config_files method exiting")
#        return configFiles
#
#    def _write_pcf(self, okFiles):
#        """
#        Write the ProductConfigurationFile for the external algorithm.
#
#        Inputs: okFiles - a dictionary with G2File objects that represent
#                          the available and already prepared inputs for 
#                          the execution of this package as keys, and
#                          lists with the paths to these files as values.
#        
#        Returns: a string indicating the full path to the newly created
#                 file.
#
#        The product configuration file of the pre-processing packages
#        is only a file with a list of the inputs
#        """
#
#        self.logger.debug("_write_pcf method called.")
#        pcfPath = "%s/preProcessorConfigurationFile.txt" % self.workingDir
#        self.logger.debug("ProductConfigurationFile path: %s" % pcfPath)
#        fileContents = ""
#        for pathList in okFiles.itervalues():
#            for path in pathList:
#                fileContents += "%s\n" % path
#        confFile = open(pcfPath, "w") # this should be wrapped in a try block
#        confFile.write(fileContents)
#        self.logger.debug("_write_pcf method exiting.")
#        return pcfPath
#
#
#class G2GRIB2HDF5(G2PreProcessPackage):
#
#    def __init__(self, xmlSettings, timeslot, mode, area, suiteName, 
#                 version=None):
#        """
#        This class will create a temporary output location to save the HDF5 GRIB files.
#        These files will then be moved to a proper output destination, after sorting
#        their respective timeslots.
#        """
#
#        self.logger = logging.getLogger("G2ProcessingLine.G2GRIB2HDF5")
#        self.logger.debug("__init__ method called")
#        G2PreProcessPackage.__init__(self, xmlSettings, timeslot, mode, area, suiteName,
#                                     version)
#        self.tempOutputDir = "%s/tempOutputs" % self.workingDir
#        self._create_dir_tree(self.tempOutputDir)
#        self.logger.debug("__init__ method exiting")
#
#    #def run(self, configFiles):
#    #    """
#    #    Run the external algorithm.
#
#    #    This method runs the external FORTRAN or C++ algorithm and saves
#    #    the outputs in a temporary directory. After the algorithm has been
#    #    run successfully the outputs are sorted according to their timeslot
#    #    and moved to their final destination.
#    #    """
#
#    #    self.logger.debug("run method called")
#    #    exitCode, outputLines = G2PreProcessPackage.run(self, configFiles, "%s/" % self.tempOutputDir)
#    #    if exitCode == 0:
#    #        #the algorithm ran successfully
#    #        self._move_outputs_to_final_dir()
#    #    self.logger.debug("run method exiting")
#    #    return exitCode, outputLines
#
#    def _move_outputs_to_final_dir(self):
#        """
#        Move the algorithm outputs to their final destination.
#
#        Returns: nothing
#
#        This method will sort the outputs in new subfolders of the final
#        destination folder, according to each output's timeslot.
#        """
#
#        self.logger.debug("move_outputs_to_final_dir method called")
#        for fileObj in self.outputs:
#            filesFound = glob.glob("%s/%s" % (self.tempOutputDir, fileObj.searchPattern))
#            self.logger.debug("filesFound: %s" % filesFound)
#            for fileName in filesFound:
#                # get the file's timeslot
#                datePosition = re.search(r"[0-9]{12}", fileName) 
#                fileTimeslot = fileName[datePosition.start():datePosition.end()]
#                fileYear = fileTimeslot[0:4]
#                fileMonth = fileTimeslot[4:6]
#                fileDay = fileTimeslot[6:8]
#                fileFinalDir = "%s/%s/%s/%s" % (self.outputDir, fileYear, fileMonth, fileDay)
#                if not os.path.isdir(fileFinalDir):
#                    self.logger.debug("creating directory structure: %s" % (fileFinalDir))
#                    os.makedirs(fileFinalDir)
#                self.logger.debug("moving %s to %s..." % (fileName, fileFinalDir))
#                # should use a 'try' block to catch errors... next version will
#                shutil.move("%s" % fileName, fileFinalDir)
#        self.logger.debug("move_outputs_to_final_dir method exiting")
#
#
#class G2SWI(G2ProcessPackage):
#    '''
#    - ACF -> DONE!
#    - Move temps -> DONE!
#    - G2File com duas timeslots -> DONE!
#    - PCF -> DONE!
#    - run() method must call get_temp_file() move_temp_file()
#    '''
#
#    def __init__(self, xmlSettings, timeslot, mode, area, suiteName,
#                 version=None):
#        self.logger = logging.getLogger("G2ProcessingLine.G2SWI")
#        self.logger.debug("__init__ method called.")
#        G2ProcessPackage.__init__(self, xmlSettings, timeslot, mode, area, 
#                                  suiteName, version)
#        tempDirEl = xmlSettings.getElementsByTagName('inputDirs')[0].getElementsByTagName('tempDir')[0]
#        self.tempDir = self.parse_path_element(tempDirEl, self, "data")
#        staticDirEl = xmlSettings.getElementsByTagName('inputDirs')[0].getElementsByTagName('staticDir')[0]
#        self.staticDir = self.parse_path_element(staticDirEl, self, "data")
#        for dirString in (self.tempDir, self.staticDir):
#            self._create_dir_tree(dirString)
#        self.logger.debug("__init__ method exiting.")
#
#    def _write_acf(self, *args):
#        """
#        Write the AlgorithmConfigurationFile for the external algorithm.
#
#        Returns: A string indicating the full path to the newly created
#                 file.
#        """
#
#        self.logger.debug("_write_acf method called.")
#        acfPath = "%s/AlgorithmConfigurationFile" % self.workingDir
#        self.logger.debug("AlgorithmConfigurationFile path: %s" % acfPath)
#        fileContents = "&NAM_EMPLACEMENT_FICHIER_BINAIRE\n"
#        fileContents += "YFICHIER_BINAIRE = '%s'\n/\n" % (self.staticDir) 
#        fileContents += "&NAM_EMPLACEMENT_TMP\n"
#        fileContents += "YEMPLACEMENTTMP= '%s'\n/\n" % (self.tempDir) 
#        fileContents += "&NAM_FORMAT_ENTRE\n"
#        # this variable allows the SWI algorithm to read its inputs either 
#        # in BUFR or native formats
#        fileContents += "YFORMATENTREE = 1\n/\n"         
#        fileContents += "&PROCLINE_VERSION\n"
#        fileContents += "YPROCLINE_VERSION = '%s'\n/\n" % self.version
#        fileContents += "&PROCLINE_DATE_ISO\n"
#        fileContents += "YPROCLINE_DATE_ISO = '2011-02-30'\n/"
#        confFile = open(acfPath, "w") # this should be wrapped in a try block
#        confFile.write(fileContents)
#        self.logger.debug("_write_acf method exiting.")
#        return acfPath
#
#    def _write_pcf(self, okFiles):
#        """
#        Write the ProductConfigurationFile for the external algorithm.
#
#        Inputs: okFiles - a dictionary with G2File objects that represent
#                          the available and already prepared inputs for 
#                          the execution of this package as keys, and
#                          lists with the paths to these files as values.
#        
#        Returns: a string indicating the full path to the newly created
#                 file.
#
#        The ProductConfigurationFile of the SWI_g2 package has a different
#        format than the other packages. Namely, it expects only the output
#        directory and not each output file's path.
#        """
#
#        self.logger.debug("_write_pcf method called.")
#        pcfPath = "%s/ProductConfigurationFile" % self.workingDir
#        self.logger.debug("ProductConfigurationFile path: %s" % pcfPath)
#        fileContents = "&NAM_ALG_MODES\n"
#        fileContents += "MODE = %s\n/\n" % (self.pcfSettings["mode"]) 
#        fileContents += "&NAM_ALG_INPUT_FILES_PATH\n"
#        fileContents += "YFILEINP=" 
#        #sorting the filepaths
#        sortedPaths = []
#        for inputObj, pathList in okFiles.iteritems():
#            for path in pathList:
#                sortedPaths.append(path)
#            sortedPaths.sort()
#        for path in sortedPaths:
#            fileContents += "'%s', " % path
#        fileContents = fileContents[:-1] #trimming the comma
#        fileContents += "\n/\n"
#        fileContents += "&NAM_ALG_OUTPUT_FILES_PATH\n"
#        fileContents += "YFILEOUT = '%s'" % self.outputDir
#        fileContents += "\n/\n"
#        fileContents += "&NAM_STOP_STATUS_RETRIEVAL_FREQ\n"
#        fileContents += "YFREQINSECS = %s\n" % (self.pcfSettings["stopStatusRetFreq"])
#        fileContents += "/"
#        confFile = open(pcfPath, "w") # this should be wrapped in a try block
#        confFile.write(fileContents)
#        self.logger.debug("_write_pcf method exiting.")
#        return pcfPath
#
#    def move_temp_file(self):
#        """
#        Store any temporary files in a YYYY/MM directory structure.
#
#        Inputs:
#        Returns:
#        """
#
#        self.logger.debug("move_temp_file method called.")
#        for itemPath in glob.glob(os.path.join(self.tempDir, '*')):
#            if os.path.isfile(itemPath):
#                fileTs = utilities.extract_timeslot(
#                                    os.path.basename(itemPath), 14)
#                newPath = "%s%s/%s" % (self.tempDir, fileTs.strftime("%Y"),
#                                          fileTs.strftime("%m"))
#                if not os.path.isdir(newPath):
#                    os.makedirs(newPath)
#                self.logger.debug("Moving %s to %s" % (itemPath, newPath))
#                shutil.move(itemPath, newPath)
#        self.logger.debug("move_temp_file method exiting.")
#
#    def get_temp_file(self, maxLag=10):
#        """
#        Get the temp file needed to run the external package into the tempDir.
#
#        Inputs: maxLag - An integer specifying the number of days that are to
#                         be searched for a temp file.
#
#        The temp file is a binary file that gets generated by the external
#        algorithm. Every new run of the algorithm needs to access the temp
#        file generated two days before.
#        """
#
#        self.logger.debug("get_temp_file method called.")
#        # Difference in days between the instance's timeslot and the earliest
#        # usable temp file
#        lag = 2 
#        currentTs = self.timeslotDT - dt.timedelta(days=lag)
#        foundFile = False
#        while (not foundFile) and ((self.timeslotDT - currentTs).days < (lag + maxLag)):
#            searchPath = "%s%s/%s" % (self.tempDir, currentTs.strftime("%Y"),
#                                      currentTs.strftime("%m"))
#            availableFiles = glob.glob("%s/%s*" % (searchPath, 
#                                       currentTs.strftime("%Y%m%d")))
#            self.logger.debug("currentTs: %s" % currentTs)
#            self.logger.debug("searchPath: %s" % searchPath)
#            self.logger.debug("availableFiles: %s" % availableFiles)
#            if len(availableFiles) > 0:
#                self.logger.debug("Moving %s to %s" % (availableFiles[0], 
#                                  self.tempDir))
#                shutil.move(availableFiles[0], self.tempDir)
#                foundFile = True
#            else:
#                currentTs = currentTs - dt.timedelta(days=1)
#            self.logger.debug("---------------")
#        if not foundFile:
#            self.logger.info("Couldn't find a suitable temp file (DGG).")
#        self.logger.debug("get_temp_file method exiting.")
#
#    def run(self, configFiles):
#        """
#        Run the external application that processes the data.
#
#        Inputs: configFiles - a dictionary with keys: 
#                        - "AlgorithmConfigurationFile";
#                        - "ProductConfigurationFile" 
#                        and values:
#                            - a string indicating the path to the Product
#                            Configuration File.
#                            - a string indicating the path to the algorithm
#                            Configuration File.
#
#        Returns: an integer specifying the return code of the external 
#                 processor algorithm.
#
#        The SWI_g2 package expects the AlgorithmConfigurationFile and 
#        ProductConfigurationFile in a different order than the rest of the
#        packages.
#
#        """
#
#        self.logger.debug("run method called")
#        commandList = [
#               "./wrapper_g2.exe", 
#                configFiles["AlgorithmConfigurationFile"], 
#                configFiles["ProductConfigurationFile"]]
#        self.get_temp_file()
#        exitCode, outputLines = self._run_external_algorithm(commandList)
#        self.move_temp_file()
#        self.logger.debug("run method exiting")
#        return exitCode, outputLines
#
#    def clean_up(self):
#        """
#        Scan the workingDir tree, the outputDir  and any extra directories,
#        removing all unnecessary files and directories.
#        """
#
#        self.logger.debug("clean_up method called.")
#        self._clean_working_dir()
#        try:
#            self._remove_empty_dirs([self.tempDir, self.staticDir, 
#                "%sDGG" % self.outputDir])
#        except AttributeError:
#            self._remove_empty_dirs()
#        self.logger.debug("clean_up method exiting.")
#
#
#class G2Disseminator(G2Item):
#
#    def __init__(self, xmlSettings, timeslot, mode, area, suiteName, version=None):
#        """
#        ...
#        """
#
#        G2Item.__init__(self, xmlSettings, timeslot, area)
#        self.SMSSuite = suiteName
#        self.logger = logging.getLogger("G2ProcessingLine.%s" % self.__class__.__name__)
#        self.modeXML = utilities.find_xml_element(xmlSettings.\
#                       getElementsByTagName("modes")[0], "mode", "name", mode)
#        self.mode = mode
#        self.dissPackages = []
#        for dissEl in self.modeXML.getElementsByTagName("disseminatedPackage"):
#            packName = dissEl.getAttribute("name")
#            packMode = dissEl.getAttribute("mode")
#            self.logger.debug('packName: %s' % packName)
#            self.logger.debug('packMode: %s' % packMode)
#            for area in self._get_allowed_areas(packName, packMode):
#                g2pack = pc.package_creator(packName,
#                                            packMode,
#                                            self.timeslot, area, suiteName,
#                                            version)
#                g2pack.clean_up() # no need to leave the temporary dirs hanging around
#                hostName = dissEl.getElementsByTagName("disseminateTo")[0].firstChild.nodeValue
#                self.logger.debug("Aqui**")
#                self.logger.debug("package:%s" % g2pack)
#                self.logger.debug("dissEl:\n%s" % dissEl.toprettyxml())
#                basePath = self.parse_path_element(
#                           dissEl.getElementsByTagName("path")[0], 
#                           g2pack, relativePath="data", preferObject=True)
#                basePath = basePath.replace(g2pack.dataDir, "")[1:]
#                self.dissPackages.append({
#                    "package" : g2pack, 
#                    "hostName" : hostName,
#                    "basePath" : basePath
#                    })
#
#    def _get_allowed_areas(self, packName, packMode):
#        """
#        Scan the sms xml definition and find allowed areas for the package.
#        """
#
#        self.logger.debug("_get_allowed_areas method called.")
#        settings = utilities.get_new_settings()
#        sp = G2SuiteParser(self.SMSSuite, settings["sms"]["alias"])
#        areas = [t[2] for t in sp.get_nodes_data(sp.suiteNode) \
#                 if (t[3]==packName and t[1]==packMode) or \
#                 (t[3]==self.name and t[1]==self.mode)]
#        self.logger.debug("areas: %s" % areas)
#        self.logger.debug("_get_allowed_areas method exiting.")
#        return areas
#
#    def disseminate(self, itemDict=None):
#        """
#        Returns: 0 if the dissemination has been successfull and 1 otherwise.
#        """
#
#        self.logger.debug("disseminate method called.")
#        endResult = 1
#        if itemDict is None:
#            # disseminate everything
#            resultList = []
#            for item in self.dissPackages:
#                resultList.append(item["package"].send(item["hostName"], 
#                                  item["basePath"]))
#                if not False in [i == 0 for i in resultList]:
#                    endResult = 0
#        else:
#            # disseminate only the requested itemDict
#            endResult = itemDict["package"].send(itemDict["hostName"],
#                        itemDict["basePath"])
#        self.logger.debug("disseminate method exiting.")
#        return endResult
