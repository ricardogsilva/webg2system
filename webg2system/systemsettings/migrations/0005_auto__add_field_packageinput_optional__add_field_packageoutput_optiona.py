# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'PackageInput.optional'
        db.add_column('systemsettings_packageinput', 'optional', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding M2M table for field specificTimeslots on 'PackageInput'
        db.create_table('systemsettings_packageinput_specificTimeslots', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('packageinput', models.ForeignKey(orm['systemsettings.packageinput'], null=False)),
            ('timeslotdisplacer', models.ForeignKey(orm['systemsettings.timeslotdisplacer'], null=False))
        ))
        db.create_unique('systemsettings_packageinput_specificTimeslots', ['packageinput_id', 'timeslotdisplacer_id'])

        # Adding field 'PackageOutput.optional'
        db.add_column('systemsettings_packageoutput', 'optional', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'PackageInput.optional'
        db.delete_column('systemsettings_packageinput', 'optional')

        # Removing M2M table for field specificTimeslots on 'PackageInput'
        db.delete_table('systemsettings_packageinput_specificTimeslots')

        # Deleting field 'PackageOutput.optional'
        db.delete_column('systemsettings_packageoutput', 'optional')


    models = {
        'systemsettings.area': {
            'Meta': {'object_name': 'Area'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Source']"})
        },
        'systemsettings.codeclass': {
            'Meta': {'object_name': 'CodeClass'},
            'className': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'systemsettings.excepthour': {
            'Meta': {'object_name': 'ExceptHour'},
            'hour': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'systemsettings.file': {
            'Meta': {'object_name': 'File', '_ormbases': ['systemsettings.Item']},
            'exceptHours': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['systemsettings.ExceptHour']", 'symmetrical': 'False'}),
            'fileType': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'frequency': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'numFiles': ('django.db.models.fields.IntegerField', [], {}),
            'toArchive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'toCompress': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'toCopy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'toDisseminate': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'systemsettings.filepath': {
            'Meta': {'object_name': 'FilePath', '_ormbases': ['systemsettings.MarkedString']},
            'markedstring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.MarkedString']", 'unique': 'True', 'primary_key': 'True'}),
            'theFile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.File']"})
        },
        'systemsettings.filepattern': {
            'Meta': {'object_name': 'FilePattern', '_ormbases': ['systemsettings.MarkedString']},
            'markedstring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.MarkedString']", 'unique': 'True', 'primary_key': 'True'}),
            'theFile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.File']"})
        },
        'systemsettings.host': {
            'Meta': {'object_name': 'Host'},
            'basePath': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'systemsettings.item': {
            'Meta': {'object_name': 'Item'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'systemsettings.markedstring': {
            'Meta': {'object_name': 'MarkedString'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.package': {
            'Meta': {'object_name': 'Package', '_ormbases': ['systemsettings.Item']},
            'codeClass': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.CodeClass']"}),
            'inputs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inputs'", 'symmetrical': 'False', 'through': "orm['systemsettings.PackageInput']", 'to': "orm['systemsettings.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'systemsettings.packageinput': {
            'Meta': {'object_name': 'PackageInput'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inputItem': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inputItem_systemsettings_packageinput_related'", 'to': "orm['systemsettings.Item']"}),
            'optional': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packageInput_systemsettings_packageinput_related'", 'to': "orm['systemsettings.Package']"}),
            'specificAreas': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.Area']", 'null': 'True', 'blank': 'True'}),
            'specificTimeslots': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.TimeslotDisplacer']", 'null': 'True', 'blank': 'True'})
        },
        'systemsettings.packageoutput': {
            'Meta': {'object_name': 'PackageOutput'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'optional': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'outputItem': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Item']"}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packageOutput_systemsettings_packageoutput_related'", 'to': "orm['systemsettings.Package']"}),
            'specificAreas': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.Area']", 'null': 'True', 'blank': 'True'}),
            'specificTimeslots': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.TimeslotDisplacer']", 'null': 'True', 'blank': 'True'})
        },
        'systemsettings.packagepath': {
            'Meta': {'object_name': 'PackagePath', '_ormbases': ['systemsettings.MarkedString']},
            'markedstring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.MarkedString']", 'unique': 'True', 'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Package']"})
        },
        'systemsettings.source': {
            'Meta': {'object_name': 'Source'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'systemsettings.sourceextrainfo': {
            'Meta': {'object_name': 'SourceExtraInfo', '_ormbases': ['systemsettings.MarkedString']},
            'markedstring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.MarkedString']", 'unique': 'True', 'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Source']"})
        },
        'systemsettings.specificsource': {
            'Meta': {'object_name': 'SpecificSource'},
            'endDate': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Source']"}),
            'startDate': ('django.db.models.fields.DateTimeField', [], {})
        },
        'systemsettings.timeslotdisplacer': {
            'Meta': {'object_name': 'TimeslotDisplacer'},
            'endValue': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'startValue': ('django.db.models.fields.IntegerField', [], {}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['systemsettings']
