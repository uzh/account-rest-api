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

from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

from sqlalchemy import Column, DateTime, event


class AccountingBase(object):
    id = Column(UUID, default=str(uuid4()), primary_key=True)
    created_at = Column(DateTime(), default=datetime.now())
    updated_at = Column(DateTime(), onupdate=datetime.now())

    def __init__(self):
        self.id = str(uuid4())

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])

    @staticmethod
    def insert(mapper, connection, target):
        target.created_at = datetime.now()

    @staticmethod
    def update(mapper, connection, target):
        target.updated_at = datetime.now()


#event.listen(AccountingBase, "before_insert", AccountingBase.insert)
#event.listen(AccountingBase, "before_update", AccountingBase.update)
