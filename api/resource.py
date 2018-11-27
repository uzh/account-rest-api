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
from api.group import get_groups
from app import auth, config
from db.group import Member, Group
from db.handler import db_session
from db.resource import Resource
from db.user import User

logger = logging.getLogger('api.resource')


def get_resources():
    if not is_admin():
        return NoContent, 401
    return [r.dump() for r in db_session.query(Resource).all()], 200


def add_resource(name):
    if not is_admin():
        return NoContent, 401
    try:
        db_session.add(Resource(name=name, active=True))
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while creating resource")
        return NoContent, 500


def get_resource_groups(rid):
    if not is_admin():
        return NoContent, 401

    def resource_groups(resource):
        for group in resource.groups:
            group['id'] += int(config.accounting().get('gid_init'))
            yield group
    resource = db_session.query(Resource).filter(Resource.id == rid).one_or_none()
    if not resource:
        return NoContent, 404
    return [group for group in get_groups(True) if group in resource_groups(resource)], 200


def update_resource(rid, resource_update):
    if not is_admin():
        return NoContent, 401
    resource = db_session.query(Resource).filter(Resource.id == rid).one_or_none()
    if not resource:
        return NoContent, 404
    try:
        for k in resource_update:
            setattr(resource, k, resource_update[k])
        db_session.commit()
        return NoContent, 200
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500


def add_resource_group(rid, group_name):
    if not is_admin():
        return NoContent, 401
    resource = db_session.query(Resource).filter(Resource.id == rid).one_or_none()
    group = db_session.query(Group).filter(Group.name == group_name).one_or_none()
    if not resource or not group:
        return NoContent, 404
    if group in resource.groups:
        return 'Group already assigned to resource', 500
    try:
        resource.groups.append(group)
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500


def remove_resource_group(rid, group_name):
    if not is_admin():
        return NoContent, 401
    resource = db_session.query(Resource).filter(Resource.id == rid).one_or_none()
    group = db_session.query(Group).filter(Group.name == group_name).one_or_none()
    if not resource or not group:
        return NoContent, 404
    if group not in resource.groups:
        return 'Group not assigned to resource', 500
    try:
        resource.groups.remove(group)
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500
