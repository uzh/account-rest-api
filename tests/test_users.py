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

import pytest
from cryptography.fernet import Fernet

from config import Config
from app import AccountRestService
from tests import access, secret


@pytest.fixture(scope='module')
def client():
    config = Config(create=False)
    config.update('admin', 'access', access)
    config.update('admin', 'secret', secret)
    config.update('database', 'connection', 'sqlite://')
    ars = AccountRestService(config, auth=False, direct=True)
    with ars.app.app.test_client() as c:
        yield c


def test_add_user_fails_for_non_admin(client):
    lg = client.post('/api/v1/users', json={'dom_name': 'test_user', 'full_name': 'test user'})
    assert 401 == lg.status_code


def test_add_list_remove_user(client):
    with client.session_transaction() as session:
        session['admin'] = Fernet(secret.encode('utf-8')).encrypt(access.encode('utf-8'))
    lg = client.post('/api/v1/users', json={'dom_name': 'test_user_6', 'full_name': 'test user'})
    assert 201 == lg.status_code
    lg = client.get('/api/v1/users')
    assert 200 == lg.status_code
    lg = client.delete('/api/v1/users?name=test_user_6')
    assert 200 == lg.status_code
    lg = client.get('/api/v1/users')
    assert 200 == lg.status_code
