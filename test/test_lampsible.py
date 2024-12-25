import os
import unittest
from lampsible import __version__
from lampsible.lampsible import Lampsible

class TestLampsible(unittest.TestCase):

    def setUp(self):
        try:
            tmp_remote = os.environ['LAMPSIBLE_REMOTE'].split('@')
            web_user = tmp_remote[0]
            web_host = tmp_remote[1]
        except (KeyError, AttributeError):
            web_user = 'user'
            web_host = 'localhost'

        self.lampsible = Lampsible(
            web_user=web_user,
            web_host=web_host,
            action='apache',
            private_data_dir=os.path.join(
                'test',
                'tmp-private-data',
            ),
        )


    def tearDown(self):
        # TODO: This should be baked into the Lampsible class.
        self.lampsible.private_data_helper.cleanup_dir()


    def test_banner(self):
        self.assertIn(__version__, self.lampsible.banner)


    def test_apache(self):
        self.lampsible.set_action('apache')
        self._do_test_run()


    def test_ssl_selfsigned(self):
        self.lampsible.set_action('apache')
        self.lampsible.ssl_selfsigned = True
        self._do_test_run()


    def test_ssl_certbot(self):
        self.lampsible.set_action('apache')
        self.lampsible.ssl_certbot = True
        self.lampsible.ssl_test_cert = True
        self.lampsible.apache_server_admin = 'me@me.me'
        self._do_test_run()


    def _do_test_run(self):
        result = self.lampsible.run()
        self.assertEqual(result, 0)


    # TODO?
    # def test_validator(self):
    #     self.assertEqual(1, 1)
