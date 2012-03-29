#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
THE API APPROACH IS, FOR NOW, ABANDONED. AT A LATER STAGE THIS WILL 
BE REVISITED.

The api will be nice to have because it has builtin authentication,
usage limits and other good things.
'''

import logging

from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from tastypie import fields
import tastypie.constants
from operations.models import RunningPackage
from systemsettings.models import Package, Area, Host

class PackageResource(ModelResource):
    class Meta:
        queryset = Package.objects.all()
        resource_name = 'package'
        allowed_methods = ['get',]
        filtering = {
                'name' : tastypie.constants.ALL,
        }

class AreaResource(ModelResource):
    class Meta:
        queryset = Area.objects.all()
        resource_name = 'area'
        allowed_methods = ['get',]
        filtering = {
                'name' : tastypie.constants.ALL,
        }

class HostResource(ModelResource):
    class Meta:
        queryset = Host.objects.all()
        resource_name = 'host'
        allowed_methods = ['get',]
        filtering = {
                'name' : tastypie.constants.ALL,
        }

class RunningPackageResource(ModelResource):
    package = fields.ForeignKey(PackageResource, 'settings')
    area = fields.ForeignKey(AreaResource, 'area')
    host = fields.ForeignKey(HostResource, 'host')

    def __init__(self, api_name=None):
        super(RunningPackageResource, self).__init__(api_name)
        self.logger = logging.getLogger('.'.join((__name__, 
                                        self.__class__.__name__)))


    class Meta:
        queryset = RunningPackage.objects.all()
        resource_name = 'runningpackage'
        authorization = Authorization()
        filtering = {
                'package' : 2,
                'timeslot' : tastypie.constants.ALL,
                'area' : 2,
                'host' : 2,
        }

    def obj_create(self, bundle, request=None, **kwargs):
        # the bundle object is returned after the data is inserted in the 
        # database
        bundle = super(RunningPackageResource, self).obj_create(bundle, 
                                                                request, 
                                                                **kwargs)
        self.logger.debug('bundle: %s' % bundle)
        self.logger.debug('About to execute the runningPackage instance\'s run() method...')
        #bundle.obj.run()
        bundle.obj.daemonize()
        return bundle
