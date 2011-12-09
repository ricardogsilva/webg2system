#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

# TODO  - add a logger (check the utilities file for an example)
#       - add documentation
#       - move this code to the g2packages.py file
#       - use the new get_file_details(fileName) function from the utilities 
#	  module and get rid of the xmlSettings variable
#       - refactor this file and the G2Packages file. Each G2Package subclass
#	  should just implement its own _create_files method and move this 
#	  logic there.

# standard imports
import datetime as dt
import logging

# this package's specific imports
import g2files
from g2files import *
from decorators import log_calls

@log_calls
def file_creator(xmlSettings, area, timeslot, package, fileRole, isOptional):
    """
    Returns a list of G2File (or any of its subclasses) instances
    """

    fileClassString = xmlSettings.getAttribute("class")
    fileFrequency = xmlSettings.getElementsByTagName("frequency")[0].firstChild.nodeValue

    if fileClassString == '' and package.name == 'SAT_DATA_STAT_g2' \
                             and fileRole == 'input' \
                             and fileFrequency == 'dynamic':
        returnList = [G2File(xmlSettings, area, timeslot + dt.timedelta(days=i), package, fileRole, isOptional) 
                      for i in range(-30, 0)]
    elif fileClassString == 'G2GRIBFile':
        if fileRole == 'input':
            returnList = [G2GRIBFile(xmlSettings, area, timeslot, package, fileRole, isOptional)]
        elif fileRole == 'output':
            returnList = [G2GRIBFile(xmlSettings, area, timeslot + dt.timedelta(hours=i), package, fileRole, isOptional) 
                          for i in range(12, 37)]
    elif fileClassString == 'G2LSASAFMessyFile':
        returnList = [G2LSASAFMessyFile(xmlSettings, area, timeslot, package, fileRole, isOptional)]
    elif fileClassString == 'G2LSASAFFile':
        returnList = [G2LSASAFFile(xmlSettings, area, timeslot, package, fileRole, isOptional)]
    elif fileClassString == 'G2QuasiStaticFile':
        returnList = [G2QuasiStaticFile(xmlSettings, area, timeslot, package, fileRole, isOptional)]
    elif fileClassString == 'G2ASCATFile':
        #returnList = [G2File(xmlSettings, area, timeslot, package, fileRole, isOptional),
        #              G2File(xmlSettings, area, (timeslot + \
        #                      dt.timedelta(days=1)) , package, fileRole, isOptional)]
        returnList = []
        for i in range(23 + 1):
            returnList.append(G2File(xmlSettings, area, (timeslot + \
                    dt.timedelta(hours=i)) , package, fileRole, isOptional))
    elif fileClassString == 'G2QuickViewFile':
        returnList = [G2QuickViewFile(xmlSettings, area, timeslot, package, fileRole, isOptional)]
    else:
        returnList = [G2File(xmlSettings, area, timeslot, package, fileRole, isOptional)]
    return returnList
