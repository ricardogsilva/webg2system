from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('operations.views',
        url(r'(?P<timeslot>\d{8})/$', 'list_daily_ops'),
)
