from django.db import models

from inspiresettings.models import SpatialDataTheme, Collaborator, TopicCategory, Keyword, TopicCategory

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
    #web_server = models.BooleanField(default=False)

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
    product = models.ForeignKey('Product', null=True, blank=True)

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
    #product = models.ForeignKey('Product', null=True, blank=True)

    def get_except_hours(self):
        return ', '.join([str(h.hour) for h in self.exceptHours.all()])
    get_except_hours.short_description = 'Except hours'

    def get_search_paths(self):
        return ', '.join([str(p) for p in self.filepath_set.all()])
    get_search_paths.short_description = 'Search paths'

    def get_search_patterns(self):
        return ', '.join([str(p) for p in self.filepattern_set.all()])
    get_search_patterns.short_description = 'Search patterns'

    def get_package_outputs(self):
        packOutputs = self.packageoutput_set.all()
        return ', '.join([po.package.name for po in packOutputs])
    get_package_outputs.short_description = 'Output from packages'

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

    class Meta:
        verbose_name_plural = 'code classes'


    def __unicode__(self):
        return self.className

class Product(models.Model):
    #RESOURCE_TYPE_CHOICES = (('dataset', 'dataset'), 
    #                         ('series', 'series'), 
    #                         ('service', 'service'))
    OVERVIEW_TYPE_CHOICES = (('png', 'png'),)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)
    user_manual = models.CharField(
        max_length=255, help_text='Relative path to the user manual. ' \
        'The path is relative to the host\'s \'datapath\' attribute.'
    )
    originator_collaborator = models.ForeignKey(
            Collaborator,
            related_name='product_%(app_label)s_%(class)s_related',
            help_text='INSPIRE metadata. Point of contact in the '\
                      'organization responsible for the metadata.')
    principal_investigator = models.ForeignKey(Collaborator,
                                               help_text='INSPIRE metadata.')
    distributor = models.ForeignKey(Collaborator,
            help_text='INSPIRE metadata.',
            related_name='distributor_%(app_label)s_%(class)s_related')
    inspireKeyword = models.ForeignKey(SpatialDataTheme, 
                                       verbose_name='INSPIRE data theme')
    keywords = models.ManyToManyField(Keyword, null=True, blank=True)
    topicCategories = models.ManyToManyField(TopicCategory, null=True,
                                             verbose_name='ISO 19115 Topic '\
                                             'categories', blank=True,
                                             help_text='The topic categories'\
                                             ' chosen here will complement '\
                                             'the ones that already match '\
                                             'the selected INSPIRE data theme')
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
    #resource_type = models.CharField(max_length=20, help_text='INSPIRE '\
    #                                 'metadata element: Scope to which '\
    #                                 'metadata applies.',
    #                                 choices=RESOURCE_TYPE_CHOICES)
    iParentIdentifier = models.CharField(max_length=255, verbose_name='Parent'\
                                         ' Identifier', help_text='INSPIRE '\
                                         'metadata element: UUID of the '\
                                         'parent metadata series.')
    ireferenceSystemID = models.CharField(max_length=10, 
                                          verbose_name='Reference system '\
                                          'EPSG code', help_text='INSPIRE '\
                                          'metadata element: EPSG code of '\
                                          'coordinate reference system.')
    iCredit = models.TextField(verbose_name='Credit', help_text='INSPIRE '\
                               'metadata element: Product credit information.')
    graphic_overview_description = models.TextField(help_text='INSPIRE ' \
                                                    'metadata element: ' \
                                                    'Description of the ' \
                                                    'graphical overview '\
                                                    '(quicklook).')
    graphic_overview_type = models.CharField(max_length=10, 
                                             choices=OVERVIEW_TYPE_CHOICES,
                                             help_text='File format for the'\
                                             'quicklooks.')
    supplemental_info = models.CharField(max_length=255, help_text='INSPIRE '\
                                         'metadata element. URL for the '\
                                         'product page.')
    validation_report = models.CharField(max_length=255, help_text='INSPIRE '\
                                         'metadata element. URL for the '\
                                         'validation report.')
    lineage = models.TextField(help_text="INSPIRE metadata element. General "\
                               "explanation of the data producer's "\
                               "knowledge about the lineage of a dataset. "\
                               "Apart from describing the process history, "\
                               "the overall quality of the dataset (series) "\
                               "should be included in the Lineage metadata "\
                               "element. This statement should contain any "\
                               "quality information required for "\
                               "interoperability and/or valuable for use and "\
                               "evaluation of the data set (series).")
    sources = models.ManyToManyField(Source, help_text='Sources that are '\
                                     'used in the data fusion process for'\
                                     'generating this product.')
    temporal_extent = models.TextField(help_text='Description of the '\
                                       'temporal extent.')
    series_title = models.CharField(max_length=255, 
                                    help_text='Title for the dataset series.')
    SERIES_STATUS_CHOICES = (
        ('completed', 'completed'),
        ('historicalArchive', 'historicalArchive'),
        ('obsolete', 'obsolete'),
        ('onGoing', 'onGoing'),
        ('planned', 'planned'),
        ('required', 'required'),
        ('underdevelopment', 'underdevelopment'),
    )
    series_status = models.CharField(max_length=20, help_text='Status of the '\
                                     'dataset series.', 
                                     choices=SERIES_STATUS_CHOICES)

    def __unicode__(self):
        return self.short_name

class Dataset(models.Model):
    COVERAGE_CONTENT_TYPE_CHOICES = (
            ('image', 'image'), 
            ('thematicClassification', 'thematicClassification'), 
            ('physicalMeasurement', 'physicalMeasurement')
    )
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    isMainDataset = models.BooleanField(default=False)
    product = models.ForeignKey(Product)
    scalingFactor = models.IntegerField()
    missingValue = models.IntegerField()
    coverage_content_type = models.CharField(
            max_length=30, 
            help_text='INSPIRE metadata element: choices:<br />Image - '\
                    'Meaningful numerical representation of a physical '\
                    'parameter that is not the actual value of the physical '\
                    'parameter.<br />thematicClassification - code value with no '\
                    'quantitative meaning, used to represent a physical '\
                    'quantity.<br />physicalMeasurement - Value in physical '\
                    'units of the quantity being measured.',
            choices=COVERAGE_CONTENT_TYPE_CHOICES
    )
    max_value = models.IntegerField(default=0)
    min_value = models.IntegerField(default=0)
    bit_depth= models.IntegerField(default=16)

    def __unicode__(self):
        return self.name

class WebServer(models.Model):
    host = models.ForeignKey(Host)
    public_URL = models.CharField(max_length=255)

class CatalogueServer(models.Model):
    host = models.ForeignKey(Host)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=50)
    base_URL = models.CharField(max_length=255)
    csw_URI = models.CharField(max_length=255)
    login_URI = models.CharField(max_length=255)
    logout_URI = models.CharField(max_length=255)
