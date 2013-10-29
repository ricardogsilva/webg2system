#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A fabric fabfile to automate backing up geonetwork's database into the archive

It is to be executed as:

    $ fab -f backup_database.py execute_backup:db_name='geonetwork',db_user='geonetwork'
"""

import sys
import os
import datetime as dt

from fabric.api import env, local, cd, lcd, run, settings, sudo

def execute_backup(db_name, db_user):
    now = dt.datetime.utcnow()
    backup_name = now.strftime('geonetwork_db_backup_%Y_%m_%d_%H_%M.sql')
    destination_host = '192.168.151.29'
    destination_user = 'g2user'
    destination_path = '/media/Data3/geoland2/BACKUPS'
    local_backup_dir = os.path.expanduser('~/temp_backups')
    if not os.path.isdir(local_backup_dir):
        os.makedirs(local_backup_dir)
    with lcd(local_backup_dir):
        local('pg_dump -U %s %s > %s' % (db_user, db_name, backup_name))
        local('rsync %s %s@%s:%s' % (backup_name, destination_user,
              destination_host, destination_path))
    local('rm -rf %s' % local_backup_dir)
