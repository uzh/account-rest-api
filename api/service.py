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

import pyotp
from connexion import NoContent

from app import AccountRestService
from db.group import Group
from db.handler import db_session
from db.user import User

logger = logging.getLogger('api.service')
service_auth = AccountRestService.service_auth


@service_auth.login_required
def login(name, otp):
    u = db_session.query(User)
    user = u.filter(Group.name == name).one_or_none()
    if user:
        totp = pyotp.TOTP(user.seed)
        if totp.verify(otp):
            return name, 200
        else:
            logger.error("invalid otp {0} for {1}".format(otp, name))
            return NoContent, 401
    logger.warning("user {0} not found".format(name))
    return NoContent, 404


@service_auth.login_required
def get_group_id(name):
    g = db_session.query(Group)
    group = g.filter(Group.name == name).one_or_none()
    if group:
        gid = group.id + int(AccountRestService.config.accounting().get('gid_init'))
        return gid, 200
    logger.warning("group {0} not found".format(name))
    return NoContent, 404


@service_auth.login_required
def get_user_id(name):
    u = db_session.query(User)
    user = u.filter(Group.name == name).one_or_none()
    if user:
        uid = user.id + int(AccountRestService.config.accounting().get('uid_init'))
        return uid, 200
    logger.warning("user {0} not found".format(name))
    return NoContent, 404
