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
from unittest import mock

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
from flask import json

from config import Config
from app import AccountRestService


def insert_user_and_account(client):
    lg = client.post('/api/accounts', json={'name': 'test_account', 'principle_investigator': 'test_pi', 'active': True})
    assert 201 == lg.status_code
    account = json.loads(lg.data)
    lg = client.post('/api/user', json={'ldap_name': 'test_user', 'full_name': 'test user'})
    assert 201 == lg.status_code
    user = json.loads(lg.data)
    return user, account


@pytest.fixture(scope='module')
def client():
    config = Config(create=False)
    config.update("database", "connection", "sqlite://")
    ars = AccountRestService(config, auth=False, direct=True)
    with ars.app.app.test_client() as c:
        yield c


def test_add_account_fails_for_non_admin(client):
    lg = client.post('/api/accounts', json={'name': 'test_account', 'principle_investigator': 'test_pi', 'active': True})
    assert 401 == lg.status_code


def test_add_user_to_account(client):
    with client.session_transaction() as session:
        session['admin'] = True
    user, account = insert_user_and_account(client)
    lg = client.get("/api/accounts/{0}".format(account['id']))
    assert 200 == lg.status_code
    assert [] == json.loads(lg.data)
    lg = client.post("/api/accounts/{0}?admin=False".format(account['id']), json=user)
    assert 201 == lg.status_code
    lg = client.get("/api/accounts/{0}".format(account['id']))
    assert 200 == lg.status_code
    assert len(json.loads(lg.data)) == 1


def test_retrieve_accounts_as_user(client):
    test_add_user_to_account(client)
    with client.session_transaction() as session:
        session['admin'] = None
        session['username'] = 'test_user'
    lg = client.get('api/accounts')
    assert 200 == lg.status_code
    assert 'test_account' == json.loads(lg.data)[0]['name']
