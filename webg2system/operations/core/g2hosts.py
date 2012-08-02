#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module holds the G2Host classes. these classes take care of the actual
file IO operations between the different host machines involved in the
G2system's processes.

The G2Host classes should not be instantiated directly. They should use the
create_host() function, that simultaneously implements a factory and sigleton
pattern for unique hosts.
"""

# standard library imports
import shutil
import logging
import os
import re
import subprocess
from xml.etree.ElementTree import ElementTree as et
import ftplib
import socket
from pexpect import spawn
#import glob
#import fnmatch

# django imports
from django.core.exceptions import ObjectDoesNotExist


import tables

# specific imports
import systemsettings.models as ss
from sshproxy import SSHProxy
from ftpproxy import FTPProxy
from sftpproxy import SFTPProxy

# TODO
# - Review all the methods that have a FIXME tag
# - Implement the remaining methods on G2RemoteHost class

class HostFactory(object):

    _hosts = dict()

    def __init__(self, logger=None):
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

    def create_host(self, hostSettings=None):
        '''
        Return a new G2host instance or return an already existing one.

        Inputs:

            hostSettings - A systemsettings.models.Host object. If None, the
                local host's settings will be used.
        '''

        localName = socket.gethostname()
        try:
            localIP = socket.gethostbyname(localName)
        except socket.gaierror:
            self.logger.warning('Couldn\'t determine %s\'s IP address' \
                                % localName)
            localIP = None
        if hostSettings is None:
            try:
                hostSettings = ss.Host.objects.get(name=localName)
            except ObjectDoesNotExist:
                hostSettings = ss.Host.objects.get(ip=localIP)
        name = hostSettings.name
        ip = hostSettings.ip
        if name not in self._hosts.keys():
            #self.logger.debug('Creating a new %s host object...' % 
            #                 (name))
            if name == localName or ip == localIP:
                theClass = G2LocalHost
            else:
                theClass = G2RemoteHost
            hostObj = theClass(hostSettings, logger=self.logger)
            self._hosts[name] = hostObj
        return self._hosts.get(name)

        #self.logger.debug('Creating a new %s host object...' % 
        #                 (name))
        #if name == localName or ip == localIP:
        #    theClass = G2LocalHost
        #else:
        #    theClass = G2RemoteHost
        #hostObj = theClass(hostSettings)

        #return hostObj


class G2Host(object):

    name=''

    def __init__(self, settings, logger=None):
        '''
        Inputs:

            settings - A systemsettings.models.Host object

            <-- old docstring
            isLocal- A boolean. It indicates if this host object is dealing
                with the current machine or with another remote machine
                over the network.

            name - A string with the name of the host

            basePath - A string with the basepath that is to be used for
                all operations on the host

            ip - A string with the ip or hostname of the host

            username - A string with the user name of the user authorized to
                perform operations on the host

            password - A string with the password
            -->
        '''

        self.logger = logger
        self.name = settings.name
        self.connections = dict()
        self.dataPath = settings.dataPath
        if settings.codePath is None or settings.codePath == '':
            self.codePath = None
        else:
            self.codePath = settings.codePath
        self.host = settings.ip
        self.user = settings.username
        self.password = settings.password
        self.roles = [r.name for r in settings.role.all()]

    def __repr__(self):
        return self.name

    # method stubs to be implemented by subclasses
    def find(self, pathList):
        raise NotImplementedError

    def fetch(self, fullPaths, relativeDestinationDir, sourceHost):
        raise NotImplementedError

    def send(self, relativePaths, relativeDestinationDir, destinationHost):
        raise NotImplementedError

    def compress(self, relativePaths):
        raise NotImplementedError

    def decompress(self, paths):
        raise NotImplementedError

    def create_file(self):
        raise NotImplementedError

    def count_file_lines(self, filePath):
        raise NotImplementedError

    def delete_files(self):
        raise NotImplementedError

    def get_cwd(self):
        raise NotImplementedError

    def list_dir(self):
        raise NotImplementedError

    def change_dir(self):
        raise NotImplementedError

    def make_dir(self):
        raise NotImplementedError

    def remove_dir(self):
        '''Delete a directory along with any contents it may have.'''
        raise NotImplementedError

    def clean_dirs(self):
        '''Delete an empty directory and any (empty) parent directories.'''
        raise NotImplementedError

    def run_program(self):
        raise NotImplementedError

    def rename_file(self, oldPath, newPath):
        raise NotImplementedError


class G2LocalHost(G2Host):
    """
    This class has the implementation of the local file IO operations.
    """

    def list_dir(self, directory, relativeTo='data'):
        relMap = {'data' : self.dataPath, 'code' : self.codePath}
        fullPath = os.path.join(relMap.get(relativeTo), directory)
        if self.is_dir(directory, relativeTo):
            dirList = [os.path.join(fullPath, p) for p in os.listdir(fullPath)]
        else:
            dirList = []
            self.logger.warning('No such directory: %s' % fullPath)
        return dirList

    def find(self, pathList, restrictPattern=None):
        '''
        Search for the paths in the local directory tree.

        This method is to return all the paths that are found, even if there
        are duplicate files or the same file in compressed and uncompressed
        forms. It will be up to the client code to sort out which paths are
        interesting.

        Inputs:

            pathList - A list with paths for the files to search. The paths 
                are treated as regular expressions.

        Returns:

            A list with the full paths to the found files.
        '''

        foundFiles = []
        for path in pathList:
            if path.startswith(os.path.sep):
                fullSearchPath = path
            else:
                fullSearchPath = os.path.join(self.dataPath, path)
            searchDir, searchPattern = os.path.split(fullSearchPath)
            patt = re.compile(searchPattern)
            dirExists = os.path.isdir(searchDir)
            if dirExists:
                for item in os.listdir(searchDir):
                    if patt.search(item) is not None:
                        if restrictPattern is not None:
                            if re.search(restrictPattern, item) is not None:
                                foundFiles.append(os.path.join(searchDir, item))
                        else:
                            foundFiles.append(os.path.join(searchDir, item))
            else:
                self.logger.warning('No such directory: %s' % searchDir)
        return foundFiles
    
    def fetch(self, fullPaths, relativeDestinationDir, sourceHost):
        '''
        Fetch the files from sourceHost.
        
        Inputs:
        
            fullPaths - A list of strings specifying the full paths to the
                files that should be copied.
                
            relativeDestinationDir - The directory on the local host where
                the files will be copied to. It will be created in case it
                doesn't exist. This directory is relative to the host's
                codePath or dataPath attribute (see the 'relativeTo' input).
            
            sourceHost - A G2host instance representing the host where the
                files will be copied from.
                
        Returns:
        
            A list of strings with the full paths to the newly fetched files.
        '''
        
        if sourceHost is self:
            self.logger.debug('About to perform a local fetch...')
            result = self._fetch_from_local(fullPaths, relativeDestinationDir)
        else:
            self.logger.debug('About to perform a remote fetch...')
            result = self._fetch_from_remote(fullPaths, relativeDestinationDir, 
                                             sourceHost) 
        return result

    def _fetch_from_local(self, fullPaths, directory):

        fullDestPaths = []
        outputDir = os.path.join(self.dataPath, directory)
        if not self.is_dir(outputDir):
                self.make_dir(outputDir)
        for path in fullPaths:
            try:
                shutil.copy(path, outputDir)
            except shutil.Error:
                pass
            newPath = os.path.join(outputDir, os.path.basename(path))
            fullDestPaths.append(newPath)
        return fullDestPaths

    def _fetch_from_remote(self, fullPaths, directory, sourceHost, 
                           protocol='sftp'):
        '''
        Fetch the files from the remote host.

        Inputs:
            
            fullPaths - 

            directory - 

            sourceHost - A G2Host object.

        Returns:

            A list of string with the full paths to the newly fetched files.
        '''
        
        connection = self._get_connection(sourceHost, protocol)
        outputDir = os.path.join(self.dataPath, directory)
        newPaths = connection.fetch(fullPaths, outputDir)
        return newPaths

    def _get_connection(self, host, protocol):
        '''
        Return the relevant connection object.

        Inputs:

            host - A G2Host object.

            protocol - A string with the name of the connection protocol.
                Currently planned protocols are 'ftp' and 'sftp'.
        '''

        hostConnections = self.connections.get(host.name)
        if hostConnections is not None:
            connection = hostConnections.get(protocol)
            if connection is not None:
                #self.logger.debug('Reusing previously opened connection to %s.'\
                #                 % host.name)
                result = connection
            else:
                self.logger.debug('Creating connection to %s with protocol %s' % 
                                 (host.name, protocol))
                result = self._connect(host, protocol)
        else:
            self.logger.debug('Creating the first connection to %s with protocol %s' % 
                             (host.name, protocol))
            result = self._connect(host, protocol)
        return result

    def _connect(self, host, protocol):
        '''
        Establish a connection between the local host and the 'host' argument
        using 'protocol'.

        Inputs:

            host - A G2Host object

            protocol -
        '''

        if self.connections.get(host.name) is None:
            # create the dictionary that will hold the FTP and SSH connections
            self.connections[host.name] = dict()
        if self.connections.get(host.name).get(protocol) is None:
            if protocol == 'ssh':
                self.connections[host.name]['ssh'] = SSHProxy(
                    host.user, 
                    host.host, 
                    logger=self.logger
                )
            elif protocol == 'ftp':
                self.connections[host.name]['ftp'] = FTPProxy(
                    localHost=self, 
                    remoteHost=host,
                    logger=self.logger
                )
            elif protocol == 'sftp':
                self.connections[host.name]['sftp'] = SFTPProxy(
                    local_host=self,
                    remote_host=host,
                    logger=self.logger
                )
        return self.connections[host.name][protocol]

    def send(self, fullPaths, destDir, destHost=None):
        '''
        Copy files to another directory, located on a G2Host machine.

        Inputs:
            
            fullPaths - A list with the relative paths of the files to send.

            destDir - A string with the relative path on the destination
                host where the files are to be sent to.

            destHost - A G2Host instance, specifying the machine that will
                receive the files. A value of None (which is also the default)
                is interpreted as meaning a local host.

        Returns:
        '''

        if (destHost is self) or (destHost is None):
            self.logger.debug('About to perform a local send...')
            result = self._send_to_local(fullPaths, destDir)
        else:
            self.logger.debug('About to perform a remote send...')
            result = self._send_to_remote(fullPaths, destDir, destHost)
        return result

    # FIXME
    # - return the actual returncode, and not a hardcoded zero
    def _send_to_local(self, paths, destDir):
        '''
        Perform a local copy operation.

        Returns:

            A tuple with:
                - The returncode of the send operation
                - A list of full paths to the newly sent files' location.
        '''

        fullDestDir = os.path.join(self.dataPath, destDir)
        result = []
        for path in paths:
            fullPath = os.path.join(self.dataPath, path)
            shutil.copy(path, fullDestDir)
            result.append(os.path.join(fullDestDir, os.path.basename(path)))
        return (0, result)

    def _send_to_remote(self, paths, destDir, destHost, protocol='sftp'):
        connection = self._get_connection(destHost, protocol)
        returnCode = connection.send(paths, destDir)
        if returnCode == 0: # sending went OK
            remotePaths = [
                os.path.join(
                    destHost.dataPath, 
                    destDir, 
                    os.path.basename(p)
                ) for p in paths
            ]
            result = (returnCode, remotePaths)
        else: # something went wrong
            result = (returnCode, [])
        return result

    # FIXME
    # launch several subprocesses simultaneously in order to speed up
    # this method's running time
    def compress(self, paths):
        '''
        Compress the files and leave them in the same directory.

        Returns:
            
            A list with the full paths to the newly compressed files.
        '''

        newPaths = []
        toCompress = []
        for path in paths:
            if path.startswith(os.path.sep):
                thePath = path
            else:
                thePath = os.path.join(self.dataPath, path)
            if thePath.endswith('.bz2'):
                newPaths.append(thePath)
            else:
                toCompress.append(thePath)
        if len(toCompress) > 0:
            stdout, stderr, retCode = self.run_program('bzip2 -f %s' % \
                                                       ' '.join(toCompress))
            if retCode == 0:
                newPaths += [p+'.bz2' for p in toCompress]
            else:
                #there has been an error compressing the files
                raise Exception
        return newPaths

    def decompress(self, paths):
        '''
        Decompress the files and leave them in the same directory.

        Inputs:
            
            relativePaths - A list with the full paths of the files
                that are to be decompressed.

        Returns:

            A list with the new filenames, after decompression
        '''
        
        compressed = [p for p in paths if p.endswith('.bz2')]
        decompressed = [p for p in paths if not p.endswith('.bz2')]
        newPaths = decompressed
        if len(compressed) > 0:
            stdout, stderr, retCode = self.run_program('bunzip2 %s' % \
                                                       ' '.join(compressed))
            if retCode == 0:
                newPaths += [p.replace('.bz2', '') for p in compressed]
            else:
                #there has been an error decompressing the files
                self.logger.error('Error decompressing outputs. '\
                                  'Return code: %s' % retCode)
                self.logger.error('stdout: %s' % stdout)
                self.logger.error('stderr: %s' % stderr)
                raise Exception
        return newPaths

    def run_program(self, command, workingDir=None, env=None):
        '''
        Run an external program.

        Inputs:

            command - A string with the full command to run.

            workingDir - The directory where the program should be
                run.

            env - A list of two-element tuples containing the name and value
                of aditional environment variables to be set before running 
                the command. This is useful for setting the SMS_PROG variable 
                before pinging the sms server, for example.

        Returns:

            A tuple with the commands' stdout, stderr and return code.
        '''

        if env is not None:
            the_env = os.environ
            for tup in env:
                the_env[tup[0]] = tup[1]
        else:
            the_env = None
        commandList = command.split(' ')
        newProcess = subprocess.Popen(commandList, cwd=workingDir, env=the_env,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      close_fds=True)
        stdout, stderr = newProcess.communicate()
        retCode = newProcess.returncode
        return stdout, stderr, retCode

    def start_sms_server(self, working_dir=None):
        '''
        Starts a new sms server.
        '''

        #new_process = subprocess.Popen(['sms', '-b'], cwd=working_dir,
        #                               stdout=subprocess.PIPE,
        #                               stderr=subprocess.STDOUT)
        new_process = subprocess.Popen('sms -b > /dev/null 2>&1', shell=True, 
                                       cwd=working_dir)
        return new_process.wait()

    def delete_files(self, relativePathList):
        '''
        Delete the files from the filesystem.

        If the directories where the files were present become empty
        after deletion, they will also get deleted.
        '''

        for relPath in relativePathList:
            fullPath = os.path.join(self.dataPath, relPath)
            try:
                #self.logger.debug('Deleting %s...' % fullPath)
                os.remove(fullPath)
                dirPath = os.path.dirname(fullPath)
                self.clean_dirs(dirPath)
            except OSError:
                # file doesn't exist
                pass

    def get_cwd(self):
        cwd = os.getcwd()
        self.logger.info('cwd: %s' % cwd)
        return os.getcwd()

    def change_dir(self, destination):
        os.chdir(destination)

    def make_dir(self, directory, relativeTo='data'):
        '''Recursively make every directory needed to ensure relativeDirPath.'''

        if relativeTo == 'data':
            basePath = self.dataPath
        else:
            basePath = self.codePath
        fullPath = os.path.join(basePath, directory)
        if not self.is_dir(fullPath):
            os.makedirs(fullPath)
        return fullPath

    def remove_dir(self, directory, relativeTo='data'):
        '''
        Remove directory along with any content it may have.
        
        Also removes any empty parent directories.
        '''

        if relativeTo == 'data':
            basePath = self.dataPath
        else:
            basePath = self.codePath
        if self.is_dir(directory):
            fullPath = os.path.join(basePath, directory)
            shutil.rmtree(fullPath)
            parentDir = fullPath.rpartition(os.path.sep)[0]
            self.clean_dirs(parentDir)

    def clean_dirs(self, directory):
        '''Remove the directory if it is empty. Also remove empty parents.'''

        fullPath = os.path.join(self.dataPath, directory)
        try:
            os.removedirs(fullPath)
        except OSError:
            pass

    def is_dir(self, directory, relativeTo='data'):
        if relativeTo == 'data':
            basePath = self.dataPath
        else:
            basePath = self.codePath
        fullPath = os.path.join(basePath, directory)
        return os.path.isdir(fullPath)

    def is_file(self, directory, relativeTo='data'):
        if relativeTo == 'data':
            basePath = self.dataPath
        else:
            basePath = self.codePath
        fullPath = os.path.join(basePath, directory)
        return os.path.isfile(fullPath)

    def create_file(self, filePath, fileContents):
        '''
        Create a new text file.

        Inputs:

            filePath - A string with the path to the new file.

            fileContents - A list of strings with the lines of text that the
                new file should contain.

        Returns:

            A string with the full path to the newly written file.
        '''

        fullPath = os.path.join(self.dataPath, filePath)
        # use a try block
        fh = open(fullPath, 'w')
        for line in fileContents:
            fh.write(line)
        fh.close()
        return fullPath

    def count_file_lines(self, filePath):
        '''
        Return the number of lines that exist in the input file.
        '''

        fullPath = os.path.join(self.dataPath, filePath)
        numLines = 0
        fh = open(fullPath)
        for line in fh:
            numLines += 1
        fh.close()
        return numLines

    def get_hdf5_params(self, latFile, lonFile):
        '''
        Open and retrieve interesting information from the input HDF5 tiles.

        Inputs:

            latFile - Full path to the HDF5 file that has the minimum 
                'V' coordinate. 'V' refers to the Geoland-2 tile grid.
            lonFile - Full path to the HDF5 file that has the minimum 
                'H' coordinate. 'H' refers to the Geoland-2 tile grid.
        '''

        latDS = tables.openFile(latFile)
        nRows = int(latDS.root._v_attrs.NL) # verify the name of this attribute
        nCols = int(latDS.root._v_attrs.NC) # verify the name of this attribute
        pixelPatt = re.compile(r'\d+\.\d+')
        pixSize = latDS.root._v_attrs["PIXEL_SIZE"]
        gxsize, gysize = [float(n) for n in pixelPatt.findall(pixSize)]
        ullat = latDS.root._v_attrs.FIRST_LAT * 1.0 + gysize / 2.0
        dataset = self.get_dataset_name(minVFile) # <-
        scalingFactor = eval("latDS.root.%s.getAttr('SCALING_FACTOR')" % dataset)
        missingValue = int(eval("latDS.root.%s.getAttr('MISSING_VALUE')" % dataset))
        latDS.close()
        lonDS = tables.openFile(minHFile)
        ullon = lonDS.root._v_attrs.FIRST_LON * 1.0 - gxsize / 2.0
        lonDS.close()
        params = {
                'minH' : minH, 'maxH' : maxH, 'minV' : minV, 'maxV' : maxV,
                'nRows' : nRows, 'nCols' : nCols, 
                'gxsize' : gxsize, 'gysize' : gysize,
                'ullat' : ullat, 'ullon' : ullon,
                'scalingFactor' : scalingFactor,
                'missingValue' : missingValue,
                'dataset' : dataset
                }
        return params

    def rename_file(self, oldPath, newPath):
        return os.rename(oldPath, newPath)


class G2RemoteHost(G2Host):
    '''
    This class implements file IO and other operations in a remote host.
    '''


    def __init__(self, settings, logger=None):
        '''
        Inputs:

            settings - A systemsettings.models.Host object

            <-- old docstring
            isLocal- A boolean. It indicates if this host object is dealing
                with the current machine or with another remote machine
                over the network.

            name - A string with the name of the host

            basePath - A string with the basepath that is to be used for
                all operations on the host

            ip - A string with the ip or hostname of the host

            username - A string with the user name of the user authorized to
                perform operations on the host

            password - A string with the password
            -->
        '''

        super(G2RemoteHost, self).__init__(settings, logger=logger)
        # _localConnection is the connection by which the local machine
        # sends commands to this remoteHost
        factory = HostFactory(logger=self.logger)
        localHost = factory.create_host()
        self._localConnection = {
                'ftp' : FTPProxy(localHost=localHost, remoteHost=self, 
                                 logger=self.logger),
                #'ssh' : SSHProxy(self.user, self.host, self.password),
                'ssh' : SSHProxy(self.user, self.host, logger=self.logger),
                'sftp' : SFTPProxy(localHost, self, logger=self.logger),
                }

    def find(self, pathList, restrictPattern=None, protocol='sftp'):
        '''
        Find the paths.

        Inputs:

            pathList - A list with paths for the files to search. The paths 
            are treated as regular expressions.

            protocol - The name of the protocol used to find the files.
                Available values are 'sftp' (the default) and 'ftp'.

        Returns:

            A list with the full paths to the found files.
        '''

        foundFiles = []
        fullSearchPaths = []
        for path in pathList:
            if path.startswith(os.path.sep):
                fullSearchPaths.append(path)
            else:
                fullSearchPaths.append(os.path.join(self.dataPath, path))
        if protocol == 'ftp':
            foundFiles = self._localConnection['ftp'].find(fullSearchPaths, 
                                                           restrictPattern)
        elif protocol == 'sftp':
            foundFiles = self._localConnection['sftp'].find(fullSearchPaths,
                                                            restrictPattern)
        else:
            raise NotImplementedError
        return foundFiles

    #FIXME - Incorporate the workingDir argument
    def run_program(self, command, workingDir=None, env=None):
        '''
        Run an external program.

        Inputs:

            command - A string with the full command to run.

            workingDir - The directory where the program should be
                run.

            env - A list of two-element tuples containing the name and value
                of aditional environment variables to be set before running 
                the command. This is useful for setting the SMS_PROG variable 
                before pinging the sms server, for example.

        Returns:

            A tuple with the commands' stdout, stderr and return code.
        '''
        ssh = self._localConnection.get('ssh')
        if env is not None:
            for tup in env:
                result = ssh.run_command('export %s=%s' % (tup[0], tup[1]))
        result = ssh.run_command(command)
        stdout = ''.join(result)
        return stdout, '', 0
