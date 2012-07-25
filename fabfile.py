#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A fabric fabfile in order to automate system installation/upgrade on several
remote servers at once.
"""

from fabric.api import env, local, cd, run, settings

env.hosts = ['180.180.30.98']

def prepare_deploy():
    commit()
    push()

def commit():
    local('git add --patch && git commit')

def push():
    local('git push origin master')

def deploy():
    code_dir = '/home/geo4/silvar/webg2system'
    with settings(warn_only=True):
        if run('test -d %s' % code_dir).failed:
            run('git clone git@github.com:ricardogsilva/webg2system.git %s' % \
                code_dir)
    with cd(code_dir):
        run('git pull origin master')
        run('touch webg2system/wsgi.py')
