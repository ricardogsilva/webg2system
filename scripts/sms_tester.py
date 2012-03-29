#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
This script will become the SMS testing script for the new g2system.
"""

import sys
import urllib
import urllib2

def main(argList):
    # collect SMS variables for this task
    # for now its just placeholder text
    codeHost = 'localhost:8000'
    package = 'test_package'
    area = 'GOES-Disk'
    host = 'portatil'
    timeslot = '2012-02-16 17:00:00'
    force = '0'
    username = 'ricardo'
    password = 'r'

    g2systemURL = 'http://%s/operations/create/' % codeHost
    values = {
        package: package,
        area: area,
        host: host,
        timeslot: timeslot,
        username: username,
        password: password,
    }
    data = urllib.urlencode(values)
    headers = {
        'Content-Type' : 'application/x-www-form-urlencoded',
    }
    req = urllib2.Request(g2systemURL, data=data, headers=headers)
    response = urllib2.urlopen(req)
    theResponse = response.read()
    print(response)

if __name__ == "__main__":
    main(sys.argv[1:])

