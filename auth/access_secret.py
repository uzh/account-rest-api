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

import logging
import hashlib
from datetime import datetime, timedelta

from functools import wraps

from connexion import NoContent
from flask import session, request, redirect, abort
from cryptography.fernet import Fernet

from db.handler import db_session
from db.service import Service


class AccessSecretToken(object):

    logger = logging.getLogger(__name__)

    def __init__(self, config):
        self.timeout = int(config.token().get('timeout'))

    def access_secret_verify(self, access, secret):
        try:
            s = db_session.query(Service)
            service = s.filter(Service.access == access).one_or_none()
            if not service:
                self.logger.warning("could not identify service by id {0}".format(access))
                return None
            if service.secret != hashlib.sha256(secret).hexdigest():
                self.logger.error("verification failed for service with id {0}".format(access))
            return Fernet(service.secret).encrypt(datetime.now() + timedelta(seconds=self.timeout))
        except Exception as e:
            self.logger.error("failed login: {0}".format(e))
            return None

    def authorize(self):
        if 'access_token' in session:
            if 'access' not in session:
                self.logger.warning("access credentials not found")
                abort(401)
            s = db_session.query(Service)
            service = s.filter(Service.access == session['access']).one_or_none()
            if not service:
                self.logger.error("could not identify service by id {0}".format(session['access']))
                abort(401)
            if Fernet(service.secret.decode("utf-8")).decrypt(session['access_token']) < datetime.now():
                self.logger.info("access to service with id {0} already granted".format(session['access']))
                return redirect(request.referrer)
            self.logger.debug("token timed out for {0}".format(session['access']))
            abort(401)
        if 'access' in request.form and 'secret' in request.form:
            access = request.form['access']
            access_token = self.access_secret_verify(access, request.form['secret'])
            if access_token:
                session['access'] = access
                session['access_token'] = access_token
                return redirect(request.referrer)
            else:
                self.logger.error("invalid credentials for service with id {0}".format(request.form['access']))
                abort(404)
        else:
            self.logger.warning("invalid arguments supplied")
            abort(404)

    @staticmethod
    def login_required(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            if 'username' in session:
                return func(*args, **kwargs)
            return NoContent, 401
        return decorated
