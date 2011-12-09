#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

import sys
import logging

# TODO
# THIS FILE IS TO BE DELETED!
#  This functionality is being incorporated as a new package

class G2DisseminationManager(object):
    """
    This class serves as a manager for fetching and copying G2System
    data from and to other remote sources.
    """

    def __init__(self, g2package):
        self.logger = logging.getLogger()

    def send_to(self, hostName, directory, fileRole="output", 
                fileNames=[]):
        """
        Send the files represented by filetype to the directory.

        Inputs:
            hostName - A string with the name of the host that will receive
                       the data.
            directory - The directory on the host that is to receive the
                        files.
        Returns:
        """

        for g2file in self.g2package.inputs + self.g2package.outputs:
            if g2file.role == fileRole and \
            (g2file.name in fileNames or len(fileNames) == 0):
                self.logger.debug("about to send G2File: %s to host %s"\
                % (g2file.name, hostName))
                result = g2file.send_to(hostName)

    def find(self, host, filetype, directory=None):
        """
        Find existing files on the host.

        Inputs:
            host - A G2Host instance representing the host that data
                   is to be sent to.
            filetype - A G2File instance representing the files that
                       are to be sent.
            directory - The directory on the host that is to receive the
                        files.
        Returns:
        """
        raise NotImplementedError
        fileList = host.find(filetype, directory)

    def fetch_from(self, host, filetype, directory=None):
        raise NotImplementedError


def main(argList):
    dm = G2DisseminationManager()

if __name__ == "__main__":
    main(sys.argv[1:])

