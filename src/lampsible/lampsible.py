import os
from copy import deepcopy
from ansible_runner import (
    Runner, RunnerConfig, run_command, run as ansible_runner_run
)
from ansible_directory_helper.private_data import PrivateData
from fqdn import FQDN
from .constants import *


class Lampsible:

    def __init__(self, web_user, web_host, action,
            private_data_dir=DEFAULT_PRIVATE_DATA_DIR,
            apache_server_admin=DEFAULT_APACHE_SERVER_ADMIN,
            database_username=None,
            database_name=None, database_host=None, database_system_user=None,
            database_system_host=None, php_version=DEFAULT_PHP_VERSION, site_title=DEFAULT_SITE_TITLE,
            admin_username=DEFAULT_ADMIN_USERNAME, admin_email=DEFAULT_ADMIN_EMAIL,
            wordpress_version=DEFAULT_WORDPRESS_VERSION,
            wordpress_locale=DEFAULT_WORDPRESS_LOCALE,
            joomla_version=DEFAULT_JOOMLA_VERSION,
            joomla_admin_full_name=DEFAULT_JOOMLA_ADMIN_FULL_NAME,
            drupal_profile=DEFAULT_DRUPAL_PROFILE,
            app_name=None,
            app_build_path=None,
            ssl_certbot=True,
            ssl_selfsigned=False, remote_sudo_password=None,
            ssh_key_file=None, apache_vhost_name=DEFAULT_APACHE_VHOST_NAME,
            apache_document_root=DEFAULT_APACHE_DOCUMENT_ROOT, database_password=None,
            database_table_prefix=DEFAULT_DATABASE_TABLE_PREFIX, php_extensions=[],
            composer_packages=[], composer_working_directory=None,
            composer_project=None, admin_password=None,
            wordpress_insecure_allow_xmlrpc=False,
            app_local_env=False,
            laravel_artisan_commands=DEFAULT_LARAVEL_ARTISAN_COMMANDS,
            email_for_ssl=None,
            domains_for_ssl=[], ssl_test_cert=False,
            extra_packages=[], extra_env_vars={},
            apache_custom_conf_name='',
            ):

        self.web_user = web_user
        self.web_host = web_host

        if database_system_user:
            self.database_system_user = database_system_user
        else:
            self.database_system_user = self.web_user
        if database_system_host:
            self.database_system_host = database_system_host
        else:
            self.database_system_host = self.web_host

        self.private_data_helper = PrivateData(private_data_dir)
        self._init_inventory()

        self.runner_config = RunnerConfig(
            private_data_dir=private_data_dir,
            project_dir=PROJECT_DIR,
        )

        self.runner = Runner(config=self.runner_config)

        self.apache_document_root = apache_document_root
        self.apache_vhost_name    = apache_vhost_name
        self.apache_server_admin  = apache_server_admin

        self.ssl_certbot     = ssl_certbot
        self.ssl_test_cert   = ssl_test_cert
        self.ssl_selfsigned  = ssl_selfsigned
        self.email_for_ssl   = email_for_ssl
        self.domains_for_ssl = domains_for_ssl

        self.apache_custom_conf_name = apache_custom_conf_name

        self.database_username     = database_username
        self.database_password     = database_password
        self.database_name         = database_name
        self.database_host         = database_host
        self.database_table_prefix = database_table_prefix

        self.php_version                = php_version
        self.php_extensions             = php_extensions
        self.composer_packages          = composer_packages
        self.composer_project           = composer_project
        self.composer_working_directory = composer_working_directory

        self.set_action(action)

        self.site_title     = site_title
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.admin_email    = admin_email

        self.wordpress_version = wordpress_version
        self.wordpress_locale  = wordpress_locale
        self.wordpress_insecure_allow_xmlrpc  = wordpress_insecure_allow_xmlrpc

        self.joomla_version = joomla_version
        self.joomla_admin_full_name = joomla_admin_full_name

        self.drupal_profile = drupal_profile

        self.app_name = app_name
        self.app_build_path = app_build_path
        self.laravel_artisan_commands = laravel_artisan_commands
        self.app_local_env = app_local_env
        self.extra_packages = extra_packages
        self.extra_env_vars = extra_env_vars

        if ssh_key_file:
            try:
                with open(os.path.abspath(ssh_key_file), 'r') as key_file:
                    key_data = key_file.read()
                self.runner_config.ssh_key_data = key_data
            except FileNotFoundError:
                print('Warning! SSH key file not found!')

        self.remote_sudo_password = remote_sudo_password

        self.banner = LAMPSIBLE_BANNER


    def set_action(self, action):
        self.action = action

        if action == 'lamp-stack':
            required_php_extensions = ['php-mysql']
        elif action == 'wordpress':
            required_php_extensions = ['php-mysql']
            if self.database_table_prefix == DEFAULT_DATABASE_TABLE_PREFIX:
                self.database_table_prefix = 'wp_'
        elif action == 'joomla':
            required_php_extensions = [
                'php-simplexml',
                'php-dom',
                'php-zip',
                'php-gd',
                'php-mysql',
            ]
        elif action == 'drupal':
            required_php_extensions = [
                'php-mysql',
                'php-xml',
                'php-gd',
                'php-curl',
                'php-mbstring',
            ]
            if not self.composer_project:
                self.composer_project = 'drupal/recommended-project'
            if not self.composer_working_directory:
                self.composer_working_directory = '{}/drupal'.format(
                    self.apache_document_root
                )
            try:
                if 'drush/drush' not in self.composer_packages:
                    self.composer_packages.append('drush/drush')
            except AttributeError:
                self.composer_packages = ['drush/drush']
        elif action == 'laravel':
            required_php_extensions = [
                'php-mysql',
                'php-xml',
                'php-mbstring',
            ]
        else:
            required_php_extensions = []
        for ext in required_php_extensions:
            if ext not in self.php_extensions:
                self.php_extensions.append(ext)

        self.runner_config.playbook = '{}.yml'.format(self.action)


    def _set_apache_vars(self):
        if self.action in [
            'wordpress',
            'joomla',
        ]:
            if self.apache_document_root == DEFAULT_APACHE_DOCUMENT_ROOT:
                self.apache_document_root = '{}/{}'.format(
                    DEFAULT_APACHE_DOCUMENT_ROOT,
                    self.action
                )

            if self.apache_vhost_name == DEFAULT_APACHE_VHOST_NAME:
                self.apache_vhost_name = self.action

        elif self.action == 'drupal':
            if self.apache_document_root == DEFAULT_APACHE_DOCUMENT_ROOT:
                self.apache_document_root = '{}/drupal/web'.format(
                    DEFAULT_APACHE_DOCUMENT_ROOT
                )

        elif self.action == 'laravel':
            if self.apache_document_root == DEFAULT_APACHE_DOCUMENT_ROOT:
                self.apache_document_root = '{}/{}/public'.format(
                    DEFAULT_APACHE_DOCUMENT_ROOT,
                    self.app_name
                )

            if self.apache_vhost_name == DEFAULT_APACHE_VHOST_NAME:
                self.apache_vhost_name = self.app_name

        if FQDN(self.web_host).is_valid:
            server_name = self.web_host
        else:
            server_name = DEFAULT_APACHE_SERVER_NAME

        base_vhost_dict = {
            'base_vhost_file': '{}.conf'.format(DEFAULT_APACHE_VHOST_NAME),
            'document_root':  self.apache_document_root,
            'vhost_name':     self.apache_vhost_name,
            'server_name':    server_name,
            'server_admin':   self.apache_server_admin,
            'allow_override': self.get_apache_allow_override(),
        }

        self.apache_vhosts = [base_vhost_dict]

        if self.ssl_certbot:
            if not self.email_for_ssl:
                self.email_for_ssl = self.apache_server_admin
            if not self.domains_for_ssl:
                self.domains_for_ssl = [self.web_host]

        elif self.ssl_selfsigned:
            ssl_vhost_dict = deepcopy(base_vhost_dict)

            ssl_vhost_dict['base_vhost_file'] = 'default-ssl.conf'
            ssl_vhost_dict['vhost_name']      += '-ssl'

            self.apache_vhosts.append(ssl_vhost_dict)

            self.apache_custom_conf_name = 'ssl-params'

        # TODO: Do this conditionally, only for actions where we need it?
        if not self.composer_working_directory:
            self.composer_working_directory = self.apache_document_root


    def get_apache_allow_override(self):
        return (
            self.action in ['laravel', 'drupal']
            or (
                self.action == 'wordpress'
                # TODO: Deprecate this.
                and not self.wordpress_insecure_allow_xmlrpc
            )
        )


    def print_banner(self):
        print(self.banner)


    def _init_inventory(self):
        self.private_data_helper.add_inventory_groups([
            'web_servers',
            'database_servers',
        ])
        self.private_data_helper.add_inventory_host(self.web_host, 'web_servers')
        self.private_data_helper.add_inventory_host(self.database_system_host,
                'database_servers')
        self.private_data_helper.set_inventory_ansible_user(self.web_host, self.web_user)
        self.private_data_helper.set_inventory_ansible_user(
                self.database_system_host, self.database_system_user)
        self.private_data_helper.write_inventory()


    def _update_env(self):
        # TODO: Build this list conditionally, based on the action,
        # to avoid setting unnecessary variables. See ArgValidator.get_extravars_dict,
        # which we must also deprecate in favor of this method here.
        extravars = [
            'web_host',
            'apache_vhosts',
            'apache_vhost_name',
            'apache_document_root',
            'apache_server_admin',
            'apache_custom_conf_name',
            'database_username',
            # TODO: Ansible Runner has a dedicated feature for dealing
            # with passwords. Likely we'll have to implement support
            # for that in ansible-directory-helper.
            # For the time being, however, treat it as an extravar.
            'database_password',
            'database_name',
            'database_host',
            'database_table_prefix',
            'php_version',
            'php_extensions',
            'composer_packages',
            'composer_project',
            'composer_working_directory',
            'site_title',
            'admin_username',
            'admin_password',
            'admin_email',
            'wordpress_version',
            'wordpress_locale',
            'wordpress_url',
            'wordpress_insecure_allow_xmlrpc',
            'joomla_version',
            'joomla_admin_full_name',
            'drupal_profile',
            'app_name',
            'app_build_path',
            'app_source_root',
            'laravel_artisan_commands',
            'app_local_env',
            'ssl_certbot',
            'email_for_ssl',
            'certbot_domains_string',
            'ssl_test_cert',
            'ssl_selfsigned',
            'extra_packages',
            'extra_env_vars',
            # TODO: This one especially... use Ansible Runner's
            # dedicated password feature, that is, we should add it
            # ansible-directory-helper.
            'ansible_sudo_pass',
            'open_database',
        ]
        for varname in extravars:
            if varname == 'server_name':
                if FQDN.is_valid(self.web_host):
                    value = self.web_host
                else:
                    value = DEFAULT_APACHE_SERVER_NAME

            elif varname == 'wordpress_url':
                if not self.ssl_certbot or self.web_host[:4] == 'www.':
                    value = self.web_host
                else:
                    value = 'www.{}'.format(self.web_host)

                if value not in self.domains_for_ssl:
                    self.domains_for_ssl.append(value)

            elif varname == 'certbot_domains_string':
                value = '-d {}'.format(' -d '.join(self.domains_for_ssl))

            # This lets us pass extra_env_vars to Lampsible in the more sensible dictionary format,
            # while still using them in the more convenient list format.
            elif varname == 'extra_env_vars':
                value = [
                    '{}={}'.format(
                        key,
                        val
                    ) for key, val in self.extra_env_vars.items()
                ]

                # And this is to make sure that if we're installing a Laravel
                # app, we write the variables to the app's .env file, and not
                # Apache's envvars file.
                if self.action == 'laravel':
                    self.private_data_helper.set_extravar(
                        'laravel_extra_env_vars',
                        value
                    )
                    value = []

            elif varname == 'app_source_root':
                value = '{}/{}'.format(
                    DEFAULT_APACHE_DOCUMENT_ROOT,
                    self.app_name
                )

            elif varname == 'ansible_sudo_pass':
                if self.remote_sudo_password:
                    value = self.remote_sudo_password
                else:
                    continue

            elif varname == 'open_database':
                if self.database_system_host is None \
                        or self.database_system_host == self.web_host:
                    value = False
                else:
                    value = True



            else:
                value = getattr(self, varname)

            self.private_data_helper.set_extravar(varname, value)

        self.private_data_helper.write_env()


    def _prepare_config(self):
        self.runner_config.prepare()


    # TODO: Do it this way?
    #def dump_ansible_facts(self):
    #    ansible_runner_run(
    #        private_data_dir=self.private_data_dir,
    #        host_pattern=self.web_host,
    #        module='setup',
    #        module_args='no_log=true'
    #    )


    def run(self):
        self._set_apache_vars()
        self._update_env()
        self._prepare_config()
        try:
            self.runner.run()
            print(self.runner.stats)
            self.private_data_helper.cleanup_dir()
            # TODO: We could do this better, like check the fact_cache and make sure
            # everything was alright, before returning 0.
            return 0
        except RuntimeError:
            return 1
