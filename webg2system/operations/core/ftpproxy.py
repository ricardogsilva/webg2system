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
socket.setdefaulttimeout(3) # timeout for ftp connections, in seconds
import os
import re
import logging

import factories

class FTPProxy(object):
    '''
    Connect to another server through FTP and perform various actions.
    '''

    def __init__(self, user, ip, password, host=None):
        '''
        Inputs:

            user - A string with the name of the user.

            ip - A string with the ip or the name of the host.

            password - A string with the user's password.

            host - A G2Host object specifying the host that started this 
                connection. A value of None (the default) will not bind
                this connection to any host.
        '''

        self.logger = logging.getLogger(self.__class__.__name__)
        self.connection = FTP()
        self.user = user
        self.ip = ip
        self.password = password
        if host is None:
            self.host = factories.create_host()
        else:
            self.host = host

    def _connect(self):
        '''
        Establish a connection with the remote host.
        '''

        result = False
        try:
            self.connection.nlst()
            result = True
            self.logger.debug('The connection already exists')
        except AttributeError:
            #no, the connection hasn't been established yet
            self.logger.info('Connecting to %s...' % self.ip)
            try:
                self.connection.connect(self.ip)
                self.connection.login(self.user, self.password)
                result = True
                self.logger.info('Connection successful')
            except socket.error, errorMsg:
                if errorMsg[0] == 113:
                    #raise IOError('%s unreachable. Maybe the host is down?' \
                    #              % self.ip)
                    self.logger.warning('%s unreachable. Maybe the host is ' +\
                                        'down?' % self.ip)
                else:
                    #raise IOError('socket error: %s' % (str(errorMsg)))
                    self.logger.warning('socket error: %s' % (str(errorMsg)))
            except error_temp, errMsg:
                patt = re.compile(r'(^\d+)')
                errNum = patt.search(str(errMsg)).group(1)
                if errNum == '421':
                    # try to connect again in secs seconds
                    secs = 15
                    self.logger.info('Too many connections at the moment. ' \
                          'Waiting %i seconds' % secs)
                    time.sleep(secs)
                    result = self._connect()
        except error_temp, errMsg:
            if errMsg[0] == 421:
                self.logger.warning('The connection has timed out. Closing '\
                                    'this connection and re-connecting...')
                self.connection.quit()
                self.connection = None
                self.connection = FTP()
        return result

    def find(self, paths):
        '''
        Return a list of paths that match the 'paths' argument.
        
        Inputs:

            paths - A list of strings specifying the full path to the paths
                to search. Each string is interpreted as a regular expression.
        '''

        fileList = []
        if self._connect():
            for pathRegExp in paths:
                searchDir, searchPattern = os.path.split(pathRegExp)
                self.logger.debug('searchDir: %s' % searchDir)
                self.logger.debug('searchPattern: %s' % searchPattern)
                pattRE = re.compile(searchPattern)
                try:
                    self.connection.cwd(searchDir)
                    currentDir = self.connection.pwd()
                    rawfileList = self.connection.nlst()
                    for rawPath in rawfileList:
                        if pattRE.search(rawPath) is not None:
                            fileList.append(os.path.join(currentDir, rawPath))
                except error_perm, msg:
                    self.logger.warning(msg)
                    #raise
        return fileList

    def send(self, paths, destination):
        '''
        Get the paths from the remote server to the local destination.

        Inputs:
            
            paths - A list of paths in the remote host that are to be copied. 
            
            destination - The target directory on the local machine where to 
                put the copied files. It will be created in case it doesn't 
                exist.

        Returns:
            
            A list with the paths to the newly-copied files.
        '''

        copiedPaths = []
        if self._connect():
            pathsToCopy = self.find(paths)
            if len(pathsToCopy) > 0:
                oldDir = self.host.get_cwd()
                if not self.host.is_dir(destination):
                    self.host.make_dir(destination)
                self.host.change_dir(destination)
                for path in pathsToCopy:
                    dirPath, fname = os.path.split(path)
                    self.connection.retrbinary('RETR %s' % path, 
                                               open(fname, 'wb').write)
                    copiedPaths.append(os.path.join(destination, fname))
                os.chdir(oldDir)
                self.host.change_dir(oldDir)
        return copiedPaths

    # FIXME
    #   - this method hasn't been tested yet and it certainly is wrong
    #     because:
    #           - it is not using the boolean return value of the _connect()
    #             method into account;
    #           - other reasons
    def fetch(self, paths, destination):
        '''
        Put the local paths to the remote server.

        Inputs:

            paths - A list of paths in the local file system. This list is
                assumed to contain full paths to files and not search 
                patterns.

            destination - The directory on the remote server where the
                paths will be put. It will be created in case it doesn't 
                exist.

        Returns:

            The total return code of the transfer(s).
        '''

        self._connect()
        oldDir = os.getcwd()
        results = []
        for path in paths:
            dirPath, fname = os.path.split(path)
            if os.path.isdir(dirPath):
                os.chdir(dirPath)
                self._create_remote_dirs(destination)
                self.connection.cwd(path)
                result = self.connection.storbinary("STOR %s" % fname,
                                                    open(fname, "rb"))
                results.append(float(result.split()[0]))
        os.chdir(oldDir)
        endResult = 1
        if not False in [i == 226.0 for i in results]:
            # 226 is the FTP return code that indicates a successful transfer
            endResult = 0
        self.logger.debug("send method exiting.")
        return endResult

    # FIXME
    #   - this method hasn't been tested yet.
    def _create_remote_dirs(self, path):
        """
        Create the directory structure specified by 'path' on the remote host.
        """

        oldDir = self.connection.pwd()
        self.connection.cwd("/")
        for part in path.split("/"):
            try:
                self.connection.cwd(part)
            except ftplib.error_perm:
                self.connection.mkd(part)
                self.connection.cwd(part)
        self.connection.cwd(oldDir)
