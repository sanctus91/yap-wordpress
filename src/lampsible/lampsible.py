import os
from copy import deepcopy
from shutil import rmtree
from ansible_runner import (
    Runner, RunnerConfig, run_command, run as ansible_runner_run
)
from ansible_directory_helper.private_data import PrivateData
from fqdn import FQDN
from . import __version__
from .constants import *
from .arg_validator import ArgValidator


class Lampsible:

    def __init__(self, web_user, web_host, action,
            private_data_dir=DEFAULT_PRIVATE_DATA_DIR,
            # These are from CLI flags. There were a few that I skipped,
            # because they either will be deprecated, or are not relevant in
            # this context.
            # TODO: Maybe type hint, and maybe use default values?
            apache_server_admin=DEFAULT_APACHE_SERVER_ADMIN,
            database_username=None,
            database_name=None, database_host=None, database_system_user=None,
            database_system_host=None, php_version=None, site_title=None,
            admin_username=None, admin_email=None, wordpress_version=None,
            wordpress_locale=None, joomla_version=None,
            joomla_admin_full_name=None, drupal_profile=None, app_name=None,
                                 # TODO: Deprecate this one
            app_build_path=None,
            # TODO: For now, for back-compat, False by default, but
            # it should actually be True.
            ssl_certbot=False,
            ssl_selfsigned=False, remote_sudo_password=None,
            ssh_key_file=None, apache_vhost_name=DEFAULT_APACHE_VHOST_NAME,
            apache_document_root=DEFAULT_APACHE_DOCUMENT_ROOT, database_password=None,
            database_table_prefix=DEFAULT_DATABASE_TABLE_PREFIX, php_extensions=None,
            composer_packages=None, composer_working_directory=None,
            composer_project=None, admin_password=None,
            # TODO: Deprecate this.
            wordpress_insecure_allow_xmlrpc=False,
            app_local_env=None,
            laravel_artisan_commands=None, email_for_ssl=None,
            domains_for_ssl=[], ssl_test_cert=False, insecure_skip_fail2ban=False,
            extra_packages=[], extra_env_vars=[],

            # These are from arg_validator. In v1, arg_validator generates these
            # variables, and passes them into extravars. We'll still need them here.
            apache_vhosts=None, apache_custom_conf_name='',
            # TODO: We shouldn't need these, but don't forget it for now.
            # certbot_domains_string, certbot_test_cert_string
            wordpress_auth_vars=None,
            # TODO: I don't want to have to use this one...
            wordpress_url=None,
            # TODO: Also don't know about this one...
            app_source_root=None,

            private_data_helper=None,
            runner_config=None,
            runner=None
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
        self.set_action(action)

        self.runner = Runner(config=self.runner_config)
        # ...
        self.apache_document_root = apache_document_root
        self.apache_vhost_name    = apache_vhost_name
        self.apache_server_admin  = apache_server_admin

        self.ssl_certbot     = ssl_certbot
        self.ssl_test_cert   = ssl_test_cert
        self.ssl_selfsigned  = ssl_selfsigned
        self.email_for_ssl   = email_for_ssl
        self.domains_for_ssl = domains_for_ssl

        self.app_name = app_name
        # TODO: Deprecate this.
        self.wordpress_insecure_allow_xmlrpc = wordpress_insecure_allow_xmlrpc
        self.apache_custom_conf_name = apache_custom_conf_name

        # ...
        self.database_username     = database_username
        self.database_password     = database_password
        self.database_name         = database_name
        self.database_host         = database_host
        self.database_table_prefix = database_table_prefix
        # TODO: All that other stuff...
        #     # Maybe a little better, but the setters need to each
        #     # be implemented.
        #     getattr(self, 'set_' + k)(v)

        # Or instead, like this? Simple but messy...
        # self.web_user = web_user
        # self.web_host = web_host
        # self.action = action
        # self.database_username = database_username
        # self.database_name = database_name
        # self.database_host = database_host
        # self.database_system_user = database_system_user
        # self.database_system_host = database_system_host
        # self.php_version = php_version
        # self.site_title = site_title
        # self.admin_username = admin_username
        # self.admin_email = admin_email
        # self.
        self.extra_packages = extra_packages
        self.extra_env_vars = extra_env_vars
        # TODO: Deprecate this?
        self.insecure_skip_fail2ban = insecure_skip_fail2ban

        self.banner = LAMPSIBLE_BANNER


    def set_action(self, action):
        self.action = action
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
        extravars = [
            'web_host',
            'apache_vhosts',
            'apache_vhost_name',
            'apache_document_root',
            'apache_server_admin',
            'apache_custom_conf_name',
            'ssl_certbot',
            'email_for_ssl',
            'certbot_domains_string',
            'ssl_test_cert',
            'ssl_selfsigned',
            'database_username',
            # TODO: Ansible Runner has a dedicated feature for dealing
            # with passwords. Likely we'll have to implement support
            # for that in ansible-directory-helper.
            # For the time being, however, treat it as an extravar.
            'database_password',
            'database_name',
            'database_host',
            'database_table_prefix',
            'extra_packages',
            'extra_env_vars',
            'insecure_skip_fail2ban',
        ]
        for varname in extravars:
            if varname == 'server_name':
                if FQDN.is_valid(self.web_host):
                    value = self.web_host
                else:
                    value = DEFAULT_APACHE_SERVER_NAME
            elif varname == 'certbot_domains_string':
                value = '-d {}'.format('-d '.join(self.domains_for_ssl))
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
            # TODO: We could do this better, like check the fact_cache and make sure
            # everything was alright, before returning 0.
            return 0
        except RuntimeError:
            return 1
