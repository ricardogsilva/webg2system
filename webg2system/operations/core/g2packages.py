import os
import time
import re
from random import randint
from uuid import uuid1
import datetime as dt

import systemsettings.models as ss

from g2item import GenericItem
from g2files import G2File
import mappers
import metadatas
import utilities

class GenericPackage(GenericItem):
    '''
    Base class for ALL G2Packages.

    All GenericPackages must inherit from GenericItem and provide concrete
    implementations for the method stubs defined here.

    The private methods (the ones indicated with '_' before their name) are
    concrete implementations that should not need to be reimplemented.
    '''

    name = ''

    def prepare(self, callback=None):
        pass

    def delete_outputs(self, callback=None):
        raise NotImplementedError

    def run_main(self, callback=None):
        raise NotImplementedError

    def clean_up(self, callback=None):
        raise NotImplementedError

    def __unicode__(self):
        return unicode(self.name)

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
                    #self.logger.debug('Creating file: %s ' % generalFileSettings.name)
                    #self.logger.debug('timeslot: %s' % spTimeslot)
                    #self.logger.debug('area: %s' % spArea) 
                    newObject = G2File(generalFileSettings, spTimeslot, spArea,
                                       hostSettings, specificSettings.optional,
                                       parent=self)
                    #self.logger.debug('----------') 
                    objects.append(newObject)
        return objects

    def _find_files(self, g2files, useArchive):
        '''
        Inputs:

            g2files - A list of g2file instances

            useArchive - A boolean indicating if the archives are to be
                searched if the files are not found in their expected
                location.

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
                self.logger.info('Looking for %s...' % g2f.name)
                result[g2f] = g2f.find(useArchive)
        return result

    def _fetch_files(self, g2files, relTargetDir, useArchive, 
                     decompress=False):
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
                                          decompress=decompress)
                result[g2f] = localPathList
        return result

    def _delete_directories(self, dirPaths):
        '''
        Delete the directories specified and any contents they may have.

        Also deletes any parent directories that may become empty.
        '''

        for dirPath in dirPaths:
            self.host.remove_dir(dirPath)


class ProcessingPackage(GenericPackage):

    def __init__(self, settings, timeslot, area, host):
        '''
        This class inherits all the extra variables and has the 'normal'
        implementation for find_inputs, find_outputs, fetch_inputs and
        
        '''

        super(ProcessingPackage, self).__init__(timeslot, area.name, host)
        for extraInfo in settings.packageextrainfo_set.all():
            #exec('self.%s = "%s"' % (extraInfo.name, extraInfo.string))
            exec('self.%s = utilities.parse_marked(extraInfo, self)' % extraInfo.name)
        # a random number for generating unique working dirs
        self.random = randint(0, 100)

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

    def delete_outputs(self, callback=None, deleteStatics=False):
        '''
        Delete the package's output files.

        Inputs:

            deleteStatics - A boolean indicating if the static outputs should
                be deleted (if there are any).
        '''

        foundOutputs = self.find_outputs(useArchive=False)
        for g2f, foundDict in foundOutputs.iteritems():
            if not (g2f.frequency == 'static' and deleteStatics):
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

        foundOutputs = self.find_outputs(useArchive=False)
        toCompress = []
        for g2f, foundDict in foundOutputs.iteritems():
            if g2f.toCompress:
                for p in foundDict['paths']:
                    toCompress.append(p)
            else:
                self.logger.debug('%s is not marked as \'Compress\' in the '\
                                  'settings, skipping...' % g2f.name)
        self.logger.info('Compressing %s outputs...' % self.name)
        self.host.compress(toCompress)

    def decompress_outputs(self):
        '''
        Decompress the outputs of this package with bunzip2.
        '''

        self.logger.info('Decompressing %s outputs...' % self.name)
        foundOutputs = self.find_outputs(useArchive=False)
        toDecompress = []
        for g2f, foundDict in foundOutputs.iteritems():
            for p in foundDict['paths']:
                toDecompress.append(p)
        self.host.decompress(toDecompress)


class FetchData(ProcessingPackage):
    '''
    This class uses:

        - outputDir
    '''

    def __init__(self, settings, timeslot, area, host, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object

            host - A systemsettings.models.Host object

            createIO - A boolean indicating if the inputs and outputs
                are to be created. Defaults to True.
        '''

        super(FetchData, self).__init__(settings, timeslot, area, host)
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

    def prepare(self, callback=None):
        '''
        Prepare the inputs for running the main code.

        The fetchData class has no real use for this method, as it only
        moves files from their temporary input location to their final 
        destination.
        '''
        #import time
        #callback('sleeping a bit...', 1)
        #time.sleep(20)
        return 0

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

    def __init__(self, settings, timeslot, area, host, createIO=True):
        super(LRITPreprocessor, self).__init__(settings, timeslot, area, host)
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
        relCodeDir = utilities.parse_marked(
                settings.packagepath_set.get(name='codeDir'), 
                self)
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

    def __init__(self, settings, timeslot, area, host, createIO=True):
        super(GRIBPreprocessor, self).__init__(settings, timeslot, area, host)
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
        relCodeDir = utilities.parse_marked(
                settings.packagepath_set.get(name='codeDir'), 
                self)
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

    def __init__(self, settings, timeslot, area, host, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object

            host - A systemsettings.models.Host object

            createIO - A boolean indicating if the inputs and outputs
                are to be created. Defaults to True.
        '''

        super(Processor, self).__init__(settings, timeslot, 
                                                   area, host)
        self.rawSettings = settings
        self.name = settings.name
        relOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        self.outputDir = os.path.join(self.host.dataPath, relOutDir)
        relCodeDir = utilities.parse_marked(
                settings.packagepath_set.get(name='codeDir'), 
                self)
        self.codeDir = os.path.join(self.host.codePath, relCodeDir)
        relWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), 
                self)
        self.workingDir = os.path.join(self.host.dataPath, relWorkDir)
        relAcfTemplateDir = utilities.parse_marked(
                settings.packagepath_set.get(name='acfTemplate'), 
                self)
        self.acfTemplateDir = os.path.join(self.host.dataPath, relAcfTemplateDir)
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


class SWIProcessor(ProcessingPackage):

    def __init__(self, settings, timeslot, area, host, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object

            host - A systemsettings.models.Host object

            createIO - A boolean indicating if the inputs and outputs
                are to be created. Defaults to True.
        '''

        super(SWIProcessor, self).__init__(settings, timeslot, area, host)
        self.rawSettings = settings
        self.name = settings.name
        relOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        self.outputDir = os.path.join(self.host.dataPath, relOutDir)
        relCodeDir = utilities.parse_marked(
                settings.packagepath_set.get(name='codeDir'), 
                self)
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


class DataFusion(ProcessingPackage):
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

    def __init__(self, settings, timeslot, area, host, createIO=True):
        '''
        Inputs:

            settings - A systemsettings.models.Package object

            timeslot - A datetime.datetime object

            area - A systemsettings.models.Area object

            host - A systemsettings.models.Host object
        '''

        super(DataFusion, self).__init__(settings, timeslot, area, host)
        self.rawSettings = settings
        self.name = settings.name
        relativeOutDir = utilities.parse_marked(
                settings.packagepath_set.get(name='outputDir'), 
                self)
        relativeCodeDir = utilities.parse_marked(
                settings.packagepath_set.get(name='codeDir'), 
                self)
        relativeWorkDir = utilities.parse_marked(
                settings.packagepath_set.get(name='workingDir'), 
                self)
        self.outputDir = os.path.join(self.host.dataPath, relativeOutDir)
        self.codeDir = os.path.join(self.host.codePath, relativeCodeDir)
        self.workingDir = os.path.join(self.host.dataPath, relativeWorkDir)
        if createIO:
            self.inputs = self._create_files(
                'input', 
                settings.packageInput_systemsettings_packageinput_related.all()
            )
            self.outputs = self._create_files(
                'output', 
                settings.packageOutput_systemsettings_packageoutput_related.all()
            )


class WebDisseminator(ProcessingPackage):
    '''
    This class takes care of creating quickviews, WMS and CSW integration.
    '''

    def __init__(self, settings, timeslot, area, host, createIO=True):
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
        self.inputs = self._create_files(
            'input', 
            settings.packageInput_systemsettings_packageinput_related.all()
        )
        self.mapper = mappers.NGPMapper(self.inputs[0]) # <- badly defined
        self.mdGenerator = metadatas.MetadataGenerator(self.xmlTemplate)

    def clean_up(self, callback=None):
        self._delete_directories([self.workingDir])
        self.host.clean_dirs(self.mapfileOutDir)
        self.host.clean_dirs(self.quickviewOutDir)
        self.host.clean_dirs(self.xmlOutDir)
        return 0

    def prepare(self, callback=None):
        pass

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

    def generate_quicklooks_mapfile(self, fileList):
        '''
        Generate mapfile.

        Inputs:

            fileList - A list of file paths with the files to be included in 
                the mapfiles.

        Returns:

            A string with the full path to the newly generated mapfile.
        '''

        globalTifName = '%s_%s%s%s%s%s.tif' % (self.mapper.product.shortName,
                                               self.year, self.month, 
                                               self.day, self.hour, 
                                               self.minute)
        if not self.host.is_dir(self.geotifOutDir):
            self.host.make_dir(self.geotifOutDir)
        globalProd = self.mapper.create_global_tiff(fileList, self.geotifOutDir,
                                                    globalTifName)
        templateName = 'template_quicklooks.map'
        template = os.path.join(self.mapfileTemplateDir, templateName)
        mapfileName = 'quicklooks.map'
        mapfilePath = os.path.join(self.mapfileOutDir, mapfileName)
        if not self.host.is_dir(self.mapfileOutDir):
            self.host.make_dir(self.mapfileOutDir)
        commonGeotifPath = os.path.commonprefix((self.commonGeotifDir, 
                                                globalProd))
        relativeGeotifPath = re.sub(commonGeotifPath, '', globalProd)[1:]
        mapfile = self.mapper.create_mapfile(relativeGeotifPath, 
                                             self.commonGeotifDir, 
                                             mapfilePath, template)
        return mapfile

    def generate_quicklooks(self, mapfile, fileList):

        self.host.make_dir(self.quickviewOutDir)
        quicklooks = self.mapper.generate_quicklooks(self.quickviewOutDir, 
                                                     mapfile, fileList)
        return quicklooks

    def generate_xml_metadata(self, fileList):

        if not self.host.is_dir(self.xmlOutDir):
            self.host.make_dir(self.xmlOutDir)
        today = dt.date.today().strftime('%Y-%m-%d')
        genMeta = ss.GeneralMetadata.objects.get()
        for fNum, path in enumerate(fileList):
            self.logger.debug('(%i/%i) - Creating xml...' % 
                              (fNum+1, len(fileList)))
            fs = utilities.get_file_settings(path)
            minx, miny, maxx, maxy = self.mapper.get_bounds(path)
            uuid = uuid1()
            self.mdGenerator.update_element('fileIdentifier', str(uuid))
            self.mdGenerator.update_element('parentIdentifier', 
                                            fs.product.iParentIdentifier)
            self.mdGenerator.update_element('hierarchyLevel', 
                                            fs.product.iResourceType)
            self.mdGenerator.update_element('organisationName', 
                                            genMeta.orgName)
            self.mdGenerator.update_element('organisationAddress', 
                                            genMeta.orgStreetAddress)
            self.mdGenerator.update_element('organisationCity', 
                                            genMeta.orgCity)
            self.mdGenerator.update_element('organisationPostalCode', 
                                            genMeta.orgPostalCode)
            self.mdGenerator.update_element('electronicMailAddress', 
                                            genMeta.contactEmail)
            self.mdGenerator.update_element('dateStamp', today)
            rowSize = fs.fileextrainfo_set.get(name='nLines').string
            self.mdGenerator.update_element('rowSize', rowSize)
            self.mdGenerator.update_element('rowResolution', '%.2f' % 
                                            fs.product.pixelSize)
            colSize = fs.fileextrainfo_set.get(name='nCols').string
            self.mdGenerator.update_element('colSize', colSize)
            self.mdGenerator.update_element('colResolution', '%.2f' %
                                            fs.product.pixelSize)
            cornerPoint = '%.1f %.1f' % (maxy, minx)
            self.mdGenerator.update_element('cornerPoint', cornerPoint)
            self.mdGenerator.update_element('referenceSystemIdentifier', 
                                            fs.product.ireferenceSystemID)
            self.mdGenerator.update_element('title', fs.product.iResourceTitle)
            # For now, assuming the metadata is being created on the same day
            # that the products got generated. This assumption is not good.
            # A better solution would be to move this method (and the 
            # quicklooks too, for similar reason) to the class that actually 
            # generates the product and have it be generated right after the
            # product.
            self.mdGenerator.update_element('date', today)
            #self.mdGenerator.update_element('Resource abstract', 
            #                                fs.product.iResourceAbstract)
            #self.mdGenerator.update_element('Resource type', 
            #                                fs.product.iResourceType)
            #self.mdGenerator.update_element('westLongitude', '%.2f' % minx)
            #self.mdGenerator.update_element('eastLongitude', '%.2f' % maxx)
            #self.mdGenerator.update_element('southLatitude', '%.2f' % miny)
            #self.mdGenerator.update_element('northLatitude', '%.2f' % maxy)
            #self.mdGenerator.update_element('uuid', str(uuid))
            #self.mdGenerator.update_element('idCode', str(uuid))
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
