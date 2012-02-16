# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SpatialDataTheme'
        db.create_table('inspiresettings_spatialdatatheme', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('annex', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('isoTopicCategory', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.TopicCategory'])),
        ))
        db.send_create_signal('inspiresettings', ['SpatialDataTheme'])


    def backwards(self, orm):
        
        # Deleting model 'SpatialDataTheme'
        db.delete_table('inspiresettings_spatialdatatheme')


    models = {
        'inspiresettings.spatialdatatheme': {
            'Meta': {'object_name': 'SpatialDataTheme'},
            'annex': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isoTopicCategory': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.TopicCategory']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'systemsettings.topiccategory': {
            'Meta': {'object_name': 'TopicCategory'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['inspiresettings']
