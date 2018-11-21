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
from flask import session
from sqlalchemy.exc import SQLAlchemyError

from api.admin import is_admin
from app import AccountRestService
from db.group import Member, Group
from db.handler import db_session
from db.user import User


logger = logging.getLogger('api.user')
auth = AccountRestService.auth


def generate_username(dom_name):
    first = dom_name
    second = None
    if '@' in dom_name:
        first, second = dom_name.split('@')
    name = first
    if len(first.split('.')) > 1:
        pre, post = first.split('.')
        pre = pre[:2] if len(pre) > 2 else pre
        post = post[:6] if len(post) > 6 else post
        name = pre + post
    if second:
        suggestion = "{0}.{1}".format(name, second.split('.')[0])
        if not db_session.query(User).filter(User.logon_name == suggestion).one_or_none():
            return suggestion
        else:
            for i in range(10):
                suggestion = "{0}.{1}".format(suggestion, i)
                if not db_session.query(User).filter(User.logon_name == suggestion).one_or_none():
                    return suggestion
    else:
        suggestion = first
        if not db_session.query(User).filter(User.logon_name == suggestion).one_or_none():
            return suggestion
        else:
            for i in range(10):
                suggestion = "{0}.{1}".format(suggestion, i)
                if not db_session.query(User).filter(User.logon_name == suggestion).one_or_none():
                    return suggestion
    return None


def get_user_with_groups(uid):
    u = db_session.query(User)
    user = u.filter(User.id == uid).one_or_none()
    if not user:
        logger.warning("user with id {0} not found".format(uid))
        return None
    user = user.dump()
    user['id'] += int(AccountRestService.config.accounting().get('uid_init'))
    user.pop('seed', None)
    user['groups'] = []
    for member in db_session.query(Member).filter(Member.user_id == uid).all():
        group = db_session.query(Group).filter(Group.id == member.group_id).one().dump()
        group['id'] += int(AccountRestService.config.accounting().get('gid_init'))
        user['groups'].append(group)
    return user


def get_users():
    if not is_admin():
        return NoContent, 401
    return [get_user_with_groups(u.id) for u in db_session.query(User).all() if u]


@auth.login_required
def find_groups(admin=False):
    u = db_session.query(User)
    user = u.filter(User.dom_name == session['username']).one_or_none()
    if not user:
        logger.warning("user {0} not found".format(session['username']))
        return "user doesn't exist", 404
    ua = db_session.query(Member)
    ug = ua.filter(Member.user == user)
    if admin:
        return [g.group.dump() for g in ug if g.admin], 200
    else:
        return [g.group.dump() for g in ug], 200


@auth.login_required
def add_user(user):
    if not is_admin():
        return NoContent, 401
    user['seed'] = pyotp.random_base32()
    logon_name = generate_username(user['dom_name'])
    if not logon_name:
        logger.error("could not generate a logon name for {0}".format(user))
        return 'Error while generating logon name', 500
    user['logon_name'] = logon_name
    u = User(**user)
    try:
        db_session.add(u)
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while creating account")
        return NoContent, 500


@auth.login_required
def remove_user(name):
    if not is_admin():
        return NoContent, 401
    try:
        db_session.query(User).filter(User.dom_name == name).delete()
        db_session.commit()
        return NoContent, 200
    except SQLAlchemyError:
        logger.exception("error while creating account")
        return NoContent, 500


@auth.login_required
def get_user(uid):
    if not is_admin():
        return NoContent, 401
    return get_user_with_groups(uid), 200


@auth.login_required
def find_user(name):
    if is_admin():
        user = db_session.query(User).filter(User.dom_name == name).one_or_none()
        if not user:
            logger.warning("user with name {0} not found".format(name))
            return NoContent, 404
        return get_user_with_groups(user.id), 200
    if 'username' in session:
        session_user = db_session.query(User).filter(User.dom_name == session['username']).one_or_none()
        if not session_user:
            return NoContent, 401
        user = db_session.query(User).filter(User.dom_name == name).one_or_none()
        if not user:
            return NoContent, 401
        for admin in db_session.query(Member).filter(Member.user_id == session_user.id and Member.admin).all():
            if db_session.query(Member).filter(Member.group_id == admin.group_id and Member.user_id == user.id).one_or_none():
                return get_user_with_groups(user.id), 200
        return NoContent, 401
    return NoContent, 401


@auth.login_required
def get_myself():
    if 'username' not in session:
        return NoContent, 500
    user = db_session.query(User).filter(User.dom_name == session['username']).one_or_none()
    if not user:
        logger.error("session user {0} not in database".format(session['username']))
        return NoContent, 500
    result = get_user_with_groups(user.id)
    result['seed'] = user.seed
    result['seed_img'] = pyotp.totp.TOTP(user.seed).provisioning_uri(user.dom_name, issuer_name=AccountRestService.config.general().get('totp_issuer'))
    return result, 200


@auth.login_required
def regen_totp():
    if 'username' not in session:
        return NoContent, 500
    user = db_session.query(User).filter(User.dom_name == session['username']).one_or_none()
    if not user:
        logger.error("session user {0} not in database".format(session['username']))
        return NoContent, 500
    user.seed = pyotp.random_base32()
    try:
        db_session.commit()
        return NoContent, 200
    except SQLAlchemyError:
        logger.exception("error while creating account")
        return NoContent, 500

