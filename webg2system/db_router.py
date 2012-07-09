#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

apps = [
    'operations', 
]
db_name = 'operations_db'

class MyAppRouter(object):

    def db_for_read(self, model, **hints):
        if model._meta.app_label in apps:
            return db_name
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in apps:
            return db_name
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label in apps or obj2._meta.app_label in apps:
            return True
        return None

    def allow_syncdb(self, db, model):
        if model._meta.app_label in ['south']:
            return True
        if db == db_name:
            return model._meta.app_label in apps
        elif model._meta.app_label in apps:
            return False
        return None
