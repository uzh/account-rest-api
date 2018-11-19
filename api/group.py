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

from api.admin import is_admin, is_group_admin
from app import AccountRestService
from db.group import GroupUser, Group
from db.handler import db_session
from db.user import User

logger = logging.getLogger('api.account')
auth = AccountRestService.auth


def get_groups(active, limit=50):
    if not is_admin():
        return NoContent, 401
    groups = db_session.query(Group)
    if not active:
        return [g.dump() for g in groups][:limit]
    return [g.dump() for g in groups if g.active][:limit]


@auth.login_required
def add_group(group):
    if not is_admin():
        return NoContent, 401
    try:
        db_session.add(Group(**group))
        db_session.commit()
        return 201
    except SQLAlchemyError:
        logger.exception("error while creating group")
        return NoContent, 500


@auth.login_required
def update_group(group_update):
    if not is_group_admin(group_update.name):
        return NoContent, 401
    group = db_session.query(Group).filter(Group.name == group_update.name).one_or_none()
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
    if not is_admin():
        if 'username' not in session or not db_session.query(GroupUser).filter(GroupUser.group.name == name and GroupUser.user.dom_name == session['username']).one_or_none():
            logger.warning("user {0} not found as part of group".format(session['username'], name))
            return NoContent, 401
    users = []
    for group_users in db_session.query(GroupUser).filter(GroupUser.group.name == name).all():
        for group_user in group_users:
            users.append(dict(dom_name=group_user.user.dom_name, full_name=group_user.user.full_name, admin=group_user.admin))
    return users, 200


@auth.login_required
def add_group_user(user_name, group_name, admin):
    if not is_group_admin(group_name):
        return NoContent, 401
    user = db_session.query(User).filter(User.dom_name == user_name).one_or_none()
    if not user:
        return 'User does not exist', 404
    group = db_session.query(Group).filter(Group.name == group_name).one()
    try:
        db_session.add(GroupUser(group=group, user=user, admin=admin))
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500


@auth.login_required
def remove_group_user(user_name, group_name):
    if not is_group_admin(group_name):
        return NoContent, 401
    user = db_session.query(User).filter(User.dom_name == user_name).one_or_none()
    if not user:
        return 'User does not exist', 404
    group = db_session.query(Group).filter(Group.name == group_name).one()
    try:
        db_session.query(GroupUser).filter(GroupUser.group == group and GroupUser.user == user).delete()
        db_session.commit()
        return NoContent, 200
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500
