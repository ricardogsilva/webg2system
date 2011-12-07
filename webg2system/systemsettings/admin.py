from models import *
from django.contrib import admin

class HostAdmin(admin.ModelAdmin):
    list_display = ('name', 'basePath', 'ip')

class SpecificSourceInline(admin.StackedInline):
    model = SpecificSource
    extra = 1

class SourceExtraInfoInline(admin.StackedInline):
    model = SourceExtraInfo
    extra = 1

class AreaInline(admin.StackedInline):
    model = Area
    extra = 1

class FilePathInline(admin.StackedInline):
    model = FilePath
    extra = 1

class FilePatternInline(admin.StackedInline):
    model = FilePattern
    extra = 1

class PackagePathInline(admin.StackedInline):
    model = PackagePath
    extra = 1

class PackageInputInline(admin.StackedInline):
    model = PackageInput
    fk_name = 'package'
    extra = 1

class PackageOutputInline(admin.StackedInline):
    model = PackageOutput
    fk_name = 'package'
    extra = 1

class FileAdmin(admin.ModelAdmin):
    inlines = [FilePathInline, FilePatternInline]
    list_display = ('name', 'toCopy', 'toCompress', 'toArchive',
                    'toDisseminate', 'get_except_hours', 'get_search_paths',
                    'get_search_patterns')
    filter_horizontal = ('exceptHours',)

class PackageAdmin(admin.ModelAdmin):
    inlines = [PackagePathInline, PackageInputInline, PackageOutputInline]
    list_display = ('name', 'version', 'codeClass', 'get_inputs', 'get_outputs')

class SourceAdmin(admin.ModelAdmin):
    inlines = [AreaInline, SpecificSourceInline, SourceExtraInfoInline]
    list_display = ('name', 'areas', 'specific_names')

#admin.site.register(ExceptHour)
admin.site.register(TimeslotDisplacer)
admin.site.register(Host, HostAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Source, SourceAdmin)
