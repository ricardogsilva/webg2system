from models import *
from django.contrib import admin

class AreaInline(admin.StackedInline):
    model = Area
    extra = 1

class SpecificSourceInline(admin.StackedInline):
    model = SpecificSource
    extra = 1

class SourceExtraInfoInline(admin.StackedInline):
    model = SourceExtraInfo
    extra = 1

class SourceSettingAdmin(admin.ModelAdmin):
    inlines = [AreaInline, SpecificSourceInline, SourceExtraInfoInline]
    list_display = ('name', 'areas', 'specific_names')

class HostSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'basePath', 'ip')

class FileSearchPathInline(admin.StackedInline):
    model = FileSearchPath
    extra = 1

class FileSearchPatternInline(admin.StackedInline):
    model = FileSearchPattern
    extra = 1

class FileSettingAdmin(admin.ModelAdmin):
    inlines = [FileSearchPathInline, FileSearchPatternInline]
    list_display = ('name', 'frequency', 'search_paths', 'search_patterns', 
                    'toArchive', 'toCompress', 'toDisseminate', 'toCopy')
    filter_horizontal = ('exceptHours',)
    list_filter = ('frequency', 'toDisseminate', 'toArchive')
    search_fields = ['name']

class PackageSpecificAdmin(admin.ModelAdmin):
    pass

class InputDirInline(admin.StackedInline):
    model = PackageInputDir
    extra = 1

class OutputDirInline(admin.StackedInline):
    model = PackageOutputDir
    extra = 1

class InternalDirInline(admin.StackedInline):
    model = PackageInternalDir
    extra = 1

class TimeslotDisplacerInline(admin.StackedInline):
    model = TimeslotDisplacer
    extra = 1

class WorkingDirInline(admin.StackedInline):
    model = PackageWorkingDir
    extra = 1
    
class PackageSettingAdmin(admin.ModelAdmin):
    inlines = [WorkingDirInline, OutputDirInline, InternalDirInline, InputDirInline]
    list_display = ('name', )

class PackageRelatedItemSettingAdmin(admin.ModelAdmin):
    inlines = [TimeslotDisplacerInline]
    filter_horizontal = ('specificAreas',)
    radio_fields = {'relatedItemRole' : admin.HORIZONTAL}
    list_display = ('id', 'packageSetting', 'relatedItemSetting', 'relatedItemRole',
                    'show_specific_areas', 'show_timeslot_displacements')
    list_filter = ('packageSetting', 'relatedItemSetting', 'relatedItemRole')
    search_fields = ['packageSetting__name', 'relatedItemSetting__name']

admin.site.register(Hour)
admin.site.register(SourceSetting, SourceSettingAdmin)
admin.site.register(HostSetting, HostSettingAdmin)
admin.site.register(FileSetting, FileSettingAdmin)
admin.site.register(PackageSetting, PackageSettingAdmin)
admin.site.register(PackageRelatedItemSetting, PackageRelatedItemSettingAdmin)
admin.site.register(TimeslotDisplacer)
