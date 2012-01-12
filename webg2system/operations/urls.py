from django.conf.urls.defaults import *
from django.views.generic import DetailView, ListView
from operations.models import RunningPackage

urlpatterns = patterns('',
        url(r'^$', ListView.as_view(
            queryset=RunningPackage.objects.order_by('timeslot')[:5],
            context_object_name='latest_package_list',
            template_name='operations/index.html'),
            name='package_list'),
        url(r'(?P<pk>\d+)/$', DetailView.as_view(
            model=RunningPackage,
            template_name='packages/detail.html'),
            name='package_details'),
)

urlpatterns = patterns('operations.views',
        url(r'(?P<timeslot>\d{8})/$', 'list_daily_ops'),
)
