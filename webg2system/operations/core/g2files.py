#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

import os

from systemsettings import models as ss

from g2item import GenericItem
from g2hosts import G2Host
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

    hosts = dict()

    def __init__(self, fileSettings, timeslot, areaSettings, hostSettings, optional=False):
        '''
        Inputs

            fileSettings - A systemsettings.models.File object
                defined in the XML file.

            timeslot - A datetime.datetime object

            areaSettings - A systemsettings.models.Area object

            hostSettings - A systemsettings.models.Host object

            optional - A boolean indicating if the object is optional or not.
        '''

        super(G2File, self).__init__(timeslot, areaSettings, hostSettings)
        self.name = fileSettings.name
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
        if self.toArchive:
            self.archives = [G2Host(hs) for hs in fileSettings.specificArchives.all()]
        else:
            self.archives = None

    # FIXME
    # - Should this method filter out any opssible duplicate files (compressed 
    # vs non-copmpressed, etc) or is it being done somewhere else?
    # - NEW FEATURE: files that specify absolute searchPaths should get 
    # searched in the host that they specify, regardless of it being an archive
    def find(self, useArchives=None, host=None):
        '''
        Find the files and return their fullPaths.

        Inputs:

            useArchives - A list of G2Host objects where the files may be
                archived. If None (the default), no archives will be searched.

            host - A G2Host object where the search for the files is to be 
                made. If None (the default), the object's own host will be
                used.

        Returns:

            A dictionary with keys 'host' and 'paths'...
        '''

        result = {'host' : host, 'paths' : []}
        if host is None:
            host = self.host
        allPaths = []
        for path in self.searchPaths:
            allPaths += [os.path.join(path, p) for p in self.searchPatterns]

        hostList = [host]
        if useArchives is not None:
            hostList += useArchives
        hostIndex = 0
        allFound = False
        lastHost = False
        # search every host
        while (not allFound) and (not lastHost):
            theHost = hostList[hostIndex]
            if theHost is not host:
                self.logger.info('Trying the archives: %s' % theHost)
            pathsFound = theHost.find(allPaths)
            if len(pathsFound) > 0:
                allFound = True
                numFound = len(pathsFound)
                if numFound < self.numFiles:
                    self.logger.warning('Not all files have been found. '\
                            'Found %i files. Was expecting at least %i.' 
                            % (numFiles, self.numFiles))
                result['host'] = host
                result['paths'] = pathsFound
            if hostIndex + 1 == len(hostList):
                lastHost = True
            else:
                hostIndex += 1
        return result

    def get_path(self, markedString, obj):
        '''
        Return a path that has been specified via the markedString mechanism.

        Inputs:

            markedString
        '''

        if markedString.string == 'fromOriginator':
            dirName = markedString.name
            originatorList = [po.package for po in \
                             ss.PackageOutput.objects.all() if \
                             po.outputItem.name==self.name]
            if len(originatorList) != 0:
                theOriginator = originatorList[0]
                markedString = theOriginator.packagepath_set.get(name=dirName)
        thePath = utilities.parse_marked(markedString, obj)
        return thePath
             

#    def find(self, hostName=None, useArchive=None, lookForBigFiles=False):
#        '''
#        Find this object's files in hostName.
#
#        This method will also sort the found files, removing possible
#        duplicates. If the same file is present on more than one directory,
#        only one of them will be returned. Also, if a file is present in
#        compressed and uncompressed forms, only the uncompressed one will
#        be returned.
#        If the files cannot be found in the host, the archives may also be 
#        searched.
#
#        Inputs:
#
#            hostName - The name of a G2Host object specifying where to look 
#                       for the files. If it is None (the default), the 
#                       instance's default host will be used.
#
#            useArchive - A string indicating what kind of file is to be
#                searched for in the archives. Accepted values are 'inputs'
#                and 'outputs'. A value of None (the default) causes the
#                archives not to be searched at all.
#
#            lookForBigFiles - escrever aqui ...
#
#        Returns:
#
#            A dictionary with keys:
#                'host' : the name of the host where the files have been found
#                'paths' : a list with the full paths of found files
#            If the files cannot be found, the method will return None.
#        '''
#
#        relPaths = self._get_all_relative_paths()
#        absPaths = self._get_all_absolute_paths()
#        result = None
#        if hostName is None:
#            theHost = self.defaultHost
#        else:
#            theHost = factories.create_host(hostName)
#        relFound = theHost.find(relPaths)
#        relatives = self._return_unique_file_names(relFound)
#        absFound = theHost.find(absPaths, absolute=True)
#        absolutes = self._return_unique_file_names(absFound)
#        allPaths = relatives + absolutes
#        if len(allPaths) > 0:
#            # the files have been found
#            result = {'host' : theHost.name, 'paths' : allPaths}
#        elif len(allPaths) == 0 and useArchive is not None:
#            # nothing has been found in the host
#            if not self.makeCopies and not lookForBigFiles:
#                # don't search for the files in the archives
#                self.logger.warning('%s is not marked as "makeCopies"'\
#                                    ', skipping its search in the archives' % \
#                                    self.name)
#            else:
#                # let's try the archives
#                self.logger.info('Trying the archives...')
#                archives = utilities.get_archive_names(useArchive)
#                for archName in archives:
#                    host = factories.create_host(archName)
#                    relFound = host.find(relPaths)
#                    relatives = self._return_unique_file_names(relFound)
#                    absFound = host.find(absPaths)
#                    absolutes = self._return_unique_file_names(absFound)
#                    allPaths = relatives + absolutes
#                    if len(allPaths) > 0:
#                        result = {'host': archName, 'paths' : allPaths}
#                        break
#        return result
#
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
