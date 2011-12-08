# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'RunningPackage.status'
        db.add_column('operations_runningpackage', 'status', self.gf('django.db.models.fields.CharField')(default='stopped', max_length=50), keep_default=False)

        # Adding field 'RunningPackage.result'
        db.add_column('operations_runningpackage', 'result', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'RunningPackage.status'
        db.delete_column('operations_runningpackage', 'status')

        # Deleting field 'RunningPackage.result'
        db.delete_column('operations_runningpackage', 'result')


    models = {
        'operations.runningpackage': {
            'Meta': {'object_name': 'RunningPackage'},
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'settings': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Package']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Source']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'stopped'", 'max_length': '50'}),
            'timeslot': ('django.db.models.fields.DateTimeField', [], {})
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
        'systemsettings.host': {
            'Meta': {'object_name': 'Host'},
            'basePath': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
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
        'systemsettings.package': {
            'Meta': {'object_name': 'Package', '_ormbases': ['systemsettings.Item']},
            'codeClass': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.CodeClass']"}),
            'inputs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inputs'", 'symmetrical': 'False', 'through': "orm['systemsettings.PackageInput']", 'to': "orm['systemsettings.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'systemsettings.packageinput': {
            'Meta': {'object_name': 'PackageInput'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inputItem': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inputItem_systemsettings_packageinput_related'", 'to': "orm['systemsettings.Item']"}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packageInput_systemsettings_packageinput_related'", 'to': "orm['systemsettings.Package']"}),
            'specificAreas': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.Area']", 'null': 'True', 'blank': 'True'})
        },
        'systemsettings.source': {
            'Meta': {'object_name': 'Source'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['operations']
