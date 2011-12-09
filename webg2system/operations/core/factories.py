#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

import datetime as dt
import logging
import socket
import getpass

from g2packages import *
from g2files import G2File
from g2sources import G2Source
from g2hosts import *
import utilities
from decorators import log_calls

factoriesLogger = logging.getLogger(__name__)
_hosts = dict()

#@log_calls
def create_source(name, area=None):
    '''
    Return a new G2Source instance.

    Inputs:

        name - The name of the source to create, as defined in the XML 
            settings.

        area - The name of the source's area to create. If None (the
            default) the first of the areas defined in the XML settings
            will be used.
    '''

    sourceObj = None
    try:
        sourceDetails = utilities.get_source_details(name)
        if area is None:
            area = sourceDetails.get('areas')[0]
        else:
            area = [a for a in sourceDetails.get('areas') if a == area][0]
        specNames = []
        for spDict in sourceDetails['specificNames']:
            startTS = dt.datetime.strptime(spDict['activeFrom'], '%Y%m%d%H%M')
            endTS = dt.datetime.strptime(spDict['activeUntil'], '%Y%m%d%H%M')
            specNames.append((spDict['specificName'], startTS, endTS))
        sourceObj = G2Source(name, area, specNames)
    except KeyError:
        factoriesLogger.error('Couldn\'t find %s in the source settings.' % name)
    return sourceObj

#@log_calls
def create_host(name=None):
    '''
    Return a new G2host instance.

    This function, coupled with the _hosts module variable, implements a 
    (soft)singleton pattern. This is to prevent the creation of multiple
    G2Host objects pointing to the same host and eventually creating multiple
    SSH or FTP connections that may overload the network. The objective of
    this mechanism is to have only one connection to from a host to another
    one.

    Inputs:

        name - A string with the name of the host to be created. This string
            is searched for in the names of the hosts defined in the settings.
            If name is None (the default) a new G2Host instance will be
            created based on the current machine's settings and a cross search
            in the xml settings.
    '''

    global _hosts
    localName = socket.gethostname()
    if name is None:
        name = localName
    if name not in _hosts.keys():
        factoriesLogger.debug('About to try to create a new %s host' % name)
        try:
            localIP = socket.gethostbyname(name)
        except socket.gaierror:
            factoriesLogger.warning('Couldn\'t determine %s\'s IP address' \
                                    % name)
            localIP = None
        if name == localName:
            theClass = G2LocalHost
            # try to get the other settings from the configuration file
            basePath = utilities.get_settings()['dataDir']
            username = getpass.getuser()
            hostObj = theClass(name, basePath, localIP,
                               username, password=None)
        else:
            hostObj = None
            hostDetails = utilities.get_host_details(name).copy()
            del hostDetails['archive']
            if hostDetails is not None:
                if name == localName:
                    theClass = G2LocalHost
                else:
                    theClass = G2RemoteHost
                hostObj = theClass(name, **hostDetails)
        _hosts[name] = hostObj
    return _hosts.get(name)

# FIXME
# - Is this factory even necessary?
#   It's just converting the timeslot to datetime and creating the host and 
#   source objects
#@log_calls
def create_package(packName, timeslot, source, host=None):
    '''
    Return a new G2Package instance.

    Inputs:

        packName - A string with the name of the package to create. It must
            be a name present in the settings.

        timeslot - A string in the form of 'yyymmddHHMM' representing the
            package's timeslot.

        source - A string with the name of the source of the package

        host - A string with the name of the G2host object to create
            for the package.
    '''

    timeslotDT = dt.datetime.strptime(timeslot, '%Y%m%d%H%M')
    hostDetails = utilities.get_host_details(host)
    sourceObj = create_source(source)
    if host is None:
        hostObj = create_host()
    else:
        hostObj = create_host(host)
    newPackage = None
    try:
        packDetails = utilities.get_package_details(packName)
        newClass = eval(packDetails['theClass'])
    except TypeError:
        factoriesLogger.debug('Wrong class name.')
        raise
    #del packDetails['theClass']
    #pairsToDelete = [k for k, v in packDetails.iteritems() if v is None]
    #for p in pairsToDelete:
    #    del packDetails[p]
    #newPackage = newClass(packName, sourceObj, timeslotDT, hostObj, 
    #                      **packDetails)
    newPackage = newClass(packName, sourceObj, timeslotDT, hostObj)
    return newPackage

#@log_calls
def create_file(name, timeslot, source, area=None, hostName=None):
    '''
    Create a G2File instance.

    The G2File instance will only be created if the hour specified in the
    timeslot argument is allowed in the xml settings.

    Inputs:

        name - The name of the G2File object to create

        timeslot - A string with the timeslot for the G2File

        source - A string with the name of the source

        area - A string with the name of the area

        hostName - A string specifying the name of the host. If
            this input is None, the host name defined in the
            file settings will be used.

        Example:

            f1 = create_file('visible goese', '200912100100', 'GOESE')
    '''

    newFile = None
    fileDetails = utilities.get_file_details(name)
    if fileDetails is not None:
        theDetails = fileDetails.copy()
        timeslotDT = dt.datetime.strptime(timeslot, '%Y%m%d%H%M')
        if timeslotDT.hour in theDetails['hours']:
            del theDetails['hours']
            sourceObj = create_source(source, area)
            if hostName is None:
                hostName = theDetails['host']
            del theDetails['host']
            try:
                newClass = eval(theDetails['theClass'])
                del theDetails['theClass']
                newFile = newClass(name, sourceObj, timeslotDT, hostName, 
                                   **theDetails)
            except TypeError:
                pass
        else:
            factoriesLogger.info('The specified file name is defined as not '\
                    'being available at the specified hour. Skipping...')
    return newFile

#@log_calls
def OLD_create_package(packName, packMode, timeslot, source, host=None, 
                   packVersion='current'):
    '''
    Return a new G2Package instance.

    Inputs:

        packName - A string with the name of the package to create. It must
            be a name present in the settings.

        packMode - A string with the mode of the package to create.

        timeslot - A string in the form of 'yyymmddHHMM' representing the
            package's timeslot.

        source - A string with the name of the source of the package

        host - A string with the name of the G2host object to create
            for the package.

        packVersion - A string with the version number of the package to
            create. It can also take the value 'current' in which case the
            current version will be used.
    '''

    timeslotDT = dt.datetime.strptime(timeslot, '%Y%m%d%H%M')
    hostDetails = utilities.get_host_details(host)
    sourceObj = create_source(source)
    if host is None:
        hostObj = create_host()
    else:
        hostObj = create_host(host)
    newPackage = None
    try:
        packDetails = utilities.get_package_details(packName)
        newClass = eval(packDetails['theClass'])
    except TypeError:
        factoriesLogger.debug('Wrong class name.')
        raise
    if packVersion == 'current':
        try:
            version = utilities.get_current_version_number(packName, packMode)
        except KeyError:
            # this package doesn't have the concept of a version
            version = None
    else:
        version = packVersion
    modeDetails = utilities.get_mode_details(packName, packMode).copy()
    #del modeDetails['name']
    if version is not None:
        del modeDetails['versions']
        newPackage = newClass(packName, packMode, sourceObj, timeslotDT, 
                              hostObj, version, **modeDetails)
    else:
        del modeDetails['defaultSource']
        del modeDetails['defaultArea']
        newPackage = newClass(packName, packMode, sourceObj, timeslotDT,
                              hostObj, **modeDetails)
    return newPackage
