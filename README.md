# Lampsible

## About

Complete LAMP stack setup, with a single CLI command. Powered by Ansible under the hood.
This tool can automate almost anything that you'd expect from a LAMP stack.

### Features

* WordPress
* Joomla
* Drupal
* Custom Laravel app
* Custom Apache configuration (custom webroot, vhosts, etc.)
* Production ready SSL via Certbot
* SSL for test servers (to avoid being rate limited by Let's Encrypt)
* Self signed SSL for hardcore DIY folks
* Apache and database on the same server, or separate servers, whatever you prefer
* Specify PHP version
* Specify PHP extensions
* And so on...


## Requirements

* Local: Unix system with Python 3.11 or newer. Tested on Ubuntu and Gentoo Linux. Might work on macOS, but I haven't tested that. Won't work on Windows,
  because Ansible requires a Unix like system.
* Remote: Ubuntu 20 or newer. Might work on older versions, but I doubt it. Support for other distros is planned in a future version.

## Installing

Install with Pip: `python3 -m pip install lampsible`

Alternatively, install from wheel file...: `python3 -m pip install /path/to/local/lampsible-SOME_VERSION-py3-none-any.whl`

... or from source:
```
git clone https://github.com/saint-hilaire/lampsible
cd lampsible
python3 -m pip install .
```

## Usage

There are 2 ways to use Lampsible: as a CLI tool, or as a Python library.

### CLI tool

Once you've installed Lampsible onto your local environment, you can run the `lampsible` command.

It takes the format: `lampsible user@host ACTION [OPTIONS]`

It is designed to be very simple to use. If you omit some important parameter,
like admin user, password, site title, etc, you will be prompted to enter a value,
or fall back to a default.

Below are some examples:

* Install a production ready WordPress site:

```
lampsible someuser@somehost.com wordpress \
    --email-for-ssl you@yourdomain.com
```

Install a production ready Joomla site:

```
lampsible someuser@somehost.com joomla \
    --email-for-ssl you@yourdomain.com
```

Install Drupal on a test server. Certbot will set up a
test certificate. Also, Apache and MySQL will run on two separate hosts.

```
lampsible someuser@somehost.com drupal \
    --database-system-user-host otheruser@dbserver.somehost.com \
    --database-host 10.0.1.2 \
    --database-username dbuser
    --ssl-test-cert \
    --apache-server-admin you@yourdomain.com \
```

Set up a LAMP stack with various custom configuration and a self signed SSL certificate on some local VM:

```
lampsible someuser@192.168.123.123 lamp-stack \
    --ask-remote-sudo \
    --ssl-selfsigned \
    --database-username dbuser \
    --database-name testdb \
    --php-version 8.1 \
    --apache-vhost-name some-legacy-app \
    --apache-document-root /var/www/html/some-legacy-app/some-dir/public \
    --php-extensions mysql,xml,mbstring,xdebug,gd
```

Run `lampsible --help` for a full list of options.

### Python library

Lampsible can be used as a Python library, so if you want to build your own tool,
and want to leverage Lampsible's features to automate various Apache webserver setups,
you can do that.

It could look something like this:

```python
# my_automation_tool.py

from lampsible.lampsible import Lampsible

# Simple WordPress setup
lampsible = Lampsible(
    web_user='someuser',
    web_host='somehost.example.com',
    action='wordpress',
    # Required for Certbot. You can also use email_for_ssl
    apache_server_admin='someuser@example.com',
    database_name='wordpress',
    database_username='db-user',
    database_password='topsecret',
    admin_username='your-wordpress-admin',
    admin_email='wp-admin@example.com',
    admin_password='anothertopsecret',
    site_title='My WordPress Blog',
)

result = lampsible.run()


# Joomla setup. This example is a little more complex,
# to showcase some more features. Webserver and
# database server are two different hosts,
# Certbot will run with the --test-cert flag,
# an older version of Joomla will be installed,
# some custom PHP extensions will be installed
# alongside the ones required by Joomla,
# and some extra environment variables will be set.
lampsible = Lampsible(
    web_user='someuser',
    web_host='somehost.example.com',
    # This assumes that you want your database server
    # to be reachable from the outside via the
    # domain dbserver.example.com, and within your
    # internal network, including your Joomla webserver,
    # via the private IP address 10.0.1.2.
    database_system_user='root',
    database_system_host='dbserver.example.com',
    database_host='10.0.1.2',
    action='joomla',
    email_for_ssl='someuser@example.com',
    ssl_test_cert=True,
    database_name='joomla',
    database_username='db-user',
    database_password='topsecret',
    admin_username='your-joomla-admin',
    admin_email='joomla-admin@example.com',
    admin_password='anothertopsecret',
    # These extensions will be appended to the list of
    # extensions required by the system you are
    # installing (in this case Joomla).
    php_extensions=['php-curl', 'php-gd'],
    joomla_admin_full_name='Your Name',
    joomla_version='5.1.4',
    site_title='My Joomla Site',
    extra_env_vars={'FOO': 'bar', 'HELLO': 'world'}
)

result = lampsible.run()

```

## FAQ

* Why not just use Docker?

Lampsible is intended to be an homage to the old school: A simple and versatile LAMP stack.
If you want something similar with Docker, consider using [Docksible](https://github.com/saint-hilaire/docksible),
another project that I maintain. It will install a web app onto your remote server with Docker Compose.
It also leverages Ansible locally under the hood.

## Contributing 

Please do! I'd be more than happy to see Issues, Pull Requests and any other kind of feedback ;-)

### Running unit tests

```
export LAMPSIBLE_REMOTE=realuser@your-real-server.com
# These 2 aren't super important, if you omit them, the
# Laravel tests will simply be skipped.
export LAMPSIBLE_LARAVEL_NAME=my-laravel-app
export LAMPSIBLE_LARAVEL_PATH=/path/to/my-laravel-app-2.0.tar.gz
python -m unittest
```

Lampsible will install various things onto the host specified by `LAMPSIBLE_REMOTE`, so beware!
This server should be insensitive in that regard. Also, Lampsible will set insecure passwords
on that server, so again, beware! You should tear down that server after running tests.

Also, these tests should be taken with a grain of salt. They are not true unit tests,
When Lampsible runs, it calls Ansible playbooks under the hood, and when those playbooks
finish running, Lampsible returns a status code of 0, no matter what happens on the
remote server. And this status code is what the tests ultimately check.
So when you run tests, you have to actually keep an eye on the console output
printed by Ansible, as well as the results on your remote server.

Also, if you run the whole test suite, at some point, the test
will "fail" on the "Ansible side" because of some edge case
related to Composer packages, caused by a non empty
`composer_working_directory`. This is not really a problem.
Lampsible is not intended to install Drupal, WordPress, etc, alongside
each other on the same host. So to really run these tests, you
should run them one at a time
( `python -m unittest test.test_lampsible.TestLampsible.test_wordpress`, etc. ),
and rebuild the server after each test case.

The nature of Ansible automations - it requires some real remote server -
poses a unique challenge with regards to unit tests. However,
in spite of this little drawback, these tests are still quite convenient
when you change the code but want to make sure nothing breaks.
