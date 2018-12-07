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
from tests import access, secret, encoded_secret, generate_token_headers


@pytest.fixture(scope='module')
def client():
    config = Config(create=False)
    config.update('admin', 'access', access)
    config.update('admin', 'secret', secret)
    config.update('database', 'connection', 'sqlite://')
    ars = application(config)
    with ars.app.test_client() as c:
        yield c


def test_add_resource_fails_for_non_admin(client):
    lg = client.post('/api/v1/resources?name=test_resource')
    assert 401 == lg.status_code


def test_add_list_resource(client):
    lg = client.post("/api/v1/login?username={0}&password={1}".format(access, encoded_secret))
    assert 200 == lg.status_code
    token = json.loads(lg.data)

    lg = client.post('/api/v1/resources?name=test_resource', headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.get('/api/v1/resources', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    resources = json.loads(lg.data)
    assert 1 == len(resources)

    lg = client.post('/api/v1/logout', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code


def test_add_remove_group_from_resource(client):
    lg = client.post("/api/v1/login?username={0}&password={1}".format(access, encoded_secret))
    assert 200 == lg.status_code
    token = json.loads(lg.data)

    lg = client.post('/api/v1/resources?name=test_resource_1', headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    resource = json.loads(lg.data)
    user_name = 'test_resource_user'
    group_name = 'test_resource_group'
    lg = client.post('/api/v1/users', json={'dom_name': user_name, 'full_name': 'test pi'}, headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.post('/api/v1/groups', json={'name': group_name, 'dom_name': user_name, 'active': True}, headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.put("/api/v1/resource/{0}?name={1}".format(resource['id'], group_name), headers=generate_token_headers(dict(), token))
    assert 201 == lg.status_code
    lg = client.get("/api/v1/resource/{0}".format(resource['id']), headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
    groups = json.loads(lg.data)
    assert 1 == len(groups)

    lg = client.post('/api/v1/logout', headers=generate_token_headers(dict(), token))
    assert 200 == lg.status_code
