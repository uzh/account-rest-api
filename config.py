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

import configparser
import logging

from pathlib import Path
from os.path import exists, dirname, expandvars, expanduser


class DefaultConfig(object):

    @staticmethod
    def create():
        config = configparser.ConfigParser()
        config.add_section("general")
        config.set("general", "CORS", False)
        config.set("general", "secret", "change-me-please")
        config.set("general", "port", 8080)
        config.set("general", "debug", False)

        # config.add_section("token")
        # config.set("token", "secret", "super-secret-key-please-change")
        # config.set("token", "name", "auth-token")
        # config.set("token", "location", "cookie")

        config.add_section("database")
        config.set("database", "connection", "mysql://root:password@localhost:3306/accounting")

        config.add_section("ldap")
        config.set("ldap", "host", "localhost")
        config.set("ldap", "port", 389)
        config.set("ldap", "schema", "ldap")
        config.set("ldap", "domain", "example.com'")
        config.set("ldap", "search_base", "OU=Domain Users,DC=example,DC=com")
        config.set("ldap", "administrator_groups", [])
        config.set("ldap", "required_groups", [])

        config.add_section("accounting")
        config.set("accounting", "ldap_server", "ldaps://localhost:636")
        config.set("accounting", "ldap_user_loc", "uid")



        config.add_section("gunicorn")
        config.set("gunicorn", "bind", "0.0.0.0:{0}".format(config.get("general", "port")))
        config.set("gunicorn", "pidfile", "/var/run/srg.pid")
        config.set("gunicorn", "keepalive", "650")
        config.set("gunicorn", "max_requests", "0")
        config.set("gunicorn", "max_requests_jitter", "0")
        config.set("gunicorn", "worker_class", "egg:meinheld#gunicorn_worker")
        config.set("gunicorn", "workers", "2")
        return config


class Config(object):

    logger = logging.getLogger(__name__)

    def __init__(self, config_file=None, create=True):
        self.config = DefaultConfig().create()
        if create:
            self.write(expandvars(expanduser(config_file)))
        if config_file and exists(expandvars(expanduser(config_file))):
            self.config.read(expandvars(expanduser(config_file)))

    def write(self, path):
        if not exists(path):
            self.logger.debug("writing new config to {0}".format(path))
            if not exists(dirname(path)):
                Path.mkdir(Path(dirname(path)), parents=True)
            with open(path, "w") as cf:
                self.config.write(cf)
        else:
            self.logger.debug("already found config at {0}, using it".format(path))

    def _fetch(self, section):
        result = {}
        options = self.config.options(section)
        for option in options:
            try:
                result[option] = self.config.get(section, option)
            except configparser.Error as e:
                self.logger.error("exception reading config on {0} ({1})".format(option, e))
                result[option] = None
        return result

    def general(self):
        return self._fetch("general")

    def token(self):
        return self._fetch("token")

    def database(self):
        return self._fetch("database")

    def ldap(self):
        return self._fetch("ldap")

    def accounting(self):
        return self._fetch("accounting")

    def gunicorn(self):
        return self._fetch("gunicorn")

    def update(self, section, option, value):
        self.config.set(section, option, value)
