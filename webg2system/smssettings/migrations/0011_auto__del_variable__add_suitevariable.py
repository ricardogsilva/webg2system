# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Variable'
        db.delete_table('smssettings_variable')

        # Adding model 'SuiteVariable'
        db.create_table('smssettings_suitevariable', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('suite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Suite'])),
        ))
        db.send_create_signal('smssettings', ['SuiteVariable'])


    def backwards(self, orm):
        
        # Adding model 'Variable'
        db.create_table('smssettings_variable', (
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Suite'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('smssettings', ['Variable'])

        # Deleting model 'SuiteVariable'
        db.delete_table('smssettings_suitevariable')


    models = {
        'smssettings.smsserver': {
            'Meta': {'object_name': 'SMSServer'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'host_settings': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rpc_num': ('django.db.models.fields.IntegerField', [], {})
        },
        'smssettings.smstype': {
            'Meta': {'object_name': 'SMSType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'smssettings.suite': {
            'Meta': {'object_name': 'Suite'},
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            '_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sms_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.SMSType']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'smssettings.suitevariable': {
            'Meta': {'object_name': 'SuiteVariable'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'suite': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.Suite']"}),
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
