from django.db import models

# TODO
#   - add a help_text attribute to all the fields that need one.
#   - bring back the TimeslotDisplacer class and add a foreign key to 
#   the inputs and outputs to it.
#   - integrate with python-piston and expose a REST API for creating
#   packages.

class Host(models.Model):
    name = models.CharField(max_length=100)
    basePath = models.CharField(max_length=255)
    ip = models.IPAddressField()
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

class MarkedString(models.Model):
    name = models.CharField(max_length=50, blank=True)
    string = models.CharField(max_length=255)
    marks = models.CharField(max_length=255, blank=True)
    
    def __unicode__(self):
        if self.name == '':
            result = '%s : (%s)' % (self.string, self.marks)
        else:
            result = '%s - %s : (%s)' % (self.name, self.string, self.marks)
        return result

class FilePath(MarkedString):
    theFile = models.ForeignKey('File')

class FilePattern(MarkedString):
    theFile = models.ForeignKey('File')

class PackagePath(MarkedString):
    package = models.ForeignKey('Package')

class ExceptHour(models.Model):
    hour = models.IntegerField()
    
    def __unicode__(self):
        return str(self.hour)

class Item(models.Model):
    name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.name

class Package(Item):
    codeClass = models.CharField(max_length=50, verbose_name='Code class')
    version = models.CharField(max_length=10)
    inputs = models.ManyToManyField(Item, through='PackageInput',
                                    related_name='inputs')

    def get_inputs(self):
        return ', '.join([str(i) for i in self.inputs.all()])
    get_inputs.short_description = 'Inputs'

    def get_outputs(self):
        return ', '.join([str(i) for i in self.outputs.all()])
    get_outputs.short_description = 'Outputs'

class File(Item):
    numFiles = models.IntegerField()
    fileType = models.CharField(max_length=10)
    frequency = models.CharField(max_length=10)
    toArchive = models.BooleanField(verbose_name='Archive')
    toCompress = models.BooleanField(verbose_name='Compress')
    toDisseminate = models.BooleanField(verbose_name='Disseminate')
    toCopy = models.BooleanField(verbose_name='Copy')
    exceptHours = models.ManyToManyField(ExceptHour)

    def get_except_hours(self):
        return ', '.join([str(h.hour) for h in self.exceptHours.all()])
    get_except_hours.short_description = 'Except hours'

    def get_search_paths(self):
        return ', '.join([str(p) for p in self.filepath_set.all()])
    get_search_paths.short_description = 'Search paths'

    def get_search_patterns(self):
        return ', '.join([str(p) for p in self.filepattern_set.all()])
    get_search_patterns.short_description = 'Search patterns'

class PackageInput(models.Model):
    package = models.ForeignKey(Package, help_text='A package '\
            'that will be the parent of this setting type.', 
            related_name='packageInput_%(app_label)s_%(class)s_related',
            verbose_name='Package')
    inputItem = models.ForeignKey(Item, help_text='A file or '\
            'package that is to be related to this one.',
            related_name='inputItem_%(app_label)s_%(class)s_related',
            verbose_name='input item')
    specificAreas = models.ManyToManyField('Area', null=True, blank=True)

class PackageOutput(models.Model):
    package = models.ForeignKey(Package, related_name='packageOutput_%(app_label)s_%(class)s_related')
    outputItem = models.ForeignKey(Item)
    specificAreas = models.ManyToManyField('Area', null=True, blank=True)
    specificTimeslots = models.ManyToManyField('TimeslotDisplacer', null=True, 
                                               blank=True, verbose_name='timeslots')

class Source(models.Model):
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

class SourceExtraInfo(MarkedString):
    source = models.ForeignKey(Source)

class SpecificSource(models.Model):
    name = models.CharField(max_length=100)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    source = models.ForeignKey(Source)
       
    def __unicode__(self):
        return self.name

class Area(models.Model):
    name = models.CharField(max_length=100)
    source = models.ForeignKey(Source)
    
    def __unicode__(self):
        return self.name

class TimeslotDisplacer(models.Model):
    UNIT_CHOICES = (('day', 'day'), ('hour', 'hour'), ('minute', 'minute'))
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    startValue = models.IntegerField(verbose_name='Start value', 
                                     help_text='The starting value for the '\
                                     'displaced timeslots.')
    endValue = models.IntegerField(verbose_name='End value', 
                                     help_text='The ending value for the '\
                                     'displaced timeslots. It is not '\
                                     'included in the calculation.')

    def __unicode__(self):
        return '%s <= %s < %s' % (self.startValue, self.unit, self.endValue)
