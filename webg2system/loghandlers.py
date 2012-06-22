#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Some custom logging handlers.
"""

import logging

class CallBackHandler(logging.Handler):

    def __init__(self, callback, level=logging.NOTSET):
        super(CallBackHandler, self).__init__(level)
        self.callback = callback

    def emit(self, record):
        msg = self.format(record)
        self.callback('handled by the logging callback: %s' % msg)
        #self.callback(msg)
