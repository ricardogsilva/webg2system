from models import *
from django.contrib import admin

class RunningPackageAdmin(admin.ModelAdmin):
    list_display = ('id', 'show_settings', 'show_timeslot', 'show_area', 
                    'status', 'result', 'show_timestamp')

admin.site.register(RunningPackage, RunningPackageAdmin)
