#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A script to reprocess some timeslots from the processing lines.

It should be run like this:

    $ python reprocess_data.py -k populateCSW:True lst_metadata 201301010000 \
            201301312300 1

This example will reprocess the lst_metadata package from 2013/01/01 00:00 
until 2013/01/31 23:00 using an hourly frequency. It will supply the 
populateCSW argument to the package, using a value of True.
'''

import os
import sys
import datetime as dt
import logging
import argparse

from django.core.management import setup_environ
sys.path.append('/home/geo2/dev/webg2system/webg2system')
import settings as s
setup_environ(s)

import operations.models as om

def get_kwarg(item):
    key,value = item.split(':')
    value = eval(value)
    return {key: value}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('package')
    parser.add_argument('start_timeslot')
    parser.add_argument('end_timeslot')
    parser.add_argument('frequency', default=1, type=int, help='Frequency '
                        'for the pakcages (in hours)')
    parser.add_argument('-k', '--package_kwargs', type=get_kwarg,
                        action='append')
    args = parser.parse_args()
    package_kwargs = dict()
    [package_kwargs.update(dd) for dd in args.package_kwargs]
    timeslots = []
    start_ts = dt.datetime.strptime(args.start_timeslot, '%Y%m%d%H%M')
    end_ts = dt.datetime.strptime(args.end_timeslot, '%Y%m%d%H%M')
    delta = dt.timedelta(hours=args.frequency)
    current_ts = start_ts
    while current_ts <= end_ts:
        timeslots.append(current_ts)
        current_ts += delta
    for index, ts in enumerate(timeslots):
        print('processing timeslot %s (%i/%i)' % \
              (ts.strftime('%Y/%m/%d %H:%M'), index+1, len(timeslots)))
        rp = om.RunningPackage(settings=args.package, area='.*',
                               timeslot=ts)
        result = rp.run(log_level=logging.INFO, **package_kwargs)
