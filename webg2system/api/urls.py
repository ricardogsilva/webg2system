from django.conf.urls.defaults import patterns, include, url
from piston.resource import Resource
from api.handlers import RunningPackageHandler

running_package_handler = Resource(RunningPackageHandler)

urlpatterns = patterns('',
        url(r'^package/(?P<packId>[^/]+)/', running_package_handler),
        url(r'^packages/', running_package_handler),
        url(r'^package/create/(?P<settings>\w)/(?P<area>\w)/(?P<timeslot>\d{12})/(?P<host>\w)/', running_package_handler),
)
