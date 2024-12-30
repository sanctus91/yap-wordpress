import os
from re import match
from copy import copy, deepcopy
from warnings import warn
from getpass import getpass
from requests import head as requests_head
# from fqdn import FQDN
from ansible_runner import Runner, RunnerConfig
from ansible_directory_helper.inventory_file import InventoryFile
from lampsible.constants import *


class ArgValidator():

    def __init__(self, args, ansible_facts):
        self.args           = args
        self.validated_args = deepcopy(args)
        self.ansible_facts  = ansible_facts


    @staticmethod
    def pre_validate_args(raw_args):
        tmp_args = deepcopy(raw_args)
        try:
            os.makedirs(tmp_args.private_data_dir)
        except FileExistsError:
            pass

        try:
            tmp_inventory = tmp_args.web_user_host.split('@')
            assert len(tmp_inventory) == 2
            tmp_args.web_user = tmp_inventory[0]
            tmp_args.web_host = tmp_inventory[1]
        except (AttributeError, AssertionError):
            print('FATAL! First positional argument must be in the format of user@host')
            return 1
        return tmp_args


    def get_validated_args(self):
        return self.validated_args


    def get_apache_vhosts(self):
        return self.apache_vhosts


    # TODO: No more need for this, get rid of it.
    def get_apache_custom_conf_name(self):
        try:
            return self.apache_custom_conf_name
        except AttributeError:
            return ''


    def get_wordpress_url(self):
        try:
            return self.wordpress_url
        except AttributeError:
            return ''


    # TODO: No more need for this, get rid of it.
    def get_apache_allow_override(self):
        return (
            self.validated_args.action in ['laravel', 'drupal']
            or (
                self.validated_args.action == 'wordpress'
                and not self.validated_args.wordpress_insecure_allow_xmlrpc
            )
        )


    def get_certbot_domains_string(self):
        try:
            return '-d {}'.format(' -d '.join(self.validated_args.domains_for_ssl))
        except TypeError:
            return ''


    def get_certbot_test_cert_string(self):
        return '--test-cert' if self.validated_args.test_cert else ''


    # TODO: Deprecate this in favor of Lampsible._update_env
    def get_extravars_dict(self):
        extravars = {
            'web_host': self.validated_args.web_host,
            'apache_vhosts': self.get_apache_vhosts(),
            'apache_document_root': self.validated_args.apache_document_root,
            'apache_vhost_name': self.validated_args.apache_vhost_name,
            'apache_custom_conf_name': self.get_apache_custom_conf_name(),
            'database_username': self.validated_args.database_username,
            'database_password': self.validated_args.database_password,
            'database_host': self.validated_args.database_host,
            'database_name': self.validated_args.database_name,
            'database_table_prefix': self.validated_args.database_table_prefix,
            'ssl_certbot': self.validated_args.ssl_certbot,
            'ssl_selfsigned': self.validated_args.ssl_selfsigned,
            'email_for_ssl': self.validated_args.email_for_ssl,
            'certbot_domains_string': self.get_certbot_domains_string(),
            'certbot_test_cert_string': self.get_certbot_test_cert_string(),
            'insecure_skip_fail2ban': self.validated_args.insecure_skip_fail2ban,
            'extra_packages': self.validated_args.extra_packages,
            'extra_env_vars': self.validated_args.extra_env_vars,
        }
        if self.validated_args.remote_sudo_password:
            # TODO
            # TODO: It would be better to not include this as an extravar, but to
            # make use of Ansible Runner's password feature in the
            # Input Directory Hierarchy.
            extravars['ansible_sudo_pass'] = self.validated_args.remote_sudo_password

        if self.args.action in [
            'lamp-stack',
            'php',
            'wordpress',
            'joomla',
            'laravel',
            'drupal',
        ]:
            extravars['php_version'] = self.validated_args.php_version
            extravars['php_extensions'] = self.validated_args.php_extensions
            extravars['composer_packages'] = self.validated_args.composer_packages
            extravars['composer_working_directory'] = \
                    self.validated_args.composer_working_directory
            extravars['composer_project'] = self.validated_args.composer_project

        if self.args.action in [
            'wordpress',
            'joomla',
            'drupal',
        ]:
            extravars['site_title'] = self.validated_args.site_title
            extravars['admin_username'] = self.validated_args.admin_username
            extravars['admin_email'] = self.validated_args.admin_email
            extravars['admin_password'] = self.validated_args.admin_password

        if self.args.action == 'wordpress':
            extravars['wordpress_version'] = self.validated_args.wordpress_version
            extravars['wordpress_locale'] = self.validated_args.wordpress_locale
            extravars['wordpress_insecure_allow_xmlrpc'] = \
                self.validated_args.wordpress_insecure_allow_xmlrpc
            extravars['wordpress_url'] = self.get_wordpress_url()

        elif self.args.action == 'joomla':
            # TODO: We could do something like 'cms_version' instead.
            extravars['joomla_version'] = self.validated_args.joomla_version
            extravars['joomla_admin_full_name'] = \
                self.validated_args.joomla_admin_full_name

        elif self.args.action == 'laravel':
            extravars['app_build_path'] = self.validated_args.app_build_path
            extravars['app_source_root'] = self.validated_args.app_source_root
            extravars['app_local_env'] = self.validated_args.app_local_env
            extravars['laravel_artisan_commands'] = \
                self.validated_args.laravel_artisan_commands
            extravars['laravel_extra_env_vars'] = self.validated_args.laravel_extra_env_vars

        elif self.args.action == 'drupal':
            extravars['drupal_profile'] = self.validated_args.drupal_profile

        return extravars


    def handle_defaults(
        self,
        default_args,
        ask_user=False,
        verbose=False
    ):
        """Handles defaults in various cases, optionally setting values with
        application wide defaults or overriding values, and optionally
        printing warnings.

        Positional arguments

        default_args -- A list of dictionaries, which defines the arguments,
                        and how to treat them. The following dictionary serves
                        as an example:
            {
                # required
                'arg_name': 'some_cli_arg', # The user passed this in as
                                            # --some-cli-arg - We also have a
                                            # helper function to get the arg
                                            # name in that format.
                # required
                'cli_default_value': DEFAULT_ARG_VALUE,
                # optional
                'override_default_value': 'some use case specific default',
            }

        ask_user -- Optional. If True, then if we got default values,
                    prompt the user to input their own value,
                    and if they leave it blank,
                    fall back to default values. Defaults to False.

        verbose --  Optional. If True, then if we are using some
                    default value, warn the user about this. This is useful
                    for credentials, in case we're falling back to some
                    insecure value.
        """
        for arg_dict in default_args:
            try:
                default_value = arg_dict['override_default_value']
            except KeyError:
                default_value = arg_dict['cli_default_value']
            user_value = getattr(self.args, arg_dict['arg_name'])

            if user_value == arg_dict['cli_default_value']:
                if ask_user:
                    tmp_val = input(
                        'Got no {}. Please enter a value now, or leave blank to default to \'{}\': '.format(

                            self.var_name_to_cli_arg(arg_dict['arg_name']),
                            default_value
                        )
                    )
                    if tmp_val == '':
                        tmp_val = default_value
                    default_value = tmp_val

                setattr(
                    self.validated_args,
                    arg_dict['arg_name'],
                    default_value
                )

                if verbose:
                    print('\nUsing {} value \'{}\'.'.format(
                        self.var_name_to_cli_arg(arg_dict['arg_name']),
                        default_value
                    ))


    def var_name_to_cli_arg(self, var_name):
        return '--{}'.format(var_name.replace('_', '-'))


    def get_pass_and_check(self, prompt, min_length=0, confirm=False):
        password = getpass(prompt)
        while min_length > 0 and len(password) < min_length:
            password = getpass('That password is too short. Please enter another password: ')
        if confirm:
            double_check = getpass('Please retype password: ')
            if password == double_check:
                return password
            else:
                print('\nPasswords don\'t match. Please try again.')
                return self.get_pass_and_check(prompt, min_length, True)
        else:
            return password


    def validate_ansible_runner_args(self):
        if self.args.web_user_host:
            try:
                web_user_host = self.args.web_user_host.split('@')
                self.validated_args.web_user = web_user_host[0]
                self.validated_args.web_host = web_user_host[1]
            except (IndexError, AttributeError):
                print("FATAL! First positional argument must be in the format of 'user@host'.")
                return 1
        elif not (self.args.web_user and self.args.web_host):
            print("FATAL! Got no 'web_user' and 'web_host'.")
            return 1

        if self.args.database_system_user_host:
            try:
                db_sys_user_host = self.args.database_system_user_host.split('@')
                self.validated_args.db_sys_user = db_sys_user_host[0]
                self.validated_args.db_sys_host = db_sys_user_host[1]
            except IndexError:
                print("FATAL! --database-system-user-host must be in the format of 'user@host'. Alternatively, omit it to install database on web server.")
                return 1
        else:
            # TODO: This is already taken care of in the Lampsible constructor.
            self.validated_args.db_sys_user = self.validated_args.web_user
            self.validated_args.db_sys_host = self.validated_args.web_host
        if self.args.action not in SUPPORTED_ACTIONS:
            print('FATAL! Second positional argument must be one of {}'.format(
                ', '.join(SUPPORTED_ACTIONS)
            ))
            return 1

        if self.args.remote_sudo_password \
            and not self.args.insecure_cli_password:
            print(INSECURE_CLI_PASS_WARNING)
            return 1
        if self.args.ask_remote_sudo:
            self.validated_args.remote_sudo_password = self.get_pass_and_check(
                'Please enter sudo password for remote host: ')
        return 0


    # TODO: Most of this, if not all of it, is being moved to Lampsible.set_apache_args.
    # Refactor this.
    # def validate_apache_args(self):

    #     server_name = self.validated_args.web_host
    #     try:
    #         assert FQDN(server_name).is_valid
    #     except AssertionError:
    #         server_name = DEFAULT_APACHE_SERVER_NAME

    #     if self.args.action in [
    #         'wordpress',
    #         'joomla',
    #     ]:
    #         if self.args.apache_document_root == DEFAULT_APACHE_DOCUMENT_ROOT:
    #             self.validated_args.apache_document_root = '{}/{}'.format(
    #                 DEFAULT_APACHE_DOCUMENT_ROOT,
    #                 self.args.action
    #             )

    #         if self.args.apache_vhost_name == DEFAULT_APACHE_VHOST_NAME:
    #             self.validated_args.apache_vhost_name = self.args.action

    #     elif self.args.action == 'drupal':
    #         if self.args.apache_document_root == DEFAULT_APACHE_DOCUMENT_ROOT:
    #             self.validated_args.apache_document_root = '{}/drupal/web'.format(
    #                 DEFAULT_APACHE_DOCUMENT_ROOT
    #             )

    #     elif self.args.action == 'laravel':
    #         if self.args.apache_document_root == DEFAULT_APACHE_DOCUMENT_ROOT:
    #             self.validated_args.apache_document_root = '{}/{}/public'.format(
    #                 DEFAULT_APACHE_DOCUMENT_ROOT,
    #                 self.args.app_name
    #             )

    #         if self.args.apache_vhost_name == DEFAULT_APACHE_VHOST_NAME:
    #             self.validated_args.apache_vhost_name = self.args.app_name

    #     base_vhost_dict = {
    #         'base_vhost_file': '{}.conf'.format(DEFAULT_APACHE_VHOST_NAME),
    #         'document_root':  self.validated_args.apache_document_root,
    #         'vhost_name':     self.validated_args.apache_vhost_name,
    #         'server_name':    server_name,
    #         'server_admin':   self.args.apache_server_admin,
    #         'allow_override': self.get_apache_allow_override(),
    #     }

    #     self.apache_vhosts = [base_vhost_dict]

    #     if self.args.ssl_selfsigned:

    #         # TODO: Use deepcopy?
    #         ssl_vhost_dict = copy(base_vhost_dict)

    #         ssl_vhost_dict['base_vhost_file'] = 'default-ssl.conf'
    #         ssl_vhost_dict['vhost_name']      += '-ssl'

    #         self.apache_vhosts.append(ssl_vhost_dict)

    #         if self.args.ssl_selfsigned:
    #             self.apache_custom_conf_name = 'ssl-params'

    #     return 0


    def validate_database_args(self):

        default_database_names = {
            'wordpress': 'wordpress',
            'joomla':    'joomla',
            'drupal':    'drupal',
            'laravel':   self.args.app_name,
        }

        default_database_table_prefixes = {
            'wordpress': 'wp_',
            # TODO?
            'joomla':    '',
            'drupal':    '',
            'laravel':   '',
        }
        if self.args.database_password \
            and not self.args.insecure_cli_password:

            print(INSECURE_CLI_PASS_WARNING)
            return 1

        if self.args.action in [
            'wordpress',
            'joomla',
            'drupal',
            'laravel',
        ]:
            self.handle_defaults([
                {
                    'arg_name': 'database_name',
                    'cli_default_value': None,
                    'override_default_value': default_database_names[
                        self.args.action],
                },
                {
                    'arg_name': 'database_username',
                    'cli_default_value': None,
                    'override_default_value': DEFAULT_DATABASE_USERNAME,
                },
                {
                    'arg_name': 'database_table_prefix',
                    'cli_default_value': DEFAULT_DATABASE_TABLE_PREFIX,
                    'override_default_value': default_database_table_prefixes[
                        self.args.action],
                },
            ], True, True)

        if self.validated_args.database_username and not self.validated_args.database_password:
            self.validated_args.database_password = self.get_pass_and_check(
                'Please enter a database password: ',
                0,
                True
            )

        return 0


    # TODO: Much of this is being moved to Lampsible constructor and _update_env.
    # Refactor this.
    def validate_ssl_args(self):

        if self.args.ssl_certbot:
            ssl_action = 'certbot'
        elif self.args.ssl_selfsigned:
            ssl_action = 'selfsigned'
        else:
            ssl_action = None

        if ssl_action == 'certbot':
            self.handle_defaults([
                {
                    'arg_name': 'domains_for_ssl',
                    'cli_default_value': None,
                    'override_default_value': [self.validated_args.web_host],
                },
                {
                    'arg_name': 'email_for_ssl',
                    'cli_default_value': None,
                    'override_default_value': self.args.apache_server_admin,
                },
            ])

            if not match(r"[^@]+@[^@]+\.[^@]+", self.validated_args.email_for_ssl):
                print("\nFATAL! --email-for-ssl needs to be valid. Got '{}'. Aborting.".format(
                    self.args.email_for_ssl))
                return 1

        return 0


    # TODO: Some of this is moving to the Lampsible class as well.
    # Refactor this.
    def validate_php_args(self):

        if self.args.action in [
            'apache',
            # TODO: But if 'mysql' was passed with '--php-myadmin',
            # then we do need it. But PMA is not implemented currently.
            'mysql',
            'dump-ansible-facts',
        ]:
            return 0

        # TODO: We don't really need this anymore, because 'apt install php'
        # will work just as well as for example 'apt install php8.3'
        if self.args.php_version:
            if int(self.ansible_facts['ubuntu_version']) <= 20:
                ubuntu_version = 'legacy'
            else:
                ubuntu_version = self.ansible_facts['ubuntu_version']

            ubuntu_to_php_version = {
                'legacy': '7.4',
                '21'    : '8.0',
                '22'    : '8.1',
                '23'    : '8.2',
                '24'    : '8.3',
                'latest': '8.3',
            }
            # Sanity check
            if self.validated_args.php_version not in SUPPORTED_PHP_VERSIONS:
                print('FATAL! Invalid PHP version!')
                return 1
            # User passed a value, warn them if it's likely to not work.
            # TODO: In the future, we should have a global "non-interactive" flag,
            # based on which this can be handled better, for example, "interactive"
            # mode could offer to correct the user's input.
            elif self.validated_args.php_version != ubuntu_to_php_version[ubuntu_version]:
                print('Warning! You are trying to install PHP {} on Ubuntu {}. Unless you manually configured the APT repository, this will not work.'.format(
                    self.validated_args.php_version,
                    self.ansible_facts['ubuntu_version']
                ))

        # TODO: A little redundant maybe because the Lampsible class now does something similar.
        # Based on the action, it appends anything else that it might need.
        # But this is still needed as well.
        if self.args.php_extensions:
            extensions = [
                extension.strip()
                for extension in self.args.php_extensions.split(',')
            ]
        elif self.args.action == 'lamp-stack':
            extensions = ['mysql']

        elif self.args.action == 'wordpress':
            extensions = ['mysql']

        elif self.args.action == 'joomla':
            extensions = [
                'simplexml',
                'dom',
                'zip',
                'gd',
                'mysql',
            ]

        elif self.args.action == 'drupal':
            extensions = [
                'mysql',
                'xml',
                'gd',
                'curl',
                'mbstring',
            ]

        elif self.args.action == 'laravel':
            extensions = [
                'mysql',
                'xml',
                'mbstring'
            ]

        else:
            extensions = []

        self.validated_args.php_extensions = [
            'php{}-{}'.format(
                str(self.validated_args.php_version or ''),
                extension
            ) for extension in extensions
        ]

        try:
            self.validated_args.composer_packages = self.args.composer_packages.split(',')
            for package in self.validated_args.composer_packages:
                assert len(package.split('/')) == 2
        except AttributeError:
            self.validated_args.composer_packages = []
        except AssertionError:
            print('Got invalid --composer-packages')
            return 1

        # This would break it I think.
        # self.handle_defaults(
        #     [{
        #         'arg_name': 'composer_working_directory',
        #         'cli_default_value': None,
        #         'override_default_value': self.validated_args.apache_document_root,
        #     }]
        # )

        return 0


    def validate_wordpress_args(self):
        if self.args.action != 'wordpress':
            return 0

        if not self.is_valid_wordpress_version(self.args.wordpress_version):
            print('\nInvalid WordPress version! Leave --wordpress-version blank to default to \'{}\''.format(DEFAULT_WORDPRESS_VERSION))
            return 1

        self.handle_defaults([
            {
                'arg_name': 'site_title',
                'cli_default_value': None,
                'override_default_value': DEFAULT_SITE_TITLE,
            },
            {
                'arg_name': 'admin_username',
                'cli_default_value': None,
                'override_default_value': DEFAULT_ADMIN_USERNAME,
            },
            {
                'arg_name': 'admin_email',
                'cli_default_value': None,
                'override_default_value': DEFAULT_ADMIN_EMAIL,
            },
        ], True, True)

        if self.args.admin_password \
            and not self.args.insecure_cli_password:
            print(INSECURE_CLI_PASS_WARNING)
            return 1

        if not self.args.admin_password:
            self.validated_args.admin_password = self.get_pass_and_check(
                "Please choose a password for the website's admin user: ",
                0,
                True
            )

        # TODO: This is moving to Lampsible._update_env.
        # if self.args.ssl_certbot:
        #     if self.web_host[:4] == 'www.':
        #         www_domain = self.web_host
        #     else:
        #         www_domain = 'www.{}'.format(self.web_host)

        #     if www_domain not in self.validated_args.domains_for_ssl:
        #         self.validated_args.domains_for_ssl.append(www_domain)

        #     self.wordpress_url = www_domain

        # else:
        #     self.wordpress_url = self.web_host

        return 0


    def is_valid_wordpress_version(self, wp_version):
        if wp_version in RECENT_WORDPRESS_VERSIONS:
            return True

        try:
            r = requests_head(
                'https://wordpress.org/wordpress-{}.tar.gz'.format(wp_version)
            )
            assert r.status_code == 200
            return True
        except AssertionError:
            return False


    def validate_joomla_args(self):
        if self.args.action != 'joomla':
            return 0

        if self.validated_args.php_version:
            if int(self.args.joomla_version[0]) >= 5 \
                    and float(self.validated_args.php_version) < 8.1:
                print('FATAL! Joomla versions 5 and newer require minimum PHP version 8.1!')
                return 1
            elif int(self.args.joomla_version[0]) >= 4 \
                    and float(self.validated_args.php_version) < 7.2:
                # Actually it requires at least 7.2.5, but I'm trusting package managers
                # to get this right, also, no one should be using that old stuff anymore.
                print('FATAL! Joomla 4 requires minimum PHP version 7.2!')
                return 1

        self.handle_defaults([
            {
                'arg_name': 'site_title',
                'cli_default_value': None,
                'override_default_value': DEFAULT_SITE_TITLE,
            },
            {
                'arg_name': 'admin_username',
                'cli_default_value': None,
                'override_default_value': DEFAULT_ADMIN_USERNAME,
            },
            {
                'arg_name': 'admin_email',
                'cli_default_value': None,
                'override_default_value': DEFAULT_ADMIN_EMAIL,
            },
            {
                'arg_name': 'joomla_admin_full_name',
                'cli_default_value': None,
                'override_default_value': DEFAULT_JOOMLA_ADMIN_FULL_NAME,
            },
        ], True, True)

        # TODO: If instead of returning 1 we throw an exception, we could make
        # a small helper function out of this, see validate_wordpress_args.
        if self.args.admin_password \
            and not self.args.insecure_cli_password:
            print(INSECURE_CLI_PASS_WARNING)
            return 1

        if not self.args.admin_password:
            self.validated_args.admin_password = self.get_pass_and_check(
                "Please choose a password for the website's admin user: ",
                12,
                True
            )
        if self.args.extra_env_vars:
            print('Warning! You provided values for --extra-env-vars, but Joomla will not register these. What you are trying to do will likely not work.')

        return 0


    def validate_drupal_args(self):

        if self.args.action != 'drupal':
            return 0

        if self.validated_args.php_version \
                and float(self.validated_args.php_version) < 8.3:
            print('The latest version of Drupal requires minimum PHP 8.3.')
            return 1

        self.handle_defaults([
            {
                'arg_name': 'site_title',
                'cli_default_value': None,
                'override_default_value': DEFAULT_SITE_TITLE,
            },
            {
                'arg_name': 'admin_username',
                'cli_default_value': None,
                'override_default_value': DEFAULT_ADMIN_USERNAME,
            },
            {
                'arg_name': 'admin_email',
                'cli_default_value': None,
                'override_default_value': DEFAULT_ADMIN_EMAIL,
            },
        ], True, True)

        # TODO: If instead of returning 1 we throw an exception, we could make
        # a small helper function out of this, see validate_wordpress_args.
        if self.args.admin_password \
            and not self.args.insecure_cli_password:
            print(INSECURE_CLI_PASS_WARNING)
            return 1

        if not self.args.admin_password:
            self.validated_args.admin_password = self.get_pass_and_check(
                "Please choose a password for the website's admin user: ",
                8,
                True
            )
        return 0


    def validate_app_args(self):
        if self.args.action not in [
            'laravel',
        ]:
            return 0

        try:
            self.validated_args.app_build_path = os.path.abspath(self.args.app_build_path)
            assert os.path.isfile(self.validated_args.app_build_path)
        except TypeError:
            print('FATAL! --app-build-path required! Please specify the path of a build archive of your application.')
            return 1
        except AssertionError:
            print('FATAL! {} not found on local file system.'.format(
                self.validated_args.app_build_path
            ))
            return 1

        self.validated_args.laravel_artisan_commands = \
            self.args.laravel_artisan_commands.split(',')

        return 0


    def validate_misc_args(self):
        try:
            self.validated_args.extra_packages = self.args.extra_packages.split(',')
        except AttributeError:
            self.validated_args.extra_packages = []

        self.validated_args.extra_env_vars = {}
        try:
            tmp_split_vars = self.args.extra_env_vars.split(',')
            try:
                for key_eq_val in tmp_split_vars:
                    tmp_var = key_eq_val.split('=')
                    assert len(tmp_var) == 2
                    self.validated_args.extra_env_vars[tmp_var[0]] = tmp_var[1]
            except AssertionError:
                print('FATAL! Invalid --extra-env-vars. Aborting.')
                return 1
        except AttributeError:
            pass

        return 0


    def print_warnings(self):
        if self.args.insecure_skip_fail2ban:
            print('\nWarning! Will not install fail2ban! Your site will potentially be vulnerable to various brute force attacks. You should only pass the \'--insecure-skip-fail2ban\' flag if you have a good reason to do so. On production servers, always install fail2ban!')

        if self.args.wordpress_insecure_allow_xmlrpc:
            print('\nWarning! Your WordPress site\'s xmlrpc.php endpoint will be enabled - this is insecure! The endpoint xmlrpc.php is a feature from older WordPress versions which allowed programmatic access to the WordPress backend. Although it has numerous known security vulnerabilities, namely a brute force and a DoS vulnerability, it is still, for some reason, enabled by default in current WordPress versions. Lampsible will, by default, block this endpoint with an .htaccess configuration, unless you specify otherwise, which you just did. You should not be doing this, unless you have some good reason to do so!')

        if self.args.ssl_certbot and self.args.ssl_selfsigned:
            print('\nWarning: Got --ssl-certbot, but also got --ssl-selfsigned. Ignoring --ssl-selfsigned and using --ssl-certbot.')
        elif self.args.ssl_selfsigned:
            print('\nWarning! Creating a self signed certificate to handle the site\'s encryption. This is less secure and will appear untrustworthy to any visitors. Only use this for testing environments.')
        elif not (self.args.ssl_selfsigned or self.args.ssl_certbot):
            print('\nWARNING! Your site will not have any encryption enabled! This is very insecure, as passwords and other sensitive data will be transmitted in clear text. DO NOT use this on any remote host or over any partially untrusted network. ONLY use this for local, secure, private and trusted networks, ideally only for local development servers.')


    def validate_args(self):
        validate_methods = [
            'validate_ansible_runner_args',
            # 'validate_apache_args',
            'validate_database_args',
            'validate_ssl_args',
            'validate_php_args',
            'validate_wordpress_args',
            'validate_joomla_args',
            'validate_drupal_args',
            'validate_app_args',
            'validate_misc_args',
        ]
        for method_name in validate_methods:
            method = getattr(self, method_name)
            result = method()
            if result != 0:
                return result

        self.print_warnings()
        return 0
