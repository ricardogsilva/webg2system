#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A fabric fabfile in order to automate system installation/upgrade on several
remote servers at once.
"""

from fabric.api import env, local, cd, run, settings

# define hosts here
HOSTS = {
    '180.180.30.98' : {
        'user' : 'geoland', 
        'code_dir' : '/home/geoland/silvar/webg2system'
    },
    '180.180.30.99' : {
        'user' : 'geo5',
        'code_dir' : '/home/geo5/silvar/webg2system'
    },
    '193.137.20.109' :{
        'user' : 'geoland2',
        'code_dir' : '/home/geoland2/webg2system'
    },
}

def _prepare_env_hosts():
    '''
    Return a list suitable for fabric's env.hosts variable.

    The returned list is constructed from the global HOSTS
    variable.
    '''

    global HOSTS
    host_list = []
    for host, settings in HOSTS.iteritems():
        host_string = '%s@%s:%s' % (settings['user'], 
                                    host, 
                                    settings.get('port', 22))
        host_list.append(host_string)
    return host_list

env.hosts = _prepare_env_hosts()

def prepare_deploy():
    commit()
    push()

def commit():
    local('git add --patch && git commit')

def push():
    local('git push origin master')

def deploy():
    '''
    Deploy the latest changes present in the git repository to the
    defined hosts.
    '''

    global HOSTS
    code_dir = HOSTS[env.host]['code_dir']
    with settings(warn_only=True):
        if run('test -d %s' % code_dir).failed:
            run('git clone git@github.com:ricardogsilva/webg2system.git %s' % \
                code_dir)
    with cd(code_dir):
        run('git pull origin master')
        run('touch webg2system/wsgi.py')
