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

from falcon import testing

# Depending on your testing strategy and how your application
# manages state, you may be able to broaden the fixture scope
# beyond the default 'function' scope used in this example.
from api import AccountRestService, Config


@pytest.fixture()
def client():
    # Assume the hypothetical `myapp` package has a function called
    # `create()` to initialize and return a `falcon.API` instance.
    config = Config(create=False)
    config.update("database", "connection", "")
    return testing.TestClient(AccountRestService(Config(create=False), https_only=False, enable_auth=False))


def test_get_message(client):
    expected = {"message": "Hello, World!"}
    result = client.simulate_get('/')
    assert result.json == expected
