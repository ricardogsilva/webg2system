# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Node._parent'
        db.alter_column('smssettings_node', '_parent_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['smssettings.Node']))


    def backwards(self, orm):
        
        # User chose to not deal with backwards NULL issues for 'Node._parent'
        raise RuntimeError("Cannot reverse this migration. 'Node._parent' and its values cannot be restored.")


    models = {
        'smssettings.node': {
            'Meta': {'object_name': 'Node'},
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            '_parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'my_parent'", 'null': 'True', 'to': "orm['smssettings.Node']"}),
            '_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sms_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smssettings.SMSType']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'suite': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'my_suite'", 'null': 'True', 'to': "orm['smssettings.Node']"})
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
