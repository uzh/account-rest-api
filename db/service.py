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

from sqlalchemy import Column, String

from db.handler import Base


class Service(Base):
    __tablename__ = "services"
    name = Column(String(255), unique=True)
    access = Column(String(16))
    secret = Column(String(32))
