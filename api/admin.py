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
import random

from connexion import NoContent
from flask import session
from cryptography.fernet import Fernet
from sqlalchemy.exc import SQLAlchemyError

from app import AccountRestService
from db.group import Group, GroupUser
from db.handler import db_session
from db.service import Service
from db.user import User

logger = logging.getLogger('api.admin')
allowed_chars = u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def is_admin():
    """
    check if a user is an admin (excluding group admins)
    :return: admin yes/no
    """
    if 'admin' in session:
        access = AccountRestService.config.admin().get('access')
        secret = AccountRestService.config.admin().get('secret')
        return Fernet(secret.encode("utf-8")).decrypt(session['admin']).decode('utf-8') == access
    else:
        if 'username' in session:
            u = db_session.query(User)
            user = u.filter(User.dom_name == session['username']).one_or_none()
            if user:
                group = db_session.query(Group).filter(Group.name == 'admins').one()
                if db_session.query(GroupUser).filter(GroupUser.group == group and GroupUser.user == user).one_or_none():
                    return True
        return False


def is_group_admin(group):
    """
    inclusive search of admins and group admins
    :param group: name of the group to check
    :return: admin yes/no
    """
    if not is_admin():
        if 'username' in session:
            if db_session.query(GroupUser).filter(GroupUser.group.name == group and GroupUser.user.dom_name == session['username'] and GroupUser.admin).one_or_none():
                return True
    return False


def get_admins(limit=50):
    if not is_admin():
        return NoContent, 401
    group = db_session.query(Group).filter(Group.name == 'admins').one()
    group_users = db_session.query(GroupUser)
    users = []
    for group_user in group_users.filter(GroupUser.group == group).all():
        users.append(db_session.query(User).filter(User.id == group_user.user_id).one_or_none())
    return [u.dump() for u in users][:limit]


def add_admin(name):
    if not is_admin():
        return NoContent, 401
    user = db_session.query(User).filter(User.dom_name == name).one_or_none()
    if not user:
        return NoContent, 404
    group = db_session.query(Group).filter(Group.name == 'admins').one()
    try:
        db_session.add(GroupUser(group=group, user=user, admin=True))
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while adding admin")
        return NoContent, 500


def remove_admin(name):
    if not is_admin():
        return NoContent, 401
    user = db_session.query(User).filter(User.dom_name == name).one_or_none()
    if not user:
        return NoContent, 404
    group = db_session.query(Group).filter(Group.name == 'admins').one()
    try:
        db_session.query(GroupUser).filter(GroupUser.group == group and GroupUser.user == user).delete()
        db_session.commit()
        return NoContent, 200
    except SQLAlchemyError:
        logger.exception("error while removing admin")
        return NoContent, 500


def get_services(limit=50):
    if not is_admin():
        return NoContent, 401
    return [dict(name=s.name, access=s.access) for s in db_session.query(Service).all()][:limit]


def add_service(name):
    if not is_admin():
        return NoContent, 401
    try:
        db_session.add(Service(name=name,
                               access=''.join(random.choice(allowed_chars) for c in range(16)),
                               secret=''.join(random.choice(allowed_chars) for c in range(32))))
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while adding service")
        return NoContent, 500


def remove_service(name):
    if not is_admin():
        return NoContent, 401
    service = db_session.query(Service).filter(Service.name == name).one_or_none()
    if not service:
        return NoContent, 404
    try:
        service.delete()
        db_session.commit()
        return NoContent, 200
    except SQLAlchemyError:
        logger.exception("error while removing admin")
        return NoContent, 500
