from models import *
from django.contrib import admin

class RunningPackageAdmin(admin.ModelAdmin):
    #list_display = ('id', 'show_settings', 'show_timeslot', 'show_area', 
    #                'status', 'result', 'show_timestamp')
    list_display = ('id','show_timeslot', 'settings', 'area', 'status', 
                    'result', 'show_timestamp')
    search_fields = ['settings']

admin.site.register(RunningPackage, RunningPackageAdmin)
