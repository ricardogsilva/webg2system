# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'SMSServer.name'
        db.delete_column('smssettings_smsserver', 'name')

        # Deleting field 'SMSServer.is_running'
        db.delete_column('smssettings_smsserver', 'is_running')

        # Deleting field 'SMSServer.host'
        db.delete_column('smssettings_smsserver', 'host_id')

        # Adding field 'SMSServer.alias'
        db.add_column('smssettings_smsserver', 'alias', self.gf('django.db.models.fields.CharField')(default='to be filled', max_length=100), keep_default=False)

        # Adding field 'SMSServer._is_running'
        db.add_column('smssettings_smsserver', '_is_running', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'SMSServer.host_settings'
        db.add_column('smssettings_smsserver', 'host_settings', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['systemsettings.Host']), keep_default=False)


    def backwards(self, orm):
        
        # User chose to not deal with backwards NULL issues for 'SMSServer.name'
        raise RuntimeError("Cannot reverse this migration. 'SMSServer.name' and its values cannot be restored.")

        # Adding field 'SMSServer.is_running'
        db.add_column('smssettings_smsserver', 'is_running', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # User chose to not deal with backwards NULL issues for 'SMSServer.host'
        raise RuntimeError("Cannot reverse this migration. 'SMSServer.host' and its values cannot be restored.")

        # Deleting field 'SMSServer.alias'
        db.delete_column('smssettings_smsserver', 'alias')

        # Deleting field 'SMSServer._is_running'
        db.delete_column('smssettings_smsserver', '_is_running')

        # Deleting field 'SMSServer.host_settings'
        db.delete_column('smssettings_smsserver', 'host_settings_id')


    models = {
        'smssettings.smsserver': {
            'Meta': {'object_name': 'SMSServer'},
            '_is_running': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'base_path': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'host_settings': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rpc_num': ('django.db.models.fields.IntegerField', [], {})
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
