#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A fabric fabfile to automate backing up geonetwork's database into the archives.

It is to be executed as:

    $ fab -f backup_database.py execute_backup:db_name='geonetwork',db_user='geonetwork',backup_name='teste.sql'
"""

import sys
import os
from fabric.api import env, local, cd, lcd, run, settings, sudo

def execute_backup(db_name='geonetwork_new', 
                   db_user='geonetwork_new',
                   backup_name='geonetwork_db_backup.sql',
                   backup_dir='/home/geo3/BACKUPS'):
    destination_host = '192.168.151.29'
    destination_user = 'g2user'
    destination_path = '/media/Data3/geoland2/BACKUPS'
    with lcd(backup_dir):
        _dump_database(db_name, db_user, backup_name)
        _rsync_dump(backup_name, destination_user, 
                   destination_host, destination_path)
        _delete_dump(backup_name)

def _dump_database(db_name, db_user, backup_name):
    '''
    Execute the external pg_dump utility in order to create a backup of the
    database.
    '''
    local('pg_dump -U %s %s > %s' % (db_user, db_name, backup_name))

def _rsync_dump(backup_name, dst_user, dst_host, dst_path):
    '''
    rsync the backup file to the archive.
    '''
    local('rsync %s %s@%s:%s' % (backup_name, dst_user, dst_host, dst_path))

def _delete_dump(backup_name):
    '''
    Delete the local backup.
    '''
    local('rm %s' % backup_name)
