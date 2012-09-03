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
    code_path = host_settings.codePath
    main_code_dir = os.path.dirname(code_path)
    return main_code_dir

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
    first = False
    with settings(warn_only=True):
        if run('test -d %s' % code_dir).failed:
            first = True
    if first:
        first_deployment()
    else:
        normal_deployment()

def normal_deployment():
    code_dir = _get_code_dir()
    with cd(code_dir):
        run('git checkout -- webg2system/sqlite.db')
        run('git pull origin master')
        run('touch webg2system/wsgi.py')

def first_deployment():
    install_apt_dependencies()
    clone_repo()
    install_pip_dependencies()
    #get_extra_libs()
    #get_private_code()

def install_apt_dependencies():
    sudo('apt-get install git python-pip python-virtualenv python-pexpect ' \
         'python-pyparsing python-lxml python-tables python-imaging ' \
         'gdal-bin python-gdal python-mapscript libapache2-mod-wsgi ' \
         'cgi-mapserver mapserver-bin ttf-freefont subversion')

def clone_repo():
    code_dir = _get_code_dir()
    run('git clone git@github.com:ricardogsilva/webg2system.git %s' % \
        code_dir)

def install_pip_dependencies():
    code_dir = _get_code_dir()
    with cd(code_dir):
        sudo('pip install -r requirements.txt')

# TODO - Rework the whole installation of the external libraries (HDF5, EMOS, ...)
# in order to make it more consistent with Fabric's ethos
def get_extra_libs():
    '''
    Fetch the HDF5 libs and other libraries needed by the core algorithms.
    '''
    ec = sm.ExternalCode.objects.get(name='extra_libs')
    repo_url, repo_user, repo_pass = ec.repository_credentials()
    build_script = ec.externalcodeextrainfo_set.get(name='build_script').string
    host = sm.Host.objects.get(ip=env.host)
    install_path = os.path.join(host.codePath, ec.get_relative_install_path())
    compiled_path = os.path.join(
                        host.codePath, 
                        ec.get_relative_install_path(var_name='compiled_path')
                    )
    vcs = ec.version_control_sw
    if vcs == 'svn':
        _svn_get_code(repo_url, repo_user, repo_pass, install_path)
    else:
        pass
    with cd(install_path):
        print('build_script: %s' % build_script)
        run('./%s %s' % (build_script, compiled_path))


#FIXME - only checkout and compile code that the hosts want to run
def get_private_code():
    '''
    Checkout the latest changes to the main product algorithms.
    '''

    for ec in sm.ExternalCode.objects.all():
        repo_url, repo_user, repo_pass = ec.repository_credentials()
        host = sm.Host.objects.get(ip=env.host)
        install_path = os.path.join(host.codePath, ec.get_relative_install_path())
        vcs = ec.version_control_sw
        if vcs == 'svn':
            _svn_get_code(repo_url, repo_user, repo_pass, install_path)
        else:
            pass
        _compile_external_code(install_path)

def _svn_get_code(url, username, password, destination_dir):
    first = False
    with settings(warn_only=True):
        if run('test -d %s' % destination_dir).failed:
            first = True
    if first:
        run('mkdir -p %s' % destination_dir)
        with cd(destination_dir):
            run('svn checkout --username %s --password %s %s .' % (username, 
                                                                   password, 
                                                                   url))
    else:
        with cd(destination_dir):
            run('svn update --username %s --password %s' % (username, password))

def _compile_external_code(destination_dir):
    pass
