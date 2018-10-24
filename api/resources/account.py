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

from api.middleware.database import DatabaseError, User, Account
from api.resources import BaseResource


class AccountResources(BaseResource):

    logger = logging.getLogger(__name__)

    def on_get(self, req, resp, name):
        if not name:
            raise falcon.HTTP_PRECONDITION_FAILED('No account name', 'Account name not specified in request')
        requestor = self.session.query(User(ldap_name=req.context['user'])).one()
        if not requestor:
            raise falcon.HTTP_NOT_FOUND('No user data', 'Could not find any user data for {0}'.format(req.context['user']))
        account = self.session.query(Account(name=name)).one()
        if not account:
            self.logger.info('could not find account {0}'.format(name))
            if requestor.power_user:
                raise falcon.HTTP_NOT_FOUND('Account not found', '{0} does not exist'.format(name))
            raise falcon.HTTP_INTERNAL_SERVER_ERROR('Query failed', 'Something went wrong looking up account {0}'.format(name))
        if requestor.power_user:
            resp.body = self.format_body(account)
            resp.status = falcon.HTTP_OK
        elif requestor in account.users:
            resp.body = self.format_body(dict(name=account.name,
                                              department=account.department,
                                              faculty=account.faculty,
                                              principle_investigator=account.principal_investigator))
            resp.status = falcon.HTTP_OK
        else:
            self.logger.warning('illegal request made by {0}'.format(requestor))
            resp.status = falcon.HTTP_NOT_FOUND

    def on_put(self, req, resp, name, principal_investigator, faculty, department):
        if not name or not principal_investigator or not faculty or not department:
            raise falcon.HTTP_PRECONDITION_FAILED('Not enough data', 'name, pi, fact or dept not specified in request')
        requestor = self.session.query(User(ldap_name=req.context['user'])).one()
        if not requestor:
            raise falcon.HTTP_NOT_FOUND('No user data', 'Could not find any user data for {0}'.format(req.context['user']))
        if not requestor.power_user:
            self.logger.warning('illegal request made by {0}'.format(requestor))
            raise falcon.HTTP_INTERNAL_SERVER_ERROR('Query failed', 'Something went wrong creating account {0}'.format(name))
        self.logger.info('adding account {0}'.format(name))
        self.session.add(Account(name=name, principal_investigator=principal_investigator, faculty=faculty, department=department))
        try:
            self.session.commit()
        except DatabaseError as se:
            self.logger.exception('failed to commit changes')
            raise falcon.HTTP_INTERNAL_SERVER_ERROR('failed to add account', '{0}; {1}'.format(name, se))
        resp.status = falcon.HTTP_CREATED

    def on_post(self, req, resp):
        pass

    def on_delete(self, req, resp, name):
        pass
