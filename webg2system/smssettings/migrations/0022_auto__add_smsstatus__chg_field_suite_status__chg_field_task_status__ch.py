# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SMSStatus'
        db.create_table('smssettings_smsstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('smssettings', ['SMSStatus'])

        # Renaming column for 'Suite.status' to match new field type.
        db.rename_column('smssettings_suite', 'status', 'status_id')
        # Changing field 'Suite.status'
        db.alter_column('smssettings_suite', 'status_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.SMSStatus']))

        # Adding index on 'Suite', fields ['status']
        db.create_index('smssettings_suite', ['status_id'])

        # Renaming column for 'Task.status' to match new field type.
        db.rename_column('smssettings_task', 'status', 'status_id')
        # Changing field 'Task.status'
        db.alter_column('smssettings_task', 'status_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.SMSStatus']))

        # Adding index on 'Task', fields ['status']
        db.create_index('smssettings_task', ['status_id'])

        # Renaming column for 'Family.status' to match new field type.
        db.rename_column('smssettings_family', 'status', 'status_id')
        # Changing field 'Family.status'
        db.alter_column('smssettings_family', 'status_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.SMSStatus']))

        # Adding index on 'Family', fields ['status']
        db.create_index('smssettings_family', ['status_id'])


    def backwards(self, orm):
        
        # Removing index on 'Family', fields ['status']
        db.delete_index('smssettings_family', ['status_id'])

        # Removing index on 'Task', fields ['status']
        db.delete_index('smssettings_task', ['status_id'])

        # Removing index on 'Suite', fields ['status']
        db.delete_index('smssettings_suite', ['status_id'])

        # Deleting model 'SMSStatus'
        db.delete_table('smssettings_smsstatus')

        # Renaming column for 'Suite.status' to match new field type.
        db.rename_column('smssettings_suite', 'status_id', 'status')
        # Changing field 'Suite.status'
        db.alter_column('smssettings_suite', 'status', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Renaming column for 'Task.status' to match new field type.
        db.rename_column('smssettings_task', 'status_id', 'status')
        # Changing field 'Task.status'
        db.alter_column('smssettings_task', 'status', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Renaming column for 'Family.status' to match new field type.
        db.rename_column('smssettings_family', 'status_id', 'status')
        # Changing field 'Family.status'
        db.alter_column('smssettings_family', 'status', self.gf('django.db.models.fields.CharField')(max_length=20))


    models = {
        'smssettings.family': {
            'Meta': {'object_name': 'Family'},
            '_family': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'smssettings_family_families'", 'null': 'True', 'to': "orm['smssettings.Family']"}),
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            '_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.SMSStatus']"})
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
        'smssettings.smsstatus': {
            'Meta': {'object_name': 'SMSStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'smssettings.suite': {
            'Meta': {'object_name': 'Suite'},
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'families': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['smssettings.Family']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.SMSStatus']"})
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
            '_family': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'smssettings_task_families'", 'null': 'True', 'to': "orm['smssettings.Family']"}),
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            '_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.SMSStatus']"})
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
