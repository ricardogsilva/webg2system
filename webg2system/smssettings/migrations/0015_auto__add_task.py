# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Task'
        db.create_table('smssettings_task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('_path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('_parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Family'], null=True, blank=True)),
        ))
        db.send_create_signal('smssettings', ['Task'])


    def backwards(self, orm):
        
        # Deleting model 'Task'
        db.delete_table('smssettings_task')


    models = {
        'smssettings.family': {
            'Meta': {'object_name': 'Family'},
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            '_parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'smssettings_family_children'", 'null': 'True', 'to': "orm['smssettings.Family']"}),
            '_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'suite': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.Suite']", 'null': 'True', 'blank': 'True'})
        },
        'smssettings.familyvariable': {
            'Meta': {'object_name': 'FamilyVariable'},
            'family': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.Family']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'smssettings.smsserver': {
            'Meta': {'object_name': 'SMSServer'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'host_settings': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rpc_num': ('django.db.models.fields.IntegerField', [], {})
        },
        'smssettings.suite': {
            'Meta': {'object_name': 'Suite'},
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            '_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'smssettings.suitevariable': {
            'Meta': {'object_name': 'SuiteVariable'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'suite': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.Suite']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'smssettings.task': {
            'Meta': {'object_name': 'Task'},
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            '_parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.Family']", 'null': 'True', 'blank': 'True'}),
            '_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'})
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
        }
    }

    complete_apps = ['smssettings']
