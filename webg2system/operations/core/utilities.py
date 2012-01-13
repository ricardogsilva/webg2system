#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains some helper functions.
"""

import datetime as dt
import logging
import re
import os

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
        else:
            try:
                markValue = eval('obj.%s' % mark)
            except AttributeError:
                pass
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

def extract_timeslot(filePath):
    '''
    Try to extract a timeslot from the input filePath.

    Returns:

        A datetime.datetime object or None, if no timeslot can be found
        on the file's name.
    '''

    timeslot = None
    dirPath, fileName = os.path.split(filePath)
    timeslotREs = {
            '%Y%m%d%H%M' : re.compile(r'\d{12}'),
            'year_doy' : re.compile(r'(?P<year>\d{4})_(?P<doy>\d{3})'),
            }
    for dtExpr, regexp in timeslotREs.iteritems():
        match = regexp.search(fileName)
        if match is not None:
            try:
                timeslot = dt.datetime.strptime(match.group(), dtExpr)
            except ValueError:
                if dtExpr == 'year_doy':
                    d = match.groupdict()
                    yTS = dt.datetime(year=int(d['year']), month=1, day=1)
                    timeslot = yTS + dt.timedelta(days=int(d['doy']) - 1)
                else:
                    raise
    return timeslot
