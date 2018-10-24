# Accounting REST API 

The Accounting Rest API aims to provide a stable rest interface for managing accounts and for interacting with OpenLDAP.
The package is self contained and has a command line interface.
Information regarding the configuration options can be found in the docs.
Details regarding the CLI options can be found in the docs (and by running accounting-rest --help).
By default gunicorn hosts the application on port 5000.
Given that this service uses authentication, it can only be accessed through HTTPS. 
So order to access this service run [nginx](https://www.nginx.com/) in front of it as a reverse proxy, with HTTPS configured (check the docs for the recommended installation and settings).
If you use the systemd install mechanism provided by the CLI, the default path for the configuration is changed to /etc/accounting-rest/api.config. 
The systemd installer also assumes that you have installed this package in the default interpreter space.

NOTE: this is all still pre-alpha, only use as a reference for the time being
## Components

* [Falcon](https://github.com/falconry/falcon) framework 
* [gunicorn](https://github.com/benoitc/gunicorn) as the WSGI HTTP server and [meinheld](https://github.com/mopemope/meinheld) as the gunicorn worker
* LDAP stuff  

## Installation on Ubuntu

Prerequisites:
* Make sure you install using python3

First install the system dependencies:
```bash
sudo apt-get install libsasl2-dev python-dev python3-dev libldap2-dev libssl-dev python3-pip
```
```bash
sudo pip3 install click falcon
```
```bash
sudo python3 setup.py install
``` 

## Using
For using the service we recommend that you install it:
```bash
accounting-rest install
```
and start it using systemd:
```bash
systemctl start accounting-rest
```
Information regarding available commands:
```bash
accounting-rest --help
```
To run the tests:
```bash
pytest
```
If you want to test it out before installing, you can run:
```bash
accounting-rest start
```
but this may conflict if you also have an install.
