from django.db import models

# TODO
#   - add a help_text attribute to all the fields that need one.
#   - integrate with python-piston and expose a REST API for creating
#   packages.

class Host(models.Model):
    name = models.CharField(max_length=100)
    dataPath = models.CharField(max_length=255, help_text='Full path to'\
                                ' the parent directory that holds the data.')
    codePath = models.CharField(max_length=255, null=True, blank=True, 
                                help_text='Full path to the parent directory'\
                                'that holds for the external code.')
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
    codeClass = models.ForeignKey('CodeClass')
    inputs = models.ManyToManyField(Item, through='PackageInput',
                                    related_name='inputs')

    def get_inputs(self):
        return ', '.join([str(i) for i in self.inputs.all()])
    get_inputs.short_description = 'Inputs'

    #FIXME
    def get_outputs(self):
        outs = [o.outputItem.name for o in self.packageOutput_systemsettings_packageoutput_related.all()]
        return ', '.join(outs)
    get_outputs.short_description = 'Outputs'

class File(Item):
    numFiles = models.IntegerField()
    fileType = models.CharField(max_length=10)
    frequency = models.CharField(max_length=10)
    toArchive = models.BooleanField(verbose_name='Archive')
    toCompress = models.BooleanField(verbose_name='Compress')
    toDisseminate = models.BooleanField(verbose_name='Disseminate')
    toCopy = models.BooleanField(verbose_name='Copy')
    exceptHours = models.ManyToManyField(ExceptHour, blank=True)
    specificArchives = models.ManyToManyField(Host, null=True, blank=True,
                                              help_text='What hosts should '\
                                              'be considered to be archives '\
                                              'for this file? Leave this '\
                                              'blank if you want to search '\
                                              'all the archives.', 
                                              verbose_name='Specific archives')
    product = models.ForeignKey('Product', null=True, blank=True)

    def get_except_hours(self):
        return ', '.join([str(h.hour) for h in self.exceptHours.all()])
    get_except_hours.short_description = 'Except hours'

    def get_search_paths(self):
        return ', '.join([str(p) for p in self.filepath_set.all()])
    get_search_paths.short_description = 'Search paths'

    def get_search_patterns(self):
        return ', '.join([str(p) for p in self.filepattern_set.all()])
    get_search_patterns.short_description = 'Search patterns'

    def get_package_output(self):
        return self.packageoutput_set.get().package.name
    get_package_output.short_description = 'Output from package'

    def get_package_inputs(self):
        packInputs = self.inputItem_systemsettings_packageinput_related.all()
        return ', '.join([pi.package.name for pi in packInputs])
    get_package_inputs.short_description = 'Input to packages'

class FileExtraInfo(MarkedString):
    theFile = models.ForeignKey(File)

class PackageInput(models.Model):
    package = models.ForeignKey(Package, help_text='A package '\
            'that will be the parent of this setting type.', 
            related_name='packageInput_%(app_label)s_%(class)s_related',
            verbose_name='Package')
    inputItem = models.ForeignKey(Item, help_text='A file or '\
            'package that is to be related to this one.',
            related_name='inputItem_%(app_label)s_%(class)s_related',
            verbose_name='input item')
    optional = models.BooleanField(default=False)
    specificAreas = models.ManyToManyField('Area', null=True, blank=True)
    specificTimeslots = models.ManyToManyField('TimeslotDisplacer', null=True, 
                                               blank=True, verbose_name='timeslots')

class PackageOutput(models.Model):
    package = models.ForeignKey(Package, related_name='packageOutput_%(app_label)s_%(class)s_related')
    outputItem = models.ForeignKey(Item)
    optional = models.BooleanField(default=False)
    specificAreas = models.ManyToManyField('Area', null=True, blank=True)
    specificTimeslots = models.ManyToManyField('TimeslotDisplacer', null=True, 
                                               blank=True, verbose_name='timeslots')

class PackageExtraInfo(MarkedString):
    package = models.ForeignKey(Package)

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
    source = models.ForeignKey(Source)
    name = models.CharField(max_length=100)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    number = models.IntegerField(null=True, blank=True)
       
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
        return '%s <= %s <= %s' % (self.startValue, self.unit, self.endValue)

class CodeClass(models.Model):
    className = models.CharField(max_length=100, verbose_name='Class')
    description = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.className

class Product(models.Model):
    RESOURCE_TYPE_CHOICES = (('dataset', 'dataset'), 
                             ('series', 'series'), 
                             ('service', 'service'))
    name = models.CharField(max_length=100)
    shortName = models.CharField(max_length=20, verbose_name='Short name')
    originatorOrganization = models.ForeignKey(
            'GeneralMetadata', 
            related_name='product_%(app_label)s_%(class)s_related',
            verbose_name='Originator organization', 
            help_text='INSPIRE metadata.')
    principalInvestigatorOrganization = models.ForeignKey(
            'GeneralMetadata',
            verbose_name='Principal investigator organization',
            help_text='INSPIRE metadata.')
    keywords = models.ManyToManyField('Keyword')
    topicCategories = models.ManyToManyField('TopicCategory', 
                                             verbose_name='ISO 19115 Topic '\
                                             'categories')
    #description = models.TextField(null=True, blank=True)
    #nRows = models.IntegerField(default=0, verbose_name='Number of rows')
    #nCols = models.IntegerField(default=0, verbose_name='Number of columns')
    pixelSize = models.DecimalField(max_digits=4, decimal_places=2, default=0,
                                    verbose_name='Pixel size')
    iResourceTitle = models.CharField(max_length=255, 
                                      verbose_name='Resource title',
                                      help_text='INSPIRE metadata element: '\
                                      'Name by which the cited resource is '\
                                      'known.')
    iResourceAbstract = models.TextField(verbose_name='Resource abstract', 
                                      help_text='INSPIRE metadata element: '\
                                      'Brief narrative summary of the '\
                                      'contents of the resource(s).')
    iResourceType = models.CharField(max_length=20, verbose_name='Resource type', 
                                      help_text='INSPIRE metadata element: '\
                                      'Scope to which metadata applies.',
                                      choices=RESOURCE_TYPE_CHOICES)
    iParentIdentifier = models.CharField(max_length=255, verbose_name='Parent'\
                                         ' Identifier', help_text='INSPIRE '\
                                         'metadata element: UUID of the '\
                                         'parent metadata series.')
    ireferenceSystemID = models.CharField(max_length=10, 
                                          verbose_name='Reference system '\
                                          'EPSG code', help_text='INSPIRE '\
                                          'metadata element: EPSG code of '\
                                          'coordinate reference system.')
    iOtherDetails = models.CharField(max_length=255, verbose_name='Other '\
                                     'details', help_text='INSPIRE '\
                                     'metadata element: URL for the PUM.',
                                     null=True, blank=True)
    iCredit = models.TextField(verbose_name='Credit', help_text='INSPIRE '\
                               'metadata element: Product credit information.')

    def __unicode__(self):
        return self.shortName

class Dataset(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    isMainDataset = models.BooleanField(default=False)
    product = models.ForeignKey(Product)
    scalingFactor = models.IntegerField()
    missingValue = models.IntegerField()

    def __unicode__(self):
        return self.name

class GeneralMetadata(models.Model):
    orgName = models.CharField(max_length=255, verbose_name='Organization name')
    orgURL = models.CharField(max_length=255, verbose_name='Organization URL')
    orgStreetAddress = models.CharField(max_length=255, 
                                        verbose_name='Organization street '\
                                        'address')
    orgPostalCode = models.CharField(max_length=20, 
                                     verbose_name='Organization postal code')
    orgCity = models.CharField(max_length=100, verbose_name='Organization city')
    contactName = models.CharField(max_length=100, verbose_name='Contact name')
    contactEmail = models.EmailField(verbose_name='Contact e-mail')
    
    def __unicode__(self):
        return self.orgName
        
class Keyword(models.Model):
    name = models.CharField(max_length=100)
    controlledVocabulary = models.ForeignKey('ControlledVocabulary', 
                                             null=True, blank=True, 
                                             verbose_name='Controlled '\
                                             'vocabulary')
    description = models.TextField(null=True, blank=True)
    
    def __unicode__(self):
        return self.name

class ControlledVocabulary(models.Model):
    title = models.CharField(max_length=100)
    dateType = models.CharField(max_length=100)
    date = models.DateField()

    class Meta:
        verbose_name_plural = 'controlled vocabularies'
    
    def __unicode__(self):
        return self.title

class TopicCategory(models.Model):
    name = models.CharField(max_length=100, help_text='ISO 19115 topic '\
                            'category')
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'topic categories'
    
    def __unicode__(self):
        return self.name
