from models import *
from django.contrib import admin

class HostAdmin(admin.ModelAdmin):
    list_display = ('name', 'dataPath', 'codePath', 'ip')

class SpecificSourceInline(admin.StackedInline):
    model = SpecificSource
    extra = 0

class SourceExtraInfoInline(admin.StackedInline):
    model = SourceExtraInfo
    extra = 0

class AreaInline(admin.StackedInline):
    model = Area
    extra = 1

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
    
class CodeClassAdmin(admin.ModelAdmin):
    pass

class FileAdmin(admin.ModelAdmin):
    inlines = [FilePathInline, FilePatternInline, FileExtraInfoInline]
    list_display = ('name', 'frequency', 'toCopy', 'toCompress', 'toArchive',
                    'toDisseminate', 'get_except_hours', 'get_search_paths',
                    'get_search_patterns', 'get_package_output', 
                    'get_package_inputs')
    filter_horizontal = ('exceptHours', 'specificArchives')
    #list_filter = ['frequency', 'toCopy', 'toArchive', 'toDisseminate', 'toCompress']
    search_fields = ['name']

class PackageAdmin(admin.ModelAdmin):
    inlines = [PackagePathInline, PackageInputInline, PackageOutputInline, PackageExtraInfoInline]
    list_display = ('name', 'codeClass', 'get_inputs', 'get_outputs')
    search_fields = ['name', 'codeClass__className']

class SourceAdmin(admin.ModelAdmin):
    inlines = [AreaInline, SpecificSourceInline, SourceExtraInfoInline]
    list_display = ('name', 'areas', 'specific_names')

class ProductAdmin(admin.ModelAdmin):
    radio_fields = {'iResourceType' : admin.HORIZONTAL}
    #fieldsets = [
    #        (
    #            None, 
    #            {'fields' : ['name', 'shortName', 'pixelSize']}
    #        ),
    #        (
    #            'INSPIRE metadata', 
    #            {'fields' : [
    #                    'originatorOrganization',
    #                    'principalInvestigatorOrganization',
    #                    'inspireKeyword',
    #                    'keywords',
    #                    'topicCategories',
    #                    'iResourceTitle', 
    #                    'iResourceAbstract', 
    #                    'iResourceType',
    #                    'iParentIdentifier',
    #                    'ireferenceSystemID',
    #                    'iOtherDetails',
    #                    'iCredit',
    #                    ],
    #             'classes' : ['collapse']}
    #        ),
    #]
    inlines = [DatasetInline]
    list_display = ('shortName', 'name')

class GeneralMetadataAdmin(admin.ModelAdmin):
    model = GeneralMetadata
    extra = 0
    list_display = ('orgName', 'orgURL', 'contactName', 'contactEmail')
    
class KeywordAdmin(admin.ModelAdmin):
    model = Keyword
    extra = 0
    list_display = ('name', 'controlledVocabulary')

class ControlledVocabularyAdmin(admin.ModelAdmin):
    model = ControlledVocabulary
    extra = 0

class TopicCategoryAdmin(admin.ModelAdmin):
    model = TopicCategory
    extra = 10
    list_display = ('name', 'description')

#admin.site.register(ExceptHour)
admin.site.register(TimeslotDisplacer)
admin.site.register(CodeClass, CodeClassAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(GeneralMetadata, GeneralMetadataAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(ControlledVocabulary, ControlledVocabularyAdmin)
admin.site.register(TopicCategory, TopicCategoryAdmin)
