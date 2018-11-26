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
from flask import json

from config import Config
from app import application
from tests import access, secret


@pytest.fixture(scope='module')
def client():
    config = Config(create=False)
    config.update('admin', 'access', access)
    config.update('admin', 'secret', secret)
    config.update("database", "connection", "sqlite://")
    ars = application(config, no_auth=True)
    with ars.app.test_client() as c:
        yield c


def test_add_group_fails_for_non_admin(client):
    with client.session_transaction() as session:
        if 'admin' in session:
            del(session['admin'])
    lg = client.post('/api/v1/groups', json={'name': 'test_group', 'dom_name': 'test_pi', 'active': True})
    assert 401 == lg.status_code


def test_add_list_remove_user_from_group(client):
    with client.session_transaction() as session:
        session['admin'] = Fernet(secret.encode('utf-8')).encrypt(access.encode('utf-8'))
    dom_name = 'test_pi_1'
    group_name = 'test_group_1'
    user_name = 'test_user_1'
    lg = client.post('/api/v1/users', json={'dom_name': dom_name, 'full_name': 'test pi'})
    assert 201 == lg.status_code
    lg = client.post('/api/v1/groups', json={'name': group_name, 'dom_name': dom_name, 'active': True})
    assert 201 == lg.status_code
    lg = client.post('/api/v1/users', json={'dom_name': user_name, 'full_name': 'test user'})
    assert 201 == lg.status_code
    lg = client.get('/api/v1/groups')
    assert 200 == lg.status_code
    group_id = None
    for g in json.loads(lg.data):
        if g['name'] == group_name:
            group_id = int(g['id'])
    lg = client.get("/api/v1/groups/{0}".format(group_id))
    assert 200 == lg.status_code
    assert [] == json.loads(lg.data)
    lg = client.put("/api/v1/groups/{0}?user={1}&admin=False".format(group_id, user_name))
    assert 201 == lg.status_code
    lg = client.get("/api/v1/groups/{0}".format(group_id))
    assert 200 == lg.status_code
    assert 1 == len(json.loads(lg.data))
    lg = client.delete("/api/v1/groups/{0}?user={1}".format(group_id, user_name))
    assert 200 == lg.status_code
    lg = client.get("/api/v1/groups/{0}".format(group_id))
    assert 200 == lg.status_code
    assert 0 == len(json.loads(lg.data))


def test_retrieve_group_users_as_user(client):
    with client.session_transaction() as session:
        session['admin'] = Fernet(secret.encode('utf-8')).encrypt(access.encode('utf-8'))
    dom_name = 'test_pi_2'
    group_name = 'test_group_2'
    user_name = 'test_user_2'
    lg = client.post('/api/v1/users', json={'dom_name': dom_name, 'full_name': 'test pi'})
    assert 201 == lg.status_code
    lg = client.post('/api/v1/groups', json={'name': group_name, 'dom_name': dom_name, 'active': True})
    assert 201 == lg.status_code
    lg = client.post('/api/v1/users', json={'dom_name': user_name, 'full_name': 'test user'})
    assert 201 == lg.status_code
    lg = client.get('/api/v1/groups')
    assert 200 == lg.status_code
    group_id = None
    for g in json.loads(lg.data):
        if g['name'] == group_name:
            group_id = int(g['id'])
    lg = client.get("/api/v1/groups/{0}".format(group_id))
    assert 200 == lg.status_code
    assert [] == json.loads(lg.data)
    lg = client.put("/api/v1/groups/{0}?user={1}&admin=False".format(group_id, user_name))
    assert 201 == lg.status_code
    with client.session_transaction() as session:
        del(session['admin'])
        session['username'] = user_name
    lg = client.get("/api/v1/groups/{0}".format(group_id))
    assert 200 == lg.status_code


def test_user_list_groups(client):
    with client.session_transaction() as session:
        session['admin'] = Fernet(secret.encode('utf-8')).encrypt(access.encode('utf-8'))
    dom_name = 'test_pi_3'
    group_name = 'test_group_3'
    user_name = 'test_user_3'
    client.post('/api/v1/users', json={'dom_name': dom_name, 'full_name': 'test pi'})
    client.post('/api/v1/groups', json={'name': group_name, 'dom_name': dom_name, 'active': True})
    client.post('/api/v1/users', json={'dom_name': user_name, 'full_name': 'test user'})
    lg = client.get('/api/v1/groups')
    group_id = None
    for g in json.loads(lg.data):
        if g['name'] == group_name:
            group_id = int(g['id'])
    lg = client.put("/api/v1/groups/{0}?user={1}&admin=False".format(group_id, user_name))
    assert 201 == lg.status_code
    with client.session_transaction() as session:
        del(session['admin'])
        session['username'] = user_name
