import datetime as dt

from django.test import TestCase
import systemsettings.models as sm
from operations.core import g2packages as g2p
from operations.core import g2hosts as g2h

class SystemSettingsModelsTestCase(TestCase):
    fixtures = ['systemsettings_models_testdata.json']

    def test_ows_preparator(self):
        settings = sm.Package.objects.filter(codeClass__className='OWSPreparator')
        timeslot = dt.datetime(2012, 1, 1)
        area = sm.Area.objects.get(name='.*')
        for setting in settings:
            pack = g2p.OWSPreparator(setting, timeslot, area)
            self.assertTrue(hasattr(pack, 'codeDir'))
            self.assertTrue(hasattr(pack, 'workingDir'))
            self.assertTrue(hasattr(pack, 'mapfileOutDir'))
            self.assertTrue(hasattr(pack, 'mapfileShapePath'))
            self.assertTrue(hasattr(pack, 'mapfileTemplateDir'))
            self.assertTrue(hasattr(pack, 'geotifOutDir'))


class CoreHostFactoryTestCase(TestCase):
    fixtures = ['systemsettings_models_testdata.json']

    def setUp(self):
        self.factory = g2h.HostFactory()

    def test_local_host_creation(self):
        local_host = self.factory.create_host()
        self.assertIsInstance(local_host, g2h.G2LocalHost)
