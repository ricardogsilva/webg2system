# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Suite._path'
        db.delete_column('smssettings_suite', '_path')

        # Deleting field 'Task._parent'
        db.delete_column('smssettings_task', '_parent_id')

        # Adding field 'Task._family'
        db.add_column('smssettings_task', '_family', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Family'], null=True, blank=True), keep_default=False)

        # Deleting field 'Family._parent'
        db.delete_column('smssettings_family', '_parent_id')

        # Adding field 'Family._parent_family'
        db.add_column('smssettings_family', '_parent_family', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='smssettings_family_families', null=True, to=orm['smssettings.Family']), keep_default=False)


    def backwards(self, orm):
        
        # User chose to not deal with backwards NULL issues for 'Suite._path'
        raise RuntimeError("Cannot reverse this migration. 'Suite._path' and its values cannot be restored.")

        # Adding field 'Task._parent'
        db.add_column('smssettings_task', '_parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Family'], null=True, blank=True), keep_default=False)

        # Deleting field 'Task._family'
        db.delete_column('smssettings_task', '_family_id')

        # Adding field 'Family._parent'
        db.add_column('smssettings_family', '_parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='smssettings_family_children', null=True, to=orm['smssettings.Family'], blank=True), keep_default=False)

        # Deleting field 'Family._parent_family'
        db.delete_column('smssettings_family', '_parent_family_id')


    models = {
        'smssettings.family': {
            'Meta': {'object_name': 'Family'},
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            '_parent_family': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'smssettings_family_families'", 'null': 'True', 'to': "orm['smssettings.Family']"}),
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
            '_family': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.Family']", 'null': 'True', 'blank': 'True'}),
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            '_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'smssettings.taskvariable': {
            'Meta': {'object_name': 'TaskVariable'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.Task']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
