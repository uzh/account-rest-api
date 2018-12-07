.. acpy documentation master file, created by
   sphinx-quickstart on Tue Mar 27 08:52:38 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _gevent: http://www.gevent.org/

=============================================
Welcome to Accounting Center's documentation!
=============================================

The Accounting Center (API) aims to provide a stable rest interface for accounting resource usage of clusters and private clouds and managing users of a group/tenant.
The idea is that users authenticate on the service using an LDAP compliant account, and can see their own resource usage, and group resource usage.
If users are group administrators, they can add/remove users from the group.

In some magical way to be defined (probably with a couple of hacky scripts and cron), cluster controllers and cloud controllers will regularly update resource usage using a service account.
These controllers will also check (and modify) existing group structures within their respective systems.

Installing the package
======================
You need python 3.5 or higher to run this package. The package can be installed using ``pip install acpy``.


Using the cli
=============
Our package is self contained, so you can start and stop the server using the cli.
Simply calling ``acpy start`` starts a development server for the API.
When running in production we recommend using gevent_.

acpy [OPTIONS] COMMAND [ARGS]...

  This CLI allows you to manage the Accounting Center API, this service will
  run in the background. The service is started direct by default (don't do
  this in production, use gevent). Check your config file for settings, the
  default location is in your home folder under `~/.acpy/api.config`.

Options:
  -c, --config-file TEXT  Specify configuration file path (creates if not
                          exists)
  -v, --verbosity LVL     Either CRITICAL, ERROR, WARNING, INFO or DEBUG
  --help                  Show this message and exit.

start
*****
acpy start [OPTIONS]

  start api

Options:
  -g, --gevent  use gevent as server
  -u, --ui      enable swagger ui (url/api/v1/ui)
  -d, --debug   enable debug mode
  -f, --force   force start ignoring recorded state
  --help        Show this message and exit.

stop
****
acpy stop [OPTIONS]

  stop api

Options:
  -f, --force  kill instead of terminate
  --help       Show this message and exit.

info
****
acpy info [OPTIONS]

  rest service information

Options:
  --help  Show this message and exit.

info output will have the following information:

* gevent : started as gevent
* ui : enabled or not
* debug : enabled or not
* pid : process id


Table of contents
=================
.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
