# Accounting Center [![Build Status](https://travis-ci.org/uzh/acpy.svg?branch=master)](https://travis-ci.org/uzh/acpy)

The Accounting Center (API) aims to provide a stable rest interface for managing users, groups and resource access.
If you are running your own infrastructure within an organization, this can enable you to decouple the tight integration with internal authentication systems.
The idea is that users authenticate on the service using [Shibboleth](https://www.shibboleth.net/) or an arbitrary LDAP system, and can manage their internal account.
The internal password is a [TOTP](https://tools.ietf.org/html/rfc6238) password, which can be scanned with MFA applications such as [Authy](https://authy.com/).  

For connecting infrastructure services to this authentication mechanism please choose the following:
* pam module: [acpam](todo)

The package is self contained and has a command line interface.
Information regarding the configuration options can be found in the docs.
Details regarding the CLI options can be found in the [docs](https://acpy.readthedocs.io/en/latest/) (and by running accounting-rest --help).
By default gunicorn hosts the application on port 5000.
In production run [nginx](https://www.nginx.com/) in front of it as a reverse proxy, with HTTPS configured (check the [docs](https://acpy.readthedocs.io/en/latest/) for the recommended installation and settings).
If you use the systemd install mechanism provided by the CLI, the default path for the configuration is changed to /etc/acpy/api.config. 
The systemd installer also assumes that you have installed this package in the default interpreter space.

A Docker container for this service can be found in the [docker registry](todo) 

NOTE: this is all still pre-alpha, only use as a reference for the time being
## Components

* [Connexion](https://github.com/zalando/connexion) framework 
* [gunicorn](https://github.com/benoitc/gunicorn) as the WSGI HTTP server and [meinheld](https://github.com/mopemope/meinheld) as the gunicorn worker
* Shibboleth stuff
* LDAP stuff  

## Installation on Ubuntu

Prerequisites:
* Make sure you install using python3

First install the system dependencies:
```bash
nothing here yet
```

## Using
For using the service we recommend that you install it:
```bash
acpy install
```
and start it using systemd:
```bash
systemctl start acpy
```
Information regarding available commands:
```bash
acpy --help
```
To run the tests:
```bash
python -m pytest tests/
```
If you want to test it out before installing, you can run:
```bash
acpy start
```
but this may conflict if you also have an install.
