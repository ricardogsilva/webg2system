#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

from django.core.exceptions import ObjectDoesNotExist

import systemsettings.models as ss

class G2Source(object):
    '''
    ...
    '''

    def __init__(self, area, timeslot):
        '''
        Inputs:

            area - A systemsettings.models.Area object.

            timeslot - A datetime.datetime object.
        '''


        areaSettings = ss.Area.objects.get(name=area)
        sourceSettings = areaSettings.source
        self.name = None
        for specSource in sourceSettings.specificsource_set.all():
            if specSource.startDate <= timeslot < specSource.endDate:
                self.name = specSource.name
        self.generalName = sourceSettings.name
        #self.areas = [a.name for a in settings.area_set.all()]
        self.area = areaSettings.name
        for extraInfo in ('subSatellitePoint', 'lfac', 'cfac', 'loff',
                          'coff', 'pixelSize', 'sensor', 'altName',):
            try:
                exec('self.%s = sourceSettings.sourceextrainfo_set.get(name="%s")'
                     % (extraInfo, extraInfo))
            except ObjectDoesNotExist:
                pass
