from django.test import TestCase


class OperationsViewsTestCase(TestCase):

    def test_index(self):
        resp = self.client.get('/operations/')
        self.assertEqual(resp.status_code, 200)
