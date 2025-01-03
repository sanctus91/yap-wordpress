import argparse
from ansible_runner import Runner, RunnerConfig, run_command
from . import __version__
from .constants import *
from .lampsible import Lampsible
from .arg_validator import ArgValidator


def main():

    parser = argparse.ArgumentParser(
        prog='lampsible',
        description='LAMP Stacks with Ansible',
    )

    # ----------------------
    #                      -
    #  Required arguments  -
    #                      -
    # ----------------------

    parser.add_argument('web_user_host', nargs='?',
        help="example: someuser@somehost.com"
    )
    parser.add_argument('action', choices=SUPPORTED_ACTIONS, nargs='?')

    # ----------------------
    #                      -
    #  Basic Options       -
    #                      -
    # ----------------------

    # Ansible Runner
    # --------------
    parser.add_argument('--ask-remote-sudo', action='store_true',
        help="""
        Pass this flag if you want to be prompted for the sudo password
        of the remote server.
        """
    )

    # Apache
    # ------
    parser.add_argument('-a', '--apache-server-admin',
        default=DEFAULT_APACHE_SERVER_ADMIN,
        help="""
        the email address of the server administrator,
        which is passed to Apache's 'ServerAdmin' configuration.
        Defaults to '{}' but if you should pass in a real email address.
        """.format(DEFAULT_APACHE_SERVER_ADMIN)
    )

    # Database
    # --------
    parser.add_argument('-d', '--database-username',
        help="""
        database user - If your website requires a database,
        and you leave this blank, you will be prompted to enter a value,
        or default to '{}'.
        If no database is required, and you leave this blank,
        no database user will be created.
        """.format(DEFAULT_DATABASE_USERNAME)
    )
    parser.add_argument('-n', '--database-name',
        help="""
        name of your database - If your website requires a database,
        and you leave this blank, you will be prompted to enter a value,
        or default to a sensible default,
        depending on your app.
        If no database is required, and you leave this blank,
        no database will be created.
        """
    )
    parser.add_argument('--database-host', default=DEFAULT_DATABASE_HOST)
    parser.add_argument('--database-system-user-host',
        help="""
        If database server is different than web server,
        pass this, and Ansible will install database stuff here.
        Otherwise, leave blank, and Ansible will install database
        stuff on web server, like in v1.
        """
    )
    # TODO
    # parser.add_argument('--database-engine', default=DEFAULT_DATABASE_ENGINE)

    # PHP
    # ---
    parser.add_argument('-p', '--php-version', default=DEFAULT_PHP_VERSION,
        help="""
        the version of PHP to be installed, defaults to '{}'.
        Leave it blank to let Lampsible pick the right version
        based on your remote server
        """.format(DEFAULT_PHP_VERSION)
    )
    # TODO
    # parser.add_argument('--php-my-admin', action='store_true')

    # All CMS
    # -------
    parser.add_argument('--site-title', '-t',
        help="""
        The "Site Title" configuration of your website.
        If you leave this blank, you will be prompted to enter a value,
        or default to '{}'
        """.format(DEFAULT_SITE_TITLE)
    )
    parser.add_argument('--admin-username',
        help="""
        The admin username of your website.
        If you leave this blank, you will be prompted to enter a value,
        or default to '{}'
        """.format(DEFAULT_ADMIN_USERNAME)
    )
    parser.add_argument('--admin-email',
        help="""
        The email address of your website's admin username.
        If you leave this blank, you will be prompted to enter a value,
        or default to '{}'
        """.format(DEFAULT_ADMIN_EMAIL)
    )

    # WordPress
    # ---------
    parser.add_argument('-w', '--wordpress-version',
        default=DEFAULT_WORDPRESS_VERSION,
        help="""
        the version of WordPress to be installed, defaults to '{}'
        """.format(DEFAULT_WORDPRESS_VERSION)
    )
    parser.add_argument('--wordpress-locale',
        default=DEFAULT_WORDPRESS_LOCALE,
        help="the locale of your WordPress site, defaults to '{}'".format(
            DEFAULT_WORDPRESS_LOCALE
        )
    )

    # Joomla
    # ------

    parser.add_argument('--joomla-version', '-j',
        default=DEFAULT_JOOMLA_VERSION)
    parser.add_argument('--joomla-admin-full-name', '-J')

    # Drupal
    # ------

    parser.add_argument('--drupal-profile', choices=AVAILABLE_DRUPAL_PROFILES,
        default=DEFAULT_DRUPAL_PROFILE,
            help="""
            Drupal supports various "profiles".
            Out of the box, these are available: {}.
            Defaults to {}
            """.format(
                ', '.join(AVAILABLE_DRUPAL_PROFILES),
                DEFAULT_DRUPAL_PROFILE)
    )

    # Web applications
    # ----------------
    parser.add_argument('--app-name', default='laravel-app',
        help="""
        the name of your Laravel app, if you're installing one.
        Leave blank to default to 'laravel-app'
        """
    )

    parser.add_argument('--app-build-path',
        help="""
        If you are installing a Laravel app,
        use this option to specify the local path of a production ready
        build-archive of your app,
        for example /path/to/some-app-2.0.tar.gz
        """
    )

    # SSL
    # ---
    parser.add_argument('--ssl-test-cert', action='store_true',
        help="""
        Set this flag to run certbot with the '--test-cert' flag.
        This is useful if you frequently set up a test server,
        and need to avoid being rate limited by Let's Encrypt.
        """
    )
    parser.add_argument('--ssl-selfsigned', action='store_true',
        help="""
        Pass this flag to generate a self signed SSL certificate for your site.
        You should only do this on test servers,
        because it makes your site look untrustworthy to visitors.
        """
    )
    # SSL
    # ---
    parser.add_argument('--email-for-ssl',
        help="""
        the email address that will be passed to Certbot.
        If left blank, the value of '--apache-server-admin'
        will be used instead.
        """
    )
    parser.add_argument('--domains-for-ssl',
        help="""
        a comma separated list of domains that will be passed to Certbot.
        If left blank, Lampsible will figure out what to use
        based on your host and action.
        """
    )
    parser.add_argument('--insecure-no-ssl', action='store_true',
        help="""
        Pass this flag to set up your website without any SSL encryption.
        This is insecure, and should only be done on test servers in
        local networks.
        """
    )

    # ----------------------
    #                      -
    #  Advanced Options    -
    #                      -
    # ----------------------

    # Ansible Runner
    # --------------
    parser.add_argument('--remote-sudo-password',
        help="""
        sudo password of the remote server,
        this only works if you also pass '--insecure-cli-password'.
        This is not recommended, you should use '--ask-remote-sudo' instead.
        """
    )
    parser.add_argument('--ssh-key-file', '-i',  help='path to your private SSH key')
    parser.add_argument('--private-data-dir',
        default=DEFAULT_PRIVATE_DATA_DIR,
        help="""
        the "private data directory" that Ansible Runner will use.
        Default is '{}'. You can use this flag to pass an alternative value.
        However, it's best to just leave this blank.
        Be advised that Ansible Runner will write sensitive data here,
        like your private SSH key and passwords,
        but Lampsible will delete this directory when it finishes.
        """
    )

    # Apache
    # ------
    parser.add_argument('--apache-vhost-name',
        default=DEFAULT_APACHE_VHOST_NAME,
        help="""
        the name of your site's Apache virtual host - leave this blank to
        let Lampsible pick a good default."
        """
    )
    parser.add_argument('--apache-document-root',
        default=DEFAULT_APACHE_DOCUMENT_ROOT,
        help="""
        your Apache virtual hosts' 'DocumentRoot' configuration - leave this
        blank to let Lampsible pick a good default.
        """
    )

    # Database
    # --------
    parser.add_argument('--database-password',
        help="""
        Use this flag to pass in the database password directly. This is
        not advised, and will only work if you also pass
        '--insecure-cli-password'. You should leave this blank instead,
        and Lampsible will prompt you for a password.
        """
    )
    parser.add_argument('--database-table-prefix',
        default=DEFAULT_DATABASE_TABLE_PREFIX,
        help="""
        prefix for your database tables, this is currently only used by
        WordPress, where it defaults to '{}'
        """.format(DEFAULT_DATABASE_TABLE_PREFIX)
    )

    # PHP
    # ---
    parser.add_argument('--php-extensions',
        help="""
        A comma separated list of PHP extensions to install.
        For example, if you pass
        '--php-version 8.2 --php-extensions mysql,mbstring',
        Lampsible will install the packages php8.2-mysql and php8.2-mbstring.
        However, it's best to leave this blank, and let Lampsible pick
        sensible defaults depending on what you are installing.
        """
    )
    parser.add_argument('--composer-packages',
        help="""
        A comma separated list of PHP packages to install with Composer.
        """
    )
    parser.add_argument('--composer-working-directory',
        help="""
        If you provide '--composer-packages', this will be
        the directory in which packages are installed.
        """
    )
    parser.add_argument('--composer-project',
        help="""
        Pass this flag to create the specified Composer project.
        """
    )

    # All CMS
    # -------
    parser.add_argument('--admin-password',
        help="""
        Use this flag to provide the admin password of your CMS directly.
        This is not advised, and will only work if you also pass
        '--insecure-cli-password'. You should leave this blank instead,
        and Lampsible will prompt you for a password.
        """
    )

    # WordPress
    # ---------
    parser.add_argument('--wordpress-insecure-allow-xmlrpc',
        action='store_true',
        help="""
        Pass this flag if you want your WordPress site's insecure(!)
        endpoint xmlrpc.php to be reachable.
        This will make your site vulnerable to various exploits,
        and you really shouldn't do this if you don't have a good
        reason for this.
        """
    )
    # TODO
    # parser.add_argument('--wordpress-skip-content', action='store_true')

    # Web applications
    # ----------------
    parser.add_argument('--app-local-env', action='store_true',
        help="""
        Pass this flag if you want your Laravel app to have the configurations
        'APP_ENV=local' and 'APP_DEBUG=true'. Otherwise, they'll default to
        'APP_ENV=production' and 'APP_DEBUG=false'.
        """
    )
    parser.add_argument('--laravel-artisan-commands',
        default=','.join(DEFAULT_LARAVEL_ARTISAN_COMMANDS),
        help="""
        a comma separated list of Artisan commands to run on your server after
        setting up your Laravel app there.
        Defaults to {}, which results in these commands being run: {}
        """.format(
            ','.join(DEFAULT_LARAVEL_ARTISAN_COMMANDS),
            '; '.join([
                'php /path/to/your/app/artisan {} --force'.format(artisan_command)
                for artisan_command in DEFAULT_LARAVEL_ARTISAN_COMMANDS
            ])
        )
    )

    # Misc
    # ----
    parser.add_argument('--insecure-cli-password', action='store_true',
        help="""
        If you want to pass passwords directly over the CLI,
        you have to pass this flag as well, otherwise Lampsible will
        refuse to run. This is not advised.
        """
    )
    parser.add_argument('--extra-packages',
        help="""
        comma separated list of any extra packages to be installed
        on the remote server
        """
    )
    parser.add_argument('--extra-env-vars', '-e',
        help="""
        comma separated list of any extra environment variables that you want
        to pass to your web app. If you are installing a Laravel app,
        these variables will be appended to your app's .env file.
        Otherwise, they'll be appended to Apache's envvars file,
        typically found in /etc/apache2/envvars.
        Example: SOME_VARIABLE=some-value,OTHER_VARIABLE=other-value
        """
    )

    # Metadata
    # --------
    parser.add_argument('-V', '--version',
        action='version',
        version=__version__
    )

    args = parser.parse_args()

    print(LAMPSIBLE_BANNER)

    # Fetching Ansible Facts
    # TODO: The only reason that we do this, is so we can check the
    # PHP version against the remote Ubuntu version. So we should
    # move this ArgValidator.validate_php_args, and only call it if
    # the user passed in a php_version.

    tmp_args = ArgValidator.pre_validate_args(args)
    if tmp_args == 1:
        print('FATAL! Got invalid user input, and cannot continue. Please fix the issues listed above and try again.')
        return 1

    tmp_rc = RunnerConfig(
        private_data_dir=tmp_args.private_data_dir,
        project_dir=PROJECT_DIR,
        inventory='{}@{},'.format(tmp_args.web_user, tmp_args.web_host),
        playbook='get-ansible-facts.yml',
    )

    if args.ssh_key_file:
        try:
            with open(os.path.abspath(args.ssh_key_file), 'r') as key_file:
                key_data = key_file.read()
            tmp_rc.ssh_key_data = key_data
        except FileNotFoundError:
            print('Warning! SSH key file not found!')

    tmp_rc.prepare()
    tmp_r = Runner(config=tmp_rc)
    tmp_r.run()

    ansible_facts = tmp_r.get_fact_cache('{}@{}'.format(tmp_args.web_user, tmp_args.web_host))

    validator = ArgValidator(args, ansible_facts)
    result = validator.validate_args()

    if result != 0:
        print('FATAL! Got invalid user input, and cannot continue. Please fix the issues listed above and try again.')
        return 1

    args = validator.get_validated_args()

    lampsible = Lampsible(
        web_user=args.web_user,
        web_host=args.web_host,
        action=args.action,
        private_data_dir=args.private_data_dir,
        apache_server_admin=args.apache_server_admin,
        apache_document_root=args.apache_document_root,
        apache_vhost_name=args.apache_vhost_name,
        # TODO: Improve this. The Lampsible library should handle this,
        # otherwise users will experience annoying errors.
        ssl_certbot=(not (
            args.insecure_no_ssl
            or args.ssl_selfsigned
            or args.action in [
                'dump-ansible-facts',
                'php',
                'mysql',
            ]
            )),
        ssl_selfsigned=args.ssl_selfsigned,
        ssl_test_cert=args.ssl_test_cert,
        email_for_ssl=args.email_for_ssl,
        database_username=args.database_username,
        database_password=args.database_password,
        database_name=args.database_name,
        database_host=args.database_host,
        database_table_prefix=args.database_table_prefix,
        database_system_user=args.database_system_user,
        database_system_host=args.database_system_host,
        php_version=args.php_version,
        php_extensions=args.php_extensions,
        composer_packages=args.composer_packages,
        composer_working_directory=args.composer_working_directory,
        composer_project=args.composer_project,
        site_title=args.site_title,
        admin_username=args.admin_username,
        admin_password=args.admin_password,
        admin_email=args.admin_email,
        wordpress_version=args.wordpress_version,
        wordpress_locale=args.wordpress_locale,
        wordpress_insecure_allow_xmlrpc=args.wordpress_insecure_allow_xmlrpc,
        joomla_version=args.joomla_version,
        joomla_admin_full_name=args.joomla_admin_full_name,
        drupal_profile=args.drupal_profile,
        app_name=args.app_name,
        app_build_path=args.app_build_path,
        laravel_artisan_commands=args.laravel_artisan_commands,
        app_local_env=args.app_local_env,
        extra_env_vars=args.extra_env_vars,
        extra_packages=args.extra_packages,
        ssh_key_file=args.ssh_key_file,
        remote_sudo_password=args.remote_sudo_password
    )

    # TODO: Improve this?
    galaxy_result = ensure_ansible_galaxy_dependencies(
        os.path.join(
            PROJECT_DIR,
            'ansible-galaxy-requirements.yml'
        ),
        USER_HOME_DIR
    )
    if galaxy_result == 1:
        return 1


    if args.action == 'dump-ansible-facts':
        # TODO: Refactor this.
        run_command(
            executable_cmd='ansible',
            cmdline_args=[
                '-i',
                '{}@{},'.format(
                    args.web_user,
                    args.web_host,
                ),
                'ungrouped',
                '-m',
                'setup'
            ]
        )
        lampsible.private_data_helper.cleanup_dir()
        return 0

    else:
        lampsible.run()

    return 0


if __name__ == '__main__':
    main()
