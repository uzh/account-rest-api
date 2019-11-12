# Accounting Center [![Build Status](https://travis-ci.org/witlox/acpy.svg?branch=master)](https://travis-ci.org/witlox/acpy) [![PyPI version fury.io](https://badge.fury.io/py/acpy.svg)](https://pypi.org/project/acpy/)

The Accounting Center (API) aims to provide a stable rest interface for accounting resource usage of clusters and private clouds and managing users of a group/tenant.
The idea is that users authenticate on the service using an LDAP compliant account, and can see their own resource usage, and group resource usage.
If users are group administrators, they can add/remove users from the group.

In some magical way to be defined (probably with a couple of hacky scripts and cron), cluster controllers and cloud controllers will regularly update resource usage using a service account.
These controllers will also check (and modify) existing group structures within their respective systems.

The package is self contained and has a command line interface.
Information regarding the configuration options can be found in the docs.
Details regarding the CLI options can be found in the [docs](https://acpy.readthedocs.io/en/latest/) (and by running acpy --help).
The application is hosted on port 8080 by default.
In production run [nginx](https://www.nginx.com/) in front of it as a reverse proxy, with HTTPS configured (check the [docs](https://acpy.readthedocs.io/en/latest/) for the recommended installation and settings).

NOTE: this is all still alpha, only use as a reference for the time being

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
