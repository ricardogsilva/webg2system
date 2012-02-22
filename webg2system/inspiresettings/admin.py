from models import *
from django.contrib import admin

class CollaboratorInline(admin.StackedInline):
    model = Collaborator
    extra = 0

class SpatialDataThemeAdmin(admin.ModelAdmin):
    radio_fields = {'annex' : admin.HORIZONTAL}
    model = SpatialDataTheme
    extra = 3
    list_display = ('name', 'annex', 'isoTopicCategory', 'description')

class TopicCategoryAdmin(admin.ModelAdmin):
    model = TopicCategory
    extra = 0
    list_display = ('name', 'description')

class KeywordAdmin(admin.ModelAdmin):
    model = Keyword
    extra = 0
    list_display = ('name', 'controlled_vocabulary', 'description')

class ControlledVocabularyAdmin(admin.ModelAdmin):
    model = ControlledVocabulary
    extra = 0

class OrganizationAdmin(admin.ModelAdmin):
    inlines = [CollaboratorInline]
    list_display = ('name', 'url')

admin.site.register(SpatialDataTheme, SpatialDataThemeAdmin)
admin.site.register(TopicCategory, TopicCategoryAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(ControlledVocabulary, ControlledVocabularyAdmin)
admin.site.register(Organization, OrganizationAdmin)
