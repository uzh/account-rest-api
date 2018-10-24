#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
#
# Copyright (C) 2018 University of Zurich. All rights reserved.
#
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
import os
import sys
from os.path import exists, join
from pathlib import Path

from setuptools import setup

version = "0.1"

prerequisites = ["click",
                 "click-log",
                 "python-ldap",
                 "psutil",
                 "falcon",
                 "falcon_require_https",
                 "falcon_auth",
                 "sqlalchemy",
                 "jsonschema",
                 "lxml",
                 "gunicorn"]
test_requirements = ["pytest", "tox"]

if sys.argv[-1] == "tag":
    os.system("git tag -a {0} -m 'version {1}'".format(version, version))
    os.system("git push origin master --tags")
    sys.exit()

if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    os.system("python setup.py bdist_wheel upload")
    sys.exit()

if sys.argv[-1] == "test":
    try:
        modules = map(__import__, test_requirements)
    except ImportError as e:
        raise ImportError("{0} is not installed. Install your test requirements.".format(
            str(e).replace("No module named ", ""))
        )
    os.system('py.test')
    sys.exit()

if sys.argv[-1] == "install":
    Path.mkdir(Path("/etc/accounting-rest"), parents=True, exist_ok=True)
    if exists("/usr/lib/systemd/system"):
        with open(join("/usr/lib/systemd/system", "accounting-rest.service"), "w") as sfp:
            sfp.write("[Unit]\n")
            sfp.write("Description=LDAP Accounting Rest API web service\n")
            sfp.write("After=network.target slurmctld.service\n")
            sfp.write("\n")
            sfp.write("[Service]\n")
            sfp.write("Type=forking\n")
            sfp.write("PermissionsStartOnly=true\n")
            sfp.write("PIDFile=/var/run/ara.pid\n")
            sfp.write("ExecStart=/usr/bin/accounting-rest -c /etc/accounting-rest/api.config start\n")
            sfp.write("ExecReload=/usr/bin/accounting-rest restart\n")
            sfp.write("ExecStop=/usr/bin/accounting-rest stop\n")
            sfp.write("\n")
            sfp.write("[Install]\n")
            sfp.write("WantedBy=multi-user.target\n")
    os.system("systemctl daemon-reload")

try:
    modules = map(__import__, prerequisites)
except ImportError as e:
    raise ImportError("{0} is not installed, please install it using pip.".format(
        str(e).replace("No module named ", ""))
    )


setup(name="accounting-rest",
      version=version,
      description="LDAP Accounting Rest API",
      long_description=open("README.md").read(),
      author="Pim Witlox",
      author_email="pim.witlox@uzh.ch",
      url="https://github.com/uzh/ldap-accounting-rest",
      license="GPLv3",
      entry_points={
          "console_scripts": [
              "accounting-rest = api.__init__:cli",
          ]
      },
      packages=["api"],
      install_requires=[
          "falcon-require-https",
          "falcon-auth",
          "python-ldap",
          "pamela",
          "jsonschema",
          "ujson",
          "gunicorn",
          "meinheld",
          "psutil",
          "click-log",
      ] + prerequisites,
      python_requires=">=3.4",
      keywords="Web, Python, Python3, Refactoring, REST, Framework, RPC",
      project_urls={
          "Documentation": "https://ldap-accounting-rest-api.readthedocs.io/en/latest/",
          "Source": "https://github.com/uzh/ldap-accounting-rest/",
          "Tracker": "https://github.com/uzh/ldap-accounting-rest/issues",
      },
      test_suite="tests",
      tests_require=test_requirements,
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Administrators",
                   "Natural Language :: English",
                   "Environment :: Console",
                   "License :: OSI Approved :: MIT License",
                   "Programming Language :: Python",
                   "Programming Language :: Python :: 3",
                   "Programming Language :: Python :: 3.4",
                   "Programming Language :: Python :: 3.5",
                   "Programming Language :: Python :: 3.6",
                   "Topic :: Software Development :: Libraries",
                   "Topic :: Utilities"],
      )
