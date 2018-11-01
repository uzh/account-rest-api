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
import ldap

from functools import wraps

from flask import session, request, redirect, abort, current_app, url_for

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


class LDAP(object):

    logger = logging.getLogger(__name__)

    ldap_id_fields = [
        'sAMAccountName',
        'distinguishedName',
        'uid',
        'cn'
    ]

    ldap_fields = [
        'givenName',  # 'first_name'
        'memberOf',
        'name',  # 'name_lat',
        'displayName',  # 'display_name',
        'mail',  # 'mail',
    ]

    def __init__(self, app, config):
        self.uri = "{0}://{1}:{2}".format(config.ldap().get('schema'), config.ldap().get('host'), config.ldap().get('schema'))
        self.domain = config.ldap().get('domain')
        self.search_base = config.ldap().get('search_base')
        self.administrator_groups = config.ldap().get('administrator_groups')
        self.required_groups = config.ldap().get('required_groups')
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def connect(self):
        self.logger.debug("connecting to {0}".format(self.uri))
        self.conn = ldap.initialize(self.uri)
        return self.conn

    def teardown(self, exception):
        ctx = stack.top
        if hasattr(ctx, 'ldap_host'):
            ctx.ldap_host.close()

    @property
    def connection(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'ldap_host'):
                ctx.ldap_host = self.connect()
            return ctx.ldap_host

    def ldap_query(self, query):
        records = self.conn.search_s(self.search_base, ldap.SCOPE_SUBTREE, query, self.ldap_fields)
        self.conn.unbind_s()
        res = []
        for rec in records:
            if rec[0] is None:
                continue
            newrec = {}
            for field in rec[1].keys():
                try:
                    newrec[field] = rec[1][field][0] if len(rec[1][field]) == 1 else rec[1][field]
                except:
                    newrec[field] = None
            res.append(newrec)
        return res

    def ldap_login(self, username, pwd):
        try:
            self.connect()
            user = "{0}@{1}".format(username, self.domain)
            self.conn.set_option(ldap.OPT_REFERRALS, 0)
            self.conn.simple_bind_s(user, pwd.encode('utf8'))
            for key in self.ldap_id_fields:
                for user in self.ldap_query("{0}={1}".format(key, username)):
                    self.mu = dict(_id=user[key])
                    self.mu['username'] = user.get(key)
                    for field in self.ldap_fields:
                        self.mu[field] = user.get(field)
            for group in self.required_groups:
                if group not in self.mu.get('memberOf'):
                    self.logger.warning("{0} authenticated but not authorized".format(user))
                    return False
            for admin_group in self.administrator_groups:
                if admin_group in self.mu.get('memberOf'):
                    session['admin'] = True
            session['username'] = username
            return True
        except Exception as e:
            self.logger.error("failed login: {0}".format(e))
            return False

    def login(self):
        if 'username' in session:
            self.logger.info("user {0} already logged in".format(session['username']))
            return redirect(request.referrer)
        if 'username' in request.form and 'password' in request.form:
            if self.ldap_login(request.form['username'], request.form['password']):
                for i in self.mu.keys():
                    session[i] = self.mu[i]
                return redirect(request.referrer)
            else:
                self.logger.error("invalid credentials for user {0}".format(request.form['username']))
                abort(404)
        else:
            self.logger.warning("invalid arguments supplied")
            abort(404)


class LdapAuth(object):
    @staticmethod
    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'username' in session:
                return f(*args, **kwargs)
            return redirect(url_for(current_app.config['LDAP_LOGIN_PATH']))
        return decorated
