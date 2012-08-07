from django.test import TestCase

import systemsettings.models as ss
import operations.core.g2hosts as g2h


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

