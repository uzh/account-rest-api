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

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from db.base import AccountingBase

Base = declarative_base(cls=AccountingBase)
db_session = None


def init_db(uri, persist=True):
    global db_session
    engine = create_engine(uri, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    Base.query = db_session.query_property()
    if not persist:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(bind=engine)
    return db_session
