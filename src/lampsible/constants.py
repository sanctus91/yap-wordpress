import os
from . import __version__
from .helpers import *

# Lampsible
# ---------
LAMPSIBLE_BANNER = """\


     |                                   _)  |      |       
     |      _` |  __ `__ \\   __ \\    __|  |  __ \\   |   _ \\ 
     |     (   |  |   |   |  |   | \\__ \\  |  |   |  |   __/ 
    _____|\\__._| _|  _|  _|  .__/  ____/ _| _.__/  _| \\___| 
                            _|                              
    =======================================================

          --------------------------------------------
             LAMP stacks with Ansible  -  v{}
          --------------------------------------------

""".format(__version__)
SUPPORTED_ACTIONS = [
    # LAMP-Stack basics
    'lamp-stack',
    'apache',
    'mysql',
    'php',
    # PHP CMS
    'wordpress',
    'joomla',
    'drupal',
    # PHP frameworks
    'laravel',
    # Local debugging
    'dump-ansible-facts',
]

# Script paths
# ------------
USER_HOME_DIR            = os.path.expanduser('~')
PROJECT_DIR              = find_package_project_dir()
DEFAULT_PRIVATE_DATA_DIR = os.path.join(USER_HOME_DIR, '.lampsible')
# If the user does not supply a value, this will be overwritten by a path
# inside the package installation, which we detect later on.

# Apache
# ------
DEFAULT_APACHE_VHOST_NAME = '000-default'
DEFAULT_APACHE_SERVER_NAME = 'localhost'
DEFAULT_APACHE_SERVER_ADMIN = 'webmaster@localhost'
DEFAULT_APACHE_DOCUMENT_ROOT = '/var/www/html'

# Database
# --------
DEFAULT_DATABASE_ENGINE       = 'mysql'
DEFAULT_DATABASE_USERNAME     = 'db-username'
DEFAULT_DATABASE_HOST         = 'localhost'
DEFAULT_DATABASE_TABLE_PREFIX = ''

# PHP
# ---
DEFAULT_PHP_VERSION = None
SUPPORTED_PHP_VERSIONS = [
    '8.4', '8.3', '8.2', '8.1', '8.0',
    '7.4', '7.3', '7.2', '7.1', '7.0',
    '5.6', '5.5', '5.4',
]

# All CMS
# -------
DEFAULT_SITE_TITLE     = 'Sample Site'
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_EMAIL    = 'admin@example.com'

# WordPress
# ---------
DEFAULT_WORDPRESS_VERSION = 'latest'
DEFAULT_WORDPRESS_LOCALE  = 'en_US'
RECENT_WORDPRESS_VERSIONS = [
    'latest',
    'nightly',
    '6.7.1', '6.7',
    '6.6.2', '6.6.1', '6.6',
    '6.5.5', '6.5.4', '6.5.3', '6.5.2', '6.5',
    '6.4.4', '6.4.3', '6.4.2', '6.4.1', '6.4',
]

# Joomla
# ------
DEFAULT_JOOMLA_VERSION         = '5.2.2'
DEFAULT_JOOMLA_ADMIN_FULL_NAME = 'Sample User'

# DRUPAL

AVAILABLE_DRUPAL_PROFILES = ['standard', 'minimal']
DEFAULT_DRUPAL_PROFILE    = 'standard'
# ------

# Web applications
# ----------------
DEFAULT_LARAVEL_ARTISAN_COMMANDS = [
    'key:generate',
    'migrate',
    'db:seed',
]

# Misc
# ----
INSECURE_CLI_PASS_WARNING = 'It\'s insecure to pass passwords via CLI args! If you are sure that you want to do this, rerun this command with the --insecure-cli-password flag.'
