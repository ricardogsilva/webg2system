#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

from pexpect import spawn
import re
import os

class SSHProxy(object):
    '''
    Connect to another server through SSH and perform various actions.
    '''

    sshPrompt = r'.+@.+:.+\$'
    # for removing ASCII escape characters from the connection's response
    # see:
    #    http://en.wikipedia.org/wiki/ANSI_escape_sequences
    #    http://stackoverflow.com/questions/1833873/python-regex-escape-characters/1834669#1834669
    # for more detail
    CSIPattern = r'\x1b\[\d+.?\d*\w?'

    def __init__(self, user=None, host=None, otherOptions=None):
        '''
        Inputs:

            user - A string with the name of the user.

            host - A string with the ip or the name of the host.

            otherOptions - A string with extra commands for the ssh login.
        '''

        self.connection = None
        self.user = user
        self.host = host
        self.otherOptions = otherOptions

    def setup(self, user, host, otherOptions=None):
        '''
        Inputs:

            user - A string with the name of the user.

            host - A string with the ip or the name of the host.

            otherOptions - A string with extra commands for the ssh login.
        '''

        self.user = user
        self.host = host
        self.otherOptions = otherOptions

    def _connect(self):
        if self.connection is not None and not self.connection.closed:
            #print('already connected')
            pass
        else:
            print('About to connect to %s' % self.host)
            if self.otherOptions is not None:
                otherOptions = self.otherOptions
            else:
                otherOptions = ''
            self.connection = spawn('ssh %s %s@%s' % (otherOptions, self.user,
                                    self.host))
            self.connection.expect(self.sshPrompt)
            result = self.connection.after.split('\r\n')
            if re.search(self.sshPrompt, result[-1]) is not None:
                print('connection successful')

    def run_command(self, command):
        '''
        Run a command and parse the result into a clean list.

        Inputs:

            command - A string with the full command to run.

        Returns:

            A list of strings with the output of the command.
        '''

        self._connect()
        self.connection.sendline(command)
        result = self.connection.expect(self.sshPrompt)
        output = self.connection.after.split('\r\n')
        # output [0] is the command that was run
        # output [-1] is the sshPrompt
        # that is why they are stripped from the result
        # also removing ASCII escape characters that serve for
        # outputing color information
        result = [re.sub(self.CSIPattern, '', i) for i in output[1:-1]]
        return result

    def list(self, rePattern=r''):
        '''
        Perform an 'ls' command using the rePattern.

        this method needs some more work in order to be consistent.
        '''

        searchDir, searchPattern = os.path.split(rePattern)
        if searchDir == '':
            searchDir = searchPattern
            searchPattern = '.*'
        if searchPattern == '':
            searchPattern = '.*'
        lsResult = self.run_command('ls -1 %s' % searchDir)
        patt = re.compile(searchPattern)
        result = []
        for line in lsResult:
            if patt.search(line) is not None:
                result.append(os.path.join(searchDir,line))
        return result
