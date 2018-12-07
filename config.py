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
import random

from pathlib import Path
from os.path import exists, dirname, expandvars, expanduser

allowed_chars = u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


class DefaultConfig(object):

    @staticmethod
    def create():
        config = configparser.ConfigParser()
        config.add_section('general')
        config.set('general', 'CORS', 'False')
        config.set('general', 'secret', ''.join(random.choice(allowed_chars) for c in range(14)))
        config.set('general', 'port', '8080')
        config.set('general', 'run_time', expandvars(expanduser('~/.acpy/run_time.data')))

        config.add_section('logging')
        config.set('logging', 'log_file', expandvars(expanduser('~/.acpy/acpy.log')))
        config.set('logging', 'max_bytes', '2621440')
        config.set('logging', 'backup_count', '5')

        config.add_section('admin')
        config.set('admin', 'access', ''.join(random.choice(allowed_chars) for c in range(12)))
        config.set('admin', 'secret', ''.join(random.choice(allowed_chars) for c in range(24)))

        config.add_section('token')
        config.set('token', 'issuer', 'com.example.accounting')
        config.set('token', 'secret', ''.join(random.choice(allowed_chars) for c in range(14)))
        config.set('token', 'lifetime', '3600')
        config.set('token', 'algorithm', 'HS256')

        config.add_section('database')
        config.set('database', 'connection', 'sqlite://')

        config.add_section('authentication')
        config.set('authentication', 'host', 'localhost')
        config.set('authentication', 'port', '636')
        config.set('authentication', 'ssl', 'True')
        config.set('authentication', 'base_dn', 'OU=Domain Users,DC=example,DC=com')
        config.set('authentication', 'rdn_attr', 'uid')
        config.set('authentication', 'login_attr', 'mail')
        config.set('authentication', 'bind_user', 'ldap_admin')
        config.set('authentication', 'bind_pass', 'ldap_admin_pass')

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
            with open(path, 'w') as cf:
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
        return self._fetch('general')

    def logging(self):
        return self._fetch('logging')

    def admin(self):
        return self._fetch('admin')

    def token(self):
        return self._fetch('token')

    def database(self):
        return self._fetch('database')

    def authentication(self):
        return self._fetch('authentication')

    def update(self, section, option, value):
        self.config.set(section, option, value)
