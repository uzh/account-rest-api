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
from app import application
from tests import access, secret, generate_token_headers, encoded_secret


@pytest.fixture(scope='module')
def client():
    config = Config(create=False)
    config.update('admin', 'access', access)
    config.update('admin', 'secret', secret)
    config.update('database', 'connection', 'sqlite://')
    ars = application(config)
    with ars.app.test_client() as c:
        yield c


def test_add_admin_fails_for_non_admin(client):
    lg = client.post('/api/v1/admins?name=test_user')
    assert 401 == lg.status_code


def test_add_service_fails_for_non_admin(client):
    lg = client.post('/api/v1/services?name=test_service')
    assert 401 == lg.status_code


def test_add_list_remove_as_admin(client):
    lg = client.post("/api/v1/login?username={0}&password={1}".format(access, encoded_secret))
    assert 200 == lg.status_code
    token = json.loads(lg.data)

    lg = client.post('/api/v1/users', json={'dom_name': 'test_user', 'full_name': 'test user'}, headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.post('/api/v1/admins?name=test_user', headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code

    lg = client.post('/api/v1/logout', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code

    from api.auth import generate_token
    from api.auth import tokens

    user_token = generate_token('test_user')
    tokens['test_user'] = user_token
    with client.session_transaction() as session:
        session['username'] = 'test_user'

    lg = client.delete('/api/v1/admins?name=test_user', headers={'X-TOKEN': user_token})
    assert 200 == lg.status_code
    lg = client.get('/api/v1/admins', headers={'X-TOKEN': user_token})
    assert 401 == lg.status_code
    lg = client.post('/api/v1/logout', headers={'X-TOKEN': user_token})
    assert 200 == lg.status_code

    tokens.pop('test_user', None)
    with client.session_transaction() as session:
        if 'username' in session:
            del(session['username'])

    lg = client.post("/api/v1/login?username={0}&password={1}".format(access, encoded_secret))
    assert 200 == lg.status_code
    token = json.loads(lg.data)

    lg = client.get('/api/v1/admins', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    assert [] == json.loads(lg.data)

    lg = client.post('/api/v1/logout', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code


def test_add_list_remove_service(client):
    lg = client.post("/api/v1/login?username={0}&password={1}".format(access, encoded_secret))
    assert 200 == lg.status_code
    token = json.loads(lg.data)

    lg = client.post('api/v1/services?name=test_service', headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.get('api/v1/services', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    services = json.loads(lg.data)
    service = [x for x in services if x['name'] == 'test_service']
    assert 1 == len(service)
    lg = client.delete('api/v1/services?name=test_service', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code

    lg = client.post('/api/v1/logout', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
