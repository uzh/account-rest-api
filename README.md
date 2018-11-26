# Accounting Center [![Build Status](https://travis-ci.org/uzh/acpy.svg?branch=master)](https://travis-ci.org/uzh/acpy) [![PyPI version fury.io](https://badge.fury.io/py/acpy.svg)](https://pypi.org/project/acpy/)

The Accounting Center (API) aims to provide a stable rest interface for managing users, groups and resource access.
If you are running your own infrastructure within an organization, this can enable you to decouple the tight integration with internal authentication systems.
The idea is that users authenticate on the service using an EduID (ex. [shibboleth](https://www.shibboleth.net/)) compliant service.

For connecting infrastructure services to this authentication mechanism please use the following:
* 

The package is self contained and has a command line interface.
Information regarding the configuration options can be found in the docs.
Details regarding the CLI options can be found in the [docs](https://acpy.readthedocs.io/en/latest/) (and by running acpy --help).
The application is hosted on port 8080 by default.
In production run [nginx](https://www.nginx.com/) in front of it as a reverse proxy, with HTTPS configured (check the [docs](https://acpy.readthedocs.io/en/latest/) for the recommended installation and settings).

NOTE: this is all still pre-alpha, only use as a reference for the time being
## Components

* [Connexion](https://github.com/zalando/connexion) framework 
* EduID stuff
* LDAP stuff


## Installation

Either install the package using pip:
```bash
pip install acpy
```
or clone this repo and run:
```bash
pip install -e .
```
or simply build and run the docker image:
```bash
docker build -t acpy .
docker run -p 8080:8080 acpy start
```

## Using
Information regarding available commands:
```bash
acpy --help
```
To run the tests:
```bash
python -m pytest tests/
```
To start the service:
```bash
acpy start
```
