#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A module providing a class for executing file transfer operations through SFTP.
"""

from ftplib import FTP, error_temp, error_perm
import socket # needed to check ftplib's error
socket.setdefaulttimeout(10) # timeout for ftp connections, in seconds
import os
import re
import logging
import time

import pysftp

class SFTPProxy(object):
    '''
    Connect to another server through SFTP and perform various actions.
    '''

    def __init__(self, local_host, remote_host, logger=None):
        '''
        Inputs:

            host - A G2Host object specifying the host that started this 
                connection. 
        '''

        self.logger = logger
        self.local_host = local_host
        self.remote_host = remote_host
        self.connection = None

    def _connect(self):
        result = True
        if self.connection is None:
            try:
                self.logger.debug('Connecting to %s...' % \
                                  self.remote_host.host)
                self.connection = pysftp.Connection(
                                      host=self.remote_host.host, 
                                      username=self.remote_host.user,
                                      password=self.remote_host.password
                                  )
            except pysftp.paramiko.AuthenticationException:
                self.connection = None
                result = False
            except pysftp.paramiko.SSHException as e:
                self.connection = None
                result = False
                self.logger.error(e)
        return result

    def find(self, path_list, restrict_pattern=None):
        '''
        Return a list of paths that match the 'path_list' argument.
        
        Inputs:

            path_list - A list of strings specifying the full path to the paths
                to search. Each string is interpreted as a regular expression.
        '''

        if self._connect():
            file_list = []
            for path in path_list:
                search_dir, search_pattern = os.path.split(path)
                patt_RE = re.compile(search_pattern)
                try:
                    self.connection.chdir(search_dir)
                    current_dir = self.connection.getcwd()
                    raw_file_list = self.connection.listdir()
                    for raw_path in raw_file_list:
                        if patt_RE.search(raw_path) is not None:
                            if restrict_pattern is not None:
                                if re.search(restrict_pattern, raw_path) is not None:
                                    file_list.append(os.path.join(current_dir, 
                                                     raw_path))
                            else:
                                file_list.append(os.path.join(current_dir, 
                                                 raw_path))
                except IOError as err:
                    self.logger.error(err)
        else:
            self.logger.error('Not connected to the remote SFTP host')
            file_list = []
        return file_list

    #def remote_find(self, other_host, path_list, restrict_pattern=None):
    #    '''
    #    Perform a remote find on other_host.

    #    The connection to other_host is established by this instance\'s
    #    remote_host. This means that the local_host will not connect
    #    to other_host, it will use remote_host as a proxy between
    #    itself and other_host.
    #    '''

    #    if self._connect():
    #        ls_result = self.connection.execute('ls -al')
    #        self.logger.debug('ls_result: %s' % ls_result)

    def run_command(self, command, working_dir=None):
        result = None
        if self._connect():
            if working_dir is not None:
                old_dir = self.connection.execute('pwd')
                self.connection.execute('cd %s' % working_dir)
                result = self.connection.execute(command)
                self.connection.execute('cd %s' % old_dir)
            else:
                result = self.connection.execute(command)
        return result

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

        copied_paths = []
        if self._connect():
            old_dir = self.local_host.get_cwd()
            if not self.local_host.is_dir(destination):
                self.local_host.make_dir(destination)
            self.local_host.change_dir(destination)
            for path in paths:
                dirPath, fname = os.path.split(path)
                self.connection.get(path)
                copied_paths.append(os.path.join(destination, fname))
            self.local_host.change_dir(old_dir)
        else:
            self.logger.error('Not connected to the remote SFTP host')
        return copied_paths

    def send(self, paths, destination):
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

        result = 0
        if self._connect():
            for path in paths:
                directory, fname = os.path.split(path)
                if os.path.isdir(directory):
                    dirs = self._create_remote_dirs(destination)
                    if dirs:
                        ret_code = self.connection.put(
                                    path, 
                                    os.path.join(destination, fname)
                                )
                    else:
                        raise
        else:
            self.logger.error('Not connected to the remote SFTP host')
            result = 1
        return result

    def _create_remote_dirs(self, path):
        """
        Create the directory structure specified by 'path' on the remote host.
        """

        result = False
        if self._connect:
            out_list = self.connection.execute('mkdir -p %s' % path)
            if len(out_list) > 0:
                # Either the path already exists or it could not be created
                if 'exists' in out_list[0]:
                    self.logger.info(out_list[0])
                    result = True
                else:
                    # something went wrong. 
                    self.logger.error(out_list[0])
            else:
                result = True
        else:
            self.logger.error('Not connected to the remote SFTP host')
        return result

    def close_connection(self):
        if self.connection is not None:
            self.connection.close()

