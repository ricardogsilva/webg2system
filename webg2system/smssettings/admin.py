from models import *
from django.contrib import admin

class SuiteVariableInLine(admin.StackedInline):
    model = SuiteVariable
    extra = 0

class FamilyVariableInLine(admin.StackedInline):
    model = FamilyVariable
    extra = 0

class TaskVariableInLine(admin.StackedInline):
    model = TaskVariable
    extra = 0

class RepeatInLine(admin.StackedInline):
    model = Repeat
    extra = 0

class SMSStatusAdmin(admin.ModelAdmin):
    pass

class SuiteAdmin(admin.ModelAdmin):
    inlines = [SuiteVariableInLine]

class FamilyAdmin(admin.ModelAdmin):
    inlines = [FamilyVariableInLine]
    list_display = ('name', 'path')

class TaskAdmin(admin.ModelAdmin):
    inlines = [TaskVariableInLine]
    list_display = ('name', 'path')

class SMSServerAdmin(admin.ModelAdmin):
    list_display = ('alias', 'host_settings', 'rpc_num')

admin.site.register(SMSStatus, SMSStatusAdmin)
admin.site.register(Suite, SuiteAdmin)
admin.site.register(Family, FamilyAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(SMSServer, SMSServerAdmin)
