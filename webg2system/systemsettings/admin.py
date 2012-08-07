from models import *
from django.contrib import admin

class HostRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class HostAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'get_roles', 'dataPath', 'codePath', 'ip')
    actions = ['toggle_active']

    def toggle_active(self, request, queryset):
        for obj in queryset:
            obj.active = not obj.active
            obj.save()
    toggle_active.short_description = 'Toggle selected host\'s active flag.'

class SpecificSourceInline(admin.StackedInline):
    model = SpecificSource
    extra = 0

class SourceExtraInfoInline(admin.StackedInline):
    model = SourceExtraInfo
    extra = 0

class AreaInline(admin.StackedInline):
    model = Area
    extra = 1

class ExternalCodeExtraInfoInline(admin.StackedInline):
    model = ExternalCodeExtraInfo
    extra = 0

class FilePathInline(admin.StackedInline):
    model = FilePath
    extra = 0

class FilePatternInline(admin.StackedInline):
    model = FilePattern
    extra = 0

class PackagePathInline(admin.StackedInline):
    model = PackagePath
    extra = 0

class PackageInputInline(admin.StackedInline):
    model = PackageInput
    fk_name = 'package'
    extra = 0

class PackageOutputInline(admin.StackedInline):
    model = PackageOutput
    fk_name = 'package'
    extra = 0

class PackageExtraInfoInline(admin.StackedInline):
    model = PackageExtraInfo
    extra = 0

class FileExtraInfoInline(admin.StackedInline):
    model = FileExtraInfo
    extra = 0

class DatasetInline(admin.StackedInline):
    model = Dataset
    extra = 0
    radio_fields = {'coverage_content_type' : admin.HORIZONTAL}
    
class CodeClassAdmin(admin.ModelAdmin):
    pass

class FileAdmin(admin.ModelAdmin):
    inlines = [FilePathInline, FilePatternInline, FileExtraInfoInline]
    list_display = ('name', 'frequency', 'toCopy', 'toCompress', 'toArchive',
                    'toDisseminate', 'get_except_hours', 'get_search_paths',
                    'get_search_patterns', 'get_package_outputs',
                    'get_package_inputs')
    filter_horizontal = ('exceptHours', 'specificArchives')
    #list_filter = ['frequency', 'toCopy', 'toArchive', 'toDisseminate', 'toCompress']
    search_fields = ['name']
    pass

class PackageAdmin(admin.ModelAdmin):
    inlines = [PackagePathInline, PackageInputInline, PackageOutputInline, PackageExtraInfoInline]
    list_display = ('name', 'get_inputs', 'get_outputs', 'code_class', 'product')
    search_fields = ['name']

class ExternalCodeAdmin(admin.ModelAdmin):
    inlines = [ExternalCodeExtraInfoInline]
    list_display = ('name', 'version', 'get_repository')

class SourceAdmin(admin.ModelAdmin):
    inlines = [AreaInline, SpecificSourceInline, SourceExtraInfoInline]
    list_display = ('name', 'areas', 'specific_names')

class ProductAdmin(admin.ModelAdmin):
    #radio_fields = {'iResourceType' : admin.HORIZONTAL}
    inlines = [DatasetInline]
    list_display = ('short_name', 'name', 'series_status')
    filter_horizontal = ('keywords', 'topicCategories', 'sources',)
    fieldsets = [
            ('Dataset Series information', {
                'fields' : ['series_title', 'series_status'],
            }),
            ('Dataset information', {
                'fields' : ['name', 'short_name', 'user_manual', 
                            'originator_collaborator', 
                            'principal_investigator', 'distributor',
                            'inspireKeyword', 'keywords', 'topicCategories',
                            'pixelSize', 'iResourceTitle', 
                            'iResourceAbstract', 'iParentIdentifier', 
                            'parent_id_continental', 'sdi_service_id',
                            'ireferenceSystemID', 'iCredit',
                            'graphic_overview_description',
                            'graphic_overview_type', 'supplemental_info',
                            'validation_report', 'lineage', 'sources',
                            'temporal_extent'],
            }),
    ]

class WebServerAdmin(admin.ModelAdmin):
    list_display = ('host', 'public_URL')
    
    def has_add_permission(self, request):
        return False

class CatalogueServerAdmin(admin.ModelAdmin):
    list_display = ('host', 'base_URL')
    
    def has_add_permission(self, request):
        return False


#admin.site.register(ExceptHour)
admin.site.register(TimeslotDisplacer)
admin.site.register(HostRole, HostRoleAdmin)
admin.site.register(CodeClass, CodeClassAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(ExternalCode, ExternalCodeAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(WebServer, WebServerAdmin)
admin.site.register(CatalogueServer, CatalogueServerAdmin)
