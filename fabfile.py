#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A fabric fabfile in order to automate system installation/upgrade on several
remote servers at once.
"""
import sys
sys.path.append('webg2system')

from fabric.api import env, local, cd, run, settings

from django.core.management import setup_environ
import settings as s
setup_environ(s)

import systemsettings.models as sm



# define hosts here
HOSTS = {
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

#FIXME - Finish this method
def get_private_code(repository_url=None):
    '''
    Checkout the latest changes to the main product algorithms.
    '''

    if repository_url is None:
        repository_url = 'http://gridpt13.meteo.pt/ciac/G2System/trunk'
    ext_code = {
        'GRIB2HDF5_g2' : 'PRE_PROCESS/GRIB2HDF5_g2/GRIB2HDF5_g2_v%s',
        'LRIT2HDF5_g2' : 'PRE_PROCESS/LRIT2HDF5_g2/LRIT2HDF5_g2_v%s',
        'CMa_g2' : 'PRODUCTS/CMa_g2/CMa_g2_v%s',
        'DSLF_g2' : 'PRODUCTS/DSLF_g2/DSLF_g2_v%s',
        'DSSF_g2' : 'PRODUCTS/DSSF_g2/DSSF_g2_v%s',
        'GSA_g2' : 'PRODUCTS/GSA_g2/GSA_g2_v%s',
        'GSA_PP_g2' : 'PRODUCTS/GSA_PP_g2/GSA_PP_g2_v%s',
        'LST_g2' : 'PRODUCTS/LST_g2/LST_g2_v%s',
        'REF_g2' : 'PRODUCTS/REF_g2/REF_g2_v%s',
        'SAT_DATA_STAT_g2' : 'PRODUCTS/SAT_DATA_STAT_g2/SAT_DATA_STAT_g2_v%s',
        'SA_g2' : 'PRODUCTS/SA_g2/SA_g2_v%s',
        'SWI_g2' : 'PRODUCTS/SWI_g2/SWI_g2_v%s',
    }
    defined_packages = set()
    for pack in sm.Package.objects.all():
        code_name = None
        version = None
        for ei in pack.packageextrainfo_set.all():
            if ei.name == 'codeName':
                code_name = ei.string
            elif ei.name == 'version':
                version = ei.string
        defined_packages.add((code_name, version))
    for tup in defined_packages:
        code_name, version = tup
        extra_url = ext_code.get(code_name)
        if extra_url is not None:
            url = '/'.join((repository_url, extra_url % version))
            print('url: %s' % url)



