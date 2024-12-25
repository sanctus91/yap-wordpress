# Lampsible

## About

Lampsible - LAMP stacks with Ansible and a super simple CLI. This tool can automate anything from
a production ready WordPress site on your VPS to a custom Apache setup on a virtual machine
in your local network.
.

## Requirements

* Local: Unix system with Python 3.8 or newer. Tested on Ubuntu and Gentoo Linux. Might work on macOS, but I haven't tested that. Won't work on Windows.
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


## Sample usage

Lampsible is designed to be very simple to use. If you forget some important
parameter, Lampsible will prompt you for it, or pick some sensible defaults.


Install Apache on your server:

```
lampsible someuser@somehost.com apache
```

Install a production ready WordPress site:

```
lampsible someuser@somehost.com wordpress \
    --ssl-certbot \
    --email-for-ssl you@yourdomain.com
```

Install a production ready Joomla site:

```
lampsible someuser@somehost.com joomla \
    --ssl-certbot \
    --email-for-ssl you@yourdomain.com
```

Install a Laravel app on a test server:

```
lampsible someuser@somehost.com laravel \
    --ssl-certbot \
    --test-cert \
    --apache-server-admin you@yourdomain.com \
    --app-name cool-laravel-app \
    --app-build-path /path/to/your/local/cool-laravel-app-0.7rc.tar.gz \
    --laravel-artisan-commands key:generate,migrate
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

## Running unit tests

Lampsible has basic unit tests since version 2. However, there are some caveats. They are not true unit tests, more
like some kind of integration tests. They require access to a real remote server, and will run real Ansible playbooks
against that server to perform various test installations, so beware! This server should be unimportant and unsensitive
in that regard.

It is also a bit unconventional to pass custom arguments to unit tests. But the tests make use of the
environment variable `LAMPSIBLE_REMOTE`, so you can do something like this:
```
export LAMPSIBLE_REMOTE="you@yourserver.com"; python -m unittest
```


## Contributing 

Please do! I'd be more than happy to see Issues, Pull Requests and any other kind of feedback ;-)
