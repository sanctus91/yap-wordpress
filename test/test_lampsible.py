import os
import unittest
from lampsible import __version__
from lampsible.lampsible import Lampsible
from lampsible.constants import *

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
            database_username=DEFAULT_DATABASE_USERNAME,
            database_password='password',
            database_host=DEFAULT_DATABASE_HOST,
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
        self._prepare_test_certbot()
        self._do_test_run()


    def test_mysql(self):
        self.lampsible.set_action('mysql')
        self.lampsible.database_name = 'test_database'
        self._do_test_run()


    def test_simple_php(self):
        self.lampsible.set_action('php')
        self._do_test_run()


    def test_full_php(self):
        self.lampsible.set_action('php')
        self.lampsible.php_extensions = [
            'php-mysql',
            'php-xml',
            'php-gd',
            'php-curl',
            'php-mbstring',
        ]
        self.lampsible.composer_packages = ['drush/drush', 'guzzlehttp/guzzle']
        self.lampsible.composer_project = 'drupal/recommended-project'
        self.lampsible.composer_working_directory = '/var/www/html/test-app'
        self._do_test_run()


    def test_extra_apt_packages(self):
        self.lampsible.set_action('apache')
        self.lampsible.extra_packages = ['tmux', 'neofetch']
        self._do_test_run()


    def test_lamp_stack(self):
        self.lampsible.set_action('lamp-stack')
        self.lampsible.database_name = 'test_database'
        self.lampsible.php_extensions = ['php-mysql', 'php-xml']
        self._prepare_test_certbot()
        self._do_test_run()


    def _do_test_run(self):
        result = self.lampsible.run()
        self.assertEqual(result, 0)


    def _prepare_test_certbot(self):
        self.lampsible.ssl_certbot = True
        self.lampsible.ssl_test_cert = True
        self.lampsible.apache_server_admin = 'me@me.me'


    # TODO?
    # def test_validator(self):
    #     self.assertEqual(1, 1)
