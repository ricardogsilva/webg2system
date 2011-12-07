# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Host'
        db.create_table('systemsettings_host', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('basePath', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('systemsettings', ['Host'])

        # Adding model 'MarkedString'
        db.create_table('systemsettings_markedstring', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('string', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('marks', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('systemsettings', ['MarkedString'])

        # Adding model 'FilePath'
        db.create_table('systemsettings_filepath', (
            ('markedstring_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['systemsettings.MarkedString'], unique=True, primary_key=True)),
            ('theFile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.File'])),
        ))
        db.send_create_signal('systemsettings', ['FilePath'])

        # Adding model 'FilePattern'
        db.create_table('systemsettings_filepattern', (
            ('markedstring_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['systemsettings.MarkedString'], unique=True, primary_key=True)),
            ('theFile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.File'])),
        ))
        db.send_create_signal('systemsettings', ['FilePattern'])

        # Adding model 'PackagePath'
        db.create_table('systemsettings_packagepath', (
            ('markedstring_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['systemsettings.MarkedString'], unique=True, primary_key=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.Package'])),
        ))
        db.send_create_signal('systemsettings', ['PackagePath'])

        # Adding model 'ExceptHour'
        db.create_table('systemsettings_excepthour', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hour', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('systemsettings', ['ExceptHour'])

        # Adding model 'Item'
        db.create_table('systemsettings_item', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('systemsettings', ['Item'])

        # Adding model 'Package'
        db.create_table('systemsettings_package', (
            ('item_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['systemsettings.Item'], unique=True, primary_key=True)),
            ('codeClass', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('systemsettings', ['Package'])

        # Adding model 'File'
        db.create_table('systemsettings_file', (
            ('item_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['systemsettings.Item'], unique=True, primary_key=True)),
            ('numFiles', self.gf('django.db.models.fields.IntegerField')()),
            ('fileType', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('frequency', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('toArchive', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('toCompress', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('toDisseminate', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('toCopy', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('systemsettings', ['File'])

        # Adding M2M table for field exceptHours on 'File'
        db.create_table('systemsettings_file_exceptHours', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('file', models.ForeignKey(orm['systemsettings.file'], null=False)),
            ('excepthour', models.ForeignKey(orm['systemsettings.excepthour'], null=False))
        ))
        db.create_unique('systemsettings_file_exceptHours', ['file_id', 'excepthour_id'])

        # Adding model 'PackageInput'
        db.create_table('systemsettings_packageinput', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(related_name='packageInput_systemsettings_packageinput_related', to=orm['systemsettings.Package'])),
            ('inputItem', self.gf('django.db.models.fields.related.ForeignKey')(related_name='inputItem_systemsettings_packageinput_related', to=orm['systemsettings.Item'])),
        ))
        db.send_create_signal('systemsettings', ['PackageInput'])

        # Adding M2M table for field specificAreas on 'PackageInput'
        db.create_table('systemsettings_packageinput_specificAreas', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('packageinput', models.ForeignKey(orm['systemsettings.packageinput'], null=False)),
            ('area', models.ForeignKey(orm['systemsettings.area'], null=False))
        ))
        db.create_unique('systemsettings_packageinput_specificAreas', ['packageinput_id', 'area_id'])

        # Adding model 'PackageOutput'
        db.create_table('systemsettings_packageoutput', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(related_name='packageOutput_systemsettings_packageoutput_related', to=orm['systemsettings.Package'])),
            ('outputItem', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.Item'])),
        ))
        db.send_create_signal('systemsettings', ['PackageOutput'])

        # Adding M2M table for field specificAreas on 'PackageOutput'
        db.create_table('systemsettings_packageoutput_specificAreas', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('packageoutput', models.ForeignKey(orm['systemsettings.packageoutput'], null=False)),
            ('area', models.ForeignKey(orm['systemsettings.area'], null=False))
        ))
        db.create_unique('systemsettings_packageoutput_specificAreas', ['packageoutput_id', 'area_id'])

        # Adding model 'Source'
        db.create_table('systemsettings_source', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('systemsettings', ['Source'])

        # Adding model 'SourceExtraInfo'
        db.create_table('systemsettings_sourceextrainfo', (
            ('markedstring_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['systemsettings.MarkedString'], unique=True, primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.Source'])),
        ))
        db.send_create_signal('systemsettings', ['SourceExtraInfo'])

        # Adding model 'SpecificSource'
        db.create_table('systemsettings_specificsource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('startDate', self.gf('django.db.models.fields.DateTimeField')()),
            ('endDate', self.gf('django.db.models.fields.DateTimeField')()),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.Source'])),
        ))
        db.send_create_signal('systemsettings', ['SpecificSource'])

        # Adding model 'Area'
        db.create_table('systemsettings_area', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.Source'])),
        ))
        db.send_create_signal('systemsettings', ['Area'])


    def backwards(self, orm):
        
        # Deleting model 'Host'
        db.delete_table('systemsettings_host')

        # Deleting model 'MarkedString'
        db.delete_table('systemsettings_markedstring')

        # Deleting model 'FilePath'
        db.delete_table('systemsettings_filepath')

        # Deleting model 'FilePattern'
        db.delete_table('systemsettings_filepattern')

        # Deleting model 'PackagePath'
        db.delete_table('systemsettings_packagepath')

        # Deleting model 'ExceptHour'
        db.delete_table('systemsettings_excepthour')

        # Deleting model 'Item'
        db.delete_table('systemsettings_item')

        # Deleting model 'Package'
        db.delete_table('systemsettings_package')

        # Deleting model 'File'
        db.delete_table('systemsettings_file')

        # Removing M2M table for field exceptHours on 'File'
        db.delete_table('systemsettings_file_exceptHours')

        # Deleting model 'PackageInput'
        db.delete_table('systemsettings_packageinput')

        # Removing M2M table for field specificAreas on 'PackageInput'
        db.delete_table('systemsettings_packageinput_specificAreas')

        # Deleting model 'PackageOutput'
        db.delete_table('systemsettings_packageoutput')

        # Removing M2M table for field specificAreas on 'PackageOutput'
        db.delete_table('systemsettings_packageoutput_specificAreas')

        # Deleting model 'Source'
        db.delete_table('systemsettings_source')

        # Deleting model 'SourceExtraInfo'
        db.delete_table('systemsettings_sourceextrainfo')

        # Deleting model 'SpecificSource'
        db.delete_table('systemsettings_specificsource')

        # Deleting model 'Area'
        db.delete_table('systemsettings_area')


    models = {
        'systemsettings.area': {
            'Meta': {'object_name': 'Area'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Source']"})
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
            'codeClass': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'inputs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inputs'", 'symmetrical': 'False', 'through': "orm['systemsettings.PackageInput']", 'to': "orm['systemsettings.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'systemsettings.packageinput': {
            'Meta': {'object_name': 'PackageInput'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inputItem': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inputItem_systemsettings_packageinput_related'", 'to': "orm['systemsettings.Item']"}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packageInput_systemsettings_packageinput_related'", 'to': "orm['systemsettings.Package']"}),
            'specificAreas': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.Area']", 'null': 'True', 'blank': 'True'})
        },
        'systemsettings.packageoutput': {
            'Meta': {'object_name': 'PackageOutput'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'outputItem': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.Item']"}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packageOutput_systemsettings_packageoutput_related'", 'to': "orm['systemsettings.Package']"}),
            'specificAreas': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.Area']", 'null': 'True', 'blank': 'True'})
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
        }
    }

    complete_apps = ['systemsettings']
