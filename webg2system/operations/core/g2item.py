#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

from random import randint
import logging

from systemsettings.models import Area

from g2sources import G2Source
from g2hosts import HostFactory


class CallBackHandler(logging.Handler):

    def __init__(self, callback, level=logging.NOTSET):
        super(CallBackHandler, self).__init__(level)
        self.callback = callback

    def emit(self, record):
        msg = self.format(record)
        self.callback(msg)


class GenericItem(object):
    '''
    All GenericItems must have:
        - timeslot
        - area 
        - host
    '''

    def __init__(self, timeslot, area, host=None, 
                 log_level=logging.DEBUG, callback=None):
        '''
        Inputs:

            timeslot - A datetime.datetime object

            area - A string with the name of the area

            host - A systemsettings.models.Host object. If None, the
                current host will be used.
        '''

        if callback is None:
            def cb(*args):
                pass
            self.callback = cb
        else:
            self.callback = callback
        self.logger = logging.getLogger(
                '.'.join((__name__, self.__class__.__name__)))
        self.logger.setLevel(log_level)
        self.timeslot = timeslot
        self.source = G2Source(area, timeslot)
        hf = HostFactory(log_level=log_level)
        self.host = hf.create_host(host)
        # a random number for generating unique working dirs
        self.random = randint(0, 100)

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

    def _use_callback(self, *args):
        msg = []
        for msgBit in args:
            msg.append(msgBit)
        self.callback(msg)
