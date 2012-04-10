# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'CatalogueServer.public_URL'
        db.delete_column('systemsettings_catalogueserver', 'public_URL')

        # Adding field 'CatalogueServer.base_URL'
        db.add_column('systemsettings_catalogueserver', 'base_URL', self.gf('django.db.models.fields.CharField')(default='to be specified', max_length=255), keep_default=False)

        # Adding field 'CatalogueServer.login_URI'
        db.add_column('systemsettings_catalogueserver', 'login_URI', self.gf('django.db.models.fields.CharField')(default='to be specified', max_length=255), keep_default=False)

        # Adding field 'CatalogueServer.logout_URI'
        db.add_column('systemsettings_catalogueserver', 'logout_URI', self.gf('django.db.models.fields.CharField')(default='to be specified', max_length=255), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'CatalogueServer.public_URL'
        db.add_column('systemsettings_catalogueserver', 'public_URL', self.gf('django.db.models.fields.CharField')(default='to be specified', max_length=255), keep_default=False)

        # Deleting field 'CatalogueServer.base_URL'
        db.delete_column('systemsettings_catalogueserver', 'base_URL')

        # Deleting field 'CatalogueServer.login_URI'
        db.delete_column('systemsettings_catalogueserver', 'login_URI')

        # Deleting field 'CatalogueServer.logout_URI'
        db.delete_column('systemsettings_catalogueserver', 'logout_URI')


    models = {
        'inspiresettings.collaborator': {
            'Meta': {'object_name': 'Collaborator'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inspiresettings.Organization']"})
        },
        'inspiresettings.controlledvocabulary': {
            'Meta': {'object_name': 'ControlledVocabulary'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'date_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'inspiresettings.keyword': {
            'Meta': {'object_name': 'Keyword'},
            'controlled_vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inspiresettings.ControlledVocabulary']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'inspiresettings.organization': {
            'Meta': {'object_name': 'Organization'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'postalCode': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'streetAddress': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'inspiresettings.spatialdatatheme': {
            'Meta': {'object_name': 'SpatialDataTheme'},
            'annex': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isoTopicCategory': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inspiresettings.TopicCategory']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'inspiresettings.topiccategory': {
            'Meta': {'object_name': 'TopicCategory'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'systemsettings.area': {
            'Meta': {'object_name': 'Area'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Source']"})
        },
        'systemsettings.catalogueserver': {
            'Meta': {'object_name': 'CatalogueServer'},
            'base_URL': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login_URI': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'logout_URI': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.codeclass': {
            'Meta': {'object_name': 'CodeClass'},
            'className': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'systemsettings.dataset': {
            'Meta': {'object_name': 'Dataset'},
            'bit_depth': ('django.db.models.fields.IntegerField', [], {'default': '16'}),
            'coverage_content_type': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isMainDataset': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'max_value': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'min_value': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'missingValue': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Product']"}),
            'scalingFactor': ('django.db.models.fields.IntegerField', [], {}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        },
        'systemsettings.excepthour': {
            'Meta': {'object_name': 'ExceptHour'},
            'hour': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'systemsettings.file': {
            'Meta': {'object_name': 'File', '_ormbases': ['systemsettings.Item']},
            'exceptHours': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['systemsettings.ExceptHour']", 'symmetrical': 'False', 'blank': 'True'}),
            'fileType': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'frequency': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'numFiles': ('django.db.models.fields.IntegerField', [], {}),
            'specificArchives': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.Host']", 'null': 'True', 'blank': 'True'}),
            'toArchive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'toCompress': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'toCopy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'toDisseminate': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'systemsettings.fileextrainfo': {
            'Meta': {'object_name': 'FileExtraInfo', '_ormbases': ['systemsettings.MarkedString']},
            'markedstring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.MarkedString']", 'unique': 'True', 'primary_key': 'True'}),
            'theFile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.File']"})
        },
        'systemsettings.filepath': {
            'Meta': {'object_name': 'FilePath', '_ormbases': ['systemsettings.MarkedString']},
            'markedstring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.MarkedString']", 'unique': 'True', 'primary_key': 'True'}),
            'theFile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.File']"})
        },
        'systemsettings.filepattern': {
            'Meta': {'object_name': 'FilePattern', '_ormbases': ['systemsettings.MarkedString']},
            'markedstring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.MarkedString']", 'unique': 'True', 'primary_key': 'True'}),
            'theFile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.File']"})
        },
        'systemsettings.host': {
            'Meta': {'object_name': 'Host'},
            'codePath': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'dataPath': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'systemsettings.item': {
            'Meta': {'object_name': 'Item'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'systemsettings.markedstring': {
            'Meta': {'object_name': 'MarkedString'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.package': {
            'Meta': {'object_name': 'Package', '_ormbases': ['systemsettings.Item']},
            'codeClass': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.CodeClass']"}),
            'inputs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inputs'", 'symmetrical': 'False', 'through': "orm['systemsettings.PackageInput']", 'to': "orm['systemsettings.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Product']", 'null': 'True', 'blank': 'True'})
        },
        'systemsettings.packageextrainfo': {
            'Meta': {'object_name': 'PackageExtraInfo', '_ormbases': ['systemsettings.MarkedString']},
            'markedstring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.MarkedString']", 'unique': 'True', 'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Package']"})
        },
        'systemsettings.packageinput': {
            'Meta': {'object_name': 'PackageInput'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inputItem': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inputItem_systemsettings_packageinput_related'", 'to': "orm['systemsettings.Item']"}),
            'optional': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packageInput_systemsettings_packageinput_related'", 'to': "orm['systemsettings.Package']"}),
            'specificAreas': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.Area']", 'null': 'True', 'blank': 'True'}),
            'specificTimeslots': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.TimeslotDisplacer']", 'null': 'True', 'blank': 'True'})
        },
        'systemsettings.packageoutput': {
            'Meta': {'object_name': 'PackageOutput'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'optional': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'outputItem': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Item']"}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packageOutput_systemsettings_packageoutput_related'", 'to': "orm['systemsettings.Package']"}),
            'specificAreas': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.Area']", 'null': 'True', 'blank': 'True'}),
            'specificTimeslots': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.TimeslotDisplacer']", 'null': 'True', 'blank': 'True'})
        },
        'systemsettings.packagepath': {
            'Meta': {'object_name': 'PackagePath', '_ormbases': ['systemsettings.MarkedString']},
            'markedstring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.MarkedString']", 'unique': 'True', 'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Package']"})
        },
        'systemsettings.product': {
            'Meta': {'object_name': 'Product'},
            'distributor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'distributor_systemsettings_product_related'", 'to': "orm['inspiresettings.Collaborator']"}),
            'graphic_overview_description': ('django.db.models.fields.TextField', [], {}),
            'graphic_overview_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'iCredit': ('django.db.models.fields.TextField', [], {}),
            'iOtherDetails': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'iParentIdentifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'iResourceAbstract': ('django.db.models.fields.TextField', [], {}),
            'iResourceTitle': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inspireKeyword': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inspiresettings.SpatialDataTheme']"}),
            'ireferenceSystemID': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['inspiresettings.Keyword']", 'null': 'True', 'blank': 'True'}),
            'lineage': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'originator_collaborator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'product_systemsettings_product_related'", 'to': "orm['inspiresettings.Collaborator']"}),
            'pixelSize': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '4', 'decimal_places': '2'}),
            'principal_investigator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inspiresettings.Collaborator']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'sources': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['systemsettings.Source']", 'symmetrical': 'False'}),
            'supplemental_info': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'temporal_extent': ('django.db.models.fields.TextField', [], {}),
            'topicCategories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['inspiresettings.TopicCategory']", 'null': 'True', 'blank': 'True'}),
            'validation_report': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.source': {
            'Meta': {'object_name': 'Source'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'systemsettings.sourceextrainfo': {
            'Meta': {'object_name': 'SourceExtraInfo', '_ormbases': ['systemsettings.MarkedString']},
            'markedstring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.MarkedString']", 'unique': 'True', 'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Source']"})
        },
        'systemsettings.specificsource': {
            'Meta': {'object_name': 'SpecificSource'},
            'endDate': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Source']"}),
            'startDate': ('django.db.models.fields.DateTimeField', [], {})
        },
        'systemsettings.timeslotdisplacer': {
            'Meta': {'object_name': 'TimeslotDisplacer'},
            'endValue': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'startValue': ('django.db.models.fields.IntegerField', [], {}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'systemsettings.webserver': {
            'Meta': {'object_name': 'WebServer'},
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public_URL': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['systemsettings']
