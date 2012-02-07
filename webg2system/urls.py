from django.conf.urls.defaults import patterns, include, url
from tastypie.api import Api
from api import RunningPackageResource, PackageResource, AreaResource, HostResource

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

v1API = Api(api_name='v1')
v1API.register(RunningPackageResource())
v1API.register(PackageResource())
v1API.register(AreaResource())
v1API.register(HostResource())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'webg2system.views.home', name='home'),
    # url(r'^webg2system/', include('webg2system.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^operations/', include('operations.urls')),
    # tastypie api
    url(r'^api/', include(v1API.urls)),
)
