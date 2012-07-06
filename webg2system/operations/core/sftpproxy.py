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

class SFTPPProxy(object):
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
        try:
            self.connection = pysftp.Connection(
                                  host=self.remote_host.host, 
                                  username=self.remote_host.username,
                                  password=self.remote_host.password
                              )
        except pysftp.AuthenticationException:
            self.connection = None

    # FIXME - test this method out
    def find(self, path_list, restrict_pattern=None):
        '''
        Return a list of paths that match the 'path_list' argument.
        
        Inputs:

            path_list - A list of strings specifying the full path to the paths
                to search. Each string is interpreted as a regular expression.
        '''

        file_list = []
        for path in path_list:
            search_dir, search_pattern = os.path.split(path)
            #self.logger.debug('search_dir: %s' % search_dir)
            #self.logger.debug('search_pattern: %s' % search_pattern)
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
        return fileList

    # FIXME - test this method out
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
        old_dir = self.local_host.get_cwd()
        if not self.local_host.is_dir(destination):
            self.local_host.make_dir(destination)
        self.local_host.change_dir(destination)
        for path in paths:
            dirPath, fname = os.path.split(path)
            self.connection.get(path)
            copied_paths.append(os.path.join(destination, fname))
        self.local_host.change_dir(old_dir)
        return copied_paths
