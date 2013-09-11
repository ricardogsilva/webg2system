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
        self.toDelete = fileSettings.toDelete
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
        hf = HostFactory()
        return [hf.create_host(hs) for hs in specific_buffers]

    def _get_archives(self, settings):
        '''
        Return a list of G2Host instances that are the archives for this file.

        The G2Host list is created from the specificArchives attribute. If
        there are no specificArchives defined, then all the hosts that have
        the 'archive' role and are 'active' will be used.
        '''

        specific_archives = settings.specificArchives.all()
        if len(specific_archives) == 0:
            specific_archives = [hs for hs in \
                ss.Host.objects.filter(role__name='archive', active=True)]
        hf = HostFactory()
        return [hf.create_host(hs) for hs in specific_archives]

    #def find(self, restrict_pattern=None, use_archive=False, 
    #         use_io_buffer=True, 
    #         staticFiles='latest timeslot absolute'):
    #    '''
    #    Find the files and return their fullPaths.

    #    Inputs:

    #        restrict_pattern - A string, to be interpreted as a regular 
    #            expression, to filter among all the possible files. This is 
    #            useful for finding just a single tile from all the possible 
    #            ones.

    #        use_archive - A boolean indicating if the file's specific 
    #            archives are to be searched. Defaults to False.

    #        use_io_buffer - A boolean indicating if the file's io_buffer
    #            hosts are to be searched. Defaults to True.

    #        search_archive_through_io_buffer - A boolean indicating if the
    #            io_buffer hosts should be used to search the archives if
    #            the paths are not find in their own filesystems.

    #        staticFiles - A string indicating what behaviour to adopt for
    #            static files. Accepted values:
    #                - latest timeslot absolute: The files are assumed to have 
    #                    a timeslot on their filename. They are sorted and only
    #                    the latest file is fetched. Being the latest means 
    #                    that the file is as recent as the instance's timeslot,
    #                    but not more recent than that. This is the default 
    #                    behaviour.
    #                - latest timeslot month: Works like 'latest timeslot day'
    #                    but only the files that have the same month as the 
    #                    instance's timeslot are relevant for the fetching.
    #                - latest run: The files are assumed to have a run pattern
    #                    on their filename. they are sorted accordingly and
    #                    the latest run is returned.
    #                - first: The first file in the filelist is fetched.
    #                - all: All the files in the file are fetched.

    #    Returns:

    #        A dictionary with keys 'host' and 'paths'. The values are a G2Host
    #        object and a list with the full paths to the files.

    #    NOTE: The files may be searched for, in order, in the following hosts:
    #            - the file\'s own host;
    #            - the file\'s io_buffers. This can be disabled with the 
    #              use_io_buffer argument;
    #            - the file\'s archives. This can be disabled with the
    #              use_archive argument.
    #          By default, this method will search for the files in the file\'s
    #          own host and then in the io_buffers, not using the archives at
    #          all. The prefered way to execute a thorough search is to try to
    #          find the files in the io_buffer and let the io_buffer connect to
    #          the archives to search for the files there.

    #    This method will also remove any duplicate files from the list. A
    #    duplicate is a file that has the same name as another one, regardless
    #    of its path or compression state.
    #    '''

    #    result = {'host' : self.host, 'paths' : []}
    #    allPaths = []
    #    for path in self.searchPaths:
    #        allPaths += [os.path.join(path, p) for p in self.searchPatterns]
    #    hostList = set([self.host])
    #    if use_io_buffer:
    #        hostList.update(self.io_buffers)
    #    if use_archive:
    #        hostList.update(self.archives)
    #    hostIndex = 0
    #    allFound = False
    #    lastHost = False
    #    # search every host
    #    while (not allFound) and (not lastHost):
    #        theHost = hostList[hostIndex]
    #        self.logger.info('Trying %s...' % theHost)
    #        pathsFound = theHost.find(allPaths, restrict_pattern)
    #        numFound = len(pathsFound)
    #        if numFound > 0:
    #            allFound = True
    #            if numFound < self.numFiles and restrict_pattern is None:
    #                self.logger.warning('Not all files have been found. '\
    #                       'Found %i files. Was expecting at least %i.' 
    #                        % (numFound, self.numFiles))
    #            result['host'] = theHost
    #            uniquePaths = self._return_unique_file_names(pathsFound)
    #            result['paths'] = self._filter_file_list(uniquePaths, 
    #                                                     staticFiles)
    #        if hostIndex + 1 == len(hostList):
    #            lastHost = True
    #        else:
    #            hostIndex += 1
    #    return result

    def _find_in_archive(self, archive_host, path_patterns, 
                         restrict_pattern=None, 
                         through_io_buffer=False):
        if through_io_buffer:
            found = self._find_through_io_buffers(archive_host, path_patterns,
                                                  restrict_pattern)
        else:
            found = archive_host.find(path_patterns, restrict_pattern)
        return found

    def _find_through_io_buffers(self, other_host, path_patterns, 
                                 restrict_pattern=None):
        '''
        Search other_host through the io_buffers.
        '''

        all_found = False
        last_host = False
        host_index = 0
        while (not all_found) and (not last_host):
            h = self.io_buffers[host_index]
            self.logger.debug('Searching through %s (io_buffer)...' % h.name)
            found = h.find_in_remote(other_host, path_patterns, 
                                     restrict_pattern)
            if len(found) > 0:
                all_found = True
            if host_index + 1 == len(self.io_buffers):
                last_host = True
            else:
                host_index += 1
        return found

    def _find_in_io_buffer(self, io_buffer_host, path_patterns, 
                           restrict_pattern=None,
                           go_to_archives=False):
        '''
        Search the io_buffers for the files.
        '''

        found = io_buffer_host.find(path_patterns, restrict_pattern)
        if len(found) == 0 and go_to_archives:
            self.logger.debug('going to the archives through %s ' \
                              '(io buffer)...' % io_buffer_host.name)
            all_found = False
            last_host = False
            host_index = 0
            while (not all_found) and (not last_host):
                arch_host = self.archives[host_index]
                self.logger.debug('Trying %s...' % arch_host)
                if io_buffer_host == self.host:
                    # perform a normal find on the archives
                    found = self._find_in_archive(arch_host, path_patterns, 
                                                  restrict_pattern)
                else:
                    # perform a 'through find' using the external script
                    found = self._find_in_archive(arch_host, path_patterns, 
                                                  restrict_pattern, 
                                                  through_io_buffer=True)
                if len(found) > 0:
                    all_found = True
                if host_index + 1 == len(self.archives):
                    last_host = True
                else:
                    host_index += 1
        return found

    def _sort_hosts(self, use_local, use_io_buffer, use_archive):
        host_list = []
        if use_local:
            host_list.append(self.host)
        if use_io_buffer:
            for h in self.io_buffers:
                if h not in host_list:
                    host_list.append(h)
        if use_archive:
            for h in self.archives:
                if h not in host_list:
                    host_list.append(h)
        return host_list

    def find(self, use_local=True, use_io_buffer=False, use_archive=False,
             static_files='latest timeslot absolute', restrict_pattern=None,
             io_buffer_goes_to_archive=True):
        '''
        '''

        result = {'host' : None, 'paths' : []}
        all_paths = []
        for path in self.searchPaths:
            all_paths += [os.path.join(path, p) for p in self.searchPatterns]
        all_found = False
        last_host = False
        host_index = 0
        host_list = self._sort_hosts(use_local, use_io_buffer, use_archive)
        if len(host_list) > 0:
            while (not all_found) and (not last_host):
                the_host = host_list[host_index]
                self.logger.debug('Trying %s...' % the_host)
                if the_host in self.archives and use_archive: # this order of the if block seems incorrect...
                    self.logger.debug('using the _find_in_archive method')
                    found = self._find_in_archive(the_host, all_paths, 
                                                  restrict_pattern)
                elif the_host in self.io_buffers and use_io_buffer:
                    self.logger.debug('using the _find_io_buffers method')
                    found = self._find_in_io_buffer(
                        the_host, 
                        all_paths, 
                        restrict_pattern, 
                        go_to_archives=io_buffer_goes_to_archive
                    )
                elif the_host == self.host and use_local:
                    self.logger.debug('using the _find_local method')
                    found = self.host.find(all_paths, restrict_pattern)
                num_found = len(found)
                if num_found > 0:
                    all_found = True
                    if num_found < self.numFiles and restrict_pattern is None:
                        self.logger.warning('Not all files have been found. '\
                               'Found %i files. Was expecting at least %i.' 
                                % (num_found, self.numFiles))
                    result['host'] = the_host
                    unique_paths = self._return_unique_file_names(found)
                    result['paths'] = self._filter_file_list(unique_paths, 
                                                             static_files)
                if host_index + 1 == len(host_list):
                    last_host = True
                else:
                    host_index += 1
        return result

    def fetch(self, targetDir, use_archive=False, use_io_buffer=False,
              decompress=True, restrict_pattern=None):
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

            use_archive - A boolean indicating if the files are to be searched
                for in the archives, in case they cannot be found in host.

            use_io_buffer - A boolean indicating if the fies are to be searched
                for in the io buffers in case they cannot be found in the host.
                
            decompress - A boolean indicating if the newly fetched files are
                to be decompressed. It only affects files which have actually
                been fetched, so if a file has the "copy" attribute set as
                False (meaning it will not be copied), it will never be
                decompressed.

            restrict_pattern - A string, to be interpreted as a regular 
                expression, to filter among all the possible files. This is 
                useful for finding just a single tile from all the possible 
                ones.

        Returns:

            A list of strings with the full paths of the files that have been
            fetched.
        '''

        found = self.find(use_archive=use_archive, 
                          restrict_pattern=restrict_pattern, 
                          use_io_buffer=use_io_buffer)
        result = found['paths']
        if self.toCopy:
            if len(found['paths']) > 0:
                fetched = self.host.fetch(found['paths'], targetDir, 
                                          found['host'])
                if decompress:
                    decompressed = self.host.decompress(fetched)
                    result = decompressed
                else:
                    result = fetched
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
        found = self.find(use_archive=False)['paths']
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

    def disseminate(self, temp_dir, dest_host=None, dest_dir='', file_path=0,
                    remote_protocol='sftp', compress=False, notify=[],
                    use_archive=False, use_io_buffer=False):
        '''
        Send file from its own host to dest_host.

        Inputs:

            temp_dir - A string specifying a temporary directory where the 
                files will be placed in case they have to be fetched from 
                other host

            dest_host - A G2Host instance. A value of None (the default)
                will be interpreted as the local host.

            dest_dir - A string with the path on the remote host where
                the file is to be sent to. If it starts with / then an
                absolute path is assumed. Otherwise the path will be
                assumed to be relative to dest_host's dataPath. A value
                of None (the default) will cause the file to be disseminated
                to the same directory structure as if has defined in its
                settings, only relative to it's target host's dataPath.

            file_path - An integer specifying which of the file's paths
                are to be used.

            remote_protocol - A string indicating the name of the remote
                protocol to use when sending the files. Currently supported
                protocols are 'sftp' and 'ftp'. Defaults to 'sftp'.

            compress - A boolean indicating if the files are to be compressed
                before sending

            notify - A list of string indicating types of notification to send
                with the sending status.

            use_archive - A boolean indicating if the files should be fetched
                from the archives in case they are not found locally

            use_io_buffer - A boolean indicating if the files should be fetched
                from the available io buffers in case they are not found 
                locally
        '''

        if dest_host is None:
            dest_host = HostFactory.get_host(logger=self.logger)
        if dest_dir is None:
            target_path = os.path.join(dest_host.dataPath,
                                    self.searchPath[file_path])
        elif dest_dir.startswith('/'):
            target_path = dest_dir
        else:
            target_path = os.path.join(dest_host.dataPath, dest_dir)
        fetched = self.fetch(temp_dir, use_archive=use_archive, 
                             use_io_buffer=use_io_buffer, decompress=True,
                             restrict_pattern=None)
        result = False
        if len(fetched) > 0:
            if compress:
                fetched = self.host.compress(fetched)
            return_code, sent_paths = self.host.send(
                fetched,
                target_path,
                dest_host,
                remoteProtocol=remote_protocol
            )
            if return_code == 0:
                result = True
            for notification_type in notify:
                # not implemented yet
                pass
        return result
