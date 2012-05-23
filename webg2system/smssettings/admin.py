from models import *
from django.contrib import admin

class SuiteAdmin(admin.ModelAdmin):
    pass

class SMSServerAdmin(admin.ModelAdmin):
    list_display = ('alias', 'host_settings', 'rpc_num')

admin.site.register(Suite, SuiteAdmin)
admin.site.register(SMSServer, SMSServerAdmin)
