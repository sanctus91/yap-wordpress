import os
import warnings
from shutil import rmtree
from ansible_runner import (
    Runner, RunnerConfig, run_command, run as ansible_runner_run
)
from ansible_directory_helper.private_data import PrivateData
from . import __version__
from .constants import *
from .arg_validator import ArgValidator


class Lampsible:

    # TODO: Maybe 'action' should be optional?
    def __init__(self, web_user, web_host, action,
            private_data_dir=DEFAULT_PRIVATE_DATA_DIR,
            # These are from CLI flags. There were a few that I skipped,
            # because they either will be deprecated, or are not relevant in
            # this context.
            # TODO: Maybe type hint, and maybe use default values?
            apache_server_admin=None, database_username=None,
            database_name=None, database_host=None, database_system_user=None,
            database_system_host=None, php_version=None, site_title=None,
            admin_username=None, admin_email=None, wordpress_version=None,
            wordpress_locale=None, joomla_version=None,
            joomla_admin_full_name=None, drupal_profile=None, app_name=None,
                                 # TODO: Deprecate this one
            app_build_path=None, ssl_certbot=None,
            ssl_selfsigned=None, remote_sudo_password=None,
            ssh_key_file=None, apache_vhost_name=None,
            apache_document_root=None, database_password=None,
            database_table_prefix=None, php_extensions=None,
            composer_packages=None, composer_working_directory=None,
            composer_project=None, admin_password=None,
            wordpress_insecure_allow_xmlrpc=None, app_local_env=None,
            laravel_artisan_commands=None, email_for_ssl=None,
            domains_for_ssl=None, test_cert=None, insecure_skip_fail2ban=None,
            extra_packages=None, extra_env_vars=None,

            # These are from arg_validator. In v1, arg_validator generates these
            # variables, and passes them into extravars. We'll still need them here.
            apache_vhosts=None, apache_custom_conf_name=None,
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
        self.action   = action

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
        # ...
        self.apache_document_root = apache_document_root
        self.apache_vhost_name = apache_vhost_name
        self.apache_server_admin = apache_server_admin
        self.ssl_selfsigned = ssl_selfsigned
        self.app_name = app_name
        # ...
        self.database_password = database_password
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

        self.banner = LAMPSIBLE_BANNER


    
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


    def _prepare_runner_config(self):
        self.runner_config.prepare()


    # TODO: Do it this way?
    #def dump_ansible_facts(self):
    #    ansible_runner_run(
    #        private_data_dir=self.private_data_dir,
    #        host_pattern=self.web_host,
    #        module='setup',
    #        module_args='no_log=true'
    #    )



        


    # TODO: I don't think we should do it this way. Instead, be able to set
    # individual fields.
    def set_runner_config(self, runner_config):
        self.runner_config = runner_config


    def run(self):
        self._validate_args()
        self._prepare_runner_config()
        self.runner.run()
