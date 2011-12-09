#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
This module holds the exception classes for the g2procesinglines python package.
"""

# TODO
# 
# Create loggers for these classes

import os
from glob import glob

class ProcessingLineError(Exception):
    """
    Base class for exceptions in this package.
    """

    pass


class CorruptedBZipFileError(ProcessingLineError):
    """
    Exception raised for errors decompressing bzip files.
    """

    def __init__(self, filePath, g2FileObj):
        self.filePath = filePath
        self.g2FileObj = g2FileObj
        self.fileSize = os.path.getsize(self.filePath)

    def __str__(self):
        return "file: %s\nsize: %i bytes" % (self.filePath, self.fileSize)

    def remove_corrupted_files(self):
        """
        Removes the file from its original directory (not the working dir).

        The usual workflow in the geoland processing lines is
        to copy bzipped inputs to a temporary working directory and then
        extract them in place, making them ready for further usage by the 
        Fortran algorithms. When one of these files is corrupted,
        it must be deleted, because it cannot be used in the processing
        line. However, since the file is just a copy, the original corrupted
        file is still left present at the original directory. This method
        will look for the original corrupted file and delete it, so that
        it can't be used in the future and cause aditional problems.
        """

        for path in self.get_original_filepaths():
                os.remove(path)

    def get_original_filepaths(self):
        """
        Find the original filepaths of this instance's corrupted file.
        """

        fileName = self.g2FileObj.searchPattern + ".bz2"
        filepaths = []
        for path in self.g2FileObj.searchPaths:
            filePath = os.path.join(path, fileName)
            print("fileName: %s" % fileName)
            print("path: %s" % path)
            print("filePath: %s" % filePath)
            print("----------")
            foundPaths = glob(filePath)
            for possibleFile in foundPaths:
                if os.path.isfile(possibleFile):
                    filepaths.append(possibleFile)
        return filepaths






