import pycountry

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

class Organization(models.Model):
    COUNTRY_CHOICES = [(c.alpha2, c.name) for c in pycountry.countries]
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    streetAddress = models.CharField(max_length=255, 
                                     verbose_name='Street Address')
    postalCode = models.CharField(max_length=20, 
                                  verbose_name='Postal Code')
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)

    def __unicode__(self):
        return self.name

class Collaborator(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    organization = models.ForeignKey(Organization)

    def __unicode__(self):
        return self.name

