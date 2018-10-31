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

from connexion import NoContent
from flask import session
from sqlalchemy.exc import SQLAlchemyError

from app import AccountRestService
from db.account import AccountUser, Account
from db.handler import db_session
from db.user import User

logger = logging.getLogger('api.account')
ldap = AccountRestService.ldap


@ldap.login_required
def find_accounts(admin=False, limit=20):
    u = db_session.query(User)
    user = u.filter(User.ldap_name == session['username']).one_or_none()
    if not user:
        logger.warning("User {0} not found".format(session['username']))
        return "User doesn't exist", 404
    ua = db_session.query(AccountUser)
    accounts = ua.filter(AccountUser.user == user)
    if admin:
        return [a.accounts for a in accounts if a.admin][:limit], 200
    else:
        return [a.account.dump() for a in accounts][:limit], 200


@ldap.login_required
def add_account(account):
    if not session['admin']:
        return NoContent, 401
    a = Account(**account)
    try:
        db_session.add(a)
        db_session.commit()
        db_session.refresh(a)
        return a.dump(), 201
    except SQLAlchemyError:
        logger.exception("error while creating account")
        return NoContent, 500


@ldap.login_required
def update_account(account):
    u = db_session.query(User)
    user = u.filter(User.ldap_name == session['username']).one_or_none()
    if not user:
        logger.warning("User {0} not found".format(session['username']))
        return "User doesn't exist", 404
    a = db_session.query(Account)
    dba = a.filter(Account.name == account.name).one_or_none()
    if not dba:
        logger.error("Account {0} does not exist".format(account.name))
        return "Lookup failed for {0}".format(account.name), 404
    if not session['admin']:
        ua = db_session.query(AccountUser)
        admin = ua.filter(AccountUser.user == user and AccountUser.account == dba and AccountUser.admin).one_or_none()
        if not admin:
            logger.error("user {0} not authorized for changes of {1}".format(user.ldap_name, dba.name))
            return "User {0} is not an admin".format(user.ldap_name), 403
    try:
        for k in account:
            setattr(dba, k, account[k])
        db_session.commit()
        db_session.refresh(dba)
        return dba.dump(), 201
    except SQLAlchemyError:
        logger.exception("error while updating account")
        return NoContent, 500
