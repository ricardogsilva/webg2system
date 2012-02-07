#!/usr/bin/env python
#-*- coding: utf-8 -*-

import logging

class HostCleaner(object):
    '''
    This class has methods to carry out maintenance operations on the system's
    host machines. These operations are things like checking available
    filesystem space, removing old files, notifying administrators, ...
    '''

    def __init__(self, g2host):
        self.host = g2host
        self.logger = logging.getLogger(
                '.'.join((__name__, self.__class__.__name__)))

    # FIXME
    # - Adapt the script that is currently running on saf143
    def check_filesystem_space(self):
        raise NotImplementedError

    def delete_old_files(self, g2pack, baseTimeslot, ageThreshold):
        raise NotImplementedError

    def compress_old_files(self, g2pack, baseTimeslot, ageThreshold):
        raise NotImplementedError

    def bulk_compression(self, directory):
        raise NotImplementedError
