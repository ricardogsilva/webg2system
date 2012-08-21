import datetime as dt

from django.test import TestCase

import systemsettings.models as ss
import operations.models as om
import operations.core.g2hosts as g2h
import operations.core.g2packages as g2h
import operations.core.utilities as utilities


class OperationsViewsTestCase(TestCase):

    def test_index(self):
        resp = self.client.get('/operations/')
        self.assertEqual(resp.status_code, 200)


class OperationsCoreHostFactoryTestCase(TestCase):
    fixtures = ['settings_fixtures.json']

    def setUp(self):
        self.factory = g2h.HostFactory()

    def test_host_creation(self):
        for hs in ss.Host.objects.all():
            h = self.factory.create_host(hs)
            self.assertIsNotNone(h)


class OperationsCoreG2LocalHostsTestCase(TestCase):
    fixtures = ['settings_fixtures.json']

    def setUp(self):
        factory = g2h.HostFactory()
        self.host = factory.create_host()

    def test_monitor_file_system(self):
        usage = self.host.monitor_file_system_usage()
        self.assertTrue(0 < usage < 100)


class OperationsCoreG2RemoteHostsTestCase(TestCase):
    fixtures = ['settings_fixtures.json']

    def setUp(self):
        self.hosts = []
        factory = g2h.HostFactory()
        for hs in ss.Host.objects.all():
            h = factory.create_host(hs)
            if not isinstance(h, g2h.G2LocalHost) and h.active:
                self.hosts.append(h)

    def test_monitor_file_system(self):
        for h in self.hosts:
            usage = h.monitor_file_system_usage()
            self.assertTrue(0 < usage < 100)
            h.close_connection()

class SWIPostProcessorTestCase(TestCase):

    def setUp(self):
        timeslot = dt.datetime(2012, 7, 7),
        settings = ss.Package.objects.get(name='postprocess_swi'),
        area = ss.Area.objects.get(area='.*')
        host = g2h.HostFactory().create_host()
        self.swi_pack = g2p.SWIProcessor(settings, timeslot, area, host)

class UtilitiesTestCase(TestCase):

    def test_extract_timeslot(self):
        tests = [
            'DSSF_quicklook_201201010000.map',
            'DSSF_quicklook_2012010100.map',
            'DSSF_quicklook_20120101.map',
            'DSSF_quicklook_2012_035.map',
        ]
        for t in tests:
            ts = utilities.extract_timeslot(t)
            self.assertIsNotNone(ts)
