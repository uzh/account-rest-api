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

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Table
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from db.handler import Base
from db.user import User


group_resources = Table('group_resources',
                        Base.metadata,
                        Column('group_id', Integer, ForeignKey('groups.id')),
                        Column('resource_id', Integer, ForeignKey('resources.id')))


class Owner(Base):
    __tablename__ = 'owners'
    user_id = Column(Integer, ForeignKey(User.id))
    postal_code = Column(String(10))
    city = Column(String(255))
    country = Column(String(2))

    user = relationship('User', foreign_keys='Owner.user_id')


class Group(Base):
    __tablename__ = 'groups'
    name = Column(String(100), unique=True)

    owner_id = Column(Integer, ForeignKey(Owner.id))
    active = Column(Boolean)

    owner = relationship('Owner', foreign_keys='Group.owner_id')

    resources = relationship("Resource", secondary=group_resources, back_populates="groups")


class GroupUser(Base):
    __tablename__ = 'group_users'

    group_id = Column(Integer, ForeignKey('groups.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    admin = Column(Boolean, nullable=False)

    group = relationship(Group, backref="group_users")
    user = relationship(User, backref="group_users")


Group.users = association_proxy("group_users", "users")
User.accounts = association_proxy("group_users", "groups")
