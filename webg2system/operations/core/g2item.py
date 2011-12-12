#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

from systemsettings.models import Area

from g2sources import G2Source
from g2hosts import G2Host

class GenericItem(object):
    '''
    All GenericItems must have:
        - timeslot
        - area 
        - host
    '''

    def __init__(self, timeslot, area, hostSettings):
        '''
        Inputs:

            timeslot - A datetime.datetime object

            area - A string with the name of the area

            hostSettings - A systemsettings.models.Host object
        '''

        self.timeslot = timeslot
        areaSettings = Area.objects.get(name=area)
        self.source = G2Source(areaSettings.source, timeslot)
        self.host = G2Host(hostSettings)

    @property
    def doy(self):
        '''Day number in the year.'''
        return self.timeslot.timetuple().tm_yday

    @property
    def year(self):
        return self.timeslot.strftime('%Y')

    @property
    def month(self):
        return self.timeslot.strftime('%m')

    @property
    def day(self):
        return self.timeslot.strftime('%d')

    @property
    def hour(self):
        return self.timeslot.strftime('%H')

    @property
    def minute(self):
        return self.timeslot.strftime('%M')
