from django.conf.urls.defaults import *
from django.views.generic import DetailView, ListView
from operations.models import RunningPackage

urlpatterns = patterns('',
        url(r'^$', ListView.as_view(
            queryset=RunningPackage.objects.order_by('timeslot')[:5],
            context_object_name='latest_package_list',
            template_name='operations/operations_index.html'),
            name='operations_list'),
        url(r'^(?P<pk>\d+)/$', DetailView.as_view(
            model=RunningPackage,
            context_object_name='package',
            template_name='operations/package_details.html'),
            name='package_details'),
)
urlpatterns += patterns('operations.views',
        url(r'^create/$', 'execute_package'),
        url(r'^monitor/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'monitor_state'),
        url(r'^products/(?P<prod_name>\w+)/docs/pum/$', 'get_product_user_manual'),
        
        url(r'^products/(?P<prod_name>\w+)/(?P<tile>\w+)/' \
            '(?P<timeslot>\d{12})/product/$', 'get_product_zip'),
        url(r'^products/SWI/(?P<timeslot>\d{12})/product/$', 
            'get_swi_product_zip'),

        url(r'^products/(?P<prod_name>\w+)/(?P<tile>\w+)/' \
                '(?P<timeslot>\d{12})/quicklook/$', 'get_quicklook'),

        url(r'^products/SWI/(?P<timeslot>\d{12})/quicklook/$', 'get_swi_quicklook'),


        url(r'^products/(?P<prod_name>\w+)/seriesquicklook/$', 
            'get_series_quicklook'),
)
