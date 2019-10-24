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
    config.update("database", "connection", "sqlite://")
    ars = application(config)
    with ars.app.test_client() as c:
        yield c


def test_add_group_fails_for_non_admin(client):
    lg = client.post('/api/v1/groups', json={'name': 'test_group', 'dom_name': 'test_pi', 'active': True})
    assert 401 == lg.status_code


def test_add_list_remove_user_from_group(client):
    lg = client.post("/api/v1/login?username={0}&password={1}".format(access, encoded_secret))
    assert 200 == lg.status_code
    token = json.loads(lg.data)

    dom_name = 'test_pi_1'
    group_name = 'test_group_1'
    user_name = 'test_user_1'
    lg = client.post('/api/v1/users', json={'dom_name': dom_name, 'full_name': 'test pi'}, headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.post('/api/v1/groups', json={'name': group_name, 'dom_name': dom_name, 'active': True}, headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.post('/api/v1/users', json={'dom_name': user_name, 'full_name': 'test user'}, headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.get('/api/v1/groups', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    group_id = None
    for g in json.loads(lg.data):
        if g['name'] == group_name:
            group_id = int(g['id'])
    lg = client.get("/api/v1/groups/{0}".format(group_id), headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    assert [] == json.loads(lg.data)
    lg = client.put("/api/v1/groups/{0}?u={1}&admin=False".format(group_id, user_name), headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.get("/api/v1/groups/{0}".format(group_id), headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    assert 1 == len(json.loads(lg.data))
    lg = client.delete("/api/v1/groups/{0}?u={1}".format(group_id, user_name), headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    lg = client.get("/api/v1/groups/{0}".format(group_id), headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    assert 0 == len(json.loads(lg.data))

    lg = client.post('/api/v1/logout', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code


def test_retrieve_group_users_as_user(client):
    lg = client.post("/api/v1/login?username={0}&password={1}".format(access, encoded_secret))
    assert 200 == lg.status_code
    token = json.loads(lg.data)

    dom_name = 'test_pi_2'
    group_name = 'test_group_2'
    user_name = 'test_user_2'
    lg = client.post('/api/v1/users', json={'dom_name': dom_name, 'full_name': 'test pi'}, headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.post('/api/v1/groups', json={'name': group_name, 'dom_name': dom_name, 'active': True}, headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.post('/api/v1/users', json={'dom_name': user_name, 'full_name': 'test user'}, headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.get('/api/v1/groups', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    group_id = None
    for g in json.loads(lg.data):
        if g['name'] == group_name:
            group_id = int(g['id'])
    lg = client.get("/api/v1/groups/{0}".format(group_id), headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    assert [] == json.loads(lg.data)
    lg = client.put("/api/v1/groups/{0}?u={1}&admin=False".format(group_id, user_name), headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code

    lg = client.post('/api/v1/logout', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code

    from api.auth import generate_token
    from api.auth import tokens

    user_token = generate_token(user_name)
    tokens[user_name] = user_token
    with client.session_transaction() as session:
        session['username'] = user_name

    lg = client.get('/api/v1/me', headers={'X-TOKEN': user_token})
    assert 200 == lg.status_code
    me = json.loads(lg.data)
    assert len(me['groups']) > 0

    lg = client.get("/api/v1/groups/{0}".format(me['groups'][0]['id']), headers={'X-TOKEN': user_token})
    assert 200 == lg.status_code

    tokens.pop(user_name, None)
    with client.session_transaction() as session:
        if 'username' in session:
            del(session['username'])
