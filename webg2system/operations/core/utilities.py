#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains some helper functions.
"""

import datetime as dt
import logging
import re
import os

import systemsettings.models as ss

logger = logging.getLogger(__name__)

def show_status(status, progress):
    '''
    This function is a callback to report on progress...
    '''
    print(status, progress)

def parse_marked(markedStringObj, obj, markSign='#'):
    '''
    Parse the marked string.

    Inputs:

        markedStringObj - A systemsettings.MarkedString object.

        obj - An object where the marks should be searched for.
    '''

    newString = markedStringObj.string
    markList = [i.strip() for i in markedStringObj.marks.split(',')]
    if len(markList) == 1 and markList[0] == '':
        pass
    else:
        realMarks = convert_marks(markList, obj)
        counter = 0
        while newString.partition(markSign)[1] != '':
            partList = newString.partition(markSign)
            newString = partList[0] + str(realMarks[counter]) + partList[2]
            counter += 1
    return newString

def convert_marks(markList, obj):
    newMarks = []
    for mark in markList:
        markValue = None
        if mark == 'source':
            markValue = obj.source.name
        elif mark == 'area':
            markValue = obj.source.area
        elif mark == 'specificNumber':
            markValue = obj.source.specificNumber
        elif mark == 'altName':
            markValue = obj.source.altName
        elif mark == 'version':
            try:
                markValue = eval('obj.%s' % mark)
            except AttributeError:
                markValue = obj.parent.version
        elif mark == 'codeName':
            try:
                markValue = eval('obj.%s' % mark)
            except AttributeError:
                markValue = eval('obj.rawSettings.external_code.name')
        elif mark == 'subSatellitePoint':
            # get rid of any eventual plus or minus signs in the sub satellite 
            # point
            markValue = re.sub(r'[+-]', '', obj.source.subSatellitePoint)
        elif mark == 'product':
            markValue = obj.product.short_name
        elif mark == '':
            self.logger.warning('An empty mark has been defined. There is ' \
                                'probably something badly in the settings ' \
                                'for %s.' % obj)
            pass
        else:
            try:
                markValue = eval('obj.%s' % mark)
            except AttributeError:
                pass
        if markValue is None:
            markValue = '.*'
        newMarks.append(markValue)
    return newMarks

def displace_timeslot(timeslot, displacementObj):
    displacedTimeslots = []
    if displacementObj.unit == 'day':
        displacementUnit = 24 * 60 * 60 # measured in seconds
    elif displacementObj.unit == 'hour':
        displacementUnit = 60 * 60 # measured in seconds
    elif displacementObj.unit == 'minute':
        displacementUnit = 60 # measured in seconds
    else:
        displacementUnit = 0
    if displacementObj.endValue > displacementObj.startValue:
        first = displacementObj.startValue
        last = displacementObj.endValue
    else:
        first = displacementObj.endValue
        last = displacementObj.startValue

    for i in range(first, last + 1):
        newTimeslot = timeslot + dt.timedelta(seconds=(i * displacementUnit))
        displacedTimeslots.append(newTimeslot)
    return displacedTimeslots

def recover_timeslot(fileTimeslot, displacementObj):
    '''
    Recover the original timeslot for the package.
    '''

    if displacementObj.unit == 'minute':
        displacementUnit = 60 # measured in seconds
    elif displacementObj.unit == 'hour':
        displacementUnit = 60 * 60 # measured in seconds
    elif displacementObj.unit == 'day':
        displacementUnit = 60 * 60 * 24 # measured in seconds
    else:
        raise NotImplementedError
    if displacementObj.endValue > displacementObj.startValue:
        first = displacementObj.startValue
        last = displacementObj.endValue
    else:
        first = displacementObj.endValue
        last = displacementObj.startValue
    firstTS = fileTimeslot + dt.timedelta(seconds=first * displacementUnit)
    lastTS = fileTimeslot + dt.timedelta(seconds=last * displacementUnit)

    #if firstTS == lastTS:
    #    packTimeslot = firstTS
    #else:
    #    # the timeslots don't match so there is not a way to get the original
    #    # package's timeslot
    #    raise
    packTimeslot = lastTS
    return packTimeslot

def extract_timeslot(filePath):
    '''
    Try to extract a timeslot from the input filePath.

    Returns:

        A datetime.datetime object or None, if no timeslot can be found
        on the file's name.
    '''

    timeslot = None
    dirPath, file_name = os.path.split(filePath)
    file_name = file_name.replace('.', '\.') # escape possible file extension
    timeslot_regexps = [
        ('%Y%m%d%H%M', re.compile(r'\d{12}')),
        ('%Y%m%d%H', re.compile(r'\d{10}')),
        ('%Y%m%d', re.compile(r'\d{8}')),
        ('year_doy', re.compile(r'(?P<year>\d{4})_(?P<doy>\d{3})')),
    ]

    match = None
    index = 0
    while match is None and index < len(timeslot_regexps) :
        dt_expr, regexp = timeslot_regexps[index]
        match = regexp.search(file_name)
        index +=1
    if match is not None:
        try:
            timeslot = dt.datetime.strptime(match.group(), dt_expr)
        except ValueError:
            if dt_expr == 'year_doy':
                d = match.groupdict()
                yTS = dt.datetime(year=int(d['year']), month=1, day=1)
                timeslot = yTS + dt.timedelta(days=int(d['doy']) - 1)
            else:
                raise
    return timeslot

def get_file_settings(filePath):
    '''
    Scan the file path and retrieve the relevant G2File settings.
    '''

    possibleSettings = []
    for fileSettings in ss.File.objects.all():
        searchPatterns = [p.string for p in fileSettings.filepattern_set.all()]
        for sp in searchPatterns:
            pattern = sp.replace('#', '.*')
            reObj = re.search(pattern, filePath)
            if reObj is not None:
                possibleSettings.append(fileSettings)
    if len(possibleSettings) == 1:
        result = possibleSettings[0]
    elif len(possibleSettings) > 1:
        #logger.warning('Found more than one possible file settings (%s). '\
        #               'Returning the first one...' % possibleSettings)
        result = possibleSettings[0]
    else:
        logger.warning('Couldn\'t find any file settings for the supplied path.')
        result = None
    return result

def get_host_path(oldHost, oldPath, newHost):
    '''
    Adapt a path to a new host.
    '''

    relativePath = oldPath.replace(oldHost.dataPath, '')
    pathType = 'dataPath'
    if relativePath == oldPath:
        relativePath = oldPath.replace(oldHost.codePath, '')
        pathType = 'codePath'
    newPath = os.path.join(eval('newHost.%s' % pathType), relativePath[1:])
    return newPath

def get_tile_name(fileName):
    hvPatt = re.compile(r'H(\d{2})V(\d{2})')
    reObj = hvPatt.search(fileName)
    if reObj is not None:
        areaName = reObj.group()
    else:
        try:
            areaName = os.path.basename(fileName).split('_')[4]
        except IndexError:
            logger.error('Couldn\'t find area from the file name.')
            areaName = None
    return areaName

def is_smal_tile(file_path):
    re_obj = re.search(r'H\d{2}V\d{2}', file_path)
    if re_obj is None:
        result = False
    else:
        result = True
    return result

def put_tile_into_pattern(tile_name, g2f):
    for pattern in g2f.searchPatterns:
        result = pattern
        newPatt = re.sub(
                        r'\(\?P<tile_name>.*\)',
                        tile_name,
                        pattern
                  )
        if newPatt != pattern:
            result = newPatt
            break
    return result

def convert_regexp_syntax(regexp, to='posix-extended'):
    '''
    Convert a string between python and posix-extended regex syntax.
    '''

    if to == 'posix-extended':
        result = regexp.replace('\d', '[0-9]')
        result = result.replace('?P<tile_name>', '')
        result = result.replace('?!', '')
        result = result.replace('(\.ovr)', '') # ugly hack
    elif to == 'python':
        raise NotImplementedError
    return result
