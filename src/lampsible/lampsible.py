import os
from sys import path as sys_path
import argparse
import warnings
from yaml import safe_load
from shutil import rmtree
from ansible_runner import Runner, RunnerConfig, run_command
from . import __version__
from lampsible.constants import *
from lampsible.arg_validator import ArgValidator


def init_private_data_dir(private_data_dir):
    try:
        os.makedirs(private_data_dir)
    except PermissionError:
        private_data_dir = os.path.join(USER_HOME_DIR, '.lampsible')
        print('Could not write specified directory. Defaulting to {}'.format(
            private_data_dir = os.path.join(USER_HOME_DIR, '.lampsible')
        ))
        os.makedirs(private_data_dir)
    except FileExistsError:
        pass

    return os.path.abspath(private_data_dir)


def init_project_dir(project_dir):
    if project_dir == '':
        return find_package_project_dir()
    return project_dir


def find_package_project_dir():
    for path_str in sys_path:
        try:
            try_path = os.path.join(path_str, 'lampsible', 'project')
            assert os.path.isdir(try_path)
            return try_path
        except AssertionError:
            pass
    raise RuntimeError("Got no user supplied --project-dir, and could not find one in expected package location. Your Lampsible installation is likely broken. However, if you are running this code directly from source, this is expected behavior. You probably forgot to pass the '--project-dir' flag. The directoy you're looking for is 'src/lampsible/project/'.")


def ensure_ansible_galaxy_dependencies(galaxy_requirements_file):
    with open(galaxy_requirements_file, 'r') as stream:
        required_collections = []
        tmp_collections = safe_load(stream)['collections']
        for tmp_dict in tmp_collections:
            required_collections.append(tmp_dict['name'])

    # TODO There might be a more elegant way to do this - Right now,
    # we're expecting required_collections to always be a tuple,
    # and searching for requirements in a big string, but yaml/dict
    # would be better.
    installed_collections = run_command(
        executable_cmd='ansible-galaxy',
        cmdline_args=[
            'collection',
            'list',
            '--collections-path',
            os.path.join(USER_HOME_DIR, '.ansible'),
        ],
        quiet=True
    )[0]
    missing_collections = []
    for required in required_collections:
        if required not in installed_collections:
            missing_collections.append(required)
    if len(missing_collections) == 0:
        return 0
    else:
        return install_galaxy_collections(missing_collections)



def install_galaxy_collections(collections):
    ok_to_install = input("\nI have to download and install the following Ansible Galaxy dependencies into {}:\n- {}\nIs this OK (yes/no)? ".format(
        os.path.join(USER_HOME_DIR, '.ansible/'),
        '\n- '.join(collections)
    )).lower()
    while ok_to_install != 'yes' and ok_to_install != 'no':
        ok_to_install = input("Please type 'yes' or 'no': ")
    if ok_to_install == 'yes':
        print('\nInstalling Ansible Galaxy collections...')
        run_command(
            executable_cmd='ansible-galaxy',
            cmdline_args=['collection', 'install'] + collections,
        )
        print('\n... collections installed.')
        return 0
    else:
        print('Cannot run Ansible plays without Galaxy requirements. Aborting.')
        return 1


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

    parser.add_argument('user_at_host', nargs='?',
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
        help="Pass this flag if you want to be prompted for the sudo password of the remote server.")

    # Apache
    # ------
    parser.add_argument('-a', '--apache-server-admin',
        default=DEFAULT_APACHE_SERVER_ADMIN,
        help="the email address of the server administrator, which is passed to Apache's 'ServerAdmin' configuration. Defaults to '{}' but if you are using '--ssl-cerbot', you should pass in a real email address".format(DEFAULT_APACHE_SERVER_ADMIN)
    )

    # Database
    # --------
    parser.add_argument('-d', '--database-username', help="database user - If your website requires a database, and you leave this blank, you will be prompted to enter a value, or default to '{}'. If no database is required, and you leave this blank, no database user will be created.".format(DEFAULT_DATABASE_USERNAME))
    parser.add_argument('-n', '--database-name', help="name of your database - If your website requires a database, and you leave this blank, you will be prompted to enter a value, or default to a sensible default, depending on your app. If no database is required, and you leave this blank, no database will be created.")
    # TODO
    # parser.add_argument('--database-host', default=DEFAULT_DATABASE_HOST)
    # parser.add_argument('--database-engine', default=DEFAULT_DATABASE_ENGINE)

    # PHP
    # ---
    parser.add_argument('-p', '--php-version', default=DEFAULT_PHP_VERSION,
        help="the version of PHP to be installed. Leave it blank to let Lampsible pick the right version based on your remote server."
    )
    # TODO
    # parser.add_argument('--php-my-admin', action='store_true')

    # All CMS
    # -------
    parser.add_argument('--site-title', '-t',
        help="The \"Site Title\" configuration of your website. If you leave this blank, you will be prompted to enter a value, or default to '{}'".format(
            DEFAULT_SITE_TITLE
        )
    )
    parser.add_argument('--admin-username',
        help="The admin username of your website. If you leave this blank, you will be prompted to enter a value, or default to '{}'".format(
            DEFAULT_ADMIN_USERNAME
        )
    )
    parser.add_argument('--admin-email',
        help="The email address of your website's admin username. If you leave this blank, you will be prompted to enter a value, or default to '{}'".format(
            DEFAULT_ADMIN_EMAIL
        )
    )

    # WordPress
    # ---------
    parser.add_argument('-w', '--wordpress-version',
        default=DEFAULT_WORDPRESS_VERSION,
        help="the version of WordPress to be installed, defaults to '{}'".format(
            DEFAULT_WORDPRESS_VERSION
        )
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
        default=DEFAULT_DRUPAL_PROFILE, help="Drupal supports various \"profiles\". Out of the box, these are available: {}. Defaults to {}".format(
            ', '.join(AVAILABLE_DRUPAL_PROFILES),
            DEFAULT_DRUPAL_PROFILE
        )
    )

    # Web applications
    # ----------------
    parser.add_argument('--app-name', default='laravel-app', help="the name of your Laravel app, if you're installing one. Leave blank to default to 'laravel-app'")
    parser.add_argument('--app-build-path', help="If you are installing a Laravel app, use this option to specify the local path of a production ready build-archive of your app, for example /path/to/some-app-2.0.tar.gz")

    # SSL
    # ---
    parser.add_argument('-s', '--ssl-certbot', action='store_true',
        help="Pass this flag to use Certbot to fully enable SSL for your site. You should also pass a valid email address to '--apache-server-admin', or alternatively to '--email-for-ssl'. If you are simply testing, pass '--test-cert' as well, to avoid being rate limited by Let's Encrypt."
    )
    parser.add_argument('--ssl-selfsigned', action='store_true',
        help="Pass this flag to generate a self signed SSL certificate for your site. You should only do this on test servers, because it makes your site look untrustworthy to visitors."
    )

    # ----------------------
    #                      -
    #  Advanced Options    -
    #                      -
    # ----------------------

    # Ansible Runner
    # --------------
    parser.add_argument('--remote-sudo-password', help="sudo password of the remote server, this only works if you also pass '--insecure-cli-password'. This is not recommended, you should use '--ask-remote-sudo' instead.")
    parser.add_argument('--ssh-key-file', '-i',  help='path to your private SSH key')
    parser.add_argument('--private-data-dir',
        default=DEFAULT_PRIVATE_DATA_DIR,
        help="the \"private data directory\" that Ansible Runner will use. Default is '{}'. You can use this flag to pass an alternative value. However, it's best to just leave this blank. Be advised that Ansible Runner will write sensitive data here, like your private SSH key and passwords, but Lampsible will delete this directory when it finishes.".format(
            DEFAULT_PRIVATE_DATA_DIR
        )
    )
    # parser.add_argument('--project-dir', '-Z', default=DEFAULT_PROJECT_DIR)

    # Apache
    # ------
    parser.add_argument('--apache-vhost-name',
        default=DEFAULT_APACHE_VHOST_NAME, help="the name of your site's Apache virtual host - leave this blank to let Lampsible pick a good default.")
    parser.add_argument('--apache-document-root',
        default=DEFAULT_APACHE_DOCUMENT_ROOT,
        help="your Apache virtual hosts' 'DocumentRoot' configuration - leave this blank to let Lampsible pick a good default."
    )

    # Database
    # --------
    parser.add_argument('--database-password',
        help="Use this flag to pass in the database password directly. This is not advised, and will only work if you also pass '--insecure-cli-password'. You should leave this blank instead, and Lampsible will prompt you for a password."
    )
    parser.add_argument('--database-table-prefix',
        default=DEFAULT_DATABASE_TABLE_PREFIX,
        help="prefix for your database tables, this is currently only used by WordPress, where it defaults to '{}'".format(
            DEFAULT_DATABASE_TABLE_PREFIX
        )
    )

    # PHP
    # ---
    parser.add_argument('--php-extensions', help="A comma separated list of PHP extensions to install. For example, if you pass '--php-version 8.2 --php-extensions mysql,mbstring', Lampsible will install the packages php8.2-mysql and php8.2-mbstring. However, it's best to leave this blank, and let Lampsible pick sensible defaults depending on what you are installing.")
    parser.add_argument('--composer-packages', help="A comma separated list of PHP packages to install with Composer.")
    parser.add_argument('--composer-working-directory', help="If you provide '--composer-packages', this will be the directory in which packages are installed.")
    parser.add_argument('--composer-project', help="Pass this flag to create the specified Composer project.")

    # All CMS
    # -------
    parser.add_argument('--admin-password',
        help="Use this flag to provide the admin password of your CMS directly. This is not advised, and will only work if you also pass '--insecure-cli-password'. You should leave this blank instead, and Lampsible will prompt you for a password."
    )

    # WordPress
    # ---------
    parser.add_argument('--wordpress-admin-password',
        help="deprecated, use '--admin-password' instead"
    )
    parser.add_argument('--wordpress-insecure-allow-xmlrpc',
        action='store_true',
        help="Pass this flag if you want your WordPress site's insecure(!) endpoint xmlrpc.php to be reachable. This will make your site vulnerable to various exploits, and you really shouldn't do this if you don't have a good reason for this."
    )
    # NOTE: Manually installing WordPress and passing the authentication salts
    # will be deprecated.
    parser.add_argument('--wordpress-manual-install', action='store_true',
        help="Pass this flag if you prefer to complete the \"Famous 5 Minute WordPress Install\" manually. This is not advised, and will be deprecated."
    )
    parser.add_argument('--wordpress-auth-key', help="deprecated")
    parser.add_argument('--wordpress-secure-auth-key', help="deprecated")
    parser.add_argument('--wordpress-logged-in-key', help="deprecated")
    parser.add_argument('--wordpress-nonce-key', help="deprecated")
    parser.add_argument('--wordpress-auth-salt', help="deprecated")
    parser.add_argument('--wordpress-secure-auth-salt', help="deprecated")
    parser.add_argument('--wordpress-logged-in-salt', help="deprecated")
    parser.add_argument('--wordpress-nonce-salt', help="deprecated")
    parser.add_argument('--wordpress-site-title',
        help="deprecated, use '--site-title' instead."
    )
    parser.add_argument('--wordpress-admin-username',
        help="deprecated, use '--admin-username' instead"
    )
    parser.add_argument('--wordpress-admin-email',
        help="deprecated, use '--admin-email' instead"
    )
    # TODO
    # parser.add_argument('--wordpress-skip-content', action='store_true')

    # Web applications
    # ----------------
    parser.add_argument('--app-local-env', action='store_true',
        help="Pass this flag if you want your Laravel app to have the configurations 'APP_ENV=local' and 'APP_DEBUG=true'. Otherwise, they'll default to 'APP_ENV=production' and 'APP_DEBUG=false'."
    )
    parser.add_argument('--laravel-artisan-commands',
        default=','.join(DEFAULT_LARAVEL_ARTISAN_COMMANDS),
        help="a comma separated list of Artisan commands to run on your server after setting up your Laravel app there. Defaults to {}, which results in these commands being run: {}".format(
            ','.join(DEFAULT_LARAVEL_ARTISAN_COMMANDS),
            '; '.join([
                'php /path/to/your/app/artisan {} --force'.format(artisan_command)
                for artisan_command in DEFAULT_LARAVEL_ARTISAN_COMMANDS
            ])
        )
    )

    # SSL
    # ---
    parser.add_argument('--email-for-ssl', help="the email address that will be passed to Certbot. If left blank, the value of '--apache-server-admin' will be used instead.")
    parser.add_argument('--domains-for-ssl', help="a comma separated list of domains that will be passed to Certbot. If left blank, Lampsible will figure out what to use based on your host and action.")
    parser.add_argument('--test-cert', action='store_true', help="Pass this flag along with '--ssl-certbot' if you are testing and want to avoid being rate limited by Let's Encrypt.")

    # Misc
    # ----
    parser.add_argument('--insecure-cli-password', action='store_true', help="If you want to pass passwords directly over the CLI, you have to pass this flag as well, otherwise Lampsible will refuse to run. This is not advised.")
    parser.add_argument('--insecure-skip-fail2ban', action='store_true', help="Pass this flag if you don't want to install fail2ban on your server. This is insecure not advised.")
    parser.add_argument('--extra-packages', help="comma separated list of any extra packages to be installed on the remote server")
    parser.add_argument('--extra-env-vars', '-e', help="comma separated list of any extra environment variables that you want to pass to your web app. If you are installing a Laravel app, these variables will be appended to your app's .env file. Otherwise, they'll be appended to Apache's envvars file, typically found in /etc/apache2/envvars. Example: SOME_VARIABLE=some-value,OTHER_VARIABLE=other-value")

    # Metadata
    # --------
    parser.add_argument('-V', '--version', action='version', version=__version__)


    args = parser.parse_args()

    print(LAMPSIBLE_BANNER)

    private_data_dir = init_private_data_dir(DEFAULT_PRIVATE_DATA_DIR)
    project_dir      = init_project_dir(DEFAULT_PROJECT_DIR)

    validator = ArgValidator(args, private_data_dir, project_dir)
    result = validator.validate_args()

    inventory = validator.get_inventory()

    if result != 0:
        print('FATAL! Got invalid user input, and cannot continue. Please fix the issues listed above and try again.')
        return 1
    args = validator.get_args()

    galaxy_result = ensure_ansible_galaxy_dependencies(os.path.join(
        project_dir, 'ansible-galaxy-requirements.yml'))

    if galaxy_result == 1:
        return 1


    if args.action == 'dump-ansible-facts':
        # TODO: Perhaps we can improve this. For example, if we refactor
        # the handling of inventories, we could do this with Ansible Runner's
        # 'module' feature (that is, pass the kwargs module='setup' to the
        # configuration).
        # However, for now, this also works quite well.
        run_command(
            executable_cmd='ansible',
            cmdline_args=['-i', inventory, 'ungrouped', '-m', 'setup'],
        )
        return 0

    playbook = '{}.yml'.format(args.action)
    if not os.path.exists(os.path.join(project_dir, playbook)):
        # TODO: In the future we will have to change how this is validated.
        raise NotImplementedError()

    rc = RunnerConfig(
        private_data_dir=private_data_dir,
        project_dir=project_dir,
        inventory=inventory,
        extravars=validator.get_extravars_dict(),
        playbook=playbook,
    )

    if args.ssh_key_file:
        try:
            with open(os.path.abspath(args.ssh_key_file), 'r') as key_file:
                key_data = key_file.read()
            rc.ssh_key_data = key_data
        except FileNotFoundError:
            print('Warning! SSH key file not found!')

    rc.prepare()
    r = Runner(config=rc)
    r.run()

    # TODO: Deal with these better.
    print(r.stats)

    rmtree(private_data_dir)

    return 0


if __name__ == '__main__':
    main()
