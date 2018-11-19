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

import logging

import connexion
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

from auth import NoAuth
from auth.access_secret import AccessSecretToken
from auth.ldap import LDAP
from db.group import Group
from db.handler import init_db, db_session
from db.service import Service


class AccountRestService(object):

    logger = logging.getLogger(__name__)

    auth = None
    service_auth = None
    config = None

    def __init__(self, config, auth=True, direct=False):
        """
        Service wrapper for our Gunicorn and Flask
        :param config: our configuration object
        :param auth: enable/disable authorization
        :param direct: direct start API (don't use Gunicorn)
        """
        AccountRestService.config = config
        self.direct = direct
        self.logger.debug("initializing database")
        session = init_db(self.config.database().get('connection'))
        if direct:
            self.logger.info("direct initialization requested")
            self.app = connexion.FlaskApp(__name__, specification_dir='swagger/')
        else:
            self.logger.info("initializing gunicorn application")
            self.app = connexion.FlaskApp(__name__, port=self.config.general.get('port'), specification_dir='swagger/', server='gunicorn')
        self.app.app.secret_key = self.config.general().get('secret')
        # primary authentication tables
        try:
            s = session.query(Service)
            if not s.filter(Service.name == 'admin').one_or_none():
                admin_service = Service(name='admin', access=config.admin().get('access'), secret=config.admin().get('secret'))
                session.add(admin_service)
                session.commit()
        except SQLAlchemyError:
            self.logger.exception('failed to add admin service')
        try:
            g = session.query(Group)
            if not g.filter(Group.name == 'admins').one_or_none():
                admin_group = Group(name='admins', active=True)
                session.add(admin_group)
                session.commit()
        except SQLAlchemyError:
            self.logger.exception('failed to add admin group')
        if auth:
            # add service authentication
            AccountRestService.service_auth = AccessSecretToken(self.config)
            self.app.app.add_url_rule('/service', 'service', AccountRestService.service_auth.authorize(), methods=['POST'])

            if self.config.general().get('auth'):
                # self.logger.info("initializing LDAP authorization")
                # login_path = 'login'
                # self.app.app.config['LDAP_LOGIN_PATH'] = login_path
                # AccountRestService.auth = LDAP(self.app.app, self.config)
                # self.app.app.add_url_rule("/{0}".format(login_path),
                #                           login_path,
                #                           AccountRestService.auth.login,
                #                           methods=['POST'])
                pass

        else:
            self.logger.warning("authorization disabled")
            AccountRestService.auth = NoAuth()
            AccountRestService.service_auth = NoAuth()
        self.logger.debug("initializing routes")
        self.app.add_api('api.yaml')
        if self.config.general().get('CORS'):
            self.logger.debug("initializing CORS")
            CORS(self.app.app)

    def start(self):
        """ A hook to when a Gunicorn worker calls run()."""
        self.logger.info("started accounting rest api")
        if self.direct:
            self.app.run(port=self.config.general().get('port'), debug=self.config.general().get('debug'))
        else:
            self.app.run(debug=self.config.general().get('debug'))

    def stop(self, signal):
        """ A hook to when a Gunicorn worker starts shutting down. """
        self.logger.info("stopped accounting rest api")
