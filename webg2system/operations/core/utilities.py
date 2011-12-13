#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains some helper functions.
"""

import datetime as dt

def show_status(status, progress):
    '''
    This function is a callback to report on progress...
    '''
    print(status, progress)

def parse_marked(markedStringObj, obj):
    '''
    Parse the marked string.
    '''

    newString = markedStringObj.string
    markSign = '#'
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
            markValue = obj.source
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
    for i in range(displacementObj.startValue, (displacementObj.endValue + 1)):
        newTimeslot = timeslot + dt.timedelta(seconds=(i * displacementUnit))
        displacedTimeslots.append(newTimeslot)
    return displacedTimeslots


