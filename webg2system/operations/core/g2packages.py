import os
import time
import re
from uuid import uuid1
import datetime as dt
import zipfile

import systemsettings.models as ss

from g2item import GenericItem
from g2files import G2File
from g2hosts import HostFactory
import mappers
import metadatas
import utilities

# to be deleted!
import logging

import mapscript

# TODO
# - Add a archive_ouputs() method to the package classes, that should use a _send_files
# - Add a delete_outputs() method to all the package classes and implement a hook for it
#   in the clean_up() method

class Outra(object):
    '''
    A dummy class that just sleeps for two minutes.

    This is just for testing the daemonization of RunningPackage instances.
    '''

    def __init__(self, *args, **kwargs):
        self.logger = kwargs['logger']
        #cb_handler = CallBackHandler(kwargs['callback'])
        #self.logger.addHandler(cb_handler)
        self.logger.debug('In the __init__ method')

    def clean_up(self, callback=None):
        pass

    def outputs_available(self):
        return False

    def run_main(self, callback=None, sleepSecs=5, sleepSteps=3):
        import time
        self.logger.debug('a dummy debug message.')
        self.logger.error('a dummy error message.')
        counter = 1
        self._use_callback(
            callback, 
            'About to sleep for %i seconds...' % (sleepSecs * sleepSteps), 
        )
        while counter <= sleepSteps:
            time.sleep(sleepSecs)
            self._use_callback(
                callback,
                'Still asleep - %i seconds have passed' % (counter * sleepSecs),
            )
            if counter == 2:
                self._use_callback(callback, 'Raised some error')
                raise ValueError
            counter += 1
        self._use_callback(callback, 'Not sleeping anymore, yeah!')
        return 0

    def _use_callback(self, theCallback, *args):
        msg = []
        for msgBit in args:
            msg.append(msgBit)
        theCallback(msg)


class GenericPackage(GenericItem):
    '''
    Base class for ALL G2Packages.

    All GenericPackages must inherit from GenericItem and provide concrete
    implementations for the method stubs defined here.

    The private methods (the ones indicated with '_' before their name) are
    concrete implementations that should not need to be reimplemented.
    '''

    name = ''

    def delete_outputs(self, callback=None):
        raise NotImplementedError

    def run_main(self, callback=None):
        raise NotImplementedError

    def clean_up(self, callback=None):
        raise NotImplementedError

    def __unicode__(self):
        return unicode(self.name)

    def _use_callback(self, theCallback, *args):
        msg = []
        for msgBit in args:
            msg.append(msgBit)
        theCallback(msg)

    def _create_files(self, fileRole, filesSettings):
        '''
        Inputs:

            fileRole - A string which can be either 'input' or 'output'.

            filesSettings - A list of systemsettings.models.package<Input|Output>
        '''

        objects = []
        hostSettings = ss.Host.objects.get(name=self.host.name)
        for specificSettings in filesSettings:
            timeslots = []
            for tsDisplacement in specificSettings.specificTimeslots.all():
                timeslots += utilities.displace_timeslot(self.timeslot, 
                                                         tsDisplacement)
            if len(timeslots) == 0:
                timeslots.append(self.timeslot)
            specificAreas = [a for a in specificSettings.specificAreas.all()]
            if len(specificAreas) == 0:
                specificAreas = ss.Source.objects.get(\
                                name=self.source.generalName).area_set.all()
            for spArea in specificAreas:
                for spTimeslot in timeslots:
                    # create a new input
                    generalFileSettings = eval('specificSettings.%sItem.file' \
                                               % fileRole)
                    newObject = G2File(generalFileSettings, spTimeslot, spArea,
                                       hostSettings, 
                                       optional=specificSettings.optional,
                                       parent=self,
                                       logger=self.logger)
                    objects.append(newObject)
        return objects

    def _find_files(self, g2files, useArchive, restrictPattern=None):
        '''
        Inputs:

            g2files - A list of g2file instances

            useArchive - A boolean indicating if the archives are to be
                searched if the files are not found in their expected
                location.

            restrictPattern - A string, to be interpreted as a regular 
                expression, to filter among all the possible files. This is 
                useful for finding just a single tile from all the possible 
                ones.

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
            if int(g2f.hour) in g2f.exceptHours:
                self.logger.info('%s is not supposed to be available at %s '\
                                 'hour. Skipping...' % (g2f.name, g2f.hour))
            else:
                self.logger.debug('Looking for %s...' % g2f.name)
                result[g2f] = g2f.find(use_archive=useArchive, 
                                       restrict_pattern=restrictPattern)
        return result

    def _fetch_files(self, g2files, relTargetDir, useArchive, 
                     decompress=False, restrictPattern=None):
        '''
        Fetch the input g2files from their destination to relTargetDir.

        After being copied the files will optionally be decompressed, in
        order to be ready for further usage.

        Inputs:
            
            g2files - A list of G2File instances specifying the files that
                are to be fetched.

            relTargetDir - The relative (relative to the host) path to the
                directory, where files should be placed if they were
                originally in a compressed form.

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
        
        A dictionary with the input g2files as keys and a list with the full 
        paths to the newly fetched files.
        '''
        
        result = dict()
        for g2f in g2files:
            if int(g2f.hour) in g2f.exceptHours:
                self.logger.info('%s is not supposed to be available at %s '\
                                 'hour. Skipping...' % (self.name, self.hour))
            else:
                self.logger.info('Fetching %s...' % g2f.name)
                localPathList = g2f.fetch(relTargetDir, useArchive, 
                                          decompress=decompress, 
                                          restrict_pattern=restrictPattern)
                result[g2f] = localPathList
        return result

    # FIXME
    # - Test this method out
    def _send_files(self, g2files, destDir=None, destHost=None, filePath=0):
        '''
        Send the input g2files to destinationDir.

        Inputs:

            g2files - A list of operations.core.g2files.G2File objects

            destDir - A relative directory where the files will be put. 
                If specified, the files will be sent to: 
                    
                    <destHost.basePath>/<destDir>/<g2file.searchPaths[filePath]>

                If None, the files are sent to:

                    <destHost.basePath>/<g2file.searchPaths[filePath]>

            destHost - A G2Host instance specifying the host that will receive
                the files. A value of None (the default) is interpreted as 
                meaning the local host.

            filePath - The number of the searchPath that will be used for
                specifying where on the destHost the files will be put.
                Should be left at the default value (zero) for most cases.

        Returns:
        
        A dictionary with the input g2files as keys and a list with the full 
        paths to the newly sent files on the destinationHost.
        '''

        sentResult = dict()
        for g2f in g2files:
            sent = g2f.send(destHost, destDir, filePath)
            if sent[0] != 0:
                self.logger.warning('There has been an error sending %s' \
                                    % g2f.name)
            sentResult[g2f] = sent[1]
        return sentResult

    def _delete_directories(self, dirPaths):
        '''
        Delete the directories specified and any contents they may have.

        Also deletes any parent directories that may become empty.
        '''

        for dirPath in dirPaths:
            self.host.remove_dir(dirPath)

    def _compress_files(self, g2files):
        '''
        Compress the input g2files with bzip2.

        Returns:
        
        A dictionary with the input g2files as keys and a list with the full 
        paths to the newly compressed files.
        '''

        theG2Files = [f for f in g2files if f.toCompress==True]
        for g2f in [f for f in g2files if f.toCompress==False]:
            self.logger.info('%s is not marked as \'compress\' in the '\
                             'settings. Skipping...' % g2f)
        foundFiles = self._find_files(theG2Files, useArchive=False)
        toCompress = []
        for g2f, foundDict in foundFiles.iteritems():
            for p in foundDict['paths']:
                toCompress.append(p)
        # we send them in bulk for compression but have to separate them 
        # afterwards
        compressedPaths = self.host.compress(toCompress)
        compressed = dict()
        pathPairs = []
        for path in compressedPaths:
            for g2f in foundFiles.keys():
                for pattern in g2f.searchPatterns:
                    reObj = re.search(pattern, path)
                    if reObj is not None:
                        pathPairs.append((g2f, path))
        for g2f, path in pathPairs:
            if compressed.get(g2f) is None:
                compressed[g2f] = [path]
            else:
                compressed[g2f].append(path)
        return compressed

    def _decompress_files(self, g2files):
        '''
        Decompress the input g2files with bunzip2.

        Returns:
        
        A dictionary with the input g2files as keys and a list with the full 
        paths to the newly decompressed files.
        '''

        foundFiles = self._find_files(g2files, useArchive=False)
        toDecompress = []
        for g2f, foundDict in foundFiles.iteritems():
            for p in foundDict['paths']:
                toDecompress.append(p)
        # we send them in bulk for decompression but have to separate them 
        # afterwards
        decompressedPaths = self.host.decompress(toDecompress)
        decompressed = dict()
        pathPairs = []
        for path in decompressedPaths:
            for g2f in foundFiles.keys():
                for pattern in g2f.searchPatterns:
                    reObj = re.search(pattern, path)
                    if reObj is not None:
                        pathPairs.append((g2f, path))
        for g2f, path in pathPairs:
            if decompressed.get(g2f) is None:
                decompressed[g2f] = [path]
            else:
                decompressed[g2f].append(path)
        return decompressed


class ProcessingPackage(GenericPackage):

    def __init__(self, settings, timeslot, area, host=None, logger=None):
        '''
        This class inherits all the extra variables and has the 'normal'
        implementation for find_inputs, find_outputs, fetch_inputs and
        
        '''

        super(ProcessingPackage, self).__init__(timeslot, area.name, host=host, 
                                                logger=logger)
        for extraInfo in settings.packageextrainfo_set.all():
            #exec('self.%s = "%s"' % (extraInfo.name, extraInfo.string))
            exec('self.%s = utilities.parse_marked(extraInfo, self)' % 
                 extraInfo.name)

    def find_inputs(self, useArchive=False):
        self.logger.debug('Looking for %s\'s inputs...' % self.name)
        return self._find_files(self.inputs, useArchive)

    def find_outputs(self, useArchive=False):
        self.logger.debug('Looking for %s\'s outputs...' % self.name)
        return self._find_files(self.outputs, useArchive)

    def outputs_available(self):
        '''
        Return a boolean indicating if the outputs are already available.

        The outputs are searched only in the defined host and NOT in the
        archives. If there are optional outputs that cannot be found, a
        warning message is thrown.
        '''

        allAvailable = True
        found = self.find_outputs(useArchive=False)
        for g2f, foundDict in found.iteritems():
            if len(foundDict['paths']) == 0:
                if not g2f.optional:
                    allAvailable = False
                    break
                else:
                    self.logger.warning('Couldn\'t find %s, but it is marked'\
                                        ' as \'Optional\' in the settings, '\
                                        'so continuing.' % g2f.name)
        return allAvailable

    def delete_outputs(self, callback=None):
        '''
        Delete the package's output files.
        '''

        foundOutputs = self.find_outputs(useArchive=False)
        for g2f, foundDict in foundOutputs.iteritems():
            if g2f.toDelete and foundDict['host'] is not None:
                foundDict['host'].delete_files(foundDict['paths'])

    def _delete_inputs(self):
        '''
        Delete the package's input files from their original location.

        BEWARE: This method should be used with care, because it can potentially
        delete important files.
        '''

        foundInputs = self.find_inputs(useArchive=False)
        for g2f, foundDict in foundInputs.iteritems():
            foundDict['host'].delete_files(foundDict['paths'])

    def fetch_inputs(self, useArchive=False):
        '''
        '''
        
        result = self._fetch_files(self.inputs, self.workingDir, useArchive,
                                   decompress=True)
        return result

    def compress_outputs(self):
        '''
        Compress the outputs of this package with bzip2.
        '''

        self.logger.info('Compressing %s outputs...' % self.name)
        return self._compress_files(self.outputs)

    def decompress_outputs(self):
        '''
        Decompress the outputs of this package with bunzip2.
        '''

        self.logger.info('Decompressing %s outputs...' % self.name)
        return self._decompress_files(self.outputs)

    def decompress_inputs(self):
        '''
        Decompress the inputs of this package with bunzip2.
        '''

        self.logger.info('Decompressing %s inputs...' % self.name)
        return self._decompress_files(self.inputs)

    def archive_outputs(self, compress=True):
        if compress:
            self.compress_outputs()
        archived = dict()
        for g2f in self.outputs:
            sent = g2f.archive()
            if sent[0] != 0:
                self.logger.warning('There has been an error archiving %s' \
                                    % g2f.name)
            archived[g2f] = sent[1]
        return archived

    def _filter_g2f_list(self, g2fs, attr, val):
        '''Return a list of G2File instances where attr=val'''

        result = []
        for g2f in g2fs:
            try:
                isEqual = g2f.__getattribute__(attr) == val
                if isEqual:
                    result.append(g2f)
            except AttributeError:
                pass
        return result


class FetchData(ProcessingPackage):
    '''
    This class uses:

        - outputDir
    '''

    def __init__(self, settings, timeslot, area, host=None,
                 logger=None, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object

            host - A systemsettings.models.Host object. If None (the default
                the current host will be used).

            createIO - A boolean indicating if the inputs and outputs
                are to be created. Defaults to True.
        '''

        super(FetchData, self).__init__(settings, timeslot, area, 
                                        host=host, logger=logger)
        self.rawSettings = settings
        self.name = settings.name
        relativeOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        self.outputDir = os.path.join(self.host.dataPath, relativeOutDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )

    def find_inputs(self, useArchive=False):
        '''
        IMPORTANT: In order for this method to work correctly, the 
        searchPatterns of both the inputs and outputs must match!
        '''

        self.logger.debug('Looking for %s\'s inputs...' % self.name)
        if useArchive:
            # the fetchData is special because the inputs and outputs are 
            # actually the same files. So we can search for the outputs in the
            # archive and return them as if they were the inputs.
            found = self.find_outputs(useArchive)
            result = dict()
            for inp in self.inputs:
                for outp, foundDict in found.iteritems():
                    if outp.searchPatterns == inp.searchPatterns:
                        result[inp] = foundDict.copy()
                if result.get(inp) is None:
                    result[inp] = {'host' : inp.host, 'paths' : []}
        else:
            result = self._find_files(self.inputs, useArchive)
        return result

    def fetch_inputs(self, useArchive=False):
        '''
        Copy and decompress the available inputs to the outputDir.

        IMPORTANT: In order for this method to work correctly when using
        the useArchive flag, the searchPatterns of both the inputs and 
        outputs must match!
        '''
        
        if useArchive:
            result = dict()
            # the fetchData class is special because the inputs and outputs are
            # actually the same files. So we can search for the outputs in the
            # archive and return them as if they were the inputs.
            for inp in self.inputs:
                for outp in self.outputs:
                    if outp.searchPatterns == inp.searchPatterns:
                        result[inp] = outp.fetch(self.outputDir, useArchive,
                                                 decompress=True)
        else:
            # use the default _fetch_files method
            result = self._fetch_files(self.inputs, self.outputDir, useArchive,
                                       decompress=True)
        return result

    def run_main(self, callback=None, retries=0, interval=10):
        '''
        Inputs:

            callback - A function that takes a tuple as argument. It will
                be dynamically updated with progress information as the
                package is running.

            retries - How many times should the package try to find its
                files? If None (the default), only the initial attempt will
                be performed.

            interval - How many minutes of waiting time between retries?
                Defaults to 10.

        Returns:

            An integer with the exit code. Zero means success.
        '''

        allFetched = False
        currentAttempt = 0
        while (not allFetched) and (currentAttempt <= retries):
            if currentAttempt > 0:
                self.logger.info('Retrying in %i minutes...' % interval)
                time.sleep(60 * interval)
            fetched = self.fetch_inputs(useArchive=True)
            allFetched = len(fetched.keys()) == len([1 for k, v in \
                         fetched.iteritems() if len(v) > 0])
            currentAttempt += 1
        return int(not allFetched)

    def clean_up(self, compressOutputs=True, callback=None):
        # delete the workingDir (not needed for fetchData class)
        # delete any extra dirs that may have become empty
        self._delete_inputs()
        if compressOutputs:
            self.compress_outputs()
        return 0


class PreProcessor(ProcessingPackage):
    '''
    This class is parent to the more specialized pre processing classes
    for the GRIB and LRIT inputs.

    It provides some common methods.
    '''

    def __init__(self, settings, timeslot, area, host, logger=None, 
                 createIO=True):
        super(PreProcessor, self).__init__(settings, timeslot, area, 
                                           host=host, logger=logger)
        self.version = settings.external_code.version

    def write_pcf(self, availableDict):
        '''
        Write the product configuration file.

        Inputs:

            availableDict - A dictionary with G2File objects as keys and
                lists with the full paths to the respective files as values.

        Returns:

            The full path to the newly-written product configuration file.
        '''

        pcfPath = os.path.join(self.workingDir, 
                               'preProcessorConfigurationFile.txt')
        fileContents = "" 
        for g2f, pathList in availableDict.iteritems():
          for path in pathList:
              fileContents += "%s\n" % path 
        self.host.create_file(pcfPath, fileContents)
        return pcfPath


class LRITPreprocessor(PreProcessor):

    def __init__(self, settings, timeslot, area, host, 
                 logger=None, createIO=True):
        super(LRITPreprocessor, self).__init__(settings, timeslot, area, 
                                               host=host, logger=logger)
        self.rawSettings = settings
        self.name = settings.name
        relOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        self.outputDir = os.path.join(self.host.dataPath, relOutDir)
        relStaticOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='staticOutputDir'), 
                self)
        self.staticOutputDir = os.path.join(self.host.dataPath, relStaticOutDir)
        relWorkingDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), 
                self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkingDir)
        #relCodeDir = utilities.parse_marked(
        #        settings.packagepath_set.get(name='codeDir'), 
        #        self)
        relCodeDir = utilities.parse_marked(
            settings.external_code.externalcodeextrainfo_set.get(name='path'),
            settings.external_code
        )
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )

    # FIXME
    # Add real-time logging of the FORTRAN output
    def execute_external_algorithm(self, pcfPath):
        '''
        Run the external algorithm.

        Inputs:

            pcfPath - The full path to the product configuration file
        '''

        numInputs = self.host.count_file_lines(pcfPath)
        if not self.host.is_dir(self.outputDir):
            self.host.make_dir(self.outputDir)
        if not self.host.is_dir(self.staticOutputDir):
            self.host.make_dir(self.staticOutputDir)
        command = './wrapper_g2.exe %s %s %s %i %s' % (self.source.area,
                                                       self.staticOutputDir,
                                                       self.outputDir,
                                                       numInputs,
                                                       pcfPath)
        runningDir = os.path.join(self.codeDir, '%s_v%s' % (self.codeName, 
                                                            self.version))
        #self.logger.info('external command:\n\t%s' % command)
        #self.logger.info('runningDir:\n\t%s' % runningDir)
        return self.host.run_program(command, workingDir=runningDir)

    def run_main(self, callback=None):
        fetched = self.fetch_inputs(useArchive=True)
        pcfPath = self.write_pcf(fetched)
        self.logger.info('Running FORTRAN code...')
        stdout, stderr, retCode = self.execute_external_algorithm(pcfPath)
        return retCode

    def clean_up(self, compressOutputs=True, callback=None):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.outputDir)
        self.host.clean_dirs(self.staticOutputDir)
        if compressOutputs:
            self.compress_outputs()
        return 0


class GRIBPreprocessor(PreProcessor):

    def __init__(self, settings, timeslot, area, host, 
                 logger=None, createIO=True):
        super(GRIBPreprocessor, self).__init__(settings, timeslot, area, 
                                               host=host, logger=logger)
        self.rawSettings = settings
        self.name = settings.name
        relOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        self.outputDir = os.path.join(self.host.dataPath, relOutDir)
        relWorkingDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), 
                self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkingDir)
        #relCodeDir = utilities.parse_marked(
        #        settings.packagepath_set.get(name='codeDir'), 
        #        self)
        relCodeDir = utilities.parse_marked(
            settings.external_code.externalcodeextrainfo_set.get(name='path'),
            settings.external_code
        )
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        self.tempOutputDir = os.path.join(self.workingDir, 'tempOutput')
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )

    def clean_up(self, compressOutputs=True, callback=None):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.outputDir)
        if compressOutputs:
            self.compress_outputs()
        return 0

    def execute_external_algorithm(self, pcfPath):
        '''
        Run the external algorithm.

        Inputs:

            pcfPath - The full path to the product configuration file
        '''

        numInputs = self.host.count_file_lines(pcfPath)
        if not self.host.is_dir(self.tempOutputDir):
            self.host.make_dir(self.tempOutputDir)
        command = './wrapper_g2.exe %s "" %s %i %s' % (self.source.area,
                                                    self.tempOutputDir, 
                                                    numInputs,
                                                    pcfPath)
        runningDir = os.path.join(self.codeDir, '%s_v%s' % (self.codeName, 
                                                            self.version))
        #self.logger.info('external command:\n\t%s' % command)
        #self.logger.info('runningDir:\n\t%s' % runningDir)
        return self.host.run_program(command, workingDir=runningDir)

    def run_main(self, callback=None):
        fetched = self.fetch_inputs(useArchive=True)
        pcfPath = self.write_pcf(fetched)
        self.logger.info('Running FORTRAN code...')
        stdout, stderr, retCode = self.execute_external_algorithm(pcfPath)
        self.logger.info('Moving outputs to their final destination...')
        self._move_outputs_to_final_dir()
        return retCode

    def _move_outputs_to_final_dir(self):
        '''
        Move the outputs from the external algorithm to their final dir.

        Since the external FORTRAN code will generate multiple outputs for
        several timeslots, it is necessary to adjust the outputDir.
        '''

        for filePath in self.host.list_dir(self.tempOutputDir):
            for g2f in self.outputs:
                for patt in g2f.searchPatterns:
                    if re.search(patt, filePath) is not None:
                        finalDir = g2f.searchPaths[0]
                        if not self.host.is_dir(finalDir):
                            self.host.make_dir(finalDir)
                        self.host.send([filePath], finalDir, self.host)
        

class Processor(ProcessingPackage):

    def __init__(self, settings, timeslot, area, host=None,
                 logger=None, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object

            host - A systemsettings.models.Host object

            createIO - A boolean indicating if the inputs and outputs
                are to be created. Defaults to True.
        '''

        super(Processor, self).__init__(settings, timeslot, area, 
                                        host=host, logger=logger)
        self.rawSettings = settings
        self.name = settings.name
        self.version = settings.external_code.version
        relOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        self.outputDir = os.path.join(self.host.dataPath, relOutDir)
        #relCodeDir = utilities.parse_marked(
        #        settings.packagepath_set.get(name='codeDir'), 
        #        self)
        relCodeDir = utilities.parse_marked(
            settings.external_code.externalcodeextrainfo_set.get(name='path'),
            settings.external_code
        )
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), 
                self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)
        try:
            acfTemplate = settings.packagepath_set.get(name='acfTemplate')
            relAcfTemplateDir = utilities.parse_marked(acfTemplate, self)
            self.acfTemplateDir = os.path.join(self.host.codePath, 
                                               relAcfTemplateDir)
        except ss.PackagePath.DoesNotExist:
            # this package does not define the acfTemplate variable, no problemsettings
            pass
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )

    def write_pcf(self, availableDict):
        '''
        Write the product configuration file.

        Inputs:

            availableDict - A dictionary with G2File objects as keys and
                lists with the full paths to the respective files as values.

        Returns:

            The full path to the newly-written product configuration file.
        '''

        fileContents = "&NAM_ALG_MODES\n"
        fileContents += "MODE = %s\n/\n" % (self.pcf_alg_mode) 
        fileContents += "&NAM_ALG_INPUT_FILES_PATH\n"
        fileContents += "YFILEINP=" 
        for g2f, pathList in availableDict.iteritems():
            for path in pathList:
                fileContents += "'%s',\n" % path
        fileContents = fileContents[:-2] #trimming the last newline and comma
        fileContents += "\n/\n"
        fileContents += "&NAM_ALG_OUTPUT_FILES_PATH\n"
        fileContents += "YFILEOUT = "
        for fileObj in self.outputs:
            namePattern = fileObj.searchPatterns[0]
            if namePattern.endswith(".*"):
                namePattern = namePattern[:-2] # trimming the last '.*' sign
            fileContents += "'%s/%s',\n" % (self.outputDir, namePattern)
        fileContents = fileContents[:-2]
        fileContents += "\n/\n"
        fileContents += "&NAM_STOP_STATUS_RETRIEVAL_FREQ\n"
        fileContents += "YFREQINSECS = %s\n" % (self.pcf_stop_status_ret_freq)
        fileContents += "/\n"
        pcfPath = os.path.join(self.workingDir, 'ProductConfigurationFile')
        self.host.create_file(pcfPath, fileContents)
        return pcfPath

    def write_acf(self):
        """
        Create the algorithm configuration file.

        Returns: The path to the newly created Algorithm Configuration File

        The Algorithm Configuration File is copied from a fixed template
        (located in the directory structures of the original external algorithm
        packages) to the working directory.
        """

        template = os.path.join(self.acfTemplateDir, self.acfName)
        return self.host.fetch([template], self.workingDir, self.host)[0]

    def clean_up(self, compressOutputs=True, callback=None):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.outputDir)
        if compressOutputs:
            self.compress_outputs()
        return 0

    def execute_external_algorithm(self, pcfPath, acfPath):
        '''
        Run the external algorithm.

        Inputs:

            pcfPath - The full path to the product configuration file.

            acfPath - The full path to the algorithm configuration file.
        '''

        if not self.host.is_dir(self.outputDir):
            self.host.make_dir(self.outputDir)
        command = './wrapper_g2.exe %s %s' % (pcfPath, acfPath)
        runningDir = os.path.join(self.codeDir, '%s_v%s' % (self.codeName, 
                                                            self.version))
        #self.logger.info('external command:\n\t%s' % command)
        #self.logger.info('runningDir:\n\t%s' % runningDir)
        stdout, stderr, retCode = self.host.run_program(command, 
                                                        workingDir=runningDir)
        self.logger.info(stdout)
        return retCode

    def run_main(self, callback=None):
        fetched = self.fetch_inputs(useArchive=True)
        pcfPath = self.write_pcf(fetched)
        acfPath = self.write_acf()
        self.logger.info('Running FORTRAN code...')
        retCode = self.execute_external_algorithm(pcfPath, acfPath)
        return retCode


#TODO - This class is not done yet. This is just the minimum
class GSAProcessor(ProcessingPackage):
    
    def __init__(self, settings, timeslot, area, host=None, 
                 logger=None, createIO=True):
        super(GSAProcessor, self).__init__(settings, timeslot, area, 
                                           host=host, logger=logger)
        self.rawSettings = settings
        self.name = settings.name
        self.version = settings.external_code.version
        relOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        self.outputDir = os.path.join(self.host.dataPath, relOutDir)
        relCodeDir = utilities.parse_marked(
            settings.external_code.externalcodeextrainfo_set.get(name='path'),
            settings.external_code
        )
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), 
                self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)
        #relInternalDir = utilities.parse_marked(
        #        settings.packagepath_set.get(name='internalDir'), 
        #        self)
        #self.internalDir = os.path.join(self.host.dataPath, relInternalDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )


class SWIProcessor(ProcessingPackage):

    def __init__(self, settings, timeslot, area, host=None, 
                 logger=None, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object

            host - A systemsettings.models.Host object

            createIO - A boolean indicating if the inputs and outputs
                are to be created. Defaults to True.
        '''

        super(SWIProcessor, self).__init__(settings, timeslot, area, 
                                           host=host, logger=logger)
        self.rawSettings = settings
        self.name = settings.name
        self.product = settings.product
        self.version = settings.external_code.version
        relOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        self.outputDir = os.path.join(self.host.dataPath, relOutDir)
        #relCodeDir = utilities.parse_marked(
        #        settings.packagepath_set.get(name='codeDir'), 
        #        self)
        #self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        relCodeDir = utilities.parse_marked(
            settings.external_code.externalcodeextrainfo_set.get(name='path'),
            settings.external_code
        )
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), 
                self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)
        relDggDir = utilities.parse_marked(
                settings.packagepath_set.get(name='dggDir'), 
                self)
        self.dggDir = os.path.join(self.host.dataPath, relDggDir)
        relTempOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='tempOutDir'), 
                self)
        self.tempOutDir = os.path.join(self.host.dataPath, relTempOutDir)
        relStaticDir = utilities.parse_marked(
                settings.packagepath_set.get(name='staticDir'), 
                self)
        self.staticDir = os.path.join(self.host.dataPath, relStaticDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )

    def write_acf(self):
        """
        Write the AlgorithmConfigurationFile for the external algorithm.

        Returns: A string indicating the full path to the newly created
                 file.
        """

        fileContents = "&NAM_EMPLACEMENT_FICHIER_BINAIRE\n"
        fileContents += "YFICHIER_BINAIRE = '%s/'\n/\n" % (self.staticDir) 
        fileContents += "&NAM_EMPLACEMENT_TMP\n"
        fileContents += "YEMPLACEMENTTMP= '%s/'\n/\n" % (self.tempOutDir) 
        fileContents += "&NAM_FORMAT_ENTRE\n"
        # this variable allows the SWI algorithm to read its inputs either 
        # in BUFR or native formats
        fileContents += "YFORMATENTREE = 1\n/\n"         
        fileContents += "&PROCLINE_VERSION\n"
        fileContents += "YPROCLINE_VERSION = '%s'\n/\n" % self.version
        fileContents += "&PROCLINE_DATE_ISO\n"
        fileContents += dt.datetime.utcnow().strftime("YPROCLINE_DATE_ISO = '%Y-%m-%d'\n/")
        acfPath = os.path.join(self.workingDir, 'AlgorithmConfigurationFile')
        self.host.create_file(acfPath, fileContents)
        return acfPath

    def write_pcf(self, availableDict):
        '''
        Write the product configuration file.

        Inputs:

            availableDict - A dictionary with G2File objects as keys and
                lists with the full paths to the respective files as values.

        Returns:

            The full path to the newly-written product configuration file.
        '''

        
        fileContents = '&NAM_ALG_MODES\n'
        fileContents += 'MODE = %s\n/\n' % (self.pcf_alg_mode) 
        fileContents += '&NAM_ALG_INPUT_FILES_PATH\n'
        fileContents += 'YFILEINP='
        filePaths = []
        for g2f, pathList in availableDict.iteritems():
            filePaths += pathList
        filePaths.sort()
        for path in filePaths:
            fileContents += "'%s', " % path
        fileContents = fileContents[:-1] #trimming the last comma
        #fileContents += ','.join(filePaths)
        fileContents += '\n/\n'
        fileContents += '&NAM_ALG_OUTPUT_FILES_PATH\n'
        fileContents += "YFILEOUT = '%s/'" % self.outputDir
        fileContents += '\n/\n'
        fileContents += '&NAM_STOP_STATUS_RETRIEVAL_FREQ\n'
        fileContents += 'YFREQINSECS = %s\n' % (self.pcf_stop_status_ret_freq)
        fileContents += '/\n'
        pcfPath = os.path.join(self.workingDir, 'ProductConfigurationFile')
        self.host.create_file(pcfPath, fileContents)
        return pcfPath

    def move_dgg_file(self):
        """
        Store dgg files in a YYYY/MM directory structure.

        Inputs:
        Returns:
        """

        for path in self.host.list_dir(self.tempOutDir):
            if self.host.is_file(path):
                fileTs = utilities.extract_timeslot(path)
                newDir = os.path.join(self.dggDir, fileTs.strftime('%Y'),
                                       fileTs.strftime('%m'))
                if not self.host.is_dir(newDir):
                    self.host.make_dir(newDir)
                self.logger.info("Copying %s to %s" % (path, newDir))
                self.host.send([path], newDir, self.host)

    def get_temp_file(self, maxLag=10):
        """
        Get the temp file needed to run the external package into the tempDir.

        Inputs: maxLag - An integer specifying the number of days that are to
                         be searched for a temp file.
        """
        
        if not self.host.is_dir(self.tempOutDir):
            self.host.make_dir(self.tempOutDir)
        # Difference in days between the instance's timeslot and the earliest
        # usable temp file
        #lag = 2
        lag = 1
        currentTs = self.timeslot - dt.timedelta(days=lag)
        foundFile = False
        while (not foundFile) and \
                ((self.timeslot - currentTs).days < (lag + maxLag)):
            searchPath = os.path.join(self.dggDir, currentTs.strftime("%Y"),
                                      currentTs.strftime("%m"))
            allFiles = self.host.list_dir(searchPath)
            searchPattern = re.compile(currentTs.strftime('%Y%m%d'))
            availableFiles = [p for p in allFiles if \
                    searchPattern.search(p) is not None]
            if len(availableFiles) > 0:
                theFile = availableFiles[0]
                #self.logger.info("Copying %s to %s" % (theFile, 
                #                                       self.tempOutDir))
                self.host.send([theFile], self.tempOutDir, self.host)
                foundFile = True
            else:
                currentTs = currentTs - dt.timedelta(days=1)
        if not foundFile:
            self.logger.info("Couldn't find a suitable temp file (DGG).")

    def execute_external_algorithm(self, pcfPath, acfPath):
        '''
        Run the external algorithm.

        Inputs:

            pcfPath - The full path to the product configuration file.

            acfPath - The full path to the algorithm configuration file.
            
        NOTE:
        The SWI_g2 package expects the AlgorithmConfigurationFile and 
        ProductConfigurationFile in a different order than the rest of the
        packages.
        '''

        for dirPath in (self.outputDir, self.tempOutDir):
            if not self.host.is_dir(dirPath):
                self.host.make_dir(dirPath)
        command = './wrapper_g2.exe %s %s' % (acfPath, pcfPath)
        runningDir = os.path.join(self.codeDir, '%s_v%s' % (self.codeName, 
                                                            self.version))
        #self.logger.info('external command:\n\t%s' % command)
        #self.logger.info('runningDir:\n\t%s' % runningDir)
        stdout, stderr, retCode = self.host.run_program(command, 
                                                        workingDir=runningDir)
        self.logger.info(stdout)
        self.logger.error(stderr)
        return retCode

    def run_main(self, callback=None):
        fetched = self.fetch_inputs(useArchive=True)
        self.get_temp_file()
        pcfPath = self.write_pcf(fetched)
        acfPath = self.write_acf()
        self.logger.info('Running FORTRAN code...')
        retCode = self.execute_external_algorithm(pcfPath, acfPath)
        self.move_dgg_file()
        return retCode

    def clean_up(self, compressOutputs=True, callback=None):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.outputDir)
        self.host.clean_dirs(self.staticDir)
        self.host.clean_dirs(self.tempOutDir)
        if compressOutputs:
            self.compress_outputs()
        return 0

    def get_quicklook(self):
        g2f = self._filter_g2f_list(self.outputs, 'fileType', 'png')[0]
        fetched = g2f.fetch(self.outputDir, use_archive=True)
        if len(fetched) > 0:
            result = fetched[0]
        else:
            result = None
        return result


class SWIMetadataHandler(ProcessingPackage):

    def __init__(self, settings, timeslot, area, host=None, 
                 logger=None, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object

            host - A systemsettings.models.Host object

            createIO - A boolean indicating if the inputs and outputs
                are to be created. Defaults to True.
        '''

        super(SWIMetadataHandler, self).__init__(settings, timeslot, area, 
                                                 host=host, logger=logger)
        self.rawSettings = settings
        self.name = settings.name
        self.product = settings.product
        self.version = settings.external_code.version
        relOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        self.outputDir = os.path.join(self.host.dataPath, relOutDir)
        relCodeDir = utilities.parse_marked(
            settings.external_code.externalcodeextrainfo_set.get(name='path'),
            settings.external_code
        )
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), 
                self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )
            self.md_modifier = metadatas.SWIMetadataModifier(self.product)

    def run_main(self, callback=None, send_to_csw=True):
        result = False
        xml_file = self.modify_xml()
        self.archive_outputs(compress=False)
        if send_to_csw:
            self.send_to_csw(xml_file)
        if xml_file is not None:
            result = True
        return result

    def modify_xml(self):
        '''
        Insert the correct XML fields in regard to dissemination.

        This method will modify the self-generated XML file from the external
        SWI_g2 code package. It will insert the correct information regarding:

        - UUID of the product in all the places it appears
        - UUID of the parent series
        - Contact details of the dissemination facility
        - URLs for the product and the quicklook
        '''

        self.host.make_dir(self.workingDir)
        if not self.host.is_dir(self.outputDir):
            self.host.make_dir(self.outputDir)
        g2fs = self._filter_g2f_list(self.inputs, 'fileType', 'xml')
        fetched = self._fetch_files(g2fs, self.workingDir, useArchive=True)
        self.logger.debug('fetched: %s' % fetched)
        xml_outputs = fetched.get(g2fs[0])
        if len(xml_outputs) > 0:
            xml_path = xml_outputs[0]
            self.md_modifier.parse_file(xml_path)
            self.md_modifier.modify_uuids()
            self.md_modifier.modify_metadata_contact()
            self.md_modifier.modify_principalIvestigator_contact()
            self.md_modifier.modify_quicklook_url(self.timeslot)
            self.md_modifier.modify_download_url(self.timeslot)
            xml_name = os.path.split(xml_path)[-1]
            out_path = os.path.join(self.outputDir, xml_name)
            #SANDRA
            self.md_modifier.modify_temporal_extent(self.timeslot)
            self.md_modifier._modify_citation()
            #SANDRA
            self.md_modifier.save_xml(out_path)
            result = out_path
        else:
            result = None
        return result

    def send_to_csw(self, xml_file):
        '''
        Insert metadata records in the catalogue server.

        Inputs:

            xml_file - The path to the XML file.

        Returns:
        
            A boolean with the insert operation's result.
        '''

        cswSetts = ss.CatalogueServer.objects.get()
        csw_url = '/'.join((cswSetts.base_URL, cswSetts.csw_URI))
        login_url = '/'.join((cswSetts.base_URL, cswSetts.login_URI))
        logout_url = '/'.join((cswSetts.base_URL, cswSetts.logout_URI))
        result = self.md_modifier.insert_csw(csw_url, login_url, logout_url,
                                             cswSetts.username, 
                                             cswSetts.password,
                                             xml_file)
        return result

    def clean_up(self):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.outputDir)


class DataFusion(Processor):
    '''
    !This class is not finished yet!

    This class runs the NGP2GRID_g2 external package.
    It requires the following settings:
        
        Package paths:
            outputDir
            workingDir
            codeDir

        Extra infos:
            version
    '''

    pass

    #def __init__(self, settings, timeslot, area, host=None, 
    #             logger=None, createIO=True):
    #    '''
    #    Inputs:

    #        settings - A systemsettings.models.Package object

    #        timeslot - A datetime.datetime object

    #        area - A systemsettings.models.Area object

    #        host - A systemsettings.models.Host object
    #    '''

    #    super(DataFusion, self).__init__(settings, timeslot, area, 
    #                                     host=host, logger=logger)
    #    self.rawSettings = settings
    #    self.name = settings.name
    #    self.version = settings.external_code.version
    #    relativeOutDir = utilities.parse_marked(
    #            settings.packagepath_set.get(name='outputDir'), 
    #            self)
    #    relativeCodeDir = utilities.parse_marked(
    #            settings.packagepath_set.get(name='codeDir'), 
    #            self)
    #    relativeWorkDir = utilities.parse_marked(
    #            settings.packagepath_set.get(name='workingDir'), 
    #            self)
    #    self.outputDir = os.path.join(self.host.dataPath, relativeOutDir)
    #    self.codeDir = os.path.join(self.host.codePath, relativeCodeDir)
    #    self.workingDir = os.path.join(self.host.dataPath, relativeWorkDir)
    #    if createIO:
    #        self.inputs = self._create_files(
    #            'input', 
    #            settings.packageInput_systemsettings_packageinput_related.all()
    #        )
    #        self.outputs = self._create_files(
    #            'output', 
    #            settings.packageOutput_systemsettings_packageoutput_related.all()
    #        )


class WebDisseminator(ProcessingPackage):
    '''
    This class takes care of creating quickviews, WMS and CSW integration.
    '''

    def __init__(self, settings, timeslot, area, host=None, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object

            host - A systemsettings.models.Host object
        '''

        super(WebDisseminator, self).__init__(settings, timeslot, area, host)
        self.rawSettings = settings
        self.name = settings.name
        relCodeDir = utilities.parse_marked(
                settings.packagepath_set.get(name='codeDir'), self)
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        relQuickDir = utilities.parse_marked(
                settings.packagepath_set.get(name='quickviewOutDir'), self)
        self.quickviewOutDir = os.path.join(self.host.dataPath, relQuickDir)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)
        relXmlTemplateDir = utilities.parse_marked(
                settings.packagepath_set.get(name='xmlTemplateDir'), self)
        self.xmlTemplate = os.path.join(self.host.codePath, relXmlTemplateDir,
                                        self.xmlTemplate)
        relXmlDir = utilities.parse_marked(
                settings.packagepath_set.get(name='xmlOutDir'), self)
        self.xmlOutDir = os.path.join(self.host.dataPath, relXmlDir)
        relMapfileOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='mapfileOutDir'), self)
        self.mapfileOutDir = os.path.join(self.host.dataPath, 
                                          relMapfileOutDir)
        relMapfileTemplateDir = utilities.parse_marked(
                settings.packagepath_set.get(name='mapfileTemplateDir'), self)
        self.mapfileTemplateDir = os.path.join(self.host.codePath, 
                                               relMapfileTemplateDir)
        relCommonGeotifDir = utilities.parse_marked(
                settings.packagepath_set.get(name='commonGeotifDir'), self)
        self.commonGeotifDir = os.path.join(self.host.dataPath, 
                                            relCommonGeotifDir)
        relGeotifOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='geotifOutDir'), self)
        self.geotifOutDir = os.path.join(self.host.dataPath, 
                                         relGeotifOutDir)
        relWebDir = utilities.parse_marked(
                settings.packagepath_set.get(name='hdf5WebDir'), self)
        self.hdf5WebDir = os.path.join(self.host.dataPath, relWebDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )
        self.quicklooksMapfileName = 'quicklooks.map'
        self.mapper = mappers.NGPMapper(self.inputs[0]) # <- badly defined
        self.mdGenerator = metadatas.MetadataGenerator(self.xmlTemplate, self.timeslot)

    def clean_up(self, callback=None):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.mapfileOutDir)
        self.host.clean_dirs(self.quickviewOutDir)
        self.host.clean_dirs(self.xmlOutDir)
        return 0

    def run_main(self, callback=None):
        fetched = self.fetch_inputs(useArchive=True)
        fileList = []
        for g2f, pathList in fetched.iteritems():
            fileList += pathList
        mapfile = self.generate_quicklooks_mapfile(fileList)
        quicklooks = self.generate_quicklooks(mapfile, fileList)
        return quicklooks
        #xmlMetadata = self.generate_xml_metadata(fileList)
        #self.populate_csw_server(xmlMetadata)
        #self.send_quicklooks_to_web_server(quicklooks)
        #self.send_product_to_web_server(fileList)

    def generate_quicklooks_mapfile(self, fileList):
        '''
        Generate mapfile.

        Inputs:

            fileList - A list of file paths with the files to be included in 
                the mapfiles.

        Returns:

            A string with the full path to the newly generated mapfile.
        '''

        globalTifName = '%s_%s%s%s%s%s.tif' % (self.mapper.product.short_name,
                                               self.year, self.month, 
                                               self.day, self.hour, 
                                               self.minute)
        self.host.make_dir(self.geotifOutDir)
        globalProd = self.mapper.create_global_tiff(fileList, self.geotifOutDir,
                                                    globalTifName)
        templateName = 'template_quicklooks.map'
        template = os.path.join(self.mapfileTemplateDir, templateName)
        mapfilePath = os.path.join(self.mapfileOutDir, 
                                   self.quicklooksMapfileName)
        self.host.make_dir(self.mapfileOutDir)
        commonGeotifPath = os.path.commonprefix((self.commonGeotifDir, 
                                                globalProd))
        relativeGeotifPath = re.sub(commonGeotifPath, '', globalProd)[1:]
        mapfile = self.mapper.create_mapfile(relativeGeotifPath, 
                                             self.commonGeotifDir, 
                                             mapfilePath, template)
        return mapfile

    def get_quicklooks_mapfile(self):
        '''
        Return the full path to the mapfile used for generating quicklooks.
        '''

        mapFile = os.path.join(self.mapfileOutDir, self.quicklooksMapfileName)
        if self.host.is_file(mapFile):
            result = mapFile
        else:
            result = None
        return result

    def generate_quicklooks(self, mapfile, fileList):

        self.host.make_dir(self.quickviewOutDir)
        quickLooks = []
        for fNum, path in enumerate(fileList):
            self.logger.debug('(%i/%i) - Creating quicklook...' % 
                              (fNum+1, len(fileList)))
            if fNum == 0:
                quickPath = self.generate_quicklook(mapfile, path, 
                                                    self.quickviewOutDir,
                                                    generate_legend=True)
            else:
                quickPath = self.generate_quicklook(mapfile, path, 
                                                    self.quickviewOutDir,
                                                    generate_legend=False)
            quickLooks.append(quickPath)
        return quicklooks

    def _generate_quicklooks_legend(self, layers, outputDir, mapfile, 
                                    regenerate=False):
        legendPath = os.path.join(outputDir, 'legend.png')
        if regenerate or (not self.host.is_file(legendPath)):
            legendPath = self.mapper.generate_legend(mapfile, layers, outputDir)
        return legendPath

    def generate_xml_metadata(self, fileList):
        '''
        Generate the xml metadata files.

        Inputs:

            fileList - A list with the full paths to the HDF5 tiles.

            quickLooks - A list with the full paths to the quickLooks.
        '''

        if not self.host.is_dir(self.xmlOutDir):
            self.host.make_dir(self.xmlOutDir)
        #for fNum, path in enumerate(fileList[0:1]): # for testing purposes
        for fNum, path in enumerate(fileList):
            self.logger.debug('(%i/%i) - Creating xml...' % 
                              (fNum+1, len(fileList)))
            self.mdGenerator.apply_changes(path, self.mapper, self.hdf5WebDir)
            pathFName = os.path.splitext(os.path.basename(path))[0]
            xmlPath = os.path.join(self.xmlOutDir, '%s.xml' % pathFName)
            self.mdGenerator.save_xml(xmlPath)

    def populate_csw_server(self, xmlFiles):
        '''
        Insert the records present in the xmlFiles in the csw server.

        Inputs:
            
            xmlFiles - A list of xml files
        '''

        raise NotImplementedError

    def send_quicklooks_to_web_server(self, fileList):
        destinationDir = utilities.get_host_path(self.host, 
                                                 self.quickviewOutDir, 
                                                 webServerHost)
        self._send_to_web_server(fileList, destinationDir, webServerHost)

    def send_product_to_web_server(self, fileList):
        destinationDir = utilities.get_host_path(self.host, 
                                                 self.hdf5WebDir, 
                                                 webServerHost)
        self._send_to_web_server(fileList, destinationDir, webServerHost)

    def _send_to_web_server(self, fileList, destinationDir):
        '''
        Send files to the web server.

        Inputs:

            fileList - A list of file paths.

            destinationDir - The directory on the target host where
                the files should be sent to.

        The web server is a special Host object, that has the 'web_server' 
        attribute set to True.
        '''

        hostSettings = ss.Host.objects.filter(web_server=True)[0]
        hf = HostFactory(self.logger.getEffectiveLevel())
        webServerHost = hf.create_host(hostSettings)
        self.host.send(fileList, destinationDir, webServerHost)

    def get_zip_bundle(self, tileName):
        '''
        Return a zip file with the product, quicklook and xml.
        '''

        mapFile = self.get_quicklooks_mapfile(self)
        if mapFile is not None:
            product = self._get_tile(tileName, useArchive=True)[0]
            quickLook = self.generate_quicklook(mapFile, product, self.workingDir)
            metadata = self.generate_xml(tileName)
        #bundle the product, quickLook and metadata

    def _get_tile(self, tileName, useArchive=False):
        '''
        Copy the specified tile to the working directory.
        
        This method will search the inputs for the specified tile
        and copy it to the working directory.

        Inputs:

            tileName

            useArchive - A boolean specifying if the archives should be used
                when fetching the file.

        Returns a list of paths with the files that have been retrieved.
        '''

        tilePattern = re.compile(r'(?P<tile_name>%s)' % tileName)
        patternSearch = re.compile(r'\(\?P<tile_name>.*\)')
        foundTiles = []
        for g2f in [f for f in self.inputs if f.fileType == 'hdf5']:
            for index, patt in enumerate(g2f.searchPatterns):
                oldPatt = patt[:] # copying the string
                newPatt = re.sub(patternSearch, tileName, patt)
                g2f.searchPatterns[index] = newPatt
                found = self._fetch_files([g2f], self.workingDir, useArchive, decompress=True)
                foundTiles += found.values()[0]
                #after processing is done, restore the old pattern
                g2f.searchPatterns[index] = oldPatt
        return foundTiles

    def generate_quicklook(self, mapfile, tilePath, outputDir, generate_legend=True):
        '''
        Process a single tile and generate the quicklook.

        Inputs:

            mapfile - The full path to the mapfile to use for generating
                the quicklook.

            tilePath - The full path to the tile to be processed.

            outputDir - 

        Returns the fullpath to the newly generated quicklook.
        '''

        self.host.make_dir(self.workingDir)
        self.host.make_dir(outputDir)
        prodName = self.mapper.product.short_name
        legPath = self._generate_quicklooks_legend([prodName], 
                                                   self.workingDir, 
                                                   mapfile, 
                                                   regenerate=generate_legend)
        quickPath = self.mapper.generate_quicklook(outputDir, mapfile, 
                                                   tilePath, legPath)
        #self.mapper.remove_temps([legendPath] + pathList)
        return quickPath

    def generate_xml(self, tileName):
        '''
        Process a single tile and generate the xml metadata file.

        Returns the fullpath to the newly generated xml metadata file.
        '''

        pass


class OWSPreparator(ProcessingPackage):
    '''
    This class prepares the Web Map Service.

    It will create the global geotiff file with the main dataset of the 
    product and update the relevant WMS mapfiles.

    Instances of this class can be called in order to:

        - generate the global geotiff files that serve as a basis for the WMS
            service

        - update the mapfiles
    '''

    def __init__(self, settings, timeslot, area, host=None, logger=None, 
                 createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object

            host - A systemsettings.models.Host object
        '''

        super(OWSPreparator, self).__init__(settings, timeslot, area, 
                                            host=host, logger=logger)
        self.rawSettings = settings
        self.name = settings.name
        self.product = settings.product
        relCodeDir = utilities.parse_marked(
                settings.packagepath_set.get(name='codeDir'), self)
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)
        relMapfileOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='mapfileOutDir'), self)
        self.mapfileOutDir = os.path.join(self.host.dataPath, 
                                          relMapfileOutDir)
        relShapePath = utilities.parse_marked(
                settings.packagepath_set.get(name='shapePath'), self)
        self.mapfileShapePath = os.path.join(self.host.dataPath, 
                                          relShapePath)
        relMapfileTemplateDir = utilities.parse_marked(
                settings.packagepath_set.get(name='mapfileTemplateDir'), self)
        self.mapfileTemplateDir = os.path.join(self.host.codePath, 
                                               relMapfileTemplateDir)
        relGeotifOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='geotifOutDir'), self)
        self.geotifOutDir = os.path.join(self.host.dataPath, 
                                         relGeotifOutDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )
            self.mapper = mappers.NGPMapper(self.inputs[0], self.product, 
                                            logger=self.logger)

    def update_latest_mapfile(self, geotifPath):
        '''
        This method updates the 'latest' mapfile with this product.
        '''

        mapfile = self.get_latest_mapfile()
        rp = geotifPath.replace(self.mapfileShapePath, '').partition('/')[-1]
        updatedMapfile = self.mapper.update_latest_mapfile(mapfile, 
                                                           self.mapfileShapePath, 
                                                           rp)
        return updatedMapfile

    def update_specific_mapfile(self):
        '''
        This method updates the product specific mapfile with this product.
        '''

        # this method probably shouldn't be called by the run method
        pass

    def get_latest_mapfile(self):
        '''
        Return the 'latest' mapfile. Create it from the template if needed.
        '''

        g2f = [i for i in self.inputs if i.fileType=='mapfile' and \
                hasattr(i, 'latest')][0]
        mapName = g2f.searchPatterns[0]
        mapfile = os.path.join(self.mapfileOutDir, mapName)
        if self.host.is_file(mapfile):
            result = mapfile
        else:
            self.host.make_dir(self.mapfileOutDir)
            template = os.path.join(self.mapfileTemplateDir, mapName)
            returnCode, resultList = self.host.send([template], self.mapfileOutDir)
            result = resultList[0]
        return result

    def delete_outputs(self):
        '''
        Delete the package's geotiff output but keep the mapfiles.

        This method overrides the default behaviour of deleting all the
        outputs because the mapfiles are meant to be kept.
        '''

        geotiffG2fs = [out for out in self.outputs if out.fileType=='geotiff']
        foundGeotiffs = self._find_files(geotiffG2fs, useArchive=False)
        for g2f, foundDict in foundGeotiffs.iteritems():
            if not (g2f.frequency == 'static' and deleteStatics):
                foundDict['host'].delete_files(foundDict['paths'])

    def get_specific_mapfile(self):
        '''
        Return the product specific mapfile. Create it from the template if needed.
        '''

        pass

    def generate_geotiff(self, fileList):
        '''
        Generate a global geotiff file with the input tiles.

        Inputs:

            fileList - A list of file paths with the files to be included in 
                the global geotiff.

        Returns:

            A string with the full path to the newly generated geotiff file.
        '''

        globalTifName = '%s_%s%s%s%s%s.tif' % (self.product.short_name,
                                               self.year, self.month, 
                                               self.day, self.hour, 
                                               self.minute)
        self.host.make_dir(self.geotifOutDir)
        globalProd = self.mapper.create_global_tiff(fileList, self.geotifOutDir,
                                                    globalTifName)
        return globalProd

    def run_main(self, callback=None, generate=True, update=None, 
                 archive=True, delete_local=False):
        '''
        Inputs:

            generate - A boolean flag indicating if the global geotif is to 
                be generated. Defaults to True. If False, the global geotiff
                is fetched from the archives.

            update - Controls whether the WMS mapfiles are to be updated.
                Accepted values:
                    None - Don't update. This is the default.
                    'latest' - Update only the 'latest' mapfile.
                    'product' - Update only the 'product' mapfile.
                    'all' - Update both the 'latest' and 'product' mapfiles.

            archive - Controls whether the outputs should be archived.
                This is useful in this package, because the machine that
                creates the global tiff files is not necessarily the same
                that serves the WMS service.

            delete_local - Controls whether the outputs should be deleted
                from the local host. Defaults to False.
        '''

        result = False
        if generate:
           fetched = self.fetch_inputs(useArchive=True)
           fileList = []
           for g2f, pathList in fetched.iteritems():
               if g2f.fileType == 'hdf5':
                   fileList += pathList
           if len(fileList) == 0:
               self.logger.error('Couldn\'t find the input HDF5 tiles. ' \
                                 'No Geotiff can be generated.')
               geotiff = None
           else:
               self.logger.info('Generating a new Geotiff file from %s ' \
                                'fetched tiles...' % len(fileList))
               geotiff = self.generate_geotiff(fileList)
               self.logger.info('geotiff file: %s' % geotiff)
        else:
            geotiff = self.fetch_geotiff(useArchive=True)
        if geotiff is not None:
            result = True
            if update == 'latest':
                self.update_latest_mapfile(geotiff)
            if archive:
                self.archive_outputs()
            if delete_local:
                self.delete_outputs()
        else:
            self.logger.warning('Couldn\'t find the geotiff files.')
        return result

    def fetch_geotiff(self, useArchive=True):
        g2f = [inp for inp in self.outputs if inp.fileType=='geotiff'][0]
        fetched = self._fetch_files([g2f], self.geotifOutDir, useArchive, 
                                    decompress=True)
        settings = ss.File.objects.get(name=g2f.name)
        # we want to return the actual geotiff's path, not the overhead
        # (the overhead has to be fetched too though)
        pattern = settings.filepattern_set.get(name='actual data').string
        pattern = pattern.replace('#', '')
        geotiff = None
        for filePath in fetched[g2f]:
            reObj = re.search(pattern, filePath)
            if reObj is not None:
                geotiff = filePath
        return geotiff

    def clean_up(self, callback=None):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.mapfileOutDir)
        self.host.clean_dirs(self.geotifOutDir)
        return 0


class QuickLookGenerator(ProcessingPackage):
    '''
    This class will generate the quicklook files using the corresponding
    mapfile and geotiff.

    The quicklook files can be generated in realtime, but also in bulk.

    The quicklook files must use their own mapfile generating methods in order
    to prevent clashing with the WMS services.

    1. Get the global geotif
    2. Get or generate its mapfile from a template
    3. Generate the quicklook file(s) given the specified coordinates
    '''

    def __init__(self, settings, timeslot, area, host=None, 
                 logger=None, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object
        '''

        self.rawSettings = settings
        self.name = settings.name
        self.product = settings.product
        super(QuickLookGenerator, self).__init__(settings, timeslot, area, 
                                                 host=host, logger=logger)
        relCodeDir = utilities.parse_marked(
                settings.packagepath_set.get(name='codeDir'), self)
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        relQuickDir = utilities.parse_marked(
                settings.packagepath_set.get(name='quickviewOutDir'), self)
        self.quickviewOutDir = os.path.join(self.host.dataPath, relQuickDir)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)
        relMapfileOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='mapfileOutDir'), self)
        self.mapfileOutDir = os.path.join(self.host.dataPath, 
                                          relMapfileOutDir)
        relMapfileTemplateDir = utilities.parse_marked(
                settings.packagepath_set.get(name='mapfileTemplateDir'), self)
        self.mapfileTemplateDir = os.path.join(self.host.codePath, 
                                               relMapfileTemplateDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )
            self.mapper = mappers.NewNGPMapper()

    def get_mapfile(self):
        '''
        Return the full path to the quicklooks mapfile.

        The mapfile is created (from the template) in case it cannot be
        found.
        '''

        g2f = self._filter_g2f_list(self.inputs, 'fileType', 'mapfile')[0]
        found = self._find_files([g2f], useArchive=False)
        pathList = found[g2f]['paths']
        if len(pathList) == 0:
            template = os.path.join(self.mapfileTemplateDir,
                                    self.mapfileTemplate)
            newMapfile = self.host.fetch([template], self.mapfileOutDir, 
                                         self.host)[0]
            dirname, fileName = os.path.split(newMapfile)
            mapfile = os.path.join(dirname, g2f.searchPatterns[0])
            self.host.rename_file(newMapfile, mapfile)
        else:
            mapfile = pathList[0]
        return mapfile

    def find_geotiff(self):
        '''
        Return the full path to the geotiff file or None.
        '''

        g2f = self._filter_g2f_list(self.inputs, 'fileType', 'geotiff')[0]
        fetched = self._fetch_files([g2f], self.workingDir, useArchive=True, 
                                    decompress=True)
        #fetched = self._fetch_files([g2f], g2f.searchPaths[0], useArchive=True, 
        #                            decompress=True)
        pathList = fetched[g2f]
        geotiff = None
        if len(pathList) > 0:
            geotiff = [f for f in pathList if re.search(r'\.ovr', f) is None][0]
        else:
            self.logger.error('Couldn\'t find the geotiff input')
        return geotiff

    def update_mapfile(self, geotiff):
        '''
        Update the mapfile with the correct information for the input geotiff.

        Inputs:

            geotiff - path to the geotiff file.
        '''

        shapePath, tifName = os.path.split(geotiff)
        mapfile = self.get_mapfile()
        mapObj = mapscript.mapObj(mapfile)
        mapObj.shapepath = shapePath
        mapWMSMetadata = mapObj.web.metadata
        mapWMSMetadata.set('wms_onlineresource', 
                           'http://%s/cgi-bin/mapserv?map=%s&' \
                            % (self.host.host, mapfile))
        layer = mapObj.getLayerByName(self.product.short_name)
        layer.data = tifName
        layerAbstract = '%s product generated for the %s timeslot.' % \
                        (self.product.short_name, 
                         self.timeslot.strftime('%Y-%m-%d %H:%M'))
        layer.metadata.set('wms_abstract', layerAbstract)
        mapObj.save(mapfile)
        return mapfile

    def generate_quicklook(self, mapfile, tilePath, outputDir, generate_legend=True):
        '''
        Process a single tile and generate the quicklook.

        Inputs:

            mapfile - The full path to the mapfile to use for generating
                the quicklook.

            tilePath - The full path to the tile to be processed.

            outputDir - 

        Returns the fullpath to the newly generated quicklook.
        '''

        self.host.make_dir(self.workingDir)
        self.host.make_dir(outputDir)
        legPath = self._generate_quicklooks_legend([self.product.short_name], 
                                                   self.workingDir, 
                                                   mapfile, 
                                                   regenerate=generate_legend)
        quickPath = self.mapper.generate_quicklook(outputDir, mapfile, 
                                                   tilePath, legPath, 
                                                   self.product, self.host)
        #self.mapper.remove_temps([legendPath] + pathList)
        return quickPath

    def _process_single_tile(self, tile, mapfile):
        result = None
        alreadyThere = self.host.list_dir(self.quickviewOutDir)
        for ql in alreadyThere:
            if tile in ql:
                self.logger.debug('Found the quicklook. No need to generate.')
                result = ql
        if result is None:
            g2fs = self._filter_g2f_list(self.inputs, 'fileType', 'hdf5')
            theFilePath = None
            current = 0
            while (theFilePath is None) and (current < len(g2fs)):
                g2f = g2fs[current]
                found = self._find_files([g2f], useArchive=True)
                isPresent = False
                for patt in g2f.searchPatterns:
                    if not isPresent:
                        newPatt = re.sub(r'\(.*\)', tile, patt)
                        for filePath in found[g2f]['paths']:
                            reObj = re.search(newPatt, filePath)
                            if reObj is not None:
                                theFilePath = filePath.replace('.bz2','')
                                isPresent = True
                                break
                current += 1
            if theFilePath is not None:
                self.logger.debug('About to generate a new quicklook.')
                result = self.generate_quicklook(mapfile, theFilePath, 
                                                 self.quickviewOutDir,
                                                 generate_legend=True)
            else:
                self.logger.error('The requested tile was not found.')
        return result

    def _process_all_tiles(self, mapfile):
        g2fs = self._filter_g2f_list(self.inputs, 'fileType', 'hdf5')
        found = self._find_files(g2fs, useArchive=True)
        hdfFiles = []
        quickLooks = []
        for g2f, foundDict in found.iteritems():
            hdfFiles += [p.replace('.bz2', '') for p in foundDict['paths']]
        if len(hdfFiles) > 0:
            firstFile = hdfFiles[0]
            self.logger.debug('(1/%i) Generating quicklook for %s...' % 
                              (len(hdfFiles), firstFile))
            ql = self.generate_quicklook(mapfile, firstFile, 
                                         self.quickviewOutDir,
                                         generate_legend=True)
            quickLooks.append(ql)
        if len(hdfFiles) > 1:
            for index, filePath in enumerate(hdfFiles[1:]):
                self.logger.debug('(%i/%i) Generating quicklook for %s...' % 
                                  (index+2, len(hdfFiles), filePath))
                ql = self.generate_quicklook(mapfile, filePath, 
                                             self.quickviewOutDir,
                                             generate_legend=False)
                quickLooks.append(ql)
        result = quickLooks
        return result

    def _get_all_tiles(self, use_archive=True):
        result = self._find_quicklook(use_archive=use_archive)
        if len(result) == 0:
            self.logger.debug('About to generate new quicklooks.')
            geotiff = self.find_geotiff()
            mapfile = self.update_mapfile(geotiff)
            result = self._process_all_tiles(mapfile)
        return result

    def _find_quicklook(self, tile=None, use_archive=True):
        result = []
        g2fs = self._filter_g2f_list(self.outputs, 'fileType', 'geotiff')
        already_generated = self._find_files(g2fs, useArchive=use_archive, 
                                             restrictPattern=tile)
        for g2f, found_dict in already_generated.iteritems():
            if found_dict['host'] == self.host and \
                    len(found_dict['paths']) > 0:
                self.logger.debug('found quicklook on the ' \
                                  'local host.')
                result += found_dict['paths']
            elif found_dict['host'] != self.host:
                self.logger.debug('found quicklook on an ' \
                                  'archive host. Fetching...')
                fetched = self._fetch_files(
                              [g2f], self.quickviewOutDir, 
                              useArchive=use_archive, 
                              decompress=True,
                              restrictPattern=tile
                          )
                result += fetched[g2f]
        return result

    def run_main(self, callback=None, tile=None, move_to_webserver=True, 
                 archive=False, delete_local=True):
        if tile is None:
            result = self._get_all_tiles(use_archive=True)
        else:
            result = self._get_single_tile(tile, use_archive=True)
        if ss.WebServer.objects.get().host.ip != self.host.host:
            if move_to_webserver:
                self.logger.info('moving outputs to the webserver...')
                self.move_outputs_to_webserver()
        if archive:
            self.archive_outputs()
        if delete_local:
            self.logger.info('deleting local files...')
            self.delete_outputs()
        self.logger.info('All Done')
        return result

    def _get_single_tile(self, tile, use_archive=True):
        result = self._find_quicklook(tile=tile, use_archive=use_archive)
        if len(result) == 0:
            self.logger.debug('About to generate a new quicklook.')
            geotiff = self.find_geotiff()
            mapfile = self.update_mapfile(geotiff)
            result = self._process_single_tile(tile, mapfile)
        return result

    def clean_up(self):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.mapfileOutDir)
        self.host.clean_dirs(self.quickviewOutDir)
        return 0

    def _generate_quicklooks_legend(self, layers, outputDir, mapfile, 
                                    regenerate=False):
        legendPath = os.path.join(outputDir, 'legend.png')
        if regenerate or (not self.host.is_file(legendPath)):
            legendPath = self.mapper.generate_legend(mapfile, layers, 
                                                     outputDir, self.host)
        return legendPath

    def move_outputs_to_webserver(self):
        web_server = ss.WebServer.objects.get()
        hf = HostFactory(self.logger.getEffectiveLevel())
        host_obj = hf.create_host(web_server.host)
        g2fs = self._filter_g2f_list(self.outputs, 'fileType', 'geotiff')
        send_result = self._send_files(
            g2fs, 
            destHost=host_obj
        )
        return send_result


class MetadataGenerator(ProcessingPackage):
    '''
    This class will generate and upload the xml metadata files to the 
    CSW server.
    '''

    def __init__(self, settings, timeslot, area, host=None, 
                 logger=None, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object
        '''

        self.rawSettings = settings
        self.name = settings.name
        self.product = settings.product
        super(MetadataGenerator, self).__init__(settings, timeslot, area,
                                                host=host, logger=logger)
        relCodeDir = utilities.parse_marked(
                settings.packagepath_set.get(name='codeDir'), self)
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        relMetaDir = utilities.parse_marked(
                settings.packagepath_set.get(name='xmlOutDir'), self)
        self.xmlOutDir = os.path.join(self.host.dataPath, relMetaDir)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)
        relMetaTemplateDir = utilities.parse_marked(
                settings.packagepath_set.get(name='xmlTemplateDir'), self)
        self.xmlTemplateDir = os.path.join(self.host.codePath, 
                                           relMetaTemplateDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )
            theTemplate = os.path.join(self.xmlTemplateDir, self.xmlTemplate)
            self.mapper = mappers.NewNGPMapper()
            self.mdGenerator = metadatas.MetadataGenerator(theTemplate, 
                                                           self.timeslot, 
                                                           self.product,
                                                           logger=self.logger)

    def _process_all_tiles(self, use_archive=True, force=True):
        '''
        '''

        g2fs = self._filter_g2f_list(self.inputs, 'fileType', 'hdf5')
        found = self._find_files(g2fs, useArchive=use_archive)
        results = []
        for g2f, foundDict in found.iteritems():
            for index, tile_path in enumerate(foundDict['paths']):
                metadata_path = self._process_single_tile_path(
                                    tile_path, 
                                    force=force
                                )
                results.append(metadata_path)
        return results

    def _process_single_tile_path(self, tile_path, force=True):
        #self.logger.debug('tile_path: %s' % tile_path)
        if force:
            metadata_path = self.generate_xml_metadata(tile_path)
        else:
            tile = utilities.get_tile_name(tile_path)
            already_there = self._find_output_by_tile(
                                tile, 
                                use_archive=False
                            )
            if already_there is None:
                metadata_path = self.generate_xml_metadata(tile_path)
            else:
                metadata_path = already_there
                self.logger.info('Using already present tile.')
        return metadata_path

    def _process_single_tile(self, tile, use_archive=True, force=True):
        '''
        '''

        metadata_path = None
        if force:
            metadata_path = self._force_new_metadata(
                                tile, 
                                use_archive=use_archive
                            )
        else:
            already_there = self._find_output_by_tile(
                                tile, 
                                use_archive=use_archive
                            )
            if already_there is None:
                metadata_path = self._force_new_metadata(
                                    tile, 
                                    use_archive=use_archive
                                )
            else:
                metadata_path = already_there
                self.logger.info('Using already present tile.')
        return metadata_path

    def _force_new_metadata(self, tile_name, use_archive=True):
        metadata_path = None
        input_tile = self._find_input_by_tile(tile_name, 
                                              use_archive=use_archive)
        if input_tile is not None:
            metadata_path = self.generate_xml_metadata(input_tile)
        return metadata_path

    def _find_input_by_tile(self, tile_name, use_archive=True):
        tile_path = self._find_by_tile(tile_name, use_archive=use_archive,
                                       io_type='input', filter_by='fileType',
                                       filter_value='hdf5')
        return tile_path

    def _find_output_by_tile(self, tile_name, use_archive=True):
        tile_path = self._find_by_tile(tile_name, use_archive=use_archive,
                                       io_type='output', filter_by='fileType',
                                       filter_value='xml')
        return tile_path

    def _find_by_tile(self, tile_name, use_archive=True, io_type='input', 
                      filter_by='fileType', filter_value='hdf5'):
        if io_type == 'input':
            io = self.inputs
        elif io_type == 'output':
            io = self.outputs
        g2fs = self._filter_g2f_list(io, filter_by, filter_value)
        theFilePath = None
        current = 0
        while (theFilePath is None) and (current < len(g2fs)):
            g2f = g2fs[current]
            found = self._find_files([g2f], useArchive=use_archive)
            isPresent = False
            newPatt = utilities.put_tile_into_pattern(tile_name, g2f)
            for filePath in found[g2f]['paths']:
                reObj = re.search(newPatt, filePath)
                if reObj is not None:
                    theFilePath = filePath
            current += 1
        #if theFilePath is None:
        #    self.logger.error('The requested tile was not found.')
        return theFilePath

    def generate_xml_metadata(self, tilePath):
        '''
        Returns a string with the path to the xml file or None.
        '''

        if not self.host.is_dir(self.xmlOutDir):
            self.host.make_dir(self.xmlOutDir)
        self.mdGenerator.apply_changes(tilePath, self.mapper)
        pathFName = os.path.splitext(os.path.basename(tilePath))[0]
        xmlPath = os.path.join(self.xmlOutDir, '%s.xml' % pathFName)
        self.mdGenerator.save_xml(xmlPath)
        return xmlPath

    def create_series_metadata(self, xmlFiles):
        # look for a previously created tile, to serve as a basis
        base = xmlFiles[0]
        mdGenerator = metadatas.MetadataGenerator(base, self.timeslot, 
                                                       self.product)
        mdGenerator.create_series_metadata()
        xmlPath = os.path.join(self.xmlOutDir, '%s_series.xml' % \
                               self.product.short_name)
        mdGenerator.save_xml(xmlPath)

    def insert_metadata_csw(self, xmlFiles):
        '''
        Insert metadata records in the catalogue server.

        Inputs:

            xmlFiles - A list of paths to the newly-generated XML metadata
                files.

        Returns:
        
            A boolean with the insert operation's result.
        '''

        cswSetts = ss.CatalogueServer.objects.get()
        csw_url = '/'.join((cswSetts.base_URL, cswSetts.csw_URI))
        login_url = '/'.join((cswSetts.base_URL, cswSetts.login_URI))
        logout_url = '/'.join((cswSetts.base_URL, cswSetts.logout_URI))
        result = self.mdGenerator.insert_csw(csw_url, login_url, logout_url,
                                             cswSetts.username, 
                                             cswSetts.password,
                                             filePaths=xmlFiles)
        return result

    def run_main(self, callback=None, tile=None, populateCSW=True, 
                 generate_series=False, use_archive=True, force=False):
        if tile is None:
            xmlFiles = self._process_all_tiles(use_archive=use_archive,
                                               force=force)
            result = xmlFiles
        else:
            xmlFiles = [self._process_single_tile(tile, 
                                                  use_archive=use_archive, 
                                                  force=force)]
            result = xmlFiles[0]
        if populateCSW:
            self.logger.info('Sending metadata to CSW server...')
            inserted = self.insert_metadata_csw(xmlFiles)
            result = inserted
        if generate_series:
            self.create_series_metadata(xmlFiles)
        return result

    def clean_up(self, delete_outputs=True):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.xmlOutDir)
        if delete_outputs:
            self.delete_outputs()
        return 0


class GenericAggregationPackage(GenericItem):
    '''
    Base class for ALL G2Packages that have other packages as input.
    '''

    name = ''

    def run_main(self, callback=None):
        raise NotImplementedError

    def clean_up(self, callback=None):
        '''
        Delete any temporary files.

        The default implementation just calls the clean_up() method
        of this instances inputPackages and outputPackages.
        '''

        packs = []
        if hasattr(self, 'inputPackages'):
            packs += self.inputPackages
        if hasattr(self, 'outputPackages'):
            packs += self.outputPackages
        for p in packs:
            p.clean_up()

    def __unicode__(self):
        return unicode(self.name)

    def _create_packages(self, packRole, packSettings):

        objects = []
        hostSettings = ss.Host.objects.get(name=self.host.name)
        for specificSettings in packSettings:
            timeslots = []
            for tsDisplacement in specificSettings.specificTimeslots.all():
                timeslots += utilities.displace_timeslot(self.timeslot, 
                                                         tsDisplacement)
            if len(timeslots) == 0:
                timeslots.append(self.timeslot)
            specificAreas = [a for a in specificSettings.specificAreas.all()]
            if len(specificAreas) == 0:
                specificAreas = ss.Source.objects.get(\
                                name=self.source.generalName).area_set.all()
            for spArea in specificAreas:
                for spTimeslot in timeslots:
                    # create a new package
                    generalPackSettings = eval('specificSettings.%sItem.package' \
                                               % packRole)
                    #self.logger.debug('Creating package: %s ' % generalPackSettings.name)
                    #self.logger.debug('timeslot: %s' % spTimeslot)
                    #self.logger.debug('area: %s' % spArea) 
                    className = eval(generalPackSettings.code_class.className)
                    newObject = className(generalPackSettings, spTimeslot, spArea,
                                          hostSettings, logger=self.logger)
                    #self.logger.debug('----------') 
                    objects.append(newObject)
        return objects

    def _filter_g2pack_list(self, g2packs, className):
        '''
        Return a list of G2Package instances that belong to the input class.
        '''

        result = []
        for g2p in g2packs:
            if g2p.__class__.__name__ == className:
                result.append(g2p)
        return result

    def _delete_directories(self, dirPaths):
        '''
        Delete the directories specified and any contents they may have.

        Also deletes any parent directories that may become empty.
        '''

        for dirPath in dirPaths:
            self.host.remove_dir(dirPath)


class Archivor(GenericAggregationPackage):
    '''
    This class takes care of the archiving process.

    It will create the relevant packages and archive their outputs.
    '''

    def __init__(self, settings, timeslot, area, host=None, 
                 logger=None):

        super(Archivor, self).__init__(timeslot, area.name, host=host, 
                                       logger=logger)
        for extraInfo in settings.packageextrainfo_set.all():
            #exec('self.%s = "%s"' % (extraInfo.name, extraInfo.string))
            exec('self.%s = utilities.parse_marked(extraInfo, self)' % extraInfo.name)
        self.inputPackages = self._create_packages(
            'input', 
            settings.packageInput_systemsettings_packageinput_related.all()
        )

    def clean_up(self):
        for subPackage in self.inputPackages:
            subPackage.clean_up()

    def archive_output_files(self):
        '''
        Archive the outputs of this package's input packages.
        '''

        result = dict()
        for inp in self.inputPackages:
            result[inp] = inp.archive_outputs(compress=True)
        return result

    def run_main(self):
        self.archive_output_files()


class Cleaner(GenericPackage):
    '''
    This class will remove old files from the local filesystem.
    '''

    def __init__(self, settings, timeslot, area, host=None, logger=None):
        super(Cleaner, self).__init__(timeslot, area.name, host=host, 
                                      logger=logger)
        self.name = settings.name
        self.use_active_hosts = False
        try:
            use_active = settings.packageextrainfo_set.get(name='use_active_hosts')
            self.use_active_hosts = True
        except ss.MarkedString.DoesNotExist:
            pass
        self.routine_threshold = int(
            settings.packageextrainfo_set.get(name='routine_older_than').string
        )
        self.emergency_threshold = int(
            settings.packageextrainfo_set.get(name='emergency_older_than').string
        )

    # FIXME - Test this package out
    def run_main(self, emergency=False, hosts=None, routine_threshold=None,
                 emergency_threshold=None):
        hosts = self._get_hosts(hosts)
        if routine_threshold is None:
            routine_threshold = self.routine_threshold
        if emergency_threshold is None:
            emergency_threshold = self.emergency_threshold
        if emergency:
            threshold = emergency_threshold
        else:
            threshold = routine_threshold
        results = []
        for h in hosts:
            cleaned = h.do_maintenance(threshold, emergency=emergency)
            results.append(cleaned)
        if False not in results:
            result = True
        else:
            result = False
        return result

    def _get_hosts(self, host_settings=None):
        hosts = []
        host_factory = HostFactory()
        if host_settings is None:
            if self.use_active_hosts:
                host_settings = ss.Host.objects.filter(active=True).exclude(role__name='archive')
        else:
            pass
        for host_setting in host_settings:
            hosts.append(host_factory.create_host(host_setting))
        return hosts

class TileDistributor(GenericAggregationPackage):
    '''
    This class handles dissemination of tiled products.
    '''

    def __init__(self, settings, timeslot, area, host=None,
                 logger=None):

        super(TileDistributor, self).__init__(timeslot, area.name, host=host,
                                              logger=logger)
        self.name = settings.name
        for extraInfo in settings.packageextrainfo_set.all():
            #exec('self.%s = "%s"' % (extraInfo.name, extraInfo.string))
            exec('self.%s = utilities.parse_marked(extraInfo, self)' % extraInfo.name)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)

        relZipDir = utilities.parse_marked(
                settings.packagepath_set.get(name='zipOutDir'), self)
        self.zipOutDir = os.path.join(self.host.dataPath, relZipDir)

        self.inputPackages = self._create_packages(
            'input', 
            settings.packageInput_systemsettings_packageinput_related.all()
        )

    def run_main(self, callback=None, tile=None):
        if tile is not None:
            result = self.get_zip(tile)
        else:
            result = None
        return result

    def _build_zip(self, tile):
        '''
        Return a new zip file with the product tile, quicklook and metadata xml.
        '''

        self.host.make_dir(self.workingDir)
        self.host.make_dir(self.zipOutDir)
        # get the product tile
        qlPack = self._filter_g2pack_list(self.inputPackages, 
                                          'QuickLookGenerator')[0]
        tileG2fs = qlPack._filter_g2f_list(qlPack.inputs, 'fileType', 'hdf5')
        theProduct = None
        for g2f in tileG2fs:
            fetched = g2f.fetch(self.workingDir, use_archive=True, 
                                decompress=False, restrict_pattern=tile)
            if len(fetched) > 0:
                theProduct = self.host.compress(fetched)[0]
        # get the quicklook
        quicklooks = qlPack.run_main(tile=tile, move_to_webserver=False, 
                                     delete_local=False)
        if len(quicklooks) != 0:
            theQuickLook = quicklooks[0]
        else:
            raise
        # get the xml
        xmlPack = self._filter_g2pack_list(self.inputPackages, 
                                           'MetadataGenerator')[0]
        theXml = xmlPack.run_main(tile=tile, populateCSW=False)
        # get the xsl file
        theStylesheet = self._find_stylesheet()
        # bundle them into a zip file
        zipName = os.path.basename(os.path.splitext(theProduct)[0]) + '.zip'
        theZip = os.path.join(self.zipOutDir, zipName)
        zf = zipfile.ZipFile(theZip, mode='w')
        for filePath in (theProduct, theQuickLook, theXml, theStylesheet):
            zf.write(filePath, arcname=os.path.basename(filePath))
        zf.close()
        return theZip

    def _find_stylesheet(self):
        sub_pack = self._filter_g2pack_list(self.inputPackages,
                                            'MetadataGenerator')[0]
        templates = self.host.list_dir(sub_pack.xmlTemplateDir, 
                                       relativeTo='code')
        stylesheet = [t for t in templates if t.endswith('.xsl')][0]
        return stylesheet

    def get_zip(self, tile):
        # first try to find the already generated zip file
        # if not found, generate a new one
        theZip = None
        qlPack = self._filter_g2pack_list(self.inputPackages, 
                                          'QuickLookGenerator')[0]
        tileG2fs = qlPack._filter_g2f_list(qlPack.inputs, 'fileType', 'hdf5')
        for g2f in tileG2fs:
            for patt in g2f.searchPatterns:
                for filePath in self.host.list_dir(self.zipOutDir):
                    if re.search(patt, filePath) is not None and \
                            re.search(tile, filePath) is not None and \
                            re.search(r'\.zip$', filePath) is not None:
                        self.logger.debug('Found the zip file. No need to regenerate.')
                        theZip = filePath
        if theZip is None:
            self.logger.debug('Generating a new zip file...')
            theZip = self._build_zip(tile)
        return theZip

    def clean_up(self):
        super(TileDistributor, self).clean_up()
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.zipOutDir)


class SWIDistributor(ProcessingPackage):

    def __init__(self, settings, timeslot, area, host=None, 
                 logger=None, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object
        '''

        self.rawSettings = settings
        self.name = settings.name
        self.product = settings.product
        self.version = settings.external_code.version
        super(SWIDistributor, self).__init__(settings, timeslot, area,
                                             host=host, logger=logger)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)
        relMetaTemplateDir = utilities.parse_marked(
                settings.packagepath_set.get(name='xmlTemplateDir'), self)
        self.xmlTemplateDir = os.path.join(self.host.codePath, 
                                           relMetaTemplateDir)
        relZipDir = utilities.parse_marked(
                settings.packagepath_set.get(name='zipOutDir'), self)
        self.zipOutDir = os.path.join(self.host.dataPath, relZipDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )

    def get_zip(self):
        '''
        Return the path to the zip file for dissemination.
        '''

        # look for the zip file in the localhost
        # then look for it in the archives
        # if not found, call the _build_zip method
        zip_file = [g2f for g2f in self.outputs if g2f.fileType == 'zip'][0]
        fetched = zip_file.fetch(self.zipOutDir, use_archive=True, 
                                 decompress=False)
        if len(fetched) > 0:
            #fetch or use the local one
            self.logger.debug('Re-using previously present zip file.')
            the_zip = fetched[0]
        else:
            #build a new zip
            self.logger.debug('Building a new zip file...')
            the_zip = self._build_zip()
        return the_zip

    def _build_zip(self):
        # look for the inputs in the localhost
        # thenk look for them in the archives
        # then build a zip with them
        self.host.make_dir(self.zipOutDir)
        self.host.make_dir(self.workingDir)
        paths = []
        zip_file = [g2f for g2f in self.outputs if g2f.fileType == 'zip'][0]
        file_name, zip_ext, rest = zip_file.searchPatterns[0].partition('zip')
        zip_name = ''.join((file_name, zip_ext))
        for g2f in self.inputs:
            fetched = g2f.fetch(self.workingDir, use_archive=True, 
                                decompress=False)
            if len(fetched) > 0:
                if g2f.name == 'swi':
                    fetched = self.host.compress(fetched)
                paths += fetched
        templates = self.host.list_dir(self.xmlTemplateDir, relativeTo='code')
        xsl = [t for t in templates if t.endswith('.xsl')][0]
        paths.append(xsl)
        the_zip = self.host.build_zip(zip_name, paths, self.zipOutDir)
        return the_zip

    def clean_up(self):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.zipOutDir)
        return 0

    def run_main(self):
        return self.get_zip()
