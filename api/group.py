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
from db.group import GroupUser, Group
from db.handler import db_session
from db.user import User

logger = logging.getLogger('api.account')
auth = AccountRestService.auth
gid_init = int(AccountRestService.config.accounting().get('gid_init'))


@auth.login_required
def get_group_id(name):
    if 'admin' not in session:
        u = db_session.query(User)
        user = u.filter(User.dom_name == session['username']).one_or_none()
        if not user:
            logger.warning("user {0} not found".format(session['username']))
            return NoContent, 401
    g = db_session.query(Group)
    group = g.filter(Group.name == name).one_or_none()
    if group:
        gid = group.id + gid_init
        return gid, 200
    return NoContent, 404


@auth.login_required
def add_group(group):
    if 'admin' not in session:
        return NoContent, 401
    g = Group(**group)
    try:
        db_session.add(g)
        db_session.commit()
        return 201
    except SQLAlchemyError:
        logger.exception("error while creating group")
        return NoContent, 500


@auth.login_required
def update_group(gid, group_update):
    g = db_session.query(Group)
    group = g.filter(Group.id == (gid - gid_init)).one_or_none()
    if not group:
        logger.warning("group {0} (gid) not found".format(gid))
        return NoContent, 401
    u = db_session.query(User)
    user = u.filter(User.dom_name == session['username']).one_or_none()
    if 'admin' not in session:
        if not user:
            logger.warning("user {0} not found".format(session['username']))
            return NoContent, 401
        gu = db_session.query(GroupUser)
        admin = gu.filter(GroupUser.user == user and GroupUser.admin and GroupUser.group == group).one_or_none()
        if not admin:
            logger.error("user {0} not authorized for changes of {1}".format(user.dom_name, dba.name))
            return NoContent, 401
    try:
        for k in group_update:
            setattr(group, k, group_update[k])
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500


@auth.login_required
def get_group_users(name):
    if 'admin' not in session:
        u = db_session.query(User)
        user = u.filter(User.dom_name == session['username']).one_or_none()
        if not user:
            logger.warning("user {0} not found".format(session['username']))
            return NoContent, 401
    group = db_session.query(Group).filter(Group.name == name).one_or_none()
    if not group:
        logger.warning("group {0} not found".format(name))
        if 'admin' in session:
            return 'Group not found', 404
        return NoContent, 401
    users = []
    for group_users in db_session.query(GroupUser).filter(GroupUser.group.name == name).all():
        for group_user in group_users:
            users.append(dict(dom_name=group_user.user.dom_name,
                              full_name=group_user.user.full_name,
                              admin=group_user.admin))
    if 'admin' in session or ('username' in session and session['username'] in [u['dom_name'] for u in users]):
        return users, 200
    return NoContent, 401


@auth.login_required
def add_group_user(user_name, group_name, admin):
    users, code = get_group_users(group_name)
    if code != 200:
        return users, code
    user = next(iter([u for u in users if u['dom_name'] == session['username']]), None)
    if 'admin' not in session and not user.admin:
        return NoContent, 401
    user_to_add = db_session.query(User).filter(User.name == user_name).one_or_none()
    if not user_to_add:
        return 'User does not exist', 404
    group = db_session.query(Group).filter(Group.name == group_name).one_or_none()
    try:
        db_session.add(GroupUser(group_id=group.id, user_id=user.id, admin=admin))
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500


@auth.login_required
def remove_group_user(user_name, group_name):
    users, code = get_group_users(id)
    if code != 200:
        return users, code
    user = next(iter([u for u in users if u['dom_name'] == session['username']]), None)
    if 'admin' not in session and not user.admin:
        return NoContent, 401
    user_to_remove = db_session.query(User).filter(User.name == user_name).one_or_none()
    if not user_to_remove:
        return 'User does not exist', 404
    group = db_session.query(Group).filter(Group.name == group_name).one_or_none()
    try:
        db_session.query(GroupUser).filter(GroupUser.group_id == group.id and GroupUser.user_id == user.id).delete()
        db_session.commit()
        return NoContent, 200
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500
