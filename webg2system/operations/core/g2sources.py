#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

class G2Source(object):
    '''
    ...
    '''

    def __init__(self, settings, timeslot):
        '''
        Inputs:

            settings - A systemsettings.models.Source object

            timeslot - A datetime.datetime object
        '''

        self.name = None
        for specSource in settings.specificsource_set.all():
            if specSource.startDate <= timeslot < specSource.endDate:
                self.name = specSource.name
        self.generalName = settings.name
        self.areas = [a.name for a in settings.area_set.all()]
