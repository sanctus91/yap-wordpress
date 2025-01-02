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
            ssl_test_cert=True,
            apache_server_admin='me@me.me'
        )


    def test_banner(self):
        self.assertIn(__version__, self.lampsible.banner)


    def test_apache(self):
        self.lampsible.set_action('apache')
        self._do_test_run()


    def test_ssl_selfsigned(self):
        self.lampsible.set_action('apache')
        self.lampsible.ssl_selfsigned = True
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
        self._do_test_run()


    def test_wordpress(self):
        self.lampsible.set_action('wordpress')
        self.lampsible.database_name = 'wordpress'
        self.lampsible.admin_password = 'password'
        self._do_test_run()


    def test_joomla(self):
        self.lampsible.set_action('joomla')
        self.lampsible.database_name = 'joomla'
        self.lampsible.admin_password = 'passwordpassword'
        self._do_test_run()


    def test_drupal(self):
        self.lampsible.set_action('drupal')
        self.lampsible.database_name = 'drupal'
        self.lampsible.admin_password = 'password'
        self._do_test_run()


    def test_extra_env_vars(self):
        self.lampsible.set_action('apache')
        self.lampsible.extra_env_vars = {
            'HELLO': 'world',
            'FOO'  : 'bar',

        }
        self._do_test_run()


    def test_laravel(self):
        try:
            app_build_path = os.path.abspath(
                os.environ['LAMPSIBLE_LARAVEL_PATH']
            )
            app_name = os.environ['LAMPSIBLE_LARAVEL_NAME']
        except KeyError:
            self.skipTest('Got no LAMPSIBLE_LARAVEL_PATH and LAMPSIBLE_LARAVEL_NAME')
        self.lampsible.set_action('laravel')
        self.lampsible.database_name = 'laravel'
        self.lampsible.app_build_path = app_build_path
        self.lampsible.app_name = app_name
        self.lampsible.extra_env_vars = {
            'I_SHOULD_BE_IN': '.env-and-not-in-envvars'
        }
        self._do_test_run()


    def _do_test_run(self):
        result = self.lampsible.run()
        self.assertEqual(result, 0)


    # TODO?
    # def test_validator(self):
    #     self.assertEqual(1, 1)
