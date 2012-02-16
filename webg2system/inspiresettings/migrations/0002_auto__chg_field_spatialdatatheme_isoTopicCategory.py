# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'SpatialDataTheme.isoTopicCategory'
        db.alter_column('inspiresettings_spatialdatatheme', 'isoTopicCategory_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.TopicCategory'], null=True))


    def backwards(self, orm):
        
        # Changing field 'SpatialDataTheme.isoTopicCategory'
        db.alter_column('inspiresettings_spatialdatatheme', 'isoTopicCategory_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['systemsettings.TopicCategory']))


    models = {
        'inspiresettings.spatialdatatheme': {
            'Meta': {'object_name': 'SpatialDataTheme'},
            'annex': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isoTopicCategory': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.TopicCategory']", 'null': 'True', 'blank': 'True'}),
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
