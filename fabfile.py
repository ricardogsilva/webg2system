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

def setup_web_server():
    '''
    Connect to the remote machine that is to be used as a web server and
    perform the various steps needed in order to use it.
    '''

    pass

def install_web_server_dependencies():
    '''
    Install the needed software dependencies in order to run the web server.
    '''

    # get GIS base data (world borders, etc.) from the archive
    #run('scp')

    # install apache web server, tomcat server, postgreSQL + PostGIS database, geonetwork
    #sudo('apt-get install apache2')

    # tweak apache configurations and setup virtualhosts
    # tweak tomcat configurations (memory for the Java VM, logging)
    # create the PostgreSQL Postgis template, then create the geonetwork user and database
    # tweak geonetwork's configurations
    # fetch the webg2system code


def setup_dev_machine():
    '''
    Install all the needed dependencies in order to setup a new
    dev machine.

    This task will download and install the dependencies for running
    the external product generation algorithms (such as HDF5 libraries,
    FORTRAN compilers, etc.) and also for setting up and running the 
    production system (such as the python packages that are used in the 
    system).
    After the downloading and installation, the external algorithms are 
    compiled.

    The correct order for setting up new machines is therefore:

    1 - install git
    2 - clone the webg2system repository
    3 - run this fabfile as
            
            $ fab setup_dev_machine
    '''

    install_apt_dependencies()
    install_pip_dependencies()
    install_gdal_dependencies()
    get_extra_libs()
    compile_external_code()

def install_gdal_dependencies():
    gdal_config_path = local('which gdal-config')
    print(gdal_config_path)

def compile_external_code():
    pass

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
    local('sudo apt-get install python-pip python-virtualenv ' \
         'python-dev gdal-bin python-gdal python-mapscript ' \
         'cgi-mapserver mapserver-bin ttf-freefont ' \
         'subversion gfortran')

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
