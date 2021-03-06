#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Currently, the FTPProxy class will only work with FTP operations between a 
local computer and a remote host. In the future, as the G2RemoteHost class
matures, this module will be abstracted away from local filesystem operations
(Probably by replacing ftplib calls with a Pexpect object that calls the 
external FTP client directly).
"""

from ftplib import FTP, error_temp, error_perm
import socket # needed to check ftplib's error
socket.setdefaulttimeout(10) # timeout for ftp connections, in seconds
import os
import re
import logging
import time

#import pysftp

class FTPProxy(object):
    '''
    Connect to another server through FTP and perform various actions.
    '''

    def __init__(self, localHost, remoteHost, logger=None):
        '''
        Inputs:

            host - A G2Host object specifying the host that started this 
                connection. 
        '''

        self.logger = logger
        self.connection = FTP()
        self.localHost = localHost
        self.remoteHost = remoteHost

    def _test_for_connection(self):
        '''Return True if the connection has already been established.'''

        return self.connection.getwelcome() is not None

    def _connect(self, timeoutRetries=3):
        '''
        Establish a new connection to the remote server.

        Inputs:

            timeoutRetries - An integer specifying the number of seconds
                to wait before reconnecting after a timeout error.

        Returns:

            A boolean with the result of the connection attempt.
        '''

        result = False
        if self._test_for_connection():
            #self.logger.debug('The connection already exists')
            try:
                #check for timeouts
                self.connection.pwd()
                result = True
            except error_temp, errMsg:
                patt = re.compile(r'(^\d+)')
                errNum = patt.search(str(errMsg)).group(1)
                if errNum == '421':
                    # timeout, try to connect again in timeoutRetries seconds
                    self.logger.info('The FTP connection timed out. Waiting '\
                                     '%i seconds' % timeoutRetries)
                    time.sleep(timeoutRetries)
                    del self.connection
                    self.connection = FTP()
                    result = self._connect()
        else:
            # create the connection
            self.logger.debug('Connecting to %s...' % self.remoteHost.host)
            try:
                self.connection.connect(self.remoteHost.host)
                self.connection.login(self.remoteHost.user, 
                                      self.remoteHost.password)
                result = True
                self.logger.debug('Connection successful')
            except socket.error, errorMsg:
                if errorMsg[0] == 113:
                    self.logger.error('%s unreachable. Maybe the host is ' +\
                                        'down?' % self.remoteHost.host)
                else:
                    self.logger.warning('socket error: %s' % (str(errorMsg)))
            except error_perm, errMsg:
                patt = re.compile(r'(^\d+)')
                errNum = patt.search(str(errMsg)).group(1)
                if errNum == '530':
                    self.logger.error(errMsg)
                    self.connection.quit()
                    self.connection = None
                    self.connection = FTP()
        return result

    def find(self, pathList, restrictPattern=None):
        '''
        Return a list of paths that match the 'pathList' argument.
        
        Inputs:

            pathList - A list of strings specifying the full path to the paths
                to search. Each string is interpreted as a regular expression.
        '''

        fileList = []
        if self._connect():
            for path in pathList:
                searchDir, searchPattern = os.path.split(path)
                self.logger.debug('searchDir: %s' % searchDir)
                self.logger.debug('searchPattern: %s' % searchPattern)
                pattRE = re.compile(searchPattern)
                try:
                    self.connection.cwd(searchDir)
                    currentDir = self.connection.pwd()
                    rawfileList = self.connection.nlst()
                    for rawPath in rawfileList:
                        if pattRE.search(rawPath) is not None:
                            if restrictPattern is not None:
                                if re.search(restrictPattern, rawPath) is not None:
                                    fileList.append(os.path.join(currentDir, 
                                                    rawPath))
                            else:
                                fileList.append(os.path.join(currentDir, 
                                                rawPath))
                except error_perm, msg:
                    self.logger.warning(msg)
                    #raise
        return fileList

    # FIXME
    # - test this method out
    def fetch(self, paths, destination):
        '''
        Fetch the input paths from remoteHost.
        
        The paths are copied to localHost's destination.

        Inputs:

            paths - A list with the full paths of the files to get.

            destination - The directory on this instance's localHost attribute
                where the files are to be copied to.

        Returns:

            A list with the paths to the newly fetched files.
        '''

        copiedPaths = []
        if self._connect():
            self.logger.info('Aqui')
            oldDir = self.localHost.get_cwd()
            self.logger.info('Ali')
            if not self.localHost.is_dir(destination):
                self.localHost.make_dir(destination)
            self.localHost.change_dir(destination)
            for path in paths:
                dirPath, fname = os.path.split(path)
                # this code only works with local hosts
                # as the open().write piece assumes local
                # filesystem
                fh = open(fname, 'wb')
                self.connection.retrbinary('RETR %s' % path, 
                                           fh.write)
                fh.close()
                #self.connection.retrbinary('RETR %s' % path, 
                #                           open(fname, 'wb').write)
                copiedPaths.append(os.path.join(destination, fname))
            self.localHost.change_dir(oldDir)
        return copiedPaths

    def send(self, paths, destination, temporary_extension='.tmp'):
        '''
        Put the local paths to the remote server.

        Inputs:

            paths - A list of paths in the local file system. This list is
                assumed to contain full paths to files and not search 
                patterns.

            destination - The directory on the remote server where the
                paths will be put. It will be created in case it doesn't 
                exist.

            temporary_extension - The extension to use while copying the
                files. After copying the files are renamed back to their
                original name.

        Returns:

            The total return code of the transfer(s).
        '''

        endResult = 1
        if self._connect():
            oldDir = os.getcwd()
            results = []
            for path in paths:
                dirPath, fname = os.path.split(path)
                temporary_name = ''.join((fname, temporary_extension))
                self.logger.info('path: %s' % path)
                self.logger.info('fname: %s' % fname)
                self.logger.info('temporary_name: %s' % temporary_name)
                if os.path.isdir(dirPath):
                    os.chdir(dirPath)
                    self._create_remote_dirs(destination)
                    self.connection.cwd(destination)
                    result = self.connection.storbinary("STOR %s" % \
                                                        temporary_name,
                                                        open(fname, "rb"))
                    result_code = result.split()[0]
                    if result_code == '226':
                        self.rename(temporary_name, fname)
                    results.append(result_code)
            os.chdir(oldDir)
            endResult = 1
            if not False in [i == '226' for i in results]:
                # 226 is the FTP return code that indicates a successful transfer
                endResult = 0
        return endResult

    def _create_remote_dirs(self, path):
        """
        Create the directory structure specified by 'path' on the remote host.
        """

        oldDir = self.connection.pwd()
        self.connection.cwd("/")
        for part in path.split("/"):
            try:
                self.connection.cwd(part)
            except error_perm:
                self.connection.mkd(part)
                self.connection.cwd(part)
        self.connection.cwd(oldDir)

    def rename(self, old_path, new_path):
        '''
        Rename a path.

        Inputs:

            old_path - A string with the path to rename

            new_path - A string with the new path
        '''

        self.connection.rename(old_path, new_path)


#
#class FTPPProxy(object):
#    '''
#    Connect to another server through SFTP and perform various actions.
#    '''
#
#    def __init__(self, local_host, remote_host, logger=None):
#        '''
#        Inputs:
#
#            host - A G2Host object specifying the host that started this 
#                connection. 
#        '''
#
#        self.logger = logger
#        self.local_host = local_host
#        self.remote_host = remote_host
#        try:
#            self.connection = pysftp.Connection(
#                                  host=self.remote_host.host, 
#                                  username=self.remote_host.username,
#                                  password=self.remote_host.password
#                              )
#        except pysftp.AuthenticationException:
#            self.connection = None
#
#    # FIXME - test this method out
#    def find(self, path_list, restrict_pattern=None):
#        '''
#        Return a list of paths that match the 'path_list' argument.
#        
#        Inputs:
#
#            path_list - A list of strings specifying the full path to the paths
#                to search. Each string is interpreted as a regular expression.
#        '''
#
#        file_list = []
#        for path in path_list:
#            search_dir, search_pattern = os.path.split(path)
#            #self.logger.debug('search_dir: %s' % search_dir)
#            #self.logger.debug('search_pattern: %s' % search_pattern)
#            patt_RE = re.compile(search_pattern)
#            try:
#                self.connection.chdir(search_dir)
#                current_dir = self.connection.getcwd()
#                raw_file_list = self.connection.listdir()
#                for raw_path in raw_file_list:
#                    if patt_RE.search(raw_path) is not None:
#                        if restrict_pattern is not None:
#                            if re.search(restrict_pattern, raw_path) is not None:
#                                file_list.append(os.path.join(current_dir, 
#                                                 raw_path))
#                        else:
#                            file_list.append(os.path.join(current_dir, 
#                                             raw_path))
#            except IOError as err:
#                self.logger.error(err)
#        return fileList
#
#    # FIXME - test this method out
#    def fetch(self, paths, destination):
#        '''
#        Fetch the input paths from remoteHost.
#        
#        The paths are copied to localHost's destination.
#
#        Inputs:
#
#            paths - A list with the full paths of the files to get.
#
#            destination - The directory on this instance's localHost attribute
#                where the files are to be copied to.
#
#        Returns:
#
#            A list with the paths to the newly fetched files.
#        '''
#
#        copied_paths = []
#        old_dir = self.local_host.get_cwd()
#        if not self.local_host.is_dir(destination):
#            self.local_host.make_dir(destination)
#        self.local_host.change_dir(destination)
#        for path in paths:
#            dirPath, fname = os.path.split(path)
#            self.connection.get(path)
#            copied_paths.append(os.path.join(destination, fname))
#        self.local_host.change_dir(old_dir)
#        return copied_paths
