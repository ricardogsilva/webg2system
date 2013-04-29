#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A fabric fabfile in order to automate system installation/upgrade on 
development machines.
"""

import os
import re
import time
import datetime as dt
from subprocess import Popen, PIPE
# some tasks also import the lxml module, that will be available in the 
# virtualenv

from fabric.api import local, lcd, settings, get

_hosts = {
    'archive' : 'g2user@192.168.151.29',
}

def install_first():
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

    add_ubuntugis_repo()
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

def add_ubuntugis_repo():
    contents = local('ls /etc/apt/sources.list.d', capture=True)
    if re.search(r'ubuntugis-unstable', contents) is None:
        local('sudo apt-get install python-software-properties')
        local('sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable')
    with settings(warn_only=True):
        result = local('sudo apt-get update', capture=True)

def install_second():
    install_pip_dependencies()
    install_python_gdal()
    link_mapscript_virtualenv()
    create_operations_database()

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
    virtualenv_dir = _get_virtualenv_dir()
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

    python_version = _get_python_version()
    virtualenv_dir = _get_virtualenv_dir()
    link_dir = os.path.join(virtualenv_dir, 'lib',
                            'python%s' % python_version, 'site-packages')
    link_names = ['mapscript.py', '_mapscript.so']
    for i in link_names:
        link_path = os.path.join(link_dir, i)
        if not os.path.islink(link_path):
            local('ln -s /usr/lib/python%s/dist-packages/%s %s' % \
                  (python_version, i, link_path))

def create_operations_database():
    with lcd('webg2system'):
        local('python manage.py syncdb --database=operations_db')

def install_web_server(db_name='geonetwork_db', db_user='geonetwork_user', 
                       db_pass='geonetwork_pass', 
                       server_name='geoland2.meteo.pt'):
    #get_gis_base_data() # OK!
    #install_web_server_apt_dependencies() # OK!
    #alter_auxiliary_mapfile(server_name) # OK!
    #setup_auxiliary_wms() # OK
    #setup_dynamic_wms_services() # OK
    #tune_memory() # OK
    #tune_webserver() # OK
    #tune_database_server() # OK
    #configure_tomcat() # OK
    #deploy_geonetwork() # OK
    #create_database(db_name, db_user, db_pass) # OK
    #create_geonetwork_tables(db_name, db_user) # OK
    #configure_geonetwork_config_xml(db_name, db_pass, db_user)
    #configure_geonetwork_gui(server_name) # OK
    setup_virtualhost_geonetwork()
    setup_virtualhost_g2system()

def get_gis_base_data():
    '''
    Fetch the GIS base data from the archives.
    '''

    global _hosts
    remote_directory = '/media/Data3/geoland2/STATIC_INPUTS/geoland2_aux'
    with lcd('aux_wms'):
        file_names = ['geoland2_aux.map', 'geoland2_db.sqlite']
        for fn in file_names:
            if not os.path.isfile('aux_wms/%s' % fn):
                with settings(host_string=_hosts['archive']):
                    get('%s/%s' % (remote_directory, fn), '.')

def setup_auxiliary_wms():
    _setup_wms('apache/cgi-bin/auxiliary', 'aux_wms/geoland2_aux.map')

def setup_dynamic_wms_services():
    services = [
        {
            'apache_alias_path' : 'apache/cgi-bin/latest',
            'mapfile_path' : os.path.expanduser('~/data/OUTPUT_DATA/' \
                                                'wms_preparation/mapfiles/' \
                                                'latestproducts.map'),
        },
    ]
    for s in services:
        _setup_wms(s['apache_alias_path'], s['mapfile_path'])

def alter_auxiliary_mapfile(wms_base_url='127.0.0.1'):
    '''
    '''

    the_path = os.path.realpath('aux_wms/geoland2_aux.map')
    mapfile_directory, mapfile_name = os.path.split(the_path)
    with open(the_path) as fh: 
        new_contents = []
        for line in fh:
            if re.search(r'^\s*#', line) is None:
                if re.search(r'SHAPEPATH', line) is not None:
                    new_line = "\tSHAPEPATH '%s'\n" % mapfile_directory
                    new_contents.append(new_line)
                elif re.search(r'\'wms_onlineresource\'', line) is not None:
                    new_line = "\t\t\t'wms_onlineresource' " \
                               "'http://%s/cgi-bin/mapserv?map=%s'\n" % \
                               (wms_base_url, the_path)
                    new_contents.append(new_line)
                else:
                    new_contents.append(line)
            else:
                new_contents.append(line)
    _replace_file(the_path, 'tmp_%s' % mapfile_name, new_contents)

# TODO - Evaluate the need to add vsftpd (ftp server) as aditional dependency
def install_web_server_apt_dependencies():
    '''
    Download and install the software dependencies for the web server machine.

    These dependencies are installed using apt-get and thus are installed
    system-wide.
    '''

    add_ubuntugis_repo()
    local('sudo apt-get install apache2 libapache2-mod-wsgi postgresql-9.1 ' \
          'postgis tomcat7')

def create_database(db_name, db_user, db_pass):
    '''
    Create the PostGIS database and user for the catalogue server.
    '''

    local('sudo -u postgres psql -c "CREATE ROLE %s CREATEROLE CREATEDB ' \
          'LOGIN PASSWORD \'%s\'"' % (db_user, db_pass))
    local('sudo -u postgres psql -c "CREATE DATABASE %s OWNER %s"' \
          % (db_name, db_user))
    local('sudo -u postgres psql --dbname=%s -c "CREATE EXTENSION postgis;"' \
          % db_name)

def tune_webserver():
    '''
    Change the MaxClients parameter if it proves to be problematic
    '''

    pass

def tune_database_server(ram_to_shared_buffers_ratio=0.2, backup=True):
    '''
    Alter the database server's settings.

    This task will alter the main postgresql configuration file and set
    the 'shared_buffers' parameter to (hopefully) optimal values.
    '''

    available_ram = _get_available_ram()
    ram_to_use = int(available_ram * ram_to_shared_buffers_ratio / (1024 ** 2))
    psql_output = local('sudo -u postgres psql --version', capture=True)
    pg_version = re.search(r'\d\.\d', psql_output).group()
    pg_conf_path = '/etc/postgresql/%s/main/postgresql.conf' % pg_version
    new_contents = []
    with open(pg_conf_path) as fh:
        for line in fh:
            if re.search(r'shared_buffers[ =]+\d+\w+', line) is not None:
                new_line = 'shared_buffers = %iMB\n' % ram_to_use
                new_contents.append(new_line)
            else:
                new_contents.append(line)
    _replace_file(pg_conf_path, 'tmp_postgresql.conf', new_contents,
                  user_and_group='postgres', chmod_mask=644, backup=backup)
    local('sudo service postgresql restart')

def tune_memory(ram_to_shmmax_ratio=0.25, backup=True):
    '''
    Tune the available memory appropriately.

    This task alters the shmmax and shmall kernel parameters
    and writes the new values in the /etc/sysctl.conf file so that
    the changes are persisted after a reboot.
    '''

    available_ram = _get_available_ram()
    ram_to_use = int(available_ram * ram_to_shmmax_ratio)
    shmmax_out = local('sysctl kernel.shmmax', capture=True)
    used_shmmax = float(re.search(r'\d+', shmmax_out).group()) # Bytes
    if used_shmmax <= ram_to_use:
        shmall_out = local('sysctl kernel.shmall', capture=True)
        used_shmall = float(re.search(r'\d+', shmall_out).group()) # pages
        page_size = float(local('getconf PAGE_SIZE', capture=True))
        shmall_to_use = max(used_shmall, ram_to_use * page_size)
        local('sudo sysctl -w kernel.shmmax=%i' % ram_to_use)
        local('sudo sysctl -w kernel.shmall=%i' % shmall_to_use)
        new_contents = []
        added_shmmax_param = False
        added_shmall_param = False
        conf_file_path = '/etc/sysctl.conf'
        with open(conf_file_path) as fh:
            for line in fh:
                if re.search(r'kernel\.shmmax *= *\d+', line) is not None:
                    new_line = 'kernel.shmmax = %i\n' % ram_to_use
                    new_contents.append(new_line)
                    added_shmmax_param = True
                elif re.search(r'kernel\.shmall *= *\d+', line) is not None:
                    new_line = 'kernel.shmall = %i\n' % shmall_to_use
                    new_contents.append(new_line)
                    added_shmall_param = True
                else:
                    new_contents.append(line)
        if not added_shmmax_param:
            new_contents.append('kernel.shmmax = %i\n' % ram_to_use)
        if not added_shmall_param:
            new_contents.append('kernel.shmall = %i\n' % shmall_to_use)
        _replace_file(conf_file_path, 'tmp_sysctl.conf', new_contents,
                      user_and_group='root', chmod_mask=644, backup=backup)

def configure_tomcat(Xmx_to_ram_ratio=0.17, Xms_to_ram_ratio=0.1, backup=True):
    '''
    Configure the Tomcat java server in order to optimize performance.

    This task modifies the ammount of memory available and also adds some
    tweaks specific to geonetwork.
    '''

    available_ram = _get_available_ram()
    Xmx = int((available_ram * Xmx_to_ram_ratio) / (1024 ** 2)) # MegaBytes
    Xms = int((available_ram * Xms_to_ram_ratio) / (1024 ** 2)) # MegaBytes
    perm_size = Xms
    #max_perm_size = int(Xmx / 2)
    max_perm_size = int((Xmx + Xms) / 2.0)
    memory_opts_line = 'JAVA_OPTS="$JAVA_OPTS -Xms%sm -Xmx%sm ' \
                       '-XX:PermSize=%sm -XX:MaxPermSize=%sm"\n' % \
                       (Xms, Xmx, perm_size, max_perm_size)
    tweak_opts_line = 'JAVA_OPTS="$JAVA_OPTS -XX:CompileCommand=exclude,' \
                      'net/sf/saxon/event/ReceivingContentHandler.' \
                      'startElement"\n'
    conf_file_path = '/usr/share/tomcat7/bin/catalina.sh'
    found_memory_opts_line = False
    found_tweak_line = False
    new_contents = []
    with open(conf_file_path) as fh:
        for line in fh:
            if re.search(r'\-Xms\w+ \-Xmx\w+ \-XX\:PermSize\=\w+ ' \
                         '\-XX\:MaxPermSize\=\w+', line) is not None:
                new_contents.append(memory_opts_line)
                found_memory_opts_line = True
            else:
                if re.search(r'-XX:CompileCommand\=exclude', line) is not None:
                    found_tweak_line = True
                new_contents.append(line)
    if not found_tweak_line:
        new_contents.insert(0, tweak_opts_line)
    if not found_memory_opts_line:
        new_contents.insert(0, memory_opts_line)
    _replace_file(conf_file_path, 'tmp_catalina.sh', new_contents,
                  user_and_group='root', chmod_mask=755, backup=backup)
    local('sudo service tomcat7 stop')
    local('sudo service tomcat7 start')

def deploy_geonetwork():
    '''
    Get the geonetwork war file and install it.
    '''

    global _hosts
    remote_directory = '/media/Data3/geoland2/SOFTWARE'
    war_name = 'geonetwork.war'
    tomcat_apps_directory = '/var/lib/tomcat7/webapps'
    with settings(host_string=_hosts['archive']):
        get('%s/%s' % (remote_directory, war_name), '.')
    local('sudo mv --force %s %s' % (war_name, tomcat_apps_directory))
    local('sudo chown root:root %s' % os.path.join(tomcat_apps_directory,
          war_name))
    time.sleep(5) # give tomcat some time to unpack the geonetwork.war file

def create_geonetwork_tables(db_name, db_user):
    '''
    Run the geonetwork scripts that initialize the database.
    '''

    scripts_base_dir = '/var/lib/tomcat7/webapps/geonetwork/WEB-INF/classes/' \
                       'setup/sql'
    with lcd('%s/create' % scripts_base_dir):
        local('psql -h localhost -d %s -U %s -W -f create-db-postgis.sql' \
              % (db_name, db_user))
    with lcd('%s/data' % scripts_base_dir):
        local('psql -h localhost -d %s -U %s -W -f data-db-default.sql' \
              % (db_name, db_user))

def configure_geonetwork_config_xml(db_name, db_pass, db_user, backup=True):
    '''
    '''

    from lxml import etree
    config_file_path = '/var/lib/tomcat7/webapps/geonetwork/WEB-INF/config.xml'
    tree = etree.parse(config_file_path)
    for resource in tree.xpath('/geonet/resources/resource'):
        try:
            driver = resource.xpath('./config/driver')[0]
        except IndexError:
            driver = None
        if (driver is not None) and (re.search(r'org\.postg\w+\.Driver',
                driver.text) is not None):
            resource.set('enabled', 'true')
            for c in resource.xpath('./config/*'):
                if c.tag == 'user':
                    c.text = db_user
                elif c.tag == 'password':
                    c.text = db_pass
                elif c.tag == 'driver':
                    c.text = 'org.postgis.DriverWrapper'
                elif c.tag == 'url':
                    c.text = 'jdbc:postgreslq_postGIS://localhost:5432/' \
                             '%s' % db_name
        else:
            resource.set('enabled', 'false')
    _replace_xml_file(config_file_path, 'tmp_config.xml', tree, 'tomcat7', 644,
                      backup)

def configure_geonetwork_gui(server_name, map_search_layer='coastline',
                             map_viewer_layer='coastline', backup=True):
    '''
    Enable the geoland2 WMS layers for both the map searcher and mapviewer.
    '''

    from lxml import etree
    geoland2_aux_server_url = 'http://%s/cgi-bin/auxiliary' % server_name
    geoland2_latest_server_url = 'http://%s/cgi-bin/latest' % server_name
    config_file_path = '/var/lib/tomcat7/webapps/geonetwork/WEB-INF/' \
                       'config-gui.xml'
    #config_file_path = '/home/geo2/Downloads/geonetwork/WEB-INF/config-gui.xml'
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(config_file_path, parser)
    map_search_layers_element = tree.xpath('/config/mapSearch/layers')[0]
    map_search_layers_element.clear()
    layer = etree.Element('layer')
    layer.set('server', 'http://%s/cgi-bin/auxiliary' % server_name)
    layer.set('tocName',map_search_layer)
    layer.set('params', "{layers: '%s', format: 'image/png'}" % \
              map_search_layer)
    layer.set('options', '{isBaseLayer: true}')
    map_search_layers_element.append(layer)
    map_viewer_layers_element = tree.xpath('/config/mapViewer/layers')[0]
    map_viewer_layers_element.clear()
    for product in ['LST', 'DSLF', 'DSSF']:
        layer = etree.Element('layer')
        layer.set('server', geoland2_latest_server_url)
        layer.set('tocName', product)
        layer.set('params', "{layers: '%s', transparent: 'true'}" % product)
        layer.set('options', '{visibility: false}')
        map_viewer_layers_element.append(layer)
    base_layer = etree.Element('layer')
    base_layer.set('server', geoland2_aux_server_url)
    base_layer.set('tocName', map_viewer_layer)
    base_layer.set('params', "{layers: '%s', transparent: 'true'}" % \
                   map_viewer_layer)
    base_layer.set('options', '{isBaseLayer: true}')
    map_viewer_layers_element.append(base_layer)
    _replace_xml_file(config_file_path, 'tmp_config-gui.xml', tree, 'tomcat7',
                      644, backup)

# TODO - write this task
def setup_virtualhost_geonetwork():
    pass

# TODO - finish this task
def setup_virtualhost_g2system(server_name, num_processes=1, num_threads=1):
    config_file_path = 'apache/g2system.conf'
    with open(config_file_path) as fh:
        new_contents = []
        for line in fh:
            if re.search(r'^\s*#', line) is None: # not a comment line
                if re.search(r'ServerName', line) is not None:
                    new_line = '\tServerName g2system.%s\n' % server_name
                    new_contents.append(new_line)
                elif re.search(r'WSGIScriptAlias', line) is not None:
                    new_line = '\tWSGIScriptAlias /g2system %s\n' % \
                               os.path.realpath('webg2system/wsgi.py')
                    new_contents.append(new_line)
                elif re.search(r'WSGIDaemonProcess', line) is not None:
                    user = os.getenv('USER')
                    virtualenv_dir = _get_virtualenv_dir()
                    python_version = _get_python_version()
                    python_paths = os.path.realpath('webg2system')
                    python_paths += ':%s/lib/python%s/site-packages' % \
                                    (virtualenv_dir, python_version)
                    new_line = '\tWSGIDaemonProcess webg2system user=%s ' \
                               'group=%s processes=%i threads=%i ' \
                               'display-name="%{GROUP}" python-path=%s\n' % \
                               (user, user, num_processes, num_threads,
                               python_paths)
                    new_contents.append(new_line)
                elif re.search(r'<Directory>', line) is not None:
                    template = '\t<Directory %s>\n'
                    sitestatic_dir_re = re.search(r'sitestatic', line)
                    cgi_bin_dir_re = re.search(r'cgi-bin', line)
                    if sitestatic_dir_re is None and cgi_bin_dir_re is None:
                        replacement = os.path.realpath('webg2system')
                        new_contents.append(template % replacement)
                    elif sitestatic_dir_re is not None:
                        replacement = os.path.realpath('sitestatic')
                        new_contents.append(template % replacement)
                elif re.search(r'\sAlias', line) is not None:
                    new_line = '\tAlias /static/ %s/\n' % \
                               os.path.realpath('sitestatic')
                    new_contents.append(new_line)

def _backup_file(original_path):
    '''
    Make a backup copy if the input file.
    '''

    backup_dir = os.path.expanduser('~/g2system_backups')
    local('mkdir -p %s' % backup_dir)
    now = dt.datetime.utcnow()
    file_name = os.path.basename(original_path)
    local('cp %s %s/%s.%s' % (original_path, backup_dir, file_name, 
          now.strftime('%Y_%m_%d_%H_%M')))

def _get_available_ram():
    '''
    Return the available RAM, measured in Bytes.
    '''

    ram_out = local('grep MemTotal /proc/meminfo', capture=True)
    available_ram = float(re.search(r'\d+', ram_out).group()) * 1024 # Bytes
    return available_ram

def _get_python_version():
    process = Popen(['env', 'python', '--version'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    python_version = re.search(r'(\d\.\d)', stderr).group()
    return python_version

def _get_virtualenv_dir():
    virtualenv_dir = local('echo $VIRTUAL_ENV', capture=True)
    if virtualenv_dir == '':
        print('Unable to detect virtual python environment. Did you remember ' \
              'to activate your virtualenv?')
        raise SystemExit
    return virtualenv_dir

def _replace_file(original_file_path, tmp_file_name, content_list,
                  user_and_group=None, chmod_mask=None, backup=True):
    with open(tmp_file_name, 'w') as new_fh:
            new_fh.writelines(content_list)
    if backup:
        _backup_file(original_file_path)
    with settings(warn_only=True):
        result = local('mv %s %s' % (tmp_file_name, original_file_path))
    if not result.succeeded:
        local('sudo mv %s %s' % (tmp_file_name, original_file_path))
        local('sudo chown %s:%s %s' % (user_and_group, user_and_group, 
              original_file_path))
        local('sudo chmod %s %s' % (chmod_mask, original_file_path))

def _replace_xml_file(original_file_path, tmp_file_name, xml_tree,
                      user_and_group=None, chmod_mask=None, backup=True):
    xml_tree.write(tmp_file_name, pretty_print=True)
    if backup:
        _backup_file(original_file_path)
    with settings(warn_only=True):
        result = local('mv --force %s %s' % (tmp_file_name, original_file_path))
    if not result.succeeded:
        local('sudo mv %s %s' % (tmp_file_name, original_file_path))
        local('sudo chown %s:%s %s' % (user_and_group, user_and_group,
              original_file_path))
        local('sudo chmod %s %s' % (chmod_mask, original_file_path))

def _setup_wms(apache_alias_path, mapfile_path):
    apache_alias_name = os.path.basename(apache_alias_path)
    new_contents = []
    new_line_template = 'MS_MAPFILE="%s" exec ${MAPSERV}\n'
    search_pattern = re.compile(r'^MS_MAPFILE')
    with open(apache_alias_path) as fh:
        for line in fh:
            if search_pattern.search(line) is not None:
                new_contents.append(new_line_template % \
                                    os.path.realpath(mapfile_path))
            else:
                new_contents.append(line)
    _replace_file('/usr/lib/cgi-bin/%s' % apache_alias_name,
                  'tmp_%s' % apache_alias_name, new_contents,
                  user_and_group='root', chmod_mask=755, backup=False)
