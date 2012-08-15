#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A fabric fabfile in order to automate system installation/upgrade on several
remote servers at once.
"""

import os
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

#FIXME - only checkout and compile code that the hosts want to run
def get_private_code():
    '''
    Checkout the latest changes to the main product algorithms.
    '''

    for ec in sm.ExternalCode.objects.all():
        repository_url = ec.get_repository()
        host = sm.Host.objects.get(ip=env.host)
        install_path = os.path.join(host.codePath, ec.get_relative_install_path())
        vcs = ec.version_control_sw
        if vcs == 'svn':
            _svn_do_checkout(repository_url, install_path)
        else:
            pass

def _svn_do_checkout(url, destination_dir):
    print('url: %s' % url)
    print('destination_dir: %s' % destination_dir)
