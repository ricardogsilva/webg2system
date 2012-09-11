import time
from celery import task

import models

@task
def run_package(pack_name, area, timeslot, force, log_level, **kwargs):
    '''
    Dispatches tasks to be run asynchronously.

    Inputs:

        pack_name - the name of the package to run

        area - the name of the area to process

        timeslot - a datetime.datetime object with the timeslot to process

        force - a boolean indicating if the package should run even if
            its outputs are already available

        log_level - an int specifying the log level to use

        kwargs - Other keyword arguments relevant to the package that is
            being run

    Returns:

    The uuid of the asynchronous task.
    '''

    try:
        rp = models.RunningPackage.objects.get(settings=pack_name, area=area, 
                                               timeslot=timeslot)
    except models.RunningPackage.DoesNotExist:
        logger.info('The package does not exist. It will be created.')
        rp = RunningPackage(settings=pack_name, area=area, timeslot=timeslot)
    result = False
    if rp is not None:
        runOutputList = []
        callback = runOutputList.append
        rp.force = force
        result = rp.run(callback=callback, log_level=log_level, **kwargs)
    return result
