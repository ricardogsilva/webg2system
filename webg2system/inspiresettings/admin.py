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

class OrganizationAdmin(admin.ModelAdmin):
    inlines = [CollaboratorInline]
    list_display = ('name', 'url')

admin.site.register(SpatialDataTheme, SpatialDataThemeAdmin)
admin.site.register(Organization, OrganizationAdmin)
