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

from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import scoped_session, relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError


Base = declarative_base()


def database(connection):
    return create_engine(connection)


class SQLAlchemySessionManager:
    """
    Create a scoped session for every request and close it when the request
    ends.
    """

    def __init__(self, engine):
        session_factory = sessionmaker(bind=engine)
        self.session = scoped_session(session_factory)

    def process_resource(self, req, resp, resource, params):
        resource.session = self.session()

    def process_response(self, req, resp, resource, req_succeeded):
        if hasattr(resource, 'session'):
            self.session.remove()


class DatabaseError(SQLAlchemyError):

    def __init__(self, *args, **kw):
        SQLAlchemyError.__init__(self, *args, **kw)


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    principal_investigator = Column(String(100))
    faculty = Column(String(100))
    department = Column(String(100))

    def __repr__(self):
        return "<Account(account_name='{0}', principal_investigator='{1}', faculty='{2}' department='{3}')>".format(
            self.name,
            self.principal_investigator,
            self.faculty,
            self.department
        )


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    ldap_name = Column(String(50))
    power_user = Column(Boolean)
    account_id = Column(Integer, ForeignKey('accounts.id'))

    account = relationship("Account", back_populates="users")

    def __repr__(self):
        return "<User(ldap_name='{0}', power_user='{1}', account='{2}')>".format(
            self.ldap_name,
            self.power_user,
            self.account
        )
