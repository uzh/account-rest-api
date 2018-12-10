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

import hashlib
import logging
import random

from connexion import NoContent
from flask import session
from sqlalchemy.exc import SQLAlchemyError

from db.group import Group, Member
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
        return True
    else:
        if 'username' in session:
            u = db_session.query(User)
            user = u.filter(User.dom_name == session['username']).one_or_none()
            if user:
                group = db_session.query(Group).filter(Group.name == 'admins').one()
                if db_session.query(Member).filter(Member.group == group and Member.user == user).one_or_none():
                    return True
        return False


def user_is_group_admin(user, group):
    """
    check if a user is a group admin
    :param user: user name
    :param group: group name
    :return: admin yes/no
    """
    user = db_session.query(User).filter(User.dom_name == user).one_or_none()
    group = db_session.query(Group).filter(Group.name == group).one_or_none()
    if not user or not group:
        return False
    if db_session.query(Member).filter(Member.group_id == group.id and Member.user_id == user.id and Member.admin).one_or_none():
        return True
    return False


def is_group_admin(group):
    """
    inclusive search of admins and group admins
    :param group: name or id of the group to check, note that it's the database uid (- uid_init)
    :return: admin yes/no
    """
    if is_admin():
        return True
    if 'username' in session:
        user = db_session.query(User).filter(User.dom_name == session['username']).one_or_none()
        if not user:
            return False
        if isinstance(group, int):
            if db_session.query(Member).filter(Member.group_id == group and Member.user_id == user.id and Member.admin).one_or_none():
                return True
        else:
            return user_is_group_admin(user.dom_name, group)
    return False


def get_admins():
    """
    get a list of all users that are in the group admins
    :return: list of users
    """
    if not is_admin():
        return NoContent, 401
    group = db_session.query(Group).filter(Group.name == 'admins').one()
    users = []
    for group_user in db_session.query(Member).filter(Member.group == group).all():
        users.append(db_session.query(User).filter(User.id == group_user.user_id).one_or_none())
    return [u.dump() for u in users]


def add_admin(name):
    """
    add an existing user to admins
    :param name: dom_name
    :return: success or failure
    """
    if not is_admin():
        return NoContent, 401
    user = db_session.query(User).filter(User.dom_name == name).one_or_none()
    if not user:
        return NoContent, 404
    group = db_session.query(Group).filter(Group.name == 'admins').one()
    try:
        db_session.add(Member(group=group, user=user, admin=True))
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while adding admin")
        return NoContent, 500


def remove_admin(name):
    """
    remove an existing user from admins
    :param name: dom_name
    :return: success or failure
    """
    if not is_admin():
        return NoContent, 401
    user = db_session.query(User).filter(User.dom_name == name).one_or_none()
    if not user:
        return NoContent, 404
    group = db_session.query(Group).filter(Group.name == 'admins').one()
    try:
        db_session.query(Member).filter(Member.group == group and Member.user == user).delete()
        db_session.commit()
        return NoContent, 200
    except SQLAlchemyError:
        logger.exception("error while removing admin")
        return NoContent, 500


def get_services():
    """
    list all service accounts
    :return: list of dict(name, access)
    """
    if not is_admin():
        return NoContent, 401
    return [dict(name=s.name, access=s.access) for s in db_session.query(Service).all()], 200


def add_service(name):
    """
    add a service account
    :param name: name of the service
    :return: secret key in plain text, this will only be possible once!
    """
    if not is_admin():
        return NoContent, 401
    try:
        secret = ''.join(random.choice(allowed_chars) for c in range(24))
        s = Service(name=name,
                    access=''.join(random.choice(allowed_chars) for c in range(12)),
                    secret=hashlib.sha256(secret.encode('utf-8')).hexdigest())
        db_session.add(s)
        db_session.commit()
        db_session.refresh(s)
        service = s.dump()
        service['secret'] = secret
        return service, 201
    except SQLAlchemyError:
        logger.exception("error while adding service")
        return NoContent, 500


def remove_service(name):
    """
    remove a service account
    :param name: name of the service account
    :return: success or failure
    """
    if not is_admin():
        return NoContent, 401
    service = db_session.query(Service).filter(Service.name == name).one_or_none()
    if not service:
        return NoContent, 404
    try:
        db_session.delete(service)
        db_session.commit()
        return NoContent, 200
    except SQLAlchemyError:
        logger.exception("error while removing admin")
        return NoContent, 500
