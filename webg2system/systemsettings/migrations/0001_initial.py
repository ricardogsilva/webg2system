# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SourceSetting'
        db.create_table('systemsettings_sourcesetting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('systemsettings', ['SourceSetting'])

        # Adding model 'SpecificSource'
        db.create_table('systemsettings_specificsource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('startDate', self.gf('django.db.models.fields.DateTimeField')()),
            ('endDate', self.gf('django.db.models.fields.DateTimeField')()),
            ('sourceSetting', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.SourceSetting'])),
        ))
        db.send_create_signal('systemsettings', ['SpecificSource'])

        # Adding model 'Area'
        db.create_table('systemsettings_area', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('sourceSetting', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.SourceSetting'])),
        ))
        db.send_create_signal('systemsettings', ['Area'])

        # Adding model 'HostSetting'
        db.create_table('systemsettings_hostsetting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('basePath', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('systemsettings', ['HostSetting'])

        # Adding model 'ItemSetting'
        db.create_table('systemsettings_itemsetting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('systemsettings', ['ItemSetting'])

        # Adding model 'SearchPattern'
        db.create_table('systemsettings_searchpattern', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('string', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('marks', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('systemsettings', ['SearchPattern'])

        # Adding model 'SourceExtraInfo'
        db.create_table('systemsettings_sourceextrainfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('string', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('marks', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('sourceSetting', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.SourceSetting'])),
        ))
        db.send_create_signal('systemsettings', ['SourceExtraInfo'])

        # Adding model 'PackageSetting'
        db.create_table('systemsettings_packagesetting', (
            ('itemsetting_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['systemsettings.ItemSetting'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('systemsettings', ['PackageSetting'])

        # Adding model 'PackageWorkingDir'
        db.create_table('systemsettings_packageworkingdir', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('string', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('marks', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('packageSetting', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['systemsettings.PackageSetting'], unique=True)),
        ))
        db.send_create_signal('systemsettings', ['PackageWorkingDir'])

        # Adding model 'PackageOutputDir'
        db.create_table('systemsettings_packageoutputdir', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('string', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('marks', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('packageSetting', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.PackageSetting'], null=True, blank=True)),
        ))
        db.send_create_signal('systemsettings', ['PackageOutputDir'])

        # Adding model 'PackageInputDir'
        db.create_table('systemsettings_packageinputdir', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('string', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('marks', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('packageSetting', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.PackageSetting'], null=True, blank=True)),
        ))
        db.send_create_signal('systemsettings', ['PackageInputDir'])

        # Adding model 'PackageInternalDir'
        db.create_table('systemsettings_packageinternaldir', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('string', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('marks', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('packageSetting', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.PackageSetting'], null=True, blank=True)),
        ))
        db.send_create_signal('systemsettings', ['PackageInternalDir'])

        # Adding model 'FileSearchPath'
        db.create_table('systemsettings_filesearchpath', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('string', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('marks', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('fileSetting', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.FileSetting'])),
        ))
        db.send_create_signal('systemsettings', ['FileSearchPath'])

        # Adding model 'FileSearchPattern'
        db.create_table('systemsettings_filesearchpattern', (
            ('searchpattern_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['systemsettings.SearchPattern'], unique=True, primary_key=True)),
            ('fileSetting', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.FileSetting'])),
        ))
        db.send_create_signal('systemsettings', ['FileSearchPattern'])

        # Adding model 'Hour'
        db.create_table('systemsettings_hour', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hour', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('systemsettings', ['Hour'])

        # Adding model 'FileSetting'
        db.create_table('systemsettings_filesetting', (
            ('itemsetting_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['systemsettings.ItemSetting'], unique=True, primary_key=True)),
            ('numFiles', self.gf('django.db.models.fields.IntegerField')()),
            ('fileType', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('frequency', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('toArchive', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('toCompress', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('toDisseminate', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('toCopy', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('systemsettings', ['FileSetting'])

        # Adding M2M table for field exceptHours on 'FileSetting'
        db.create_table('systemsettings_filesetting_exceptHours', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('filesetting', models.ForeignKey(orm['systemsettings.filesetting'], null=False)),
            ('hour', models.ForeignKey(orm['systemsettings.hour'], null=False))
        ))
        db.create_unique('systemsettings_filesetting_exceptHours', ['filesetting_id', 'hour_id'])

        # Adding model 'PackageRelatedItemSetting'
        db.create_table('systemsettings_packagerelateditemsetting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('packageSetting', self.gf('django.db.models.fields.related.ForeignKey')(related_name='packageSetting_systemsettings_packagerelateditemsetting_related', to=orm['systemsettings.PackageSetting'])),
            ('relatedItemSetting', self.gf('django.db.models.fields.related.ForeignKey')(related_name='relatedItemSetting_systemsettings_packagerelateditemsetting_related', to=orm['systemsettings.ItemSetting'])),
            ('relatedItemRole', self.gf('django.db.models.fields.CharField')(max_length=8)),
        ))
        db.send_create_signal('systemsettings', ['PackageRelatedItemSetting'])

        # Adding M2M table for field specificAreas on 'PackageRelatedItemSetting'
        db.create_table('systemsettings_packagerelateditemsetting_specificAreas', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('packagerelateditemsetting', models.ForeignKey(orm['systemsettings.packagerelateditemsetting'], null=False)),
            ('area', models.ForeignKey(orm['systemsettings.area'], null=False))
        ))
        db.create_unique('systemsettings_packagerelateditemsetting_specificAreas', ['packagerelateditemsetting_id', 'area_id'])

        # Adding model 'TimeslotDisplacer'
        db.create_table('systemsettings_timeslotdisplacer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
            ('packageRelatedItem', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systemsettings.PackageRelatedItemSetting'])),
        ))
        db.send_create_signal('systemsettings', ['TimeslotDisplacer'])


    def backwards(self, orm):
        
        # Deleting model 'SourceSetting'
        db.delete_table('systemsettings_sourcesetting')

        # Deleting model 'SpecificSource'
        db.delete_table('systemsettings_specificsource')

        # Deleting model 'Area'
        db.delete_table('systemsettings_area')

        # Deleting model 'HostSetting'
        db.delete_table('systemsettings_hostsetting')

        # Deleting model 'ItemSetting'
        db.delete_table('systemsettings_itemsetting')

        # Deleting model 'SearchPattern'
        db.delete_table('systemsettings_searchpattern')

        # Deleting model 'SourceExtraInfo'
        db.delete_table('systemsettings_sourceextrainfo')

        # Deleting model 'PackageSetting'
        db.delete_table('systemsettings_packagesetting')

        # Deleting model 'PackageWorkingDir'
        db.delete_table('systemsettings_packageworkingdir')

        # Deleting model 'PackageOutputDir'
        db.delete_table('systemsettings_packageoutputdir')

        # Deleting model 'PackageInputDir'
        db.delete_table('systemsettings_packageinputdir')

        # Deleting model 'PackageInternalDir'
        db.delete_table('systemsettings_packageinternaldir')

        # Deleting model 'FileSearchPath'
        db.delete_table('systemsettings_filesearchpath')

        # Deleting model 'FileSearchPattern'
        db.delete_table('systemsettings_filesearchpattern')

        # Deleting model 'Hour'
        db.delete_table('systemsettings_hour')

        # Deleting model 'FileSetting'
        db.delete_table('systemsettings_filesetting')

        # Removing M2M table for field exceptHours on 'FileSetting'
        db.delete_table('systemsettings_filesetting_exceptHours')

        # Deleting model 'PackageRelatedItemSetting'
        db.delete_table('systemsettings_packagerelateditemsetting')

        # Removing M2M table for field specificAreas on 'PackageRelatedItemSetting'
        db.delete_table('systemsettings_packagerelateditemsetting_specificAreas')

        # Deleting model 'TimeslotDisplacer'
        db.delete_table('systemsettings_timeslotdisplacer')


    models = {
        'systemsettings.area': {
            'Meta': {'object_name': 'Area'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sourceSetting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.SourceSetting']"})
        },
        'systemsettings.filesearchpath': {
            'Meta': {'object_name': 'FileSearchPath'},
            'fileSetting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.FileSetting']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.filesearchpattern': {
            'Meta': {'object_name': 'FileSearchPattern', '_ormbases': ['systemsettings.SearchPattern']},
            'fileSetting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.FileSetting']"}),
            'searchpattern_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.SearchPattern']", 'unique': 'True', 'primary_key': 'True'})
        },
        'systemsettings.filesetting': {
            'Meta': {'object_name': 'FileSetting', '_ormbases': ['systemsettings.ItemSetting']},
            'exceptHours': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.Hour']", 'null': 'True', 'blank': 'True'}),
            'fileType': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'frequency': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'itemsetting_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.ItemSetting']", 'unique': 'True', 'primary_key': 'True'}),
            'numFiles': ('django.db.models.fields.IntegerField', [], {}),
            'toArchive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'toCompress': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'toCopy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'toDisseminate': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'systemsettings.hostsetting': {
            'Meta': {'object_name': 'HostSetting'},
            'basePath': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'systemsettings.hour': {
            'Meta': {'object_name': 'Hour'},
            'hour': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'systemsettings.itemsetting': {
            'Meta': {'object_name': 'ItemSetting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'systemsettings.packageinputdir': {
            'Meta': {'object_name': 'PackageInputDir'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'packageSetting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.PackageSetting']", 'null': 'True', 'blank': 'True'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.packageinternaldir': {
            'Meta': {'object_name': 'PackageInternalDir'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'packageSetting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.PackageSetting']", 'null': 'True', 'blank': 'True'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.packageoutputdir': {
            'Meta': {'object_name': 'PackageOutputDir'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'packageSetting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.PackageSetting']", 'null': 'True', 'blank': 'True'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.packagerelateditemsetting': {
            'Meta': {'object_name': 'PackageRelatedItemSetting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'packageSetting': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packageSetting_systemsettings_packagerelateditemsetting_related'", 'to': "orm['systemsettings.PackageSetting']"}),
            'relatedItemRole': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'relatedItemSetting': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relatedItemSetting_systemsettings_packagerelateditemsetting_related'", 'to': "orm['systemsettings.ItemSetting']"}),
            'specificAreas': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['systemsettings.Area']", 'null': 'True', 'blank': 'True'})
        },
        'systemsettings.packagesetting': {
            'Meta': {'object_name': 'PackageSetting', '_ormbases': ['systemsettings.ItemSetting']},
            'itemsetting_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.ItemSetting']", 'unique': 'True', 'primary_key': 'True'}),
            'relatedItems': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'relatedItems_systemsettings_packagesetting_related'", 'symmetrical': 'False', 'through': "orm['systemsettings.PackageRelatedItemSetting']", 'to': "orm['systemsettings.ItemSetting']"})
        },
        'systemsettings.packageworkingdir': {
            'Meta': {'object_name': 'PackageWorkingDir'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'packageSetting': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['systemsettings.PackageSetting']", 'unique': 'True'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.searchpattern': {
            'Meta': {'object_name': 'SearchPattern'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.sourceextrainfo': {
            'Meta': {'object_name': 'SourceExtraInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'sourceSetting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.SourceSetting']"}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systemsettings.sourcesetting': {
            'Meta': {'object_name': 'SourceSetting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'systemsettings.specificsource': {
            'Meta': {'object_name': 'SpecificSource'},
            'endDate': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sourceSetting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.SourceSetting']"}),
            'startDate': ('django.db.models.fields.DateTimeField', [], {})
        },
        'systemsettings.timeslotdisplacer': {
            'Meta': {'object_name': 'TimeslotDisplacer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'packageRelatedItem': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systemsettings.PackageRelatedItemSetting']"}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['systemsettings']
