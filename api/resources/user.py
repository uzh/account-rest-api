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
import ldap

from api.middleware.database import DatabaseError, User
from api.resources import BaseResource


class UserResources(BaseResource):

    logger = logging.getLogger(__name__)

    def on_get(self, req, resp, name):
        user = self.session.query(User(ldap_name=name)).one()
        if not user:
            raise falcon.HTTP_NOT_FOUND('No User Data', 'Could not find any user data for {0}'.format(name))
        resp.body = self.format_body(user)
        resp.status = falcon.HTTP_OK

    def on_put(self, req, resp, name):
        if not name:
            raise falcon.HTTP_PRECONDITION_FAILED('No User Data', 'username not specified in request')
        user = self.session.query(User(ldap_name=name)).one()
        if user:
            raise falcon.HTTP_CONFLICT('User already exists', '{0} already registered in accounting system'.format(name))
        self.logger.info('checking for power user flag')
        requestor = self.session.query(User(ldap_name=req.context['user'])).one()
        if not requestor.power_user:
            self.logger.warning('{0} requested add, but not a power user'.format(requestor))
            raise falcon.HTTP_UNAUTHORIZED('Only Power Users allowed', '{0} not a power user'.format(requestor))
        self.logger.info('adding user {0}'.format(name))
        self.session.add(User(name))
        try:
            self.session.commit()
        except DatabaseError as se:
            self.logger.exception('failed to commit changes')
            raise falcon.HTTP_INTERNAL_SERVER_ERROR('failed to add user', '{0}; {1}'.format(name, se))
        resp.status = falcon.HTTP_CREATED

    def on_post(self, req, resp):
        pass

    def on_delete(self, req, resp, name):
        if not name:
            raise falcon.HTTP_PRECONDITION_FAILED('No User Data', 'username not specified in request')
        user = self.session.query(User(ldap_name=name)).one()
        if not user:
            raise falcon.HTTP_NOT_FOUND('No User Data', '{0} not in accounting system'.format(name))
        self.logger.info('checking for power user flag')
        requestor = self.session.query(User(ldap_name=req.context['user'])).one()
        if not requestor.power_user:
            self.logger.warning('{0} requested delete, but not a power user'.format(requestor))
            raise falcon.HTTP_UNAUTHORIZED('Only Power Users allowed', '{0} not a power user'.format(requestor))
        self.logger.info('deleting user {0}'.format(name))
        self.session.delete(user)
        try:
            self.session.commit()
        except DatabaseError as se:
            self.logger.exception('failed to commit changes')
            raise falcon.HTTP_INTERNAL_SERVER_ERROR('failed to remove user', '{0}; {1}'.format(name, se))
        resp.status = falcon.HTTP_OK
