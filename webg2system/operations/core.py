import os

# assorted functions

def show_status(status, progress):
    '''
    This function is a callback to report on progress...
    '''
    print(status, progress)

def parse_marked(markedStringObj, obj):
    '''
    Parse the marked string.
    '''

    markSign = '#'
    markList = [i.strip() for i in markedStringObj.marks.split(',')]
    realMarks = convert_marks(markList, obj)
    newString = markedStringObj.string
    counter = 0
    while newString.partition(markSign)[1] != '':
        partList = newString.partition(markSign)
        newString = partList[0] + str(realMarks[counter]) + partList[2]
        counter += 1
    return newString

# FIXME - Implement specificsource recognition for the marks
def convert_marks(markList, obj):
    newMarks = []
    for mark in markList:
        markValue = None
        if mark == 'source':
            markValue = obj.source
        else:
            try:
                markValue = eval('obj.%s' % mark)
            except AttributeError:
                pass
        newMarks.append(markValue)
    return newMarks


class GenericItem(object):
    '''
    All GenericItems must have:
        - timeslot
        - source
        - host
    '''

    def __init__(self, timeslot, source, host):
        self.timeslot = timeslot
        self.source = source
        self.host = host

    @property
    def year(self):
        return self.timeslot.strftime('%Y')

    @property
    def month(self):
        return self.timeslot.strftime('%m')

    @property
    def day(self):
        return self.timeslot.strftime('%d')

    @property
    def hour(self):
        return self.timeslot.strftime('%H')

    @property
    def minute(self):
        return self.timeslot.strftime('%M')


class GenericPackage(GenericItem):
    '''
    Base class for ALL G2Packages.

    All GenericPackages must inherit from GenericItem and provide concrete
    implementations for the method stubs defined here.
    '''

    def prepare(self, callback):
        raise NotImplementedError

    def run_main(self, callback):
        raise NotImplementedError

    def clean_up(self, callback):
        raise NotImplementedError

    def ensure_dirs(self, *dirlist):
        for directory in dirlist:
            if not self.host.is_dir(directory):
                self.host.make_dir(directory)


class FetchData(GenericPackage):
    '''
    This class uses:

        - outputDir
    '''

    def __init__(self, settings, timeslot, source, host):
        '''
        '''

        super(FetchData, self).__init__(timeslot, source, host)
        self.rawSettings = settings
        self.host = host
        relativeOutDir = parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        self.outputDir = os.path.join(self.host.basePath, relativeOutDir)
        # not creating any G2File objects yet
        self.inputs = settings.inputs.all()
        self.outputs = settings.packageOutput_systemsettings_packageoutput_related.all()

    def _create_inputs(self):
        for inpSettings in self.rawSettings.packageInput_system_settings_packageinput_related.all():
            pass

    def prepare(self, callback):
        import time
        callback('sleeping a bit...', 1)
        time.sleep(20)
        return 0

    def run_main(self, callback):
        return 0

    def clean_up(self, callback):
        return 0

#
#    #@log_calls
#    def _create_files(self, fileRole):
#        '''
#        Create the default files as defined in the settings file.
#
#        This method creates G2File instances and adds them to this package
#        under its 'inputs' or 'outputs' attribute.
#        This method is temporary, as it should become useless once this
#        app is converted to django (a plan for the future).
#
#        Inputs:
#
#            fileRole - A string which can be either 'inputs' or 'outputs'.
#                It specifies what type of files are to be created.
#        '''
#        
#        g2fList = []
#        optionalList = []
#        filesParamList = utilities.get_package_details(self.name)[fileRole]
#        for fileDict in filesParamList:
#            self.logger.debug('Creating %s...' % fileDict['name'])
#            timeslotsToCreate = self._sort_file_timeslots(fileDict)
#            sourcesToCreate = self._sort_file_sources(fileDict)
#            for timeslotSTR in timeslotsToCreate:
#                for source, area in sourcesToCreate:
#                    newFile = factories.create_file(fileDict['name'], 
#                                                    timeslotSTR, source, area,
#                                                    None)
#                    if newFile is not None:
#                        g2fList.append(newFile)
#                        if fileDict['optional']:
#                            optionalList.append(newFile)
#                    else:
#                        self.logger.error("Couldn't create %s object." \
#                                          % fileDict['name'])
#        return g2fList, optionalList
#
#    #@log_calls
#    def _sort_file_timeslots(self, fileSettings):
#        '''
#        Returns a list of timeslot strings for the files that are about to be 
#        created.
#        '''
#
#        timeslots = []
#        timeslotAds = fileSettings['timeslotAdjustments']
#        if len(timeslotAds) != 0:
#            for tsDict in timeslotAds:
#                adjustUnit = tsDict['unit'] 
#                adjustValue = tsDict['displace'] 
#                if adjustUnit == 'minute':
#                    delta = dt.timedelta(minutes=adjustValue)
#                elif adjustUnit == 'hour':
#                    delta = dt.timedelta(hours=adjustValue)
#                elif adjustUnit == 'day':
#                    delta = dt.timedelta(days=adjustValue)
#                else:
#                    delta = dt.timedelta()
#                newTimeslot = self.timeslot + delta
#                timeslots.append(newTimeslot.strftime('%Y%m%d%H%M'))
#        else:
#            timeslots.append(self.timeslot.strftime('%Y%m%d%H%M'))
#        return timeslots
#
#    #@log_calls
#    def _sort_file_sources(self, fileSettings):
#        '''
#        Returns a list of sources for the files that are about to be created.
#        '''
#
#        packDetails = utilities.get_package_details(self.name)
#        sources = []
#        if len(fileSettings['sources']) != 0:
#            for sourceTup in fileSettings['sources']:
#                source, area = sourceTup
#                sources.append((source, area))
#        else:
#            #apply only one source with defaultSource and defaultArea
#            sources.append((modeDetails['defaultSource'], 
#                            modeDetails['defaultArea']))
#        return sources
#
#    
#    #@log_calls
#    def find_files(self, g2files, hostName=None, useArchive=None):
#        '''
#        Inputs:
#
#            g2files - A list of g2file instances
#
#            hostName - A string with the host's name. A value of None (the
#                default) will use each file's default host.
#
#            useArchive - A string indicating what kind of file is to be
#                searched for in the archives. Accepted values are 'inputs'
#                and 'outputs'. A value of None (the default) causes the
#                archives not to be searched at all.
#
#        Returns:
#            A dictionary with the input g2files as keys and another 
#            sub-dictionary as values. This sub-dictionary contais a 'paths' 
#            key with a list of strings with full file paths as values and 
#            another key 'host', with the name of the host where the files have
#            been found as values. If a g2file was not found in any of the given
#            hostNames, the corresponding value for its key will be None.
#        '''
#
#        result = dict()
#        for g2f in g2files:
#            self.logger.info('Looking for %s...' % g2f.name)
#            result[g2f] = g2f.find(hostName, useArchive)
#        return result
#
#    #@log_calls
#    def find_inputs(self, hostName=None, useArchive=False):
#        '''
#        Look for this package's inputs.
#
#        Inputs:
#
#            hostName - A string specifying the name of a host in which to
#                search the inputs. A value of None (the default) will use
#                each input's default host.
#
#            useArchive - A boolean indicating if the files are to be searched
#                for in the archvies, in case they cannot be found in host.
#
#        Returns:
#
#            A dictionary with the package's inputs as keys and
#            sub-dictionaries as values. These sub-diciotnaries have
#            two keys: 'host' and 'paths' and specify the name of the host
#            where the files have been found and the full paths to the files.
#        '''
#
#        if useArchive:
#            useArchive = 'inputs'
#        else:
#            useArchive = None
#        return self.find_files(self.inputs, hostName, useArchive)
#
#    #@log_calls
#    def find_outputs(self, useArchive=False):
#        if useArchive:
#            useArchive = 'outputs'
#        else:
#            useArchive = None
#        return self.find_files(self.outputs, None, useArchive)
#
#    #@log_calls
#    def _get_relative_path(self, fullPath):
#        '''Return a path's relative path.'''
#
#        relPath = fullPath.replace(self.host.basePath + os.path.sep, '')
#        return relPath
#
#    #@log_calls
#    def fetch_files(self, g2files, relTargetDir, hostName=None,
#                    useArchive=None, forceCopy=False, decompress=False):
#        '''
#        Fetch the input g2files from their destination to relTargetDir.
#
#        If a file is on a remote host, it will always be copied to the target
#        directory, regardless of its compression state. If a file is on a
#        local host and it is compressed it will also always get copied over
#        to the target directory, regardless of it being decompressed
#        afterwards or not. The decompression of files is always done after 
#        copying them to the target directory and can be controlled by the
#        'decompress' argument. If a file is on a local host and it is not
#        compressed, it may be copied to the target dir or left at its original
#        location, depending on the value of the 'forceCopy' argument.
#
#        Inputs:
#
#            g2files - A list of G2File instances specifying the files that
#                are to be fetched.
#
#            relTargetDir - The relative (relative to the host) path to the
#                directory, where files should be placed if they were
#                originally in a compressed form.
#
#            hostName - A string with the names of a G2Host where the files 
#                are to be copied from.
#
#            <------
#            useArchive - A boolean indicating if the files are to be searched
#                for in the archives, in case they cannot be found in host.
#                ------->
#
#            forceCopy - A boolean indicating if the files should be copied
#                to the target directory even if they are not compressed. The
#                default is False.
#
#            decompress - A boolean indicating if the files should be
#                decompressed after being copied to the target directory.
#                The default is False.
#
#        Returns:
#            A dictionary with the input g2files as keys and a sub-dictionary
#            as values. This sub-dictionary contains...
#        '''
#
#        for g2f in g2files:
#            paths = g2f.fetch(relTargetDir, hostName, useArchive=useArchive,
#                              forceCopy=forceCopy)
#            if decompress:
#                relPaths = [self._get_relative_path(p) for p in paths]
#                paths = self._decompress_files(relPaths)
#            return paths
#
#    #@log_calls
#    def _decompress_files(self, pathList):
#        '''
#        Decompress the files in pathList and return their new path.
#        '''
#
#        return self.host.decompress(pathList)
#
#    #@log_calls
#    def fetch_inputs(self, hostName=None, useArchive=False):
#        self.ensure_dirs(self.outputDir)
#        fetchedFiles = self.fetch_files(self.inputs, self.outputDir, hostName,
#                                        useArchive, forceCopy=True, 
#                                        decompress=False)
#
#    #@log_calls
#    def send_outputs(self, relTargetDir, destHost):
#        '''
#        Copy this package's outputs to another directory at the specified host.
#
#        Inputs
#
#            relTargetDir - The relative path to a destination directory where
#                the files will be copied to.
#
#            destHost - A G2Host object.
#        '''
#
#        #return self._fetch_files('outputs', relTargetDir)
#        raise NotImplementedError
#
#    #@log_calls
#    def delete_outputs(self):
#        '''
#        Delete this package's outputs from their final output directories.
#
#        This method can be overriden by specialized classes in order to
#        introduce some filtering mechanism to allow the deleting of only
#        a subset of the outputs.
#        '''
#
#        absolutePaths = self.find_outputs()
#        for absPath in absolutePaths:
#            relPath = self._get_relative_path(absPath)
#            self.host.delete_file(relPath)
#
#    #@log_calls
#    def _delete_directories(self, *leafDirs):
#        '''
#        Recursively delete leafDirs and any empty parent directories.
#
#        Inputs:
#
#            leafDirs - A list of strings with the relative paths to the
#                leaf directories to delete.
#        '''
#
#        # not done yet, I guess it is not really recursive
#        for leafDir in leafDirs:
#            self.host.remove_dir(leafDir)
#
#    #@log_calls
#    def delete_output_dir(self):
#        return self._delete_directories(self.outputDir)
#
#    #@log_calls
#    def package_can_be_processed(self, useArchive=False):
#        '''
#        Determine if the available files are enough for processing.
#
#        Inputs:
#
#            useArchive - A boolean indicating if the files are to be searched
#                for in the archvies, in case they cannot be found in host.
#
#        Returns:
#
#            A boolean indicating if all the required inputs are available for
#            further fetching and processing.
#        '''
#
#        found = self.find_inputs(useArchive=useArchive)
#        result = True
#        for g2f, foundDict in found.iteritems():
#            self.logger.info('Evaluating %s...' % g2f.name)
#            if g2f not in self.optionalInputs:
#                # this g2file is mandatory
#                self.logger.info('%s is a mandatory file' % g2f.name)
#                if foundDict is None:
#                    self.logger.info('Couldn\'t find %s' % g2f.name)
#                    result = False
#        return result
