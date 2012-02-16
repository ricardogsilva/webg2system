from models import *
from django.contrib import admin

class SpatialDataThemeAdmin(admin.ModelAdmin):
    radio_fields = {'annex' : admin.HORIZONTAL}
    model = SpatialDataTheme
    extra = 3
    list_display = ('name', 'annex', 'isoTopicCategory', 'description')

admin.site.register(SpatialDataTheme, SpatialDataThemeAdmin)
