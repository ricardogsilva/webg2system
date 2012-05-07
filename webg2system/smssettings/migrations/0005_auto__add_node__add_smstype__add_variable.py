# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Node'
        db.create_table('smssettings_node', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('_parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='my_parent', to=orm['smssettings.Node'])),
            ('_path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('suite', self.gf('django.db.models.fields.related.ForeignKey')(related_name='my_suite', to=orm['smssettings.Node'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('sms_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.SMSType'])),
        ))
        db.send_create_signal('smssettings', ['Node'])

        # Adding model 'SMSType'
        db.create_table('smssettings_smstype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('smssettings', ['SMSType'])

        # Adding model 'Variable'
        db.create_table('smssettings_variable', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Node'])),
        ))
        db.send_create_signal('smssettings', ['Variable'])


    def backwards(self, orm):
        
        # Deleting model 'Node'
        db.delete_table('smssettings_node')

        # Deleting model 'SMSType'
        db.delete_table('smssettings_smstype')

        # Deleting model 'Variable'
        db.delete_table('smssettings_variable')


    models = {
        'smssettings.node': {
            'Meta': {'object_name': 'Node'},
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            '_parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'my_parent'", 'to': "orm['smssettings.Node']"}),
            '_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sms_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.SMSType']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'suite': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'my_suite'", 'to': "orm['smssettings.Node']"})
        },
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
        'smssettings.variable': {
            'Meta': {'object_name': 'Variable'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.Node']"}),
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
