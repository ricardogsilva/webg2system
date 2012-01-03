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
from subprocess import Popen, PIPE
from xml.etree.ElementTree import ElementTree as et
import ftplib
import socket
from pexpect import spawn
#import glob
#import fnmatch

# specific imports
import utilities
#from sshproxy import SSHProxy
#from ftpproxy import FTPProxy

# TODO
# - Review all the methods that have a FIXME tag
# - Implement the remaining methods on G2RemoteHost class

_hosts = dict()

def create_host(hostSettings):
    '''
    Return a new G2host instance.

    This function, coupled with the _hosts module variable, implements a 
    (soft)singleton pattern. This is to prevent the creation of multiple
    G2Host objects pointing to the same host and eventually creating multiple
    SSH or FTP connections that may overload the network. The objective of
    this mechanism is to have only one connection to from a host to another
    one.

    Inputs:

        hostSettings - A systemsettings.models.Host object
    '''

    global _hosts
    name = hostSettings.name
    ip = hostSettings.ip
    localName = socket.gethostname()
    try:
        localIP = socket.gethostbyname(name)
    except socket.gaierror:
        factoriesLogger.warning('Couldn\'t determine %s\'s IP address' \
                                % name)
        localIP = None
    if name not in _hosts.keys():
        # about to create a new host object
        if name == localName or ip == localIP:
            theClass = G2LocalHost
        else:
            theClass = G2RemoteHost
        hostObj = theClass(hostSettings)
        _hosts[name] = hostObj
    return _hosts.get(name)


class G2Host(object):

    name=''
    connections = dict()

    def __init__(self, settings):
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

        #self.logger = logging.getLogger(self.__class__.__name__)
        self.logger = logging.getLogger('.'.join((__name__, self.__class__.__name__)))
        self.name = settings.name
        self.connections[self.name] = dict()
        self.basePath = settings.basePath
        self.host = settings.ip
        self.user = settings.username
        self.password = settings.password
        self.isArchive = settings.isArchive
        self.hasSMS = settings.hasSMS
        self.hasMapserver = settings.hasMapserver

    def find(self, pathList):
        raise NotImplementedError

    def fetch(self, relativePaths, relativeDestinationDir, sourceHost):
        raise NotImplementedError

    def send(self, relativePaths, relativeDestinationDir, destinationHost):
        raise NotImplementedError

    def compress(self, relativePaths):
        raise NotImplementedError

    def decompress(self, relativePaths):
        raise NotImplementedError

    def create_file():
        raise NotImplementedError

    def delete_file():
        raise NotImplementedError

    def get_cwd():
        raise NotImplementedError

    def change_dir():
        raise NotImplementedError

    def make_dir():
        raise NotImplementedError

    def remove_dir():
        raise NotImplementedError

    def run_program():
        raise NotImplementedError

    def __repr__(self):
        return self.name


class G2LocalHost(G2Host):
    """
    This class has the implementation of the local file IO operations.
    """

    def find(self, pathList):
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

        #self.logger.info('locals: %s' % locals())
        foundFiles = []
        for path in pathList:
            if path.startswith(os.path.sep):
                fullSearchPath = path
            else:
                fullSearchPath = os.path.join(self.basePath, path)
            searchDir, searchPattern = os.path.split(fullSearchPath)
            patt = re.compile(searchPattern)
            dirExists = os.path.isdir(searchDir)
            if dirExists:
                for item in os.listdir(searchDir):
                    if patt.search(item) is not None:
                        foundFiles.append(os.path.join(searchDir, item))
            else:
                self.logger.warning('No such directory: %s' % searchDir)
        return foundFiles

    def fetch(self, paths, directory, sourceHost=None, absolute=False):
        '''
        Fetch the files from sourceHost.

        This method is to fetch EVERY file that matches the 'paths' input. It
        is not to make any filtering of possible duplicate files. It is up to
        the client who calls this method to sort out the correct 'paths' 
        argument so as to avoid copying duplicate files.

        Inputs:

            paths - A list of strings specifying the paths to the files to
                fetch. Each string is interpreted as a regular expression.

            directory - The directory on the local host where the files
                will be copied to. It will be created in case it doesn't
                exist.

            sourceHost - A string with the name of the host where the
                desired files are. A value of None (the default) assumes
                that the files are on the local host.

            absolute - A boolean indicating if the list of paths to search
                contains relative paths or absolute paths.

        Returns:

            A list of strings with the full paths of the files that were
            fetched.
        '''

        if sourceHost is None or sourceHost == self.name:
            result = self._fetch_from_local(paths, directory, absolute)
        else:
            result = self._fetch_from_remote(paths, directory, sourceHost, 
                                             absolute)
        return result

    def _fetch_from_local(self, paths, directory, absolute):
        '''
        Fetch the existing files to the destination path.

        Inputs:
            
            paths - A list of strings specifying the paths to the files to
                fetch. Each string is interpreted as a regular expression.

            directory - The directory on the local host where the files
                will be copied to. It will be created in case it doesn't
                exist. The directory's location is relative to the local
                host's 'basePath' attribute.

            absolute - A boolean indicating if the list of paths to search
                contains relative paths or absolute paths.

        Returns:
            
            A list with the full paths of all the files that have been copied.
        '''

        fullPaths = self.find(paths, absolute)
        fullDestPaths = []
        for path in fullPaths:
            fullDestDirPath = os.path.join(self.basePath, directory)
            if not self.is_dir(fullDestDirPath):
                self.make_dir(fullDestDirPath)
            shutil.copy(path, fullDestDirPath)
            newPath = os.path.join(fullDestDirPath, os.path.basename(path))
            fullDestPaths.append(newPath)
        return fullDestPaths

    def _fetch_from_remote(self, paths, directory, sourceHost, absolute):
        '''
        Fetch the existing files to the destination path.

        Inputs:
            
            paths - A list of strings specifying the paths to the files to
                fetch. Each string is interpreted as a regular expression.

            directory - The directory on the local host where the files
                will be copied to. It will be created in case it doesn't
                exist. The directory's location is relative to the local
                host's 'basePath' attribute.

            sourceHost - A string with the name of the host where the
                desired files are to be fetched from.

            absolute - A boolean indicating if the list of paths to search
                contains relative paths or absolute paths.

        Returns:
            
            A list with the full paths of all the files that have been copied.
        '''


        source = factories.create_host(sourceHost)
        fullPaths = source.find(paths, absolute)
        connection = self._get_connection(source.name, 'ftp')
        fullDestDirPath = os.path.join(self.basePath, directory)
        newPaths = connection.send(fullPaths, fullDestDirPath)
        return newPaths

    #FIXME - To be reviewed
    def _get_connection(self, host, protocol):
        '''
        Return the relevant connection object.

        Inputs:

            host - A string with the name of the host to connect to.

            protocol - A string with the name of the connection protocol.
                Currently planned protocols are 'ftp' and 'ssh'.
        '''

        hostConnections = self.connections[self.name].get(host)
        if hostConnections is not None:
            connection = hostConnections.get(protocol)
            if connection is not None:
                self.logger.info('Reusing previously opened connection to %s.' % host)
                result = connection
            else:
                self.logger.info('Creating connection to %s with protocol %s' % 
                      (host, protocol))
                result = self._connect(host, protocol)
        else:
            self.logger.info('Creating the first connection to %s with protocol %s' % 
                  (host, protocol))
            result = self._connect(host, protocol)
        return result

    def _connect(self, host, protocol):
        '''
        Establish a connection between the local host and the 'host' argument
        using 'protocol'.
        '''

        if self.connections[self.name].get(host) is None:
            self.connections[self.name][host] = dict()
        if self.connections[self.name].get(host).get(protocol) is None:
            hostDetails = utilities.get_host_details(host)
            if protocol == 'ssh':
                self.connections[self.name][host]['ssh'] = SSHProxy(
                        hostDetails['username'], hostDetails['ip'])
            elif protocol == 'ftp':
                self.connections[self.name][host]['ftp'] = FTPProxy(
                        hostDetails['username'], hostDetails['ip'], 
                        hostDetails['password'], host=self)
        return self.connections[self.name][host][protocol]

    #FIXME - To be reviewed
    def send(self, relativePaths, destPath, destHost, compress):
        '''
        Copy files to another directory, located on a G2Host machine.

        Inputs:
            
            fullPaths - A list with the relative paths of the files to send.

            destPath - A string with the relative path on the destination
                host where the files are to be sent to.

            destHost - A G2Host instance, specifying the machine that will
                receive the files. A value of None (which is also the default)
                is interpreted as meaning a local host.

            compress - A boolean indicating if the files should be compressed.

        Returns:
        '''

        if destHost.isLocal:
            result = self._send_to_local(relativePaths, destPath, destHost)
        else:
            result = self._send_to_remote(relativePaths, destPath, destHost)
        return result

    #FIXME - To be reviewed
    def _send_to_local(self, relativePaths, destPath, destHost, compress):
        '''
        Perform a local copy operation with an optional compression step.

        Returns:

            A list of full paths to the newly sent files' location.
        '''

        if compress:
            fullPaths = self.compress(relativePaths)
        else:
            fullPaths = [os.path.join(self.basePath, p) \
                         for p in relativePaths]
        fullDestPath = os.path.join(destHost.basePath, destPath)
        result = []
        for path in fullPaths:
            shutil.copy(path, fullDestPath)
            result.append(os.path.join(fullDestPath, os.path.basename(path)))
        return result

    #FIXME - To be reviewed
    def _send_to_remote(self, relativePaths, destPath, destHost, compress):
        raise NotImplementedError
        
    def compress(self, relativePaths):
        '''
        Compress the files and leave them in the same directory.

        Returns:
            
            A list with the full paths to the newly compressed files.
        '''

        raise NotImplementedError

    def decompress(self, relativePaths):
        '''
        Decompress the files and leave them in the same directory.

        Inputs:
            
            relativePaths - A list with the relative paths of the files
                that are to be decompressed.

        Returns:

            A list with the new filenames, after decompression
        '''

        fullPaths = [os.path.join(self.basePath, p) for p in relativePaths]
        stdout, stderr, retCode = self.run_program('bunzip2 %s' % \
                                                   ' '.join(fullPaths))
        if retCode == 0:
            decompressedPaths = [p.replace('.bz2', '') for p in fullPaths]
        else:
            #there has been an error decompressing the files
            raise Exception
        return decompressedPaths

    #FIXME - To be reviewed
    def run_program(self, command, workingDir=None):
        '''
        Run an external program.

        Inputs:

            command - A string with the full command to run.

            workingDir - The directory where the program should be
                run.

        Returns:

            A tuple with the commands' stdout, stderr and return code.
        '''

        commandList = command.split(' ')
        newProcess = Popen(commandList, cwd=workingDir, stdin=PIPE,
                           stdout=PIPE, stderr=PIPE)
        stdout, stderr = newProcess.communicate()
        retCode = newProcess.returncode
        return stdout, stderr, retCode

    #FIXME - To be reviewed
    def delete_file(self, relativeFilePath):
        '''Delete the file from the filesystem.'''

        fullPath = os.path.join(self.basePath, relativeFilePath)
        try:
            os.remove(fullPath)
        except OSError:
            # file doesn't exist
            pass

    def get_cwd(self):
        return os.getcwd()

    def change_dir(self, destination):
        os.chdir(destination)

    def make_dir(self, relativeDirPath):
        '''Recursively make every directory needed to ensure relativeDirPath.'''

        fullPath = os.path.join(self.basePath, relativeDirPath)
        os.makedirs(fullPath)

    #FIXME - To be reviewed
    def remove_dir(self, relativeDirPath):
        '''
        Remove directory along with any content it may have and also remove
        any parent directories that may become empty.
        '''

        fullPath = os.path.join(self.basePath, relativeDirPath)
        shutil.rmtree(fullPath)
        # remove the deleted dir from the path
        newPath = fullPath.rpartition(os.path.sep)[0]
        os.removedirs(newPath)

    #FIXME - To be reviewed
    def is_dir(self, relativeDirPath):
        fullPath = os.path.join(self.basePath, relativeDirPath)
        return os.path.isdir(fullPath)

    #FIXME - To be reviewed
    def create_file(self, relativePath, fileContents):
        '''
        Create a new text file.

        Inputs:

            relativePath - A string with the relative path to the new file.

            fileContents - A list of strings with the lines of text that the
                new file should contain.

        Returns:

            A string with the full path to the newly written file.
        '''

        fullPath = os.path.join(self.basePath, relativePath)
        # use a try block
        fh = open(fullPath, 'w')
        for line in fileContents:
            fh.write(line)
        fh.close()
        return fullPath


class G2RemoteHost(G2Host):
    '''
    This class implements file IO and other operations in a remote host.
    '''

    _connections = dict()

    def __init__(self, name, basePath, ip, username, password):
        '''
        Inputs:

            name - A string with the name of the host

            basePath - A string with the basepath that is to be used for
                all operations on the host

            ip - A string with the ip of the host

            username - A string with the user name of the user authorized to
                perform operations on the host

            password - A string with the password
        '''

        super(G2RemoteHost, self).__init__(name, basePath, ip, username, password)
        self.logger = logging.getLogger("G2ProcessingLine.G2RemoteHostHost")
        if self._connections.get(self.name) is None:
            self._connections[self.name] = {
                    'ftp' : FTPProxy(self.user, self.host, self.password),
                    'ssh' : SSHProxy(self.user, self.host, self.password)
                    }
        self.ftp = self._connections[self.name]['ftp']
        self.ssh = self._connections[self.name]['ssh']

    # To be removed
    def setup(self, otherOptions):
        '''
        This method is only temporary and serves only to workaround current
        testing limitations.
        '''

        self.connection.otherOptions = otherOptions

    def find(self, pathList, absolute=False, protocol='ftp'):
        '''
        Find the paths.

        Inputs:

            pathList - A list with paths for the files to search. The paths 
            are treated as regular expressions.

            absolute - A boolean indicating if the list of paths to search
                contains relative paths or absolute paths.

            protocol - The name of the protocol used to find the files.
                Available values are 'ftp' (the default) and 'ssh'.
                NOTE: currently only the 'ftp' protocol is implemented.
        Returns:

            A list with the full paths to the found files.
        '''

        fullSearchPaths = []
        for path in pathList:
            if absolute:
                fullSearchPaths.append(path)
            else:
                fullSearchPaths.append(os.path.join(self.basePath, path))
        foundFiles = eval('self.%s.find(fullSearchPaths)' % protocol)
        return foundFiles

    def run_program(self, command, workingDir=None):
        raise NotImplementedError

# older code

#class G2SCPHost(G2Host):
#    """
#    ...
#    """
#
#    def __init__(self, isLocal, name, paramDict, searchPaths):
#        G2Host.__init__(self, isLocal, name, paramDict, searchPaths)
#        self.logger = logging.getLogger("G2ProcessingLine.G2SCPHost")
#        self.connection = paramDict["connection"]
#        self.ip = paramDict["ip"]
#        self.username = paramDict["username"]
#        self.logger.debug("self.connection: %s" % self.connection)
#        self.logger.debug("self.ip: %s" % self.ip)
#        self.logger.debug("self.username: %s" % self.username)
#
#    def find(self, g2file):
#        self.logger.debug("find method called.")
#        remoteFileList = []
#        remoteCommands = ""
#        for searchPath in self.searchPaths:
#            self.logger.debug("searching in: %s" % searchPath)
#            for pattern in self._split_pattern(g2file):
#                self.logger.debug("searching for: %s" % pattern)
#                remoteCommands += "ls %s/%s;" % (searchPath, pattern)
#        sshCommand = ["ssh",
#                      "%s@%s" % (self.username, self.ip),
#                      "%s" % remoteCommands]
#        self.logger.debug("sshCommand: %s" % sshCommand)
#        externalProcess = subprocess.Popen(sshCommand, stdout=subprocess.PIPE, 
#                                           stdin=subprocess.PIPE, stderr=subprocess.PIPE)
#        stdOutput, stdError = externalProcess.communicate()
#        remoteFileList = stdOutput.split("\n")
#        errorsList = stdError.split("\n")
#        self.logger.debug("remoteFileList: %s" % remoteFileList)
#        self.logger.debug("errorsList: %s" % errorsList)
#        if len(remoteFileList) != 0:
#            remoteFileList.pop() # the last element in the list is just a blank string, so we remove it
#        self.logger.debug("find method exiting.")
#        return remoteFileList
#
#    def fetch(self, fileList, g2file, numTries=3):
#        """
#        Copy remote files to the local working directory using SCP.
#
#        Inputs: fileList - a list of paths to copy
#                numTries - an integer specifying how many attempts
#                           will be made to copy the remote files.
#
#        Returns: a list of strings with the new path to the files,
#                 on the workingDir.
#        """
#
#        self.logger.debug("fetch method called.")
#        scpString = "%s@%s:" % (self.username, self.ip)
#        if len(fileList) > 1:
#            scpString += "\\{"
#        for path in fileList:
#            scpString += "%s," % path
#        scpString = scpString[:-1] # removing the last comma sign
#        if len(fileList) > 1:
#            scpString += "\\}"
#        scpCommand = "scp %s %s" % (scpString, g2file.package.workingDir)
#        self.logger.debug("scpCommand: %s" % scpCommand)
#        self.logger.debug("copying the remote files to the local working directory...")
#        result = self._execute_scp_operation(scpCommand, numTries)
#        self.logger.debug("fetch method exiting.")
#        return ["%s/%s" % (g2file.package.workingDir, os.path.basename(path)) for path in fileList]
#
#    def send(self, fileList, path=None, numTries=3):
#        """
#        Returns: 0 in case of success and > 0 in case something went wrong.
#        """
#
#        self.logger.debug("send method called.")
#        if path is None:
#            path = self.searchPaths[0]
#        scpString = ""
#        if len(fileList) > 1:
#            scpString += "\\{"
#        for path in fileList:
#            scpString += "%s," % path
#        scpString = scpString[:-1] # removing the last comma sign
#        if len(fileList) > 1:
#            scpString += "\\}"
#        scpCommand = "scp %s %s@%s:%s" % (scpString, self.username, self.ip,
#                                          path)
#        self.logger.debug("scpCommand: %s" % scpCommand)
#        self.logger.debug("copying the remote files to the local working directory...")
#        result = self._execute_scp_operation(scpCommand, numTries)
#        self.logger.debug("send method exiting.")
#        return result
#
#    def _execute_scp_operation(self, scpCommand, numTries):
#        self.logger.debug("_execute_scp_operation method called.")
#        exitCode = -1
#        currentTry = 1
#        while exitCode != 0 and currentTry <= numTries:
#            self.logger.debug("try number: %i/%i" % (currentTry, numTries))
#            scpProcess = subprocess.Popen(scpCommand, shell=True, 
#                                          stdin=subprocess.PIPE, 
#                                          stdout=subprocess.PIPE,
#                                          stderr=subprocess.PIPE)
#            resultStdOut, resultStdErr = scpProcess.communicate()
#            exitCode = int(scpProcess.returncode)
#            self.logger.debug("returnCode: %i" % exitCode)
#            currentTry += 1
#        if exitCode > 0: #there was an error with the external scp process
#            raise Exception
#        else:
#            self.logger.debug("files processed successfully.")
#        self.logger.debug("_execute_scp_operation method exiting.")
#        return exitCode



# code from trunk

#class G2FTPHost(G2Host):
#    """
#    ...
#    """
#
#    ftp = ftplib.FTP()
#
#    def __init__(self, name, paramDict, searchPaths):
#        G2Host.__init__(self, name, paramDict, searchPaths)
#        self.logger = logging.getLogger("G2ProcessingLine.G2FTPHost")
#        self.connection = paramDict["connection"]
#        self.ip = paramDict["ip"]
#        self.username = paramDict["username"]
#        self.password = paramDict["password"]
#        self._connect()
#
#    def _connect(self):
#        #are we already connected?
#        try:
#            self.ftp.nlst()
#            self.logger.debug('The connection already exists')
#        except AttributeError:
#            #no, the connection hasn't been established yet
#            self.logger.debug('No connection exists yet')
#            try:
#                self.ftp.connect(self.ip)
#                self.ftp.login(self.username, self.password)
#                self.logger.info('Connection successful')
#            except socket.error, errorTup:
#                if errorTup[0] == 113:
#                    raise IOError("%s is unreachable. Maybe the host is down?" % self.ip)
#                else:
#                    self.logger.error('socket error: %s\t%s' % (errorTup[0], errorTup[1]))
#            except ftplib.error_temp, errMsg:
#                patt = re.compile(r'(^\d+)')
#                errNum = patt.search(str(errMsg)).group(1)
#                if errNum == '421':
#                    # try to connect again in secs seconds
#                    secs = 15
#                    self.logger.info('Too many connections at the moment. Waiting %i seconds' % secs)
#                    time.sleep(secs)
#                    self._connect()
#
#    def find(self, g2file):
#        self.logger.debug("find method called.")
#        self.logger.debug("searchPattern: %s" % g2file.searchPattern)
#        for searchPath in self.searchPaths:
#            self.logger.debug("searchPath: %s" % searchPath)
#            try:
#                self.ftp.cwd(searchPath)
#                fileList = [os.path.join(searchPath, fn)\
#                            for fn in self.ftp.nlst(g2file.searchPattern)]
#                self.logger.debug("fileList: %s" % fileList)
#            except ftplib.error_perm, msg:
#                self.logger.debug(msg)
#                raise IOError(msg)
#        self.logger.debug("find method exiting.")
#        return fileList
#
#    def fetch(self, fileList, g2file, numTries=3):
#        self.logger.debug("fetch method called.")
#        oldDir = os.getcwd()
#        self.logger.debug("Currently on %s" % os.getcwd())
#        os.chdir(g2file.package.workingDir)
#        self.logger.debug("Currently on %s" % os.getcwd())
#        resultFileList = []
#        for filePath in fileList:
#            self.logger.debug("Retrieving %s from %s" % (filePath, self.ip))
#            dirPath, fname = os.path.split(filePath)
#            self.ftp.cwd(dirPath)
#            self.ftp.retrbinary("RETR %s" % fname,
#                                open(fname, "wb").write)
#            resultFileList.append(os.path.join(g2file.package.workingDir, fname))
#        os.chdir(oldDir)
#        self.logger.debug("Currently on %s" % os.getcwd())
#        self.logger.debug("fetch method exiting.")
#        return resultFileList
#            
#    def send(self, fileList, path=None, numTries=3):
#        """
#        Returns: 0 in case of success and 1 in case something went wrong.
#        """
#
#        self.logger.debug("send method called.")
#        if path is None:
#            path = self.searchPaths[0]
#        oldDir = os.getcwd()
#        resultList = []
#        for filePath in fileList:
#            dirPath, fname = os.path.split(filePath)
#            self.logger.debug("dirPath: %s" % dirPath)
#            self.logger.debug("fname: %s" % fname)
#            self.logger.debug("remote path: %s" % path)
#            if os.path.isdir(dirPath):
#                os.chdir(dirPath)
#                self._create_remote_dirs(path)
#                self.ftp.cwd(path)
#                self.logger.debug("Sending %s to %s:%s" % (filePath, self.ip, path))
#                result = self.ftp.storbinary("STOR %s" % fname, open(fname, "rb"))
#                resultList.append(float(result.split()[0]))
#        os.chdir(oldDir)
#        endResult = 1
#        if not False in [i == 226.0 for i in resultList]:
#            # 226 is the FTP return code that indicates a successful transfer
#            endResult = 0
#        self.logger.debug("send method exiting.")
#        return endResult
#
#    def _create_remote_dirs(self, path):
#        """
#        Create the directory structure specified by 'path' on the host.
#        """
#
#        self.logger.debug("_create_remote_dirs method called.")
#        oldDir = self.ftp.pwd()
#        self.logger.debug("path: %s" % path)
#        self.ftp.cwd("/")
#        for part in path.split("/"):
#            try:
#                self.ftp.cwd(part)
#            except ftplib.error_perm:
#                self.ftp.mkd(part)
#                self.ftp.cwd(part)
#        self.ftp.cwd(oldDir)
#        self.logger.debug("_create_remote_dirs method exiting.")
