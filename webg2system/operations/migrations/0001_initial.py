# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RunningPackage'
        db.create_table('operations_runningpackage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timeslot', self.gf('django.db.models.fields.DateTimeField')()),
            ('settings', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('area', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(default='stopped', max_length=50)),
            ('force', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('result', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('operations', ['RunningPackage'])


    def backwards(self, orm):
        # Deleting model 'RunningPackage'
        db.delete_table('operations_runningpackage')


    models = {
        'operations.runningpackage': {
            'Meta': {'ordering': "['-id']", 'object_name': 'RunningPackage'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'force': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'settings': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'stopped'", 'max_length': '50'}),
            'timeslot': ('django.db.models.fields.DateTimeField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['operations']