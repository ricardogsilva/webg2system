# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Node'
        db.delete_table('smssettings_node')

        # Adding model 'Suite'
        db.create_table('smssettings_suite', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('_parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='smssettings_suite_children', null=True, to=orm['smssettings.Suite'])),
            ('_path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('sms_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.SMSType'])),
        ))
        db.send_create_signal('smssettings', ['Suite'])

        # Changing field 'Variable.node'
        db.alter_column('smssettings_variable', 'node_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Suite']))


    def backwards(self, orm):
        
        # Adding model 'Node'
        db.create_table('smssettings_node', (
            ('status', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('sms_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.SMSType'])),
            ('_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('_parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='my_parent', null=True, to=orm['smssettings.Node'], blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_path', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('smssettings', ['Node'])

        # Deleting model 'Suite'
        db.delete_table('smssettings_suite')

        # Changing field 'Variable.node'
        db.alter_column('smssettings_variable', 'node_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smssettings.Node']))


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
            '_parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'smssettings_suite_children'", 'null': 'True', 'to': "orm['smssettings.Suite']"}),
            '_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sms_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.SMSType']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'smssettings.variable': {
            'Meta': {'object_name': 'Variable'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.Suite']"}),
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
