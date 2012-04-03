# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'RunningPackage.host'
        db.delete_column('operations_runningpackage', 'host_id')

        # Adding field 'RunningPackage.timestamp'
        db.add_column('operations_runningpackage', 'timestamp', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 4, 3, 13, 43, 2, 55654)), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'RunningPackage.host'
        db.add_column('operations_runningpackage', 'host', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['systemsettings.Host']), keep_default=False)

        # Deleting field 'RunningPackage.timestamp'
        db.delete_column('operations_runningpackage', 'timestamp')


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
        'operations.runningpackage': {
            'Meta': {'object_name': 'RunningPackage'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Area']"}),
            'force': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'settings': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Package']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'stopped'", 'max_length': '50'}),
            'timeslot': ('django.db.models.fields.DateTimeField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        },
        'systemsettings.area': {
            'Meta': {'object_name': 'Area'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Source']"})
        },
        'systemsettings.codeclass': {
            'Meta': {'object_name': 'CodeClass'},
            'className': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'systemsettings.item': {
            'Meta': {'object_name': 'Item'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'systemsettings.package': {
            'Meta': {'object_name': 'Package', '_ormbases': ['systemsettings.Item']},
            'codeClass': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.CodeClass']"}),
            'inputs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inputs'", 'symmetrical': 'False', 'through': "orm['systemsettings.PackageInput']", 'to': "orm['systemsettings.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Product']", 'null': 'True', 'blank': 'True'})
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
        'systemsettings.timeslotdisplacer': {
            'Meta': {'object_name': 'TimeslotDisplacer'},
            'endValue': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'startValue': ('django.db.models.fields.IntegerField', [], {}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['operations']
