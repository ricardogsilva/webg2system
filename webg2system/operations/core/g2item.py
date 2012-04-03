#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

import logging

from systemsettings.models import Area

from g2sources import G2Source
from g2hosts import HostFactory

class GenericItem(object):
    '''
    All GenericItems must have:
        - timeslot
        - area 
        - host
    '''

    def __init__(self, timeslot, area, hostSettings=None):
        '''
        Inputs:

            timeslot - A datetime.datetime object

            area - A string with the name of the area

            hostSettings - A systemsettings.models.Host object. If None, the
                current host will be used.
        '''

        self.logger = logging.getLogger(
                '.'.join((__name__, self.__class__.__name__)))
        self.timeslot = timeslot
        self.source = G2Source(area, timeslot)
        hf = HostFactory()
        self.host = hf.create_host(hostSettings)

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

    def _use_callback(self, theCallback, *args):
        msg = []
        for msgBit in args:
            msg.append(msgBit)
        theCallback(msg)

