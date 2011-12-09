#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

import logging
import functools
import os
from functools import wraps

class log_calls(object):
    '''
    This class is to be used as a decorator for logging.

    It can be called by any function (including class methods).
    '''

    def __init__(self, func):
        self.func = func
        self.logger = logging.getLogger('G2System.log_calls')

    def __call__(self, *args, **kwargs):
        self.logger.debug('%s called' % self.func.__name__)
        self.logger.debug('args: %s' % list(locals()['args']))
        self.logger.debug('kwargs: %s' % list(locals()['kwargs']))
        result = self.func(*args, **kwargs)
        self.logger.debug('%s exited' % self.func.__name__)
        self.logger.debug('result: %s' % (result,))
        return result

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)

class working_dir_exists(object):
    '''
    This class is to be used as a decorator for all methods of
    G2Package that need to use its workingDir attribute and be
    certain that the directory exists somewhere in the filesystem.
    '''

    def __init__(self, func):
        self.func = func
        self.logger = logging.getLogger('G2System.working_dir_exists')

    def __call__(self, *args, **kwargs):
        pass



