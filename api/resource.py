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
from dateutil import parser
from flask import session
from sqlalchemy.exc import SQLAlchemyError

from api.admin import is_admin, user_is_group_admin
from api.group import get_groups
from db.group import Group, Member
from db.handler import db_session
from db.resource import Resource, ResourceUsage
from db.user import User

logger = logging.getLogger('api.resource')


def get_resources():
    """
    list all resources (admins)
    :return: list of resource
    """
    if not is_admin():
        return NoContent, 401
    return [r.dump() for r in db_session.query(Resource).all()], 200


def add_resource(name):
    """
    add new resource (admins)
    :param name: resource name
    :return: resource
    """
    if not is_admin():
        return NoContent, 401
    try:
        r = Resource(name=name, active=True)
        db_session.add(r)
        db_session.commit()
        db_session.refresh(r)
        return r.dump(), 201
    except SQLAlchemyError:
        logger.exception("error while creating resource")
        return NoContent, 500


def get_resource_groups(rid):
    """
    get groups associated with resource (admins)
    :param rid: resource id
    :return: list of group
    """
    if not is_admin():
        return NoContent, 401

    def evaluate_resource_groups(resource, gid):
        for group in resource.groups:
            if gid == group.id:
                return True
        return False

    r = db_session.query(Resource).filter(Resource.id == rid).one_or_none()
    if not r:
        return NoContent, 404
    groups, code = get_groups(True)
    return [group for group in groups if evaluate_resource_groups(r, group['id'])], 200


def update_resource(rid, resource_update):
    """
    update existing resource (admins)
    :param rid: resource id
    :param resource_update: resource
    :return: success or failure
    """
    if not is_admin():
        return NoContent, 401
    r = db_session.query(Resource).filter(Resource.id == rid).one_or_none()
    if not r:
        return NoContent, 404
    try:
        for k in resource_update:
            setattr(r, k, resource_update[k])
        db_session.commit()
        return NoContent, 200
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500


def add_resource_group(rid, name):
    """
    associate group with resource (admins)
    :param rid: resource id
    :param name: group name
    :return: success or failure
    """
    if not is_admin():
        return NoContent, 401
    r = db_session.query(Resource).filter(Resource.id == rid).one_or_none()
    g = db_session.query(Group).filter(Group.name == name).one_or_none()
    if not r or not g:
        return NoContent, 404
    if g in r.groups:
        return 'Group already assigned to resource', 500
    try:
        r.groups.append(g)
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500


def remove_resource_group(rid, name):
    """
    remove group association with resource
    :param rid: resource id
    :param name: group name
    :return: success or failure
    """
    if not is_admin():
        return NoContent, 401
    r = db_session.query(Resource).filter(Resource.id == rid).one_or_none()
    g = db_session.query(Group).filter(Group.name == name).one_or_none()
    if not r or not g:
        return NoContent, 404
    if g not in r.groups:
        return 'Group not assigned to resource', 500
    try:
        r.groups.remove(g)
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while updating group")
        return NoContent, 500


def add_resource_usage(usages):
    """
    add resource usage records
    :param usages: list of ResourceUsage
    :return: success or failure
    """
    if not is_admin():
        if 'service' not in session:
            return NoContent, 401
    if not is_admin():
        invalid = [u for u in usages if u['r'] != session['username']]
        if len(invalid) > 0:
            return 'Invalid records found, can only insert your own', 500
        for usage in usages:
            usage['resource'] = usage['r']
            usage['user'] = usage['u']
            usage.pop('r', None)
            usage.pop('u', None)
            db_session.add(ResourceUsage(**usage))
        return NoContent, 201
    for usage in usages:
        usage['resource'] = usage['r']
        usage['user'] = usage['u']
        usage['start'] = parser.parse(usage['start'])
        usage['end'] = parser.parse(usage['end'])
        usage.pop('r', None)
        usage.pop('u', None)
        db_session.add(ResourceUsage(**usage))
    return NoContent, 201


def get_resource_usage(r, u=None, start=None, end=None):
    """
    get resource usage for a resource for a given user
    :param u: user
    :param r: resource
    :param start: start time
    :param end: end time
    :return: list of ResourceUsage
    """
    resource = db_session.query(Resource).filter(Resource.name == r).one_or_none()
    user = db_session.query(User).filter(User.dom_name == u).one_or_none()
    if not is_admin():
        if not resource or not user:
            return NoContent, 401
        allowed = False
        if u and session['username'] is not u:
            for g in resource.groups:
                if db_session.query(Member).filter(Member.group_id ==  g.id and Member.user_id == user.id).one_or_none():
                    if user_is_group_admin(u, g.name):
                        allowed = True
        if not allowed:
            return NoContent, 401
    if not resource or not user:
        return NoContent, 404
    usages = db_session.query(ResourceUsage).filter(ResourceUsage.resouce == r and
                                                    ResourceUsage.user == u and
                                                    ResourceUsage.start == start and
                                                    ResourceUsage.end == end).all()

    return [u.dump() for u in usages], 200
