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

import falcon

from falcon_require_https import RequireHTTPS
from falcon_auth import FalconAuthMiddleware, BasicAuthBackend

from api.middleware import JSONTranslator, CrossDomain
from api.middleware.authentication import ldap_verify
from api.middleware.database import SQLAlchemySessionManager, database
from api.resources.account import AccountResources
from api.resources.root import RootResources
from api.resources.user import UserResources


class AccountRestService(falcon.API):
    logger = logging.getLogger(__name__)

    """Service wrapper for our Falcon API"""
    def __init__(self, config, https_only=True, enable_auth=True):
        database_engine = database(config.database().get("connection"))
        middleware = [
            CrossDomain(config.general().get("crossdomain-origin")),
            JSONTranslator(),
            SQLAlchemySessionManager(database_engine),
        ]
        if https_only:
            self.logger.debug("enabling https")
            middleware.append(RequireHTTPS())
        if enable_auth:
            auth_method = config.general().get("authentication")
            self.logger.debug("configuring authentication ({0})".format(auth_method))
            user_loader = lambda username, password: ldap_verify(config.ldap().get("server"),
                                                                 config.ldap().get("user_loc"),
                                                                 config.ldap().get("user_dn"),
                                                                 config.ldap().get("base_dn"),
                                                                 username,
                                                                 password)
            auth_backend = BasicAuthBackend(user_loader)
            auth_middleware = FalconAuthMiddleware(auth_backend, exempt_routes=['/exempt'], exempt_methods=['HEAD'])
            middleware.append(auth_middleware)

        super(AccountRestService, self).__init__(middleware=middleware)
        self.config = config
        self.logger.debug("initializing routes")
        # Build routes
        self.add_route("/", RootResources())
        self.add_route("/users", UserResources())
        self.add_route("/accounts", AccountResources())
        #self.add_route("/nodes", NodeResources())

    def start(self):
        """ A hook to when a Gunicorn worker calls run()."""
        self.logger.info("started slurm rest api")

    def stop(self, signal):
        """ A hook to when a Gunicorn worker starts shutting down. """
        self.logger.info("stopped slurm rest api")
