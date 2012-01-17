#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

import os

from systemsettings import models as ss

from g2item import GenericItem
from g2hosts import HostFactory
import utilities
import g2packages as g2p

# TODO 
#
#	-add __repr__ methods to all the classes
#	- refactor the code in order to not define the full searchPaths before
#	  there is a need to do it
#	- the file.find() and file.fetch() methods should take a list of G2Hosts 
#     as input (with the default being the hosts defined in the xml settings 
#

class G2File(GenericItem):

    def __init__(self, fileSettings, timeslot, areaSettings, hostSettings, 
                 optional=False, parent=None):
        '''
        Inputs

            fileSettings - A systemsettings.models.File object
                defined in the XML file.

            timeslot - A datetime.datetime object

            areaSettings - A systemsettings.models.Area object

            hostSettings - A systemsettings.models.Host object

            optional - A boolean indicating if the object is optional or not.

            parent - A operations.core.g2pacakges.G2Package object.
        '''

        super(G2File, self).__init__(timeslot, areaSettings, hostSettings)
        self.name = fileSettings.name
        self.parent = parent
        self.optional = optional
        self.toCopy = fileSettings.toCopy
        self.toCompress = fileSettings.toCompress
        self.toArchive = fileSettings.toArchive
        self.toDisseminate = fileSettings.toDisseminate
        self.numFiles = fileSettings.numFiles
        self.exceptHours = [eh.hour for eh in fileSettings.exceptHours.all()]
        self.fileType = fileSettings.fileType
        self.frequency = fileSettings.frequency
        self.searchPaths = []
        for filePathObj in fileSettings.filepath_set.all():
            #relativePath = utilities.parse_marked(filePathObj, self)
            relativePath = self.get_path(filePathObj, self)
            #self.searchPaths.append(os.path.join(self.host.basePath, 
            #                        relativePath))
            self.searchPaths.append(relativePath)
        self.searchPatterns = []
        for searchPattObj in fileSettings.filepattern_set.all():
            pattern = utilities.parse_marked(searchPattObj, self)
            self.searchPatterns.append(pattern)
        hf = HostFactory()
        self.archives = [hf.create_host(hs) for hs in fileSettings.specificArchives.all()]

    def find(self, useArchive=False, staticFiles='latest timeslot absolute'):
        '''
        Find the files and return their fullPaths.

        Inputs:

            useArchive - A boolean indicating if the file's specific 
                archives are to be searched. Defaults to False.

            staticFiles - A string indicating what behaviour to adopt for
                static files. Accepted values:
                    - latest timeslot absolute: The files are assumed to have 
                        a timeslot on their filename. They are sorted and only
                        the latest file is fetched. Being the latest means 
                        that the file is as recent as the instance's timeslot,
                        but not more recent than that. This is the default 
                        behaviour.
                    - latest timeslot month: Works like 'latest timeslot day'
                        but only the files that have the same month as the 
                        instance's timeslot are relevant for the fetching.
                    - latest run: The files are assumed to have a run pattern
                        on their filename. they are sorted accordingly and
                        the latest run is returned.
                    - first: The first file in the filelist is fetched.
                    - all: All the files in the file are fetched.

        Returns:

            A dictionary with keys 'host' and 'paths'. The values are a G2Host
            object and a list with the full paths to the files.

        This method will also remove any duplicate files from the list. A
        duplicate is a file that has the same name as another one, regardless
        of its path or compression state.
        '''

        result = {'host' : self.host, 'paths' : []}
        allPaths = []
        for path in self.searchPaths:
            allPaths += [os.path.join(path, p) for p in self.searchPatterns]
        hostList = [self.host]
        if useArchive:
            hostList += self.archives
        hostIndex = 0
        allFound = False
        lastHost = False
        # search every host
        while (not allFound) and (not lastHost):
            theHost = hostList[hostIndex]
            if theHost is not self.host:
                self.logger.info('Trying the archives: %s' % theHost)
            pathsFound = theHost.find(allPaths)
            numFound = len(pathsFound)
            if numFound > 0:
                allFound = True
                if numFound < self.numFiles:
                    self.logger.warning('Not all files have been found. '\
                           'Found %i files. Was expecting at least %i.' 
                            % (numFound, self.numFiles))
                result['host'] = theHost
                uniquePaths = self._return_unique_file_names(pathsFound)
                result['paths'] = self._filter_file_list(uniquePaths, 
                                                         staticFiles)
            if hostIndex + 1 == len(hostList):
                lastHost = True
            else:
                hostIndex += 1
        return result

    def fetch(self, targetDir, useArchive=None, decompress=True):
        '''
        Fetch files from the source host to the destination directory.

        This method's main purpose is to copy local or remote files to
        a destination directory.

        If self.toCopy is True the files will always get copied over to
        targetDir. This will happen regardless of the files being
        on a remote host or on the local host.

        If self.toCopy is False the files will only get copied over to
        targetDir if they are currently in a compressed state. If
        you don't want to force local copies of big files make sure they
        are not being stored in a compressed state. Otherwise they'll get
        copied and decompressed everytime this method is called.

        If self.toCopy is False and the files are not compressed they
        will not be copied to targetDir. Instead a reference to their
        current path is returned. This behaviour intends to avoid 
        unnecessary file copies.

        After being copied the files will optionally be decompressed, in
        order to be ready for further usage.

        Inputs:
            
            targetDir - A string with the relative path (relative to the
                instance's host) of the directory where the files should be
                copied to.

            useArchive - A boolean indicating if the files are to be searched
                for in the archives, in case they cannot be found in host.
                
            decompress - A boolean indicating if the newly fetched files are
                to be decompressed. It only affects files which have actually
                been fetched, so if a file has the "copy" attribute set as
                False (meaning it will not be copied), it will never be
                decompressed.

        Returns:

            A list of strings with the full paths of the files that have been
            fetched.
        '''

        self.logger.info('Fetching %s %s...' % (self.name, self.source.area))
        found = self.find(useArchive)
        result = found['paths']
        if self.toCopy:
            if len(found['paths']) > 0:
                fetched = self.host.fetch(found['paths'], targetDir, 
                                          found['host'])
                decompressed = self.host.decompress(fetched)
                result = decompressed
            else:
                self.logger.debug('Cannot fetch, no files have been found.')
        else:
            self.logger.debug('%s is not marked as "copy" in the settings. '\
                              'Returning only the original file paths...' 
                              % self.name)
        return result

    def _filter_file_list(self, paths, behaviour):
        '''
        Filters a list of paths according to the input behaviour.

        Only files whose frequency is 'static' are currently being
        filtered.
        '''

        newPaths = paths
        if self.frequency == 'static':
            behaviourList = behaviour.split() 
            if behaviourList[0] == 'latest':
                if behaviourList[1] == 'timeslot':
                    timeUnit = behaviourList[2]
                    newPaths = [self._sort_latest_timeslot(paths, timeUnit)]
                elif behaviourList[1] == 'run':
                    raise NotImplementedError
            elif behaviourList[0] == 'first':
                newPaths = [paths[0]]
            elif behaviourList[0] == 'all':
                pass
        return newPaths

    def _sort_latest_timeslot(self, paths, timeUnit):
        '''
        Return the latest file.

        Inputs:

            paths - A list of file paths to analyze.

            timeUnit - A string specifying the type of latest file
                to choose. Accepted values:
                    'absolute' - The latest file, according to this instance's
                        own timeslot.
                    'month' - The latest file belonging to the same month as
                        the instance's own timeslot.
        Returns:

            A string with the path of the latest file.
        '''

        latestPath = None
        # 20 years (in seconds), a large initialization value
        latestDiff = 60 * 60 * 24 * 365 * 20
        for path in paths:
            pTimeslot = utilities.extract_timeslot(path)
            timeDiff = self.timeslot - pTimeslot
            absTimeDiff = timeDiff.seconds + (timeDiff.days * 24 * 60 * 60)
            if timeUnit == 'absolute':
                if (absTimeDiff <= latestDiff) and (absTimeDiff >= 0):
                    latestPath = path
                    latestDiff = absTimeDiff
            elif timeUnit == 'month':
                if (pTimeslot.month == self.timeslot.month) and \
                   (absTimeDiff <= latestDiff):
                       latestPath = path
                       latestDiff = absTimeDiff
        return latestPath

    def _return_unique_file_names(self, pathList):
        '''
        Return a list with unique filepaths, discarding files that apear more
        than once, but on different directories.
        '''

        uniquePathList = []
        uniqueNames = []
        uniqueExtensions = []
        for path in pathList:
            basename = os.path.basename(path)
            name = basename.partition('.')[0]
            ext = basename.rpartition('.')[-1]
            if name in uniqueNames:
                nameIndex = uniqueNames.index(name)
                previousExtension = uniqueExtensions[uniqueNames.index(name)]
                if previousExtension == 'bz2':
                    uniquePathList[nameIndex] = path
                    uniqueExtensions[uniqueNames.index(name)] = ext
            else:
                uniquePathList.append(path)
                uniqueNames.append(name)
                uniqueExtensions.append(ext)
        return uniquePathList

    # FIXME
    # This method only works when the file being processed is output to its 
    # parent package. 
    def get_path(self, markedString, obj):
        '''
        Return a path that has been specified via the markedString mechanism.

        Inputs:

            markedString
        '''
        
        if markedString.string == 'fromOriginator':
            dirName = markedString.name
            thePath = None
            if hasattr(self.parent, 'outputs'):
                parentSettings = ss.Package.objects.get(name=self.parent.name)
                outpSetts = parentSettings.packageOutput_systemsettings_packageoutput_related.all()
                if self.name in [p.outputItem.name for p in outpSetts]:
                    # the parent is this file's originator
                    fullPath = eval('self.parent.%s' % dirName)
                    # trimming the first character in order to eliminate the '/'
                    relativePath = fullPath.replace(self.parent.host.basePath, '')[1:]
                    thePath = relativePath
            if thePath is None:
                # find out who is the parent
                for pSetts in ss.Package.objects.all():
                    outpSetts = pSetts.packageOutput_systemsettings_packageoutput_related.all()
                    for packOut in outpSetts:
                        if packOut.outputItem.name == self.name:
                            self.logger.info('%s\'s parent is %s' % 
                                             (self.name, pSetts.name))
                            originator = self._create_originator_pack(packOut)
                            self.logger.info('originator pack: %s' % originator)

                thePath = '' # dummy

        else:
            thePath = utilities.parse_marked(markedString, obj)
        return thePath

    def _create_originator_pack(self, outputSettings):
        '''
        Return the package from where this instance is an output.
        '''

        packSettings = outputSettings.package
        specificTimeslots = outputSettings.specificTimeslots.all()
        if len(specificTimeslots) == 0:
            # the package's timeslot is the same as the output's
            theTimeslot = self.timeslot
        else:
            specTimeslot = specificTimeslots[0]
            theTimeslot = utilities.recover_timeslot(self.timeslot, 
                                                      specTimeslot)
        specificAreas = outputSettings.specificAreas.all()
        if len(specificAreas) == 0:
            # the package's area is the same as the output's
            areaName = self.source.area
            theArea = ss.Area.objects.get(name=areaName)
        else:
            # get the default area
            theArea = ss.Area.objects.get(name='.*')
        theClass = packSettings.codeClass.className
        theHost = ss.Host.objects.get(name=self.host.name)
        pack = eval('g2p.%s(packSettings, theTimeslot, theArea, theHost)' % 
                    theClass)
        return pack

    def __repr__(self):
        return self.name
             

#    def _return_unique_file_names(self, pathList):
#        '''
#        Return a list with unique filepaths, discarding files that apear more
#        than once, but on different directories.
#        '''
#
#        uniquePathList = []
#        uniqueNames = []
#        uniqueExtensions = []
#        for path in pathList:
#            basename = os.path.basename(path)
#            name = basename.partition('.')[0]
#            ext = basename.rpartition('.')[-1]
#            if name in uniqueNames:
#                nameIndex = uniqueNames.index(name)
#                previousExtension = uniqueExtensions[uniqueNames.index(name)]
#                if previousExtension == 'bz2':
#                    uniquePathList[nameIndex] = path
#                    uniqueExtensions[uniqueNames.index(name)] = ext
#            else:
#                uniquePathList.append(path)
#                uniqueNames.append(name)
#                uniqueExtensions.append(ext)
#        return uniquePathList
#
#    # FIXME
#    # - Currently working on this method...
#    def fetch(self, targetDir, sourceHost=None, targetHost=None, useArchive=None,
#              forceCopy=False):
#        '''
#        Fetch files from the source host to the destination directory.
#
#        This method's main purpose is to copy local or remote files to
#        a destination directory.
#
#        However, if the instance's 'makeCopies' attribute is set to False, 
#        the files will not be copied. This is to prevent accidental copies of 
#        big files (local copies and network copies as well).
#
#        Also note that, if the files are on a local host and are not compressed,
#        the default behaviour is to not copy them, the method will just return 
#        their local path. This can be overriden by using the 'forceCopy' flag.
#
#        Inputs:
#            
#            targetDir - A string with the relative path (relative to the
#                'targetHost') of the directory where the files should be
#                copied to.
#
#            sourceHost - A string with the name of the host that is the
#                source of the files. A value of None (the default) will use
#                the file's own host as a source.
#
#            targetHost - A string with the name of the host that is the 
#                destination for the fetching. A value of None (the default)
#                will use the file's own default host as a destination.
#
#            useArchive - A string indicating what kind of file is to be
#                searched and fetched for in the archives. Accepted values are 
#                'inputs' and 'outputs'. A value of None (the default) causes 
#                the archives not to be searched at all.
#
#            forceCopy - A boolean indicating if the files must be copied even
#                if 'sourceHost' is the local host and they are not compressed.
#                This is generally not the intended behaviour and, as such, the
#                default is False.
#
#        Returns:
#
#            A list of strings with the full paths of the files that have been
#            fetched.
#        '''
#
#        result = None
#        compressedPatt = re.compile(r'\.bz2$')
#        if self.makeCopies:
#            foundDict = self.find(sourceHost, useArchive)
#            if foundDict is not None:
#                # the files have been found somewhere
#                if targetHost is None:
#                    theHost = self.defaultHost
#                else:
#                    theHost = factories.create_host(targetHost)
#                if theHost.name == foundDict['host']:
#                    # files need a local copy.
#                    toCopy = []
#                    toGetLink = []
#                    for path in foundDict['paths']:
#                        path = path + '$'
#                        if compressedPatt.search(path) is not None:
#                            # this path is compressed, it is to be copied 
#                            # regardless
#                            toCopy.append(path)
#                        else:
#                            if forceCopy:
#                                # copy the files
#                                toCopy.append(path)
#                            else:
#                                # just get their link
#                                toGetLink.append(path)
#                    fetched = theHost.fetch(toCopy, targetDir, foundDict['host']) + toGetLink
#                else:
#                    # the copy will be remote
#                    fetched = theHost.fetch(foundDict['paths'], targetDir, foundDict['host'])
#                result = fetched
#        return result
#
#    def is_file(self, filePath):
#        '''
#        Return True it the filePath is one of the files specified by this
#        object's searchPatterns.
#        '''
#
#
#        patts = [re.compile(fnmatch.translate(p)) for p in self.searchPatterns]
#        isFile = False
#        for patt in patts:
#            if patt.search(filePath) is not None:
#                isFile = True
#        return isFile
#
#    def generate_quickview(self):
#        raise NotImplementedError
#
#    def generate_xml_metadata(self):
#        raise NotImplementedError
#
#    # Is this method really necessary?
#    def get_originator_package(self):
#        '''
#        Return a G2Package instance that is the originator of this G2File
#        object.
#
#        Note: The returned package's timeslot, source and host will be the
#        same as this instance's, which can be incorrect.
#        '''
#        
#        originatorPack = None
#        result = None
#        allPackDetails = utilities.get_all_packages()
#        for packDict in allPackDetails:
#            packName = packDict['name']
#            packModes = [md.get('name') for md in packDict['modes']]
#            for mode in packModes:
#                currentVersion = utilities.get_current_version_number(packName,
#                                                                      mode)
#                outputs = utilities.get_file_names(packName, mode,
#                                                   currentVersion, 'outputs')
#                if self.name in outputs:
#                    originatorPack = factories.create_package(
#                                        packName, mode, 
#                                        self.timeslot.strftime('%Y%m%d%H%M'),
#                                        self.source.name)
#                    result = (packName, mode, self.timeslot.strftime('%Y%m%d%H%M'),self.source.name)
#        return originatorPack, result
#
#    # FIXME
#    # - this method hasn't been properly tested yet.
#    # - also, the version number shouldn't be a number, a string would be
#    #   better
#    def get_originator_version(self):
#        '''
#        Return the version of the package that originated this file.
#
#        The version returned will be the one marked as 'current' in the
#        settings. If no version can be found it will return None.
#        '''
#
#        theVersion = None
#        allPackDetails = utilities.get_all_packages()
#        for packName, packDetails in allPackDetails.iteritems():
#            for modeName, modeDetails in packDetails.get('modes').iteritems():
#                versions = modeDetails.get('versions')
#                if versions is not None:
#                    for version in versions:
#                        if version.get('status') == 'current':
#                            outputs = [o['name'] for o in version.get('outputs')]
#                            if self.name in outputs:
#                                theVersion = version.get('number')
#        return theVersion
#
#    def get_originator_output_dir(self):
#        '''
#        Return the output directory for the package that created this file.
#        '''
#
#        theDir = None
#        allPackDetails = utilities.get_all_packages()
#        for packName, packDetails in allPackDetails.iteritems():
#            for modeName, modeDetails in packDetails.get('modes').iteritems():
#                outDirTup = modeDetails.get('outputDir')
#                # working...
#
#    def get_dependent_packages(self):
#        '''
#        Return a list of G2Package instances that depend on this G2File
#        object in order to run.
#        '''
#        
#        raise NotImplementedError
#
#
#    def _get_all_relative_paths(self):
#        '''
#        Return a list with all the relative search paths and search patterns 
#        combined.
#        '''
#
#        allRelPaths = []
#        for pathDict in self.searchPaths:
#            if pathDict['isRelative']:
#                allRelPaths += [os.path.join(pathDict['path'], p) for p in \
#                                self.searchPatterns]
#        return allRelPaths
#
#    def _get_all_absolute_paths(self):
#        '''
#        Return a list with all the absolute search paths and search patterns 
#        combined.
#        '''
#
#        allAbsPaths = []
#        for pathDict in self.searchPaths:
#            if not pathDict['isRelative']:
#                allAbsPaths += [os.path.join(pathDict['path'], p) for p in \
#                                self.searchPatterns]
#        return allAbsPaths


#class G2File(G2Item):
#    """
#    ...
#    """
#
#    def __init__(self, xmlSettings, area, timeslot, package, role, isOptional=False):
#        """
#        ...
#
#        Inputs: xmlSettings - An xml object containing the settings that 
#                              initialize the object's instance.
#                area - A string specifying the geographical area that the
#                       file covers.
#                timeslot - A datetime.datetime object that holds the timeslot
#                package - A G2Package instance.
#                role - A string specifying the role of this object in its
#                       parent package. It can be either 'input' or 'output'.
#                isOptional - A boolean indicating if this file is to be
#                             treated as optional.
#        """
#
#        self.logger = logging.getLogger("G2ProcessingLine.G2File")
#        self.logger.debug("__init__ called")
#        self.xmlSettings = xmlSettings
#        if xmlSettings.getAttribute("noArchiveFetch") == '':
#            self.fetchFromArchive = True
#        else:
#            self.fetchFromArchive = False
#        self.package = package
#        self.role = role
#        timeslotDT = self._get_correct_timeslot(timeslot, xmlSettings)
#        G2Item.__init__(self, xmlSettings, timeslotDT, area)
#        self.isOptional = isOptional
#        self.originatingPackVersion = self._get_originating_pack_version()
#        self.type = xmlSettings.getElementsByTagName("type")[0].firstChild.nodeValue
#        self.frequency = xmlSettings.getElementsByTagName("frequency")[0].firstChild.nodeValue
#        self.searchPattern = self.parse_marked_element(xmlSettings.getElementsByTagName("searchPattern")[0],
#                                                       self.package)
#        self.hosts = self._create_default_hosts(xmlSettings)
#        #self.searchPaths = self.hosts[0].searchPaths # <- temporary
#
#        exHours = xmlSettings.getElementsByTagName("exceptHours")
#        self.exceptHours = []
#        if exHours:
#            self.exceptHours = [int(i.firstChild.nodeValue) for i in exHours[0].getElementsByTagName("hour")]
#        if self.exceptHours and (self.timeslotDT.hour in self.exceptHours):
#            self.numFiles = 0
#        else:
#            self.numFiles = int(xmlSettings.getElementsByTagName("numFiles")[0].firstChild.nodeValue)
#
#        self.logger.debug("--- FILE SETTINGS ---")
#        self.logger.debug("self.name: %s" % self.name)
#        self.logger.debug("self.role: %s" % self.role)
#        self.logger.debug("self.type: %s" % self.type)
#        self.logger.debug("self.sourceObj: %s" % self.sourceObj)
#        self.logger.debug("self.numFiles: %s" % self.numFiles)
#        self.logger.debug("self.searchPattern: %s" % self.searchPattern)
#        self.logger.debug("self.timeslot: %s" % self.timeslot)
#        self.logger.debug("self.originatingPackVersion: %s" % self.originatingPackVersion)
#        self.logger.debug("------------------------")
#        self.logger.debug("__init__ exiting")
#
#    def find(self, host=None):
#        """
#        Look for the files and return a list with their fullpath.
#
#        Files are searched for in accordance to their 'searchPath',
#        'searchPattern' and 'host' values. A file is only searched
#        in case the defined timeslot is not in the file's exceptHours
#        list
#
#        Inputs:
#            host - A G2Host instance. If None, the files will be searched
#                   using this instance's first host.
#        """
#
#        self.logger.debug("find method called")
#        if host is None:
#            host = self.hosts[0]
#        if self.timeslotDT.hour in self.exceptHours:
#            self.logger.debug("self.timeslotDT.hour: %i" % self.timeslotDT.hour)
#            self.logger.debug("self.exceptHours: %s" % self.exceptHours)
#            fileList = []
#        else:
#            fileList = host.find(self)
#            if "static" in self.frequency:
#                fileList = self._get_latest_file(fileList)
#                if fileList[0] is None:
#                    fileList.pop()
#                else:
#                    # we have found some static file(s), let's update the
#                    # object's timeslot elements
#                    timeslotREObj = re.search(r'[0-9]{12}', fileList[0])
#                    if timeslotREObj is not None:
#                        staticTimeslot = dt.datetime.strptime(timeslotREObj.group(),
#                                '%Y%m%d%H%M')
#                        self.update_timeslot_elements(staticTimeslot)
#        self.logger.debug("found %i files. Was expecting to find %i files." % (len(fileList), self.numFiles))
#        if len(fileList) >= self.numFiles:
#            allPresent = True
#        else:
#            allPresent = False
#        return allPresent, fileList
#        self.logger.debug("find method exiting")
#
#    def fetch(self, fileList, host=None):
#        """
#        ...
#        """
#
#        self.logger.debug("fetch method called.")
#        if host is None:
#            host = self.hosts[0]
#        newFileList = host.fetch(fileList, self)
#        self.logger.debug("fetch method exiting.")
#        return newFileList
#
#    def send(self, hostName, sendPath):
#        """
#        Send the files to the specified host.
#
#        Inputs:
#            hostName - A string specifying the name of the G2Host object
#                       that should be used to send the files. If this
#                       type of host is not already part of the object's
#                       'hosts' list, it will be created and appended to it.
#            searchPath - A string, specifying the path on the host where the
#                         files are to be sent.
#        """
#
#        self.logger.debug("send method called.")
#        if hostName in [h.name for h in self.hosts]:
#            host = [h for h in self.hosts if h.name == hostName][0]
#            # adding 'sendPath' as the first element of host.searchPaths
#            host.searchPaths = [sendPath] + host.searchPaths
#        else:
#            host = host_creator(hostName, [sendPath])
#        allThere, fileList = self.find()
#        result = host.send(fileList)
#        self.logger.debug("send method exiting.")
#        return result
#
#    def _create_default_hosts(self, xml):
#        """
#        Create a list with the default G2Host instances for this file.
#
#        Inputs:
#            xml - An XML object holding the all of the settings for this
#                  G2File object.
#        """
#
#        self.logger.debug("_create_default_hosts method called.")
#        g2hosts = []
#        for hNode in xml.getElementsByTagName("hosts")[0].getElementsByTagName("host"):
#            hostName = hNode.getAttribute("name")
#            searchPaths = []
#            for p in hNode.getElementsByTagName("searchPaths")[0].getElementsByTagName("path"):
#                searchPaths.append(self.parse_path_element(p, self.package, "data"))
#            g2hosts.append(host_creator(hostName, searchPaths))
#        self.logger.debug("_create_default_hosts method exiting.")
#        return g2hosts
#
#    def _get_correct_timeslot(self, timeslot, xmlSettings):
#        """
#        Set the correct timeslot of this instance, according to any
#        modifications that may occur (delays, ...)
#
#        Inputs: timeslot - a datetime.datetime object with the
#                           original timeslot given at initialization time
#
#        Returns: a datetime.datetime object.
#
#        This method should be reimplemented by classes that need to alter
#        the object's default timeslot. The default implementation just returns 
#        the timeslot given.
#        """
#
#        self.logger.debug("_get_correct_timeslot method called")
#        self.logger.debug("_get_correct_timeslot method exiting")
#        return timeslot
#
#    def _get_latest_file(self, fileList):
#        """
#        ...
#        """
#
#        self.logger.debug("_get_latest_file method called")
#        freqList = self.frequency.split()
#        if len(freqList) > 1:
#            frequencyType = self.frequency.split()[1].lower()
#        else:
#            frequencyType = "latest"
#        latestFile = None
#        latestDifference = 60 * 60 * 24 * 365 * 20 # a large initialization value
#        for filePath in fileList:
#            self.logger.debug("filePath: %s" % filePath)
#            try:
#                fileTimeslot = utilities.extract_timeslot(filePath)
#                self.logger.debug("fileTimeslot: %s" % fileTimeslot)
#                timeDifference = self.timeslotDT - fileTimeslot 
#                absTimeDifference = timeDifference.seconds + (timeDifference.days * 24 * 60 * 60)
#                if frequencyType == "latest":
#                    if (absTimeDifference <= latestDifference) and (absTimeDifference >= 0):
#                        latestFile = filePath
#                        latestDifference = absTimeDifference
#                elif frequencyType == "monthly":
#                    if fileTimeslot.month == self.timeslotDT.month and \
#                    (absTimeDifference <= latestDifference):
#                        latestFile = filePath
#                        latestDifference = absTimeDifference
#            except TypeError:
#                self.logger.debug("couldn't find any timeslot on the file's name")
#        self.logger.debug("fileList: %s" % fileList)
#        self.logger.debug("latestFile: %s" % latestFile)
#        self.logger.debug("_get_latest_file method exiting")
#        return [latestFile]
#
#    def _get_originating_pack_version(self):
#        """
#        Return this file's originating package version number.
#
#        Scan the packageSettings.xml file and look for this file's name in 
#        the outputs section of all the modes. When it is found, get the
#        current version of the package where the file originated.
#        """
#
#        self.logger.debug("_get_originating_pack_version method called")
#        origPackVersion = ""
#        packsXML = minidom.parse(self.packagesXMLFile)
#        for packEl in packsXML.getElementsByTagName("package"):
#            for modeEl in packEl.getElementsByTagName("modes")[0].getElementsByTagName("mode"):
#                versionsEl = modeEl.getElementsByTagName("versions")
#                if len(versionsEl) > 0: #the dissemination package has no version
#                    for versionEl in versionsEl[0].getElementsByTagName("version"):
#                        if versionEl.getAttribute("status") == "current":
#                            for outputEl in modeEl.getElementsByTagName("outputs")[0].getElementsByTagName("output"):
#                                if outputEl.getAttribute("name") == self.name:
#                                    origPackVersion = versionEl.getAttribute("number")
#        self.logger.debug("_get_originating_pack_version method exiting")
#        return origPackVersion
#
#    def generate_quickview(self):
#        """
#        Generate quickviews.
#
#        This is an abstract method. It should be reimplemented by
#        child classes to provide the actual work.
#        """
#
#        raise NotImplementedError
#
#    def generate_metadata(self, filePaths, outDir):
#        """
#        Generate metadata.
#
#        This is an abstract method. It should be reimplemented by
#        child classes to provide the actual work.
#        """
#
#        raise NotImplementedError
#
#    def __repr__(self):
#        return "%s(name=%r, source=%r, timeslot=%r)" \
#                % (self.__class__.__name__, self.name, self.sourceObj, 
#                   self.timeslot)
#
#
#class G2QuasiStaticFile(G2File):
#    """
#    ...
#    """
#
#    def _get_originating_pack_version(self):
#        """
#        ...
#        """
#
#        self.logger.debug("_get_originating_pack_version method called")
#        origPackVersion = ""
#        packsXML = minidom.parse(self.packagesXMLFile)
#        for packEl in packsXML.getElementsByTagName("package"):
#            for modeEl in packEl.getElementsByTagName("modes")[0].getElementsByTagName("mode"):
#                versionsEl = modeEl.getElementsByTagName("versions")
#                if len(versionsEl) > 0: #the dissemination package has no version
#                    for versionEl in modeEl.getElementsByTagName("versions")[0].getElementsByTagName("version"):
#                        if versionEl.getAttribute("status") == "current":
#                            for outputEl in modeEl.getElementsByTagName("outputs")[0].getElementsByTagName("output"):
#                                possibleNames = (self.name, "quasi-static %s" %self.name)
#                                if outputEl.getAttribute("name") in possibleNames:
#                                    origPackVersion = versionEl.getAttribute("number")
#        self.logger.debug("_get_originating_pack_version method exiting")
#        return origPackVersion
#
#
#class G2GRIBFile(G2File):
#    """
#    Trying to improve the detection of the output files.
#    """
#
#    def __init__(self, xmlSettings, area, timeslot, package, role, isOptional):
#        """
#        ...
#        """
#
#        G2File.__init__(self, xmlSettings, area, timeslot, package, role, isOptional)
#        # find the portion of the search pattern that holds the ECMWF run information
#        runPortion = re.search(r'_F-\*', self.searchPattern)
#        packFileTimeDiff = self.timeslotDT - self.package.timeslotDT
#        hourlyDifference = (packFileTimeDiff.days * 24.0) + (packFileTimeDiff.seconds / (60 * 60))
#        if hourlyDifference != 0: # this means that the file is being used as an output
#            newRunPortion = "_F-%.3i" % hourlyDifference
#            self.logger.debug("old SearchPattern: %s" % self.searchPattern)
#            self.searchPattern = self.searchPattern[0:runPortion.start()] + \
#                    newRunPortion + self.searchPattern[runPortion.end():]
#            self.logger.debug("new SearchPattern: %s" % self.searchPattern)
#
#    def find(self):
#        """
#        Return the files corresponding to the earliest ECMWF run
#        """
#
#        self.logger.debug("find method called")
#        allPresent, fileList = G2File.find(self)
#        earliestRunNumber = 1000 # an absurd initialization value
#        latestFile = ''
#        for file in fileList:
#            runNumberREGEXP = re.search(r"_F-[0-9]{3}", file)
#            if runNumberREGEXP:
#                runNumber = int(runNumberREGEXP.group()[3:])
#                if runNumber <= earliestRunNumber:
#                    latestFile = file
#                    earliestRunNumber = runNumber
#        self.logger.debug("find method exiting")
#        return allPresent, [latestFile]
#
#
#class G2LSASAFFile(G2File):
#    """
#    ...
#    """
#
#    def _get_correct_timeslot(self, timeslot, xmlSettings):
#        """
#        Get the correct timeslot, accounting for eventual delays
#        """
#
#        self.logger.debug("_get_correct_timeslot method called")
#        delayedTimeslot = timeslot
#        delayEl = xmlSettings.getElementsByTagName("delayTimeslot")
#        if delayEl:
#            delays = {"minutes" : delayEl[0].getAttribute("minutes"),
#                      "hours" : delayEl[0].getAttribute("hours"),
#                      "days" : delayEl[0].getAttribute("days")}
#            for key, value in delays.iteritems():
#                if value:
#                    delays[key] = int(value)
#                else:
#                    delays[key] = 0
#            delayTD = dt.timedelta(days=delays["days"], hours=delays["hours"],
#                                   minutes=delays["minutes"])
#            delayedTimeslot = timeslot - delayTD
#        self.logger.debug("corrected timeslot: %s" % delayedTimeslot.strftime("%Y%m%d%H%M"))
#        self.logger.debug("_get_correct_timeslot method called")
#        return delayedTimeslot
#
#class G2LSASAFMessyFile(G2LSASAFFile):
#    """
#    This class is part of a hack that tries to deal with the bad
#    storage of some of the LSASAF input files.
#
#    It has no methods or properties other than the ones defined
#    in its parent class. Its sole existence is to allow the G2Host
#    objects to handle the searchPattern differently when calling
#    their  '_find_remote_ssh' method and split searchPattern in a way
#    that can be managed efficiently by the remote host.
#
#    (yes, its ugly...)
#    """
#
#    pass
#
#
#class G2QuickViewFile(G2File):
#    """
#    ...
#    """
#
#    # This method should use a better way to find the G2File object to 
#    # be quickviewed. Instead of searching for a fixed string within
#    # each G2File's instance, which is not very flexible, there should be
#    # one extra tag in the xml settings of the G2File object that specifies
#    # the name of theG2File that it will try to quickview.
#    def _find_original_filepaths(self, fileObj=None):
#        """
#        Scan the parent package's g2file objects and return a list
#        of paths to the files whose quickviews are to be created.
#        """
#
#        self.logger.debug("_find_original_filepaths method called.")
#        nameToSearch = self.name.replace(" quickview", "")
#        g2FileToQuickView = [out for out in self.package.outputs \
#                             if out.name == nameToSearch][0]
#        self.logger.debug("g2FileToQuickView: %s" % g2FileToQuickView)
#        self.logger.debug("_find_original_filepaths method exiting.")
#        allThere, filePaths = g2FileToQuickView.find()
#        return filePaths
#
#    def generate_quickview(self):
#        """
#        ...
#        """
#
#        self.logger.debug("generate_quickview method called.")
#        outputDir = self.hosts[0].searchPaths[0]
#        outputPaths = []
#        filePaths = self._find_original_filepaths()
#        for fPath in filePaths:
#            result, uncompressedPath = utilities.decompress(fPath)
#            h5QuickView = HDF5TileQuickviewGenerator(uncompressedPath)
#            outputPaths.append(h5QuickView.create_quickview(outputDir=outputDir))
#            if fPath != uncompressedPath:
#                # the file was compressed before, lets compress again
#                result, compressedPath = utilities.compress(uncompressedPath)
#        self.logger.debug("generate_quickview method exiting.")
#        return outputPaths
#
#
#class G2MetadataFile(G2File):
#    """
#    ...
#    """
#
#    def generate_metadata(self, filePaths, outputDir=None):
#        raise NotImplementedError
#
#
