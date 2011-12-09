#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

# TODO  
#       - add documentation
#       - move this code to the g2packages.py file
#       - use the new get_package_details(packageName) function from the
#         utilities module and get rid of the xmlSettings variable

import datetime as dt
import logging
from xml.dom import minidom

# this package's specific imports
import g2packages
import utilities as utils
from decorators import log_calls

@log_calls
def package_creator(packName, modeName, timeslotString, area,
                    suiteName, versionName=None):
    """
    ...
    """
    
    logger = logging.getLogger("G2ProcessingLine.package_creator")
    packagesXMLFile = utilities.get_new_settings()["settingsFiles"]["packageSettings"]
    packagesXMLDoc = minidom.parse(packagesXMLFile)
    xmlSettings = utilities.find_xml_element(packagesXMLDoc, 
                                         "package", "name", packName)
    if not xmlSettings:
        raise ValueError("Invalid package name")
    timeslotDT = dt.datetime.strptime(timeslotString, "%Y%m%d%H%M")
    selectedModeXml = utilities.find_xml_element(xmlSettings, "mode", "name", modeName)
    if not selectedModeXml:
        raise ValueError("Invalid mode name")
    selectedClass = selectedModeXml.getAttribute("class")
    logger.info("selected class: %s" % selectedClass)
    packageClass = eval("g2packages.%s" % selectedClass)
    package = packageClass(xmlSettings, timeslotDT, modeName, area, 
                           suiteName, version=versionName)
    logger.info("package successfully created!")
    return package

def new_package_creator(packName, packMode):
    '''
    Return a new G2Package instance.
    '''

    packDetails = utils.get_package_details(packName)
    newPackage = None
    if packDetails is not None:
        newPackage = eval('%s(%s, %s)' % packDetails['theClass'], packMode,
                          packDetails)
    return newPackage



