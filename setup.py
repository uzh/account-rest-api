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

from setuptools import setup

version = "0.5"

requirements = ["click",
                "click-log",
                "python-dateutil",
                "sqlalchemy",
                "connexion",
                "connexion[swagger-ui]",
                "flask-cors",
                "flask-ldap3-login",
                "python-jose",
                "psutil",
                "gevent"]

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

setup(name="acpy",
      version=version,
      description="Accounting Center API",
      long_description=open("README.md").read(),
      author="Pim Witlox",
      author_email="pim.witlox@uzh.ch",
      url="https://github.com/uzh/acpy",
      license="GPLv3",
      entry_points={
          "console_scripts": [
              "acpy = app:cli",
          ]
      },
      packages=["api"],
      install_requires=requirements,
      python_requires=">=3.5",
      keywords="Web, Python, Python3, REST",
      project_urls={
          "Documentation": "https://acpy.readthedocs.io/en/latest/",
          "Source": "https://github.com/uzh/acpy/",
          "Tracker": "https://github.com/uzh/acpy/issues",
      },
      test_suite="tests",
      tests_require=test_requirements,
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: System Administrators",
                   "Natural Language :: English",
                   "Environment :: Console",
                   "License :: OSI Approved :: MIT License",
                   "Programming Language :: Python",
                   "Programming Language :: Python :: 3",
                   "Programming Language :: Python :: 3.5",
                   "Programming Language :: Python :: 3.6",
                   "Topic :: Software Development :: Libraries",
                   "Topic :: Utilities"],
      )
