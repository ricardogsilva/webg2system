# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'SpatialDataTheme.isoTopicCategory'
        db.alter_column('inspiresettings_spatialdatatheme', 'isoTopicCategory_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inspiresettings.TopicCategory'], null=True))


    def backwards(self, orm):
        
        # Changing field 'SpatialDataTheme.isoTopicCategory'
        db.alter_column('inspiresettings_spatialdatatheme', 'isoTopicCategory_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.TopicCategory'], null=True))


    models = {
        'inspiresettings.collaborator': {
            'Meta': {'object_name': 'Collaborator'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inspiresettings.Organization']"})
        },
        'inspiresettings.organization': {
            'Meta': {'object_name': 'Organization'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'postalCode': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'streetAddress': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'inspiresettings.spatialdatatheme': {
            'Meta': {'object_name': 'SpatialDataTheme'},
            'annex': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isoTopicCategory': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inspiresettings.TopicCategory']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'inspiresettings.topiccategory': {
            'Meta': {'object_name': 'TopicCategory'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['inspiresettings']
