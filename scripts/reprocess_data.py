#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A script to reprocess some timeslots from the processing lines.
'''

import os
import sys
import datetime
import logging

from django.core.management import setup_environ
sys.path.append('/home/geo2/dev/webg2system/webg2system')
import settings as s
setup_environ(s)

import operations.models as om

if __name__ == '__main__':
    products = ['swi',]
    packages = [
        {
            'name' : '%s_metadata',
            'kwargs' : {
                'send_to_csw' : True,
            }
        },
    ]

    for day in range (20, 21):
        print('---- day %i ----' % day)
        for hour in range(0, 1):
            print('\t---- hour %i ----' % hour)
            for product in products:
                print('\t\t---- product %s ----' % product)
                for pack_dict in packages:
                    pack_name = pack_dict['name'] % product
                    print('\t\t\t---- package: %s ----' % pack_name)
                    ts = datetime.datetime(2013, 10, day, hour)
                    rp = om.RunningPackage(settings=pack_name, area='.*',
                                           timeslot=ts)
                    result = rp.run(log_level=logging.INFO,
                                    **pack_dict.get('kwargs', dict()))
                    #del rp
                    print('\t\t\t\t ---- result: %s ----' % result)
