#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
#
# Copyright (C) 2019, Pim Witlox. All rights reserved.
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


class Group(Base):
    __tablename__ = 'groups'
    name = Column(String(100), unique=True)

    user_id = Column(Integer, ForeignKey(User.id))

    active = Column(Boolean)

    user = relationship('User', foreign_keys='Group.user_id')

    resources = relationship("Resource", secondary=group_resources, back_populates="groups")


class Member(Base):
    __tablename__ = 'members'

    group_id = Column(Integer, ForeignKey('groups.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    admin = Column(Boolean, nullable=False)

    group = relationship(Group, backref="members")
    user = relationship(User, backref="members")


Group.users = association_proxy("members", "users")
User.accounts = association_proxy("members", "groups")
