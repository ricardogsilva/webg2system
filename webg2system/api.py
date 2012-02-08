#!/usr/bin/env python
#-*- coding: utf-8 -*-

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
