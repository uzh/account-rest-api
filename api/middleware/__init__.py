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

import api.util.serialize as json


class CrossDomain(object):

    def __init__(self, origin):
        self.origin = origin

    def process_response(self, req, resp, resource):
        resp.set_header("Access-Control-Allow-Origin", self.origin)
        resp.set_header("Access-Control-Allow-Methods", "GET, PUT, POST, DELETE")
        resp.set_header("Access-Control-Allow-Credentials", "true")
        resp.set_header("Access-Control-Allow-Headers", "Origin, Authorization, Content-Type, X-Requested-With")


class JSONTranslator(object):

    def process_request(self, req, resp):
        if req.content_length in (None, 0):
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest("Empty request body", "A valid JSON document is required.")

        try:
            req.context["doc"] = json.loads(body.decode("utf-8"))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPBadRequest("Malformed JSON, could not decode the request body. The JSON was "
                                        "incorrect or not encoded as UTF-8.")

    def process_response(self, req, resp, resource):
        if "result" not in req.context:
            return

        resp.body = json.dumps(req.context["result"])
