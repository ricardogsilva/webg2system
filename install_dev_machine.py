#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A fabric fabfile in order to automate system installation/upgrade on 
development machines.
"""

import os
import re
import datetime as dt
from subprocess import Popen, PIPE

from fabric.api import local, lcd, settings

def install_first():
    # TODO: add an extra step:
    # - add the ubuntugis-unstable ppa in order to get GDAL from it
    local('sudo apt-get install python-software-properties')
    local('sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable')
    with settings(warn_only=True):
        result = local('sudo apt-get update', capture=True)
    install_apt_dependencies()
    print('\n- First set of dependencies installed. Now create the python ' \
          'virtual environment by executing:\n\n' \
          '\t$ virtualenv python\n\n' \
          '- Then activate the virtualenv using:\n\n' \
          '\t$ source python/bin/activate\n\n' \
          'Then proceed with the installation of the second set of ' \
          'dependencies, which are python-specific. Execute:\n\n' \
          '\t$ fab -f install_dev_machine install_second')

def install_apt_dependencies():
    '''
    Download and install the software dependencies.
    
    These dependencies are installed using apt-get and thus are installed
    system-wide.
    '''

    distro_version = local('lsb_release --release', capture=True)
    distro = re.search(r'Release:\s+([\d\.]+)', distro_version).group(1)
    distro_dt = dt.datetime.strptime(distro, '%y.%m')
    # libhdf5 changed name in Ubuntu 13.04
    if distro_dt < dt.datetime(2013, 4, 1):
        hdf5_package_names = ['libhdf5-serial-1.8.4', 'libhdf5-serial-dev']
    else:
        hdf5_package_names = ['libhdf5-7', 'libhdf5-dev']
    local('sudo apt-get install %s hdf5-tools libxml2 libxml2-dev ' \
          'libxslt1.1 libxslt1-dev gfortran subversion ttf-freefont ' \
          'libgdal-dev gdal-bin cgi-mapserver mapserver-bin fabric ' \
          'python-dev python-virtualenv python-pip python-mapscript ' \
          'python-software-properties' % ' '.join(hdf5_package_names))

def install_second():
    install_pip_dependencies()
    install_python_gdal()
    link_mapscript_virtualenv()

def install_pip_dependencies():
    '''
    Download and install the dependencies in the virtualenv.

    Use pip and requirements files to download and install most of the
    needed python dependencies into the virtualenv.
    '''

    local('pip install -r requirements_01.txt')
    local('pip install -r requirements_02.txt')
    local('pip install -r requirements_03.txt')

def install_python_gdal():
    '''
    Install python GDAL package in the virtualenv.

    The GDAL python package cannot be installed automatically by pip because
    it requires some additional configuration. The adopted strategy is to
    get the required python GDAL version from the system installed GDAL
    and then download it using pip. This downloaded egg is then setup with
    the paths to the system GDAL libs. Finally pip is used to install the egg.
    '''

    gdal_config_path = local('which gdal-config', capture=True)
    virtualenv_dir = local('echo $VIRTUAL_ENV', capture=True)
    #virtualenv_dir = os.path.dirname(local('which python', capture=True))
    local('rm --force %s' % os.path.join(virtualenv_dir, 'bin', 'gdal-config'))
    local('ln -s %s %s' % (gdal_config_path, 
                           os.path.join(virtualenv_dir, 'bin', 'gdal-config')))
    gdal_version = local('gdal-config --version', capture=True)
    min_version = re.search(r'\A(\d\.\d)', gdal_version).group()
    max_version = float(min_version) + 0.1
    lib_dir = local('gdal-config --libs', capture=True)
    re_match = re.search(r'-L(?P<dir>[\w\/]+) -l(?P<lib>[\w\.]+)', lib_dir)
    dir_name = re_match.group('dir')
    lib_name = re_match.group('lib')
    local('pip install --no-install "GDAL>=%s, <%3.1f"' % (min_version, max_version))
    build_path = os.path.join(virtualenv_dir, 'build', 'GDAL')
    if os.path.isdir(build_path):
        with lcd(build_path):
            local('python setup.py build_ext --gdal-config=%s --library-dirs=%s ' \
                  '--libraries=%s --include-dirs=%s' % (gdal_config_path, 
                  dir_name, lib_name, '/usr/include/gdal'))
        local('pip install --no-download GDAL')

def link_mapscript_virtualenv():
    '''
    Create a symlink to the system-wide mapscript package.

    Since it is not easy to install the python mapscript package inside
    a virtualenv, the approach taken here is to install the system-wide
    package and then symlink from inside the virtualenv.
    '''

    process = Popen(['env', 'python', '--version'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    python_version = re.search(r'(\d\.\d)', stderr).group()
    virtualenv_dir = local('echo $VIRTUAL_ENV', capture=True)
    if virtualenv_dir == '':
        print('Unable to detect virtual python environment. Did you remember ' \
              'to activate your virtualenv?')
        raise SystemExit
    link_dir = os.path.join(virtualenv_dir, 'lib', 
                            'python%s' % python_version, 'site-packages')
    link_names = ['mapscript.py', '_mapscript.so']
    for i in link_names:
        link_path = os.path.join(link_dir, i)
        if not os.path.islink(link_path):
            local('ln -s /usr/lib/python%s/dist-packages/%s %s' % \
                  (python_version, i, link_path))
