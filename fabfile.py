#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A fabric fabfile in order to automate system installation/upgrade on several
remote servers at once.
"""

import sys
sys.path.append('webg2system')

from fabric.api import env, local, cd, run, settings, sudo

from django.core.management import setup_environ
import settings as s
setup_environ(s)

import systemsettings.models as sm

def _get_active_hosts():
    '''
    Scan the systemsettings django app and get a list of the defined hosts.

    The returned list will not include hosts with an 'archive' role, even
    if they are defined as active. Presumably there will be no need to
    install or update anything on the archives.
    '''

    hosts = sm.Host.objects.filter(active=True).exclude(role__name='archive')
    hosts_list = ['%s@%s:22' % (h.username, h.ip) for h in hosts]
    return hosts_list

def _get_code_dir():
    host_settings = sm.Host.objects.get(ip=env.host)
    return host_settings.codePath

env.hosts = _get_active_hosts()

def prepare_deploy():
    commit()
    push()

def commit():
    local('git add --interactive && git commit')

def push():
    local('git push origin master')

def deploy():
    '''
    Deploy the latest changes present in the git repository to the
    defined hosts.
    '''

    code_dir = _get_code_dir()
    with settings(warn_only=True):
        if run('test -d %s' % code_dir).failed:
            first_deployment()
        else:
            with cd(code_dir):
                run('git pull origin master')
    with cd(code_dir):
        run('touch webg2system/wsgi.py')

def first_deployment():
    install_apt_dependencies()
    clone_repo()
    install_pip_dependencies()

def install_apt_dependencies():
    sudo('apt-get install git python-pip python-pexpect python-pyparsing ' \
         'python-lxml python-tables python-imaging gdal-bin python-gdal ' \
         'python-mapscript libapache2-mod-wsgi cgi-mapserver mapserver-bin ' \
         'ttf-freefont')

def clone_repo():
    code_dir = _get_code_dir()
    run('git clone git@github.com:ricardogsilva/webg2system.git %s' % \
        code_dir)

def install_pip_dependencies():
    code_dir = _get_code_dir()
    with cd(code_dir):
        sudo('pip install -r requirements.txt')

#FIXME - Finish this method
def get_private_code():
    '''
    Checkout the latest changes to the main product algorithms.
    '''

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
    host_obj = sm.Host.objects.get(ip=env['host'])
