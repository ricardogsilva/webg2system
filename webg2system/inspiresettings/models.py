from django.db import models

class SpatialDataTheme(models.Model):
    ANNEX_CHOICES = (('A.I', 'A.I'), 
                     ('A.II', 'A.II'), 
                     ('A.III', 'A.III'))
    name = models.CharField(max_length=100, help_text='Name defined in '\
                            'INSPIRE Directive')
    description = models.TextField(null=True, blank=True)
    annex = models.CharField(max_length=5, choices=ANNEX_CHOICES)
    isoTopicCategory = models.ForeignKey('systemsettings.TopicCategory',
                                         null=True, blank=True,
                                         verbose_name='ISO 19115 Topic '\
                                         'Category')

    def __unicode__(self):
        return self.name

