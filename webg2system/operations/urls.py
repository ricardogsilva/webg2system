from django.conf.urls.defaults import *
from django.views.generic import DetailView, ListView
from operations.models import RunningPackage

urlpatterns = patterns('',
        url(r'^$', ListView.as_view(
            queryset=RunningPackage.objects.order_by('timeslot')[:5],
            context_object_name='latest_package_list',
            template_name='operations_index.html'),
            name='operations_list'),
        url(r'^(?P<pk>\d+)/$', DetailView.as_view(
            model=RunningPackage,
            context_object_name='package',
            template_name='package_details.html'),
            name='package_details'),
)
urlpatterns += patterns('operations.views',
        url(r'^create/$', 'create_running_package'),
        url(r'^products/(?P<prodName>\w+)/(?P<area>\w+-?\w*)/(?P<timeslot>\d{12})/product$', 'get_product'),
)
