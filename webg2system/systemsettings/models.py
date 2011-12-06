from django.db import models

# TODO
#   - add a help_text attribute to all the fields that need one.
#   - integrate with python-south and try to get an easier database 
#   migration
#   - integrate with python-piston and expose a REST API for creating
#   packages.

class SourceSetting(models.Model):
    name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return '%s' % (self.name)

    def areas(self):
        '''
        Return a comma-separated string with areas associated with this source.
        '''
        
        return ', '.join([a.name for a in self.area_set.all()])

    def specific_names(self):
        '''
        Return a comma-separated string with specific names associated with this source.
        '''

        return ', '.join([sn.name for sn in self.specificsource_set.all()])


class SpecificSource(models.Model):
    name = models.CharField(max_length=100)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    sourceSetting = models.ForeignKey(SourceSetting)
       
    def __unicode__(self):
        return self.name


class Area(models.Model):
    name = models.CharField(max_length=100)
    sourceSetting = models.ForeignKey(SourceSetting)
    
    def __unicode__(self):
        return self.name


class HostSetting(models.Model):
    name = models.CharField(max_length=100)
    basePath = models.CharField(max_length=255)
    ip = models.IPAddressField()
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name
    

class ItemSetting(models.Model):
    name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.name


class MarkedString(models.Model):
    name = models.CharField(max_length=50, blank=True)
    string = models.CharField(max_length=255)
    marks = models.CharField(max_length=255, blank=True)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        if self.name == '':
            result = '%s : (%s)' % (self.string, self.marks)
        else:
            result = '%s - %s : (%s)' % (self.name, self.string, self.marks)
        return result
     

class SearchPath(MarkedString):

    class Meta:
        abstract = True


class SearchPattern(MarkedString):
    pass


class SourceExtraInfo(MarkedString):
    sourceSetting = models.ForeignKey(SourceSetting)


class PackageSetting(ItemSetting):
    relatedItems = models.ManyToManyField(ItemSetting, 
            through='PackageRelatedItemSetting',
            related_name='relatedItems_%(app_label)s_%(class)s_related')


class PackageWorkingDir(SearchPath):
    packageSetting = models.OneToOneField(PackageSetting)


class PackageOutputDir(SearchPath):
    packageSetting = models.ForeignKey(PackageSetting, null=True, blank=True)


class PackageInputDir(SearchPath):
    packageSetting = models.ForeignKey(PackageSetting, null=True, blank=True)


class PackageInternalDir(SearchPath):
    packageSetting = models.ForeignKey(PackageSetting, null=True, blank=True)


class FileSearchPath(SearchPath):
    fileSetting = models.ForeignKey('FileSetting')


class FileSearchPattern(SearchPattern):
    fileSetting = models.ForeignKey('FileSetting')


class Hour(models.Model):
    hour = models.IntegerField()
    
    def __unicode__(self):
        return str(self.hour)
    

class FileSetting(ItemSetting):
    '''
    Provides an unified class for the files handled in the G2system
    '''

    numFiles = models.IntegerField()
    fileType = models.CharField(max_length=10)
    frequency = models.CharField(max_length=10)
    toArchive = models.BooleanField(verbose_name='Archive')
    toCompress = models.BooleanField(verbose_name='Compress')
    toDisseminate = models.BooleanField(verbose_name='Disseminate')
    toCopy = models.BooleanField(verbose_name='Copy')
    exceptHours = models.ManyToManyField(Hour, blank=True, null=True)

    def search_paths(self):
        return ', '.join([str(path) for path in self.filesearchpath_set.all()])

    def search_patterns(self):
        return ', '.join([str(patt) for patt in self.filesearchpattern_set.all()])


class PackageRelatedItemSetting(models.Model):
    FILE_ROLE_CHOICES = (('input', 'input'), ('output', 'output'))
    packageSetting = models.ForeignKey(PackageSetting, help_text='A package '\
            'that will be the parent of this setting type.', 
            related_name='packageSetting_%(app_label)s_%(class)s_related',
            verbose_name='Package')
    relatedItemSetting = models.ForeignKey(ItemSetting, help_text='A file or '\
            'package that is to be related to this one.',
            related_name='relatedItemSetting_%(app_label)s_%(class)s_related',
            verbose_name='Related item')
    relatedItemRole = models.CharField(max_length=8, choices=FILE_ROLE_CHOICES, 
                                       verbose_name='Item role')
    specificAreas = models.ManyToManyField(Area, null=True, blank=True)

    def show_specific_areas(self):
        return unicode(', '.join([unicode(a) for a in self.specificAreas.all()]))
    show_specific_areas.short_description = 'Has specific areas?'

    def show_timeslot_displacements(self):
        return unicode(', '.join([unicode(a) for a in self.timeslotdisplacer_set.all()]))

    show_timeslot_displacements.short_description = 'Has displaced timeslots?'
    
    

class TimeslotDisplacer(models.Model):
    UNIT_CHOICES = (('day', 'day'),('minute', 'minute'))
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    value = models.IntegerField()
    packageRelatedItem = models.ForeignKey(PackageRelatedItemSetting)
    
    def __unicode__(self):
        return '%s %s' % (self.value, self.unit)
    

