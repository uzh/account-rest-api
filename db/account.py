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

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from db.handler import Base
from db.user import User


class Account(Base):
    __tablename__ = "accounts"
    name = Column(String(100), unique=True)
    active = Column(Boolean)
    principle_investigator = Column(String(255))
    faculty = Column(String(100))
    department = Column(String(100))

    users = association_proxy("account_users", "user")


class AccountUser(Base):
    __tablename__ = 'account_users'

    account_id = Column(Integer, ForeignKey('account.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    admin = Column(Boolean, nullable=False)

    account = relationship(Account, backref="account_users")
    user = relationship(User, backref="account_users")
