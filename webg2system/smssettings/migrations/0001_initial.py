# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SMSServer'
        db.create_table('smssettings_smsserver', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('rpc_num', self.gf('django.db.models.fields.IntegerField')()),
            ('base_path', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('is_running', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.Host'])),
        ))
        db.send_create_signal('smssettings', ['SMSServer'])


    def backwards(self, orm):
        
        # Deleting model 'SMSServer'
        db.delete_table('smssettings_smsserver')


    models = {
        'smssettings.smsserver': {
            'Meta': {'object_name': 'SMSServer'},
            'base_path': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_running': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
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
