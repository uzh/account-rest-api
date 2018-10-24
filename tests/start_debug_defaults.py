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

"""
Simple script for starting our API using defaults and an in-memory database
"""

import logging
import argparse

from api import GunicornApp, Config, AccountRestService

logger = logging.getLogger()


def prepare(spew=False, https=False):
    def set_level(level):
        for l in "sqlalchemy", "falcon", "gunicorn", "meinheld", "python-ldap":
            li = logging.getLogger(l)
            if li:
                li.setLevel(level)

    if spew:
        logger.setLevel(logging.DEBUG)
        set_level(logging.DEBUG)
    if logger.getEffectiveLevel() == logging.DEBUG:
        set_level(logging.INFO)
    elif logger.getEffectiveLevel() == logging.INFO:
        set_level(logging.WARNING)
    elif logger.getEffectiveLevel() == logging.WARNING:
        set_level(logging.ERROR)
    elif logger.getEffectiveLevel() == logging.ERROR:
        set_level(logging.CRITICAL)

    config = Config(create=False)
    config.update("database", "connection", "sqlite://")

    service = AccountRestService(config, https_only=https)
    gu_config = config.gunicorn()

    return GunicornApp(service, gu_config)


def main(parsed_arguments):
    if parsed_arguments.level == 'debug':
        logger.setLevel(logging.DEBUG)
    elif parsed_arguments.level == 'info':
        logger.setLevel(logging.INFO)
    elif parsed_arguments.level == 'warning':
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.ERROR)
    application = prepare(parsed_arguments.verbose, parsed_arguments.https)
    application.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is a helper program to launch our API with defaults')
    parser.add_argument('-v', '--verbose', action="store_true", default=False, help="very noisy debug information")
    parser.add_argument('-s', '--https', action="store_true", default=False, help="enable https")
    ll_choices = [
        'debug',
        'info',
        'warning',
        'error'
    ]
    parser.add_argument('-l', '--level', dest='level', choices=ll_choices, default='info', help="set debug level (default: info)")
    args = parser.parse_args()
    main(args)
