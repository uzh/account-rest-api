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

import falcon
import jsonschema

import api.util.serialize as json


class BaseResource(object):
    @staticmethod
    def format_body(data):
        return json.dumps(data)

    @staticmethod
    def format_input(data):
        return json.loads(data)


def validate(schema):
    def decorator(func):
        def wrapper(self, req, resp, *args, **kwargs):
            try:
                raw_json = req.stream.read()
                obj = json.loads(raw_json.decode("utf-8"))
            except Exception:
                raise falcon.HTTPBadRequest("Invalid data", "Could not properly parse the provided data as JSON")

            try:
                jsonschema.validate(obj, schema)
            except jsonschema.ValidationError as e:
                raise falcon.HTTPBadRequest("Failed data validation", e.message)

            return func(self, req, resp, *args, parsed=obj, **kwargs)
        return wrapper
    return decorator
