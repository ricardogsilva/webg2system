# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'FamilyVariable'
        db.delete_table('smssettings_familyvariable')

        # Deleting model 'Task'
        db.delete_table('smssettings_task')

        # Deleting model 'TaskVariable'
        db.delete_table('smssettings_taskvariable')

        # Deleting model 'SMSStatus'
        db.delete_table('smssettings_smsstatus')

        # Deleting model 'Repeat'
        db.delete_table('smssettings_repeat')

        # Deleting model 'Family'
        db.delete_table('smssettings_family')

        # Deleting model 'SuiteVariable'
        db.delete_table('smssettings_suitevariable')

        # Deleting field 'Suite.status'
        db.delete_column('smssettings_suite', 'status_id')

        # Deleting field 'Suite._name'
        db.delete_column('smssettings_suite', '_name')

        # Adding field 'Suite.name'
        db.add_column('smssettings_suite', 'name', self.gf('django.db.models.fields.CharField')(default='to be defined', unique=True, max_length=255), keep_default=False)

        # Adding field 'Suite.sms_representation'
        db.add_column('smssettings_suite', 'sms_representation', self.gf('django.db.models.fields.TextField')(default='suite blank\nendsuite'), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'FamilyVariable'
        db.create_table('smssettings_familyvariable', (
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('family', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Family'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('smssettings', ['FamilyVariable'])

        # Adding model 'Task'
        db.create_table('smssettings_task', (
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.SMSStatus'])),
            ('_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('_family', self.gf('django.db.models.fields.related.ForeignKey')(related_name='smssettings_task_families', null=True, to=orm['smssettings.Family'], blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_path', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('smssettings', ['Task'])

        # Adding model 'TaskVariable'
        db.create_table('smssettings_taskvariable', (
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Task'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('smssettings', ['TaskVariable'])

        # Adding model 'SMSStatus'
        db.create_table('smssettings_smsstatus', (
            ('status', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('smssettings', ['SMSStatus'])

        # Adding model 'Repeat'
        db.create_table('smssettings_repeat', (
            ('repeat_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('end', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('start', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('smssettings', ['Repeat'])

        # Adding model 'Family'
        db.create_table('smssettings_family', (
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.SMSStatus'])),
            ('_suite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Suite'], null=True, blank=True)),
            ('_path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('_family', self.gf('django.db.models.fields.related.ForeignKey')(related_name='smssettings_family_families', null=True, to=orm['smssettings.Family'], blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('repeat', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Repeat'], null=True, blank=True)),
            ('_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('smssettings', ['Family'])

        # Adding model 'SuiteVariable'
        db.create_table('smssettings_suitevariable', (
            ('suite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Suite'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('smssettings', ['SuiteVariable'])

        # Adding field 'Suite.status'
        db.add_column('smssettings_suite', 'status', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['smssettings.SMSStatus']), keep_default=False)

        # Adding field 'Suite._name'
        db.add_column('smssettings_suite', '_name', self.gf('django.db.models.fields.CharField')(default='to be defined', max_length=100), keep_default=False)

        # Deleting field 'Suite.name'
        db.delete_column('smssettings_suite', 'name')

        # Deleting field 'Suite.sms_representation'
        db.delete_column('smssettings_suite', 'sms_representation')


    models = {
        'smssettings.smsserver': {
            'Meta': {'object_name': 'SMSServer'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'host_settings': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rpc_num': ('django.db.models.fields.IntegerField', [], {})
        },
        'smssettings.suite': {
            'Meta': {'object_name': 'Suite'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'sms_representation': ('django.db.models.fields.TextField', [], {})
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
