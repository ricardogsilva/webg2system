from pydaemon import Daemon

class RPDaemon(Daemon):

    def __init__(self, runningPackage, pidfile, name='', working_dir='/', 
                 stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', 
                 uid=None):
        self.runningPackage = runningPackage
        super(RPDaemon, self).__init__(pidfile, name, working_dir, stdin,
                                       stdout, stderr, uid)

    def run(self):
        self.runningPackage.run()
