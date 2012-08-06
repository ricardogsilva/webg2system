#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
This script is run remotely by another host.

This script allows a remote machine to act as a middle agent between
two other machines. Its purpose is to be executed by hosts whose role
is io_buffer. These hosts communicate directly with the archives.
"""

import sys
import argparse
import logging
sys.path.append('../webg2system')

import pysftp

from django.core.management import setup_environ
import settings as s
setup_environ(s)

import systemsettings.models as ss
import operations.core.g2hosts as g2h

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--restrict_pattern', help='A regular expression with ' \
                        'the pattern to filter the path_list.')
    parser.add_argument('host', help='The remote host\'s name, as defined ' \
                        'in the g2system settings.')
    parser.add_argument('path_list', metavar='path', nargs='+', 
                        help='A list of paths, interpreted as ' \
                        'regular expressions to search on the remote host.')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    factory = g2h.HostFactory()
    remote_host_settings = ss.Host.objects.get(name=args.host)
    remote_host = factory.create_host(remote_host_settings)
    found = remote_host.find(args.path_list, 
                             restrict_pattern=args.restrict_pattern)
    remote_host.close_connection()
    for path in found:
        print(path)
