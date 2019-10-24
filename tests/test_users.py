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


def test_add_user_fails_for_non_admin(client):
    lg = client.post('/api/v1/users', json={'dom_name': 'test_user', 'full_name': 'test user'})
    assert 401 == lg.status_code


def test_api_call_fails_without_token(client):
    lg = client.post("/api/v1/login?username={0}&password={1}".format(access, encoded_secret))
    assert 200 == lg.status_code
    token = json.loads(lg.data)
    lg = client.post('/api/v1/users', json={'dom_name': 'test_user_6', 'full_name': 'test user'})
    assert 401 == lg.status_code
    lg = client.post('/api/v1/logout', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code


def test_add_list_remove_user(client):
    lg = client.post("/api/v1/login?username={0}&password={1}".format(access, encoded_secret))
    assert 200 == lg.status_code
    token = json.loads(lg.data)

    lg = client.post('/api/v1/users',
                     json={'dom_name': 'test_user_6', 'full_name': 'test user'},
                     headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.get('/api/v1/users', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    lg = client.delete('/api/v1/users?name=test_user_6', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    lg = client.get('/api/v1/users', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code

    lg = client.post('/api/v1/logout', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
