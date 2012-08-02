#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

import os
import re
import logging

from systemsettings import models as ss

from g2item import GenericItem
from g2hosts import HostFactory
import utilities
import g2packages as g2p

class G2File(GenericItem):
    _originatorPackages = []

    def __init__(self, fileSettings, timeslot, areaSettings, hostSettings, 
                 optional=False, parent=None, logger=None):
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

        super(G2File, self).__init__(timeslot, areaSettings, 
                                     host=hostSettings, logger=logger)
        self.name = fileSettings.name
        self.parent = parent
        self.optional = optional
        self.toCopy = fileSettings.toCopy
        self.toCompress = fileSettings.toCompress
        self.toArchive = fileSettings.toArchive
        self.toDisseminate = fileSettings.toDisseminate
        for extraInfo in fileSettings.fileextrainfo_set.all():
            exec('self.%s = utilities.parse_marked(extraInfo, self)' % extraInfo.name)
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
        #hf = HostFactory(log_level=log_level)
        specific_archives = fileSettings.specificArchives.all()
        if len(specific_archives) == 0:
            specific_archives = [hs for hs in ss.Host.objects.filter(role__name='archive')]
        hf = HostFactory()
        #self.archives = [hf.create_host(hs) for hs in specific_archives]
        self.io_buffers = self._get_io_buffers(fileSettings)
        self.archives = self._get_archives(fileSettings)

    def _get_io_buffers(self, settings):
        specific_buffers = settings.specific_io_buffers.all()
        if len(specific_buffers) == 0:
            specific_buffers = [hs for hs in \
                ss.Host.objects.filter(role__name='io buffer', active=True)]
        the_buffers = []
        for buf in specific_buffers:
            if buf.name != self.host.name:
                the_buffers.append(buf)
            else:
                self.logger.debug('%s is already the file\'s host, so no ' \
                                  'need to add it as an io buffer.' % buf.name)
        hf = HostFactory()
        return [hf.create_host(hs) for hs in the_buffers]

    def _get_archives(self, settings):
        '''
        Return a list of G2Host instances that are the archives for this file.

        The G2Host list is created from the specificArchives attribute. If
        there are no specificArchives defined, then all the hosts that have
        the 'archive' role and are 'active' will be used.
        A specificArchive will only be created if it is not already the same
        host that this instance is using.
        '''

        specific_archives = settings.specificArchives.all()
        if len(specific_archives) == 0:
            specific_archives = [hs for hs in \
                ss.Host.objects.filter(role__name='archive', active=True)]
        the_archives = []
        for arch in specific_archives:
            buffers = [b.name for b in self.io_buffers]
            excluded = buffers + [self.host.name]
            if arch.name not in excluded:
                the_archives.append(arch)
            else:
                self.logger.debug('%s is already the file\'s host or io ' \
                                  'buffer, so no need to add it as an ' \
                                  'archive.' % arch.name)
        hf = HostFactory()
        return [hf.create_host(hs) for hs in the_archives]

    def find(self, restrictPattern=None, use_archive=False, 
             use_io_buffer=True,
             staticFiles='latest timeslot absolute'):
        '''
        Find the files and return their fullPaths.

        Inputs:

            restrictPattern - A string, to be interpreted as a regular 
                expression, to filter among all the possible files. This is 
                useful for finding just a single tile from all the possible 
                ones.

            use_archive - A boolean indicating if the file's specific 
                archives are to be searched. Defaults to False.

            use_io_buffer - A boolean indicating if the file's io_buffer
                hosts are to be searched. Defaults to True.

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

        NOTE: The files may be searched for, in order, in the following hosts:
                - the file\'s own host;
                - the file\'s io_buffers. This can be disabled with the 
                  use_io_buffer argument;
                - the file\'s archives. This can be disabled with the
                  use_archive argument.
              By default, this method will search for the files in the file\'s
              own host and then in the io_buffers, not using the archives at
              all. The prefered way to execute a thorough search is to try to
              find the files in the io_buffer and let the io_buffer connect to
              the archives to search for the files there.

        This method will also remove any duplicate files from the list. A
        duplicate is a file that has the same name as another one, regardless
        of its path or compression state.
        '''

        result = {'host' : self.host, 'paths' : []}
        allPaths = []
        for path in self.searchPaths:
            allPaths += [os.path.join(path, p) for p in self.searchPatterns]
        hostList = [self.host]
        if use_io_buffer:
            hostList +=self.io_buffers
        if use_archive:
            hostList += self.archives
        hostIndex = 0
        allFound = False
        lastHost = False
        # search every host
        while (not allFound) and (not lastHost):
            theHost = hostList[hostIndex]
            self.logger.info('Trying %s...' % theHost)
            pathsFound = theHost.find(allPaths, restrictPattern)
            numFound = len(pathsFound)
            if numFound > 0:
                allFound = True
                if numFound < self.numFiles and restrictPattern is None:
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

    def fetch(self, targetDir, useArchive=None, decompress=True, 
              restrictPattern=None):
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

            restrictPattern - A string, to be interpreted as a regular 
                expression, to filter among all the possible files. This is 
                useful for finding just a single tile from all the possible 
                ones.

        Returns:

            A list of strings with the full paths of the files that have been
            fetched.
        '''

        found = self.find(useArchive=useArchive, 
                          restrictPattern=restrictPattern)
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

    def send(self, destHost=None, destDir=None, filePath=0):
        '''
        Send files from their own host to destHost.
        '''

        if destHost is None:
            destHost = self.host
        found = self.find(useArchive=False)['paths']
        if len(found) > 0:
            if destDir is None:
                relDir = os.path.join(destHost.dataPath, 
                                      self.searchPaths[filePath])
            else:
                relDir = os.path.join(destHost.dataPath, destDir, 
                                      self.searchPaths[filePath])
            sent = self.host.send(found, relDir, destHost)
        else:
            self.logger.warning('Couldn\'t send. Files are not found '\
                                'in the host.')
            sent = None
        return sent

    def archive(self, activeArchive=0):
        '''
        Sends files to the archive.

        Inputs:

            activeArchive - An integer specifying the index in the list of
                available archives.

        Returns:

            A two-element tuple. The first element is the return code of the
            sending operation (zero means success). The second element is a 
            list of paths to the sent files on their respective host.
        '''

        if self.toArchive:
            theArchive = self.archives[activeArchive]
            sent = self.send(theArchive)
        else:
            self.logger.info('%s is not marked as \'archive\' in the '\
                             'settings. Skipping...' % self.name)
            sent = (0, [])
        return sent

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
        Remove duplicate filepaths from the list even if some are bzipped.

        When the same file is present in both bzipped2 and normal form, the 
        normal file is prefered.
        '''

        uniquePaths = []
        uniqueBasenames = []
        for path in pathList:
            basename = os.path.basename(path)
            noExtension = re.sub(r'\.bz2$', '', basename)
            if basename not in uniqueBasenames:
                uniqueBasenames.append(basename)
                uniquePaths.append(path)
            else:
                index = uniqueBasenames.index(basename)
                if uniquePaths[index].endswith('.bz2'):
                    uniquePaths[index] = path
        return uniquePaths

    def get_path(self, markedString, obj):
        '''
        Return a path that has been specified via the markedString mechanism.

        Inputs:

            markedString
        '''
        
        if markedString.string == 'fromOriginator':
            dirName = markedString.name
            parentPackObj = None
            parent = ss.Package.objects.get(name=self.parent.name)
            packOutsSettings = parent.packageOutput_systemsettings_packageoutput_related.all()
            if len(packOutsSettings) > 0: # the parent package has outputs
                if self.name in [po.outputItem.name for po in packOutsSettings]:
                    # this instance is an output of its own parent package
                    parentPackObj = self.parent
            if parentPackObj is None:
                # haven't been able to find out the package that originated 
                # this instance yet
                for pSetts in ss.Package.objects.all():
                    outpSetts = pSetts.packageOutput_systemsettings_packageoutput_related.all()
                    for pOut in outpSetts:
                        if pOut.outputItem.name == self.name:
                            #self.logger.info('%s\'s parent is %s' % 
                            #                 (self.name, pSetts.name))
                            parentPackObj = self._create_originator_pack(pOut)
            fullPath = eval('parentPackObj.%s' % dirName)
            correctedDateDirs = self._correct_date_directories(fullPath)
            # trimming the first character in order to eliminate the '/'
            relativePath = correctedDateDirs.replace(self.parent.host.dataPath, '')[1:]
            thePath = relativePath
        else:
            thePath = utilities.parse_marked(markedString, obj)
        return thePath

    def _correct_date_directories(self, path):
        dateDirPatt = re.compile(r'\d{4}/\d{2}/\d{2}')
        correctDateDir = self.timeslot.strftime('%Y/%m/%d')
        return dateDirPatt.sub(correctDateDir, path)

    def _create_originator_pack(self, outputSettings):
        '''
        Return the package from where this instance is an output.

        Usually a G2File instance can be an input to several packages
        but it can only be an output from one package. However, there
        can be special cases where a G2File instance is the output
        from more than one package (for example the 'latest mapfile'
        is an output from the 'prepare_wms_dssf', 'prepare_wms_dslf'
        and other packages). In this case, this method will assume
        that it is good enough just to pick one of the possible
        originator packages and return it. This should be a good enough
        approach as most of the time we will be interested in the output
        directory of the parent package, and that will be the same.
        '''

        packSettings = outputSettings.package
        specificTimeslots = outputSettings.specificTimeslots.all()
        if len(specificTimeslots) == 0:
            # the package's timeslot is the same as the output's
            theTimeslot = self.timeslot
        else:
            # find this g2f in the outputs, take its displacement and create
            # a new timeslot simmetrically displaced
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
        theClass = packSettings.code_class.className
        theHost = ss.Host.objects.get(name=self.host.name)

        pack = None
        # lets see if the package has been created before already
        for aPack in self._originatorPackages:
            if aPack.name == packSettings.name and \
                    aPack.source.area == theArea.name and \
                    aPack.timeslot == theTimeslot and \
                    aPack.__class__.__name__ == theClass:
                        pack = aPack
        if pack is None:
            pack = eval('g2p.%s(packSettings, theTimeslot, theArea, theHost, '\
                        'createIO=False)' % theClass)
            self._originatorPackages.append(pack)
        return pack

    def __repr__(self):
        return self.name
