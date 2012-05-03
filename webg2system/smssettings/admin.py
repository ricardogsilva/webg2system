from models import *
from django.contrib import admin

class SMSServerAdmin(admin.ModelAdmin):
    model = SMSServer
    list_display = ('alias', 'host_settings', 'rpc_num')

admin.site.register(SMSServer, SMSServerAdmin)
