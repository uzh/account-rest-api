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


def ldap_verify(server, user_loc, user_dn, base_dn, username, password):
    """
    Verify user against LDAP
    :param server: LDAP URI
    :param user_loc: user prefix (uid)
    :param user_dn: users fqdn
    :param base_dn: base search dn
    :param username: username
    :param password: password
    :return: username or None
    """
    logging.debug("LDAP: trying to authenticate user {0}".format(username))
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    conn = ldap.open(server)
    search_filter = "uid=" + username
    try:
        conn.bind_s("{0}={1},{2}".format(user_loc, username, user_dn), password)
        result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter)
        logging.debug("LDAP: search result {0}".format(result))
        conn.unbind_s()
        return username
    except ldap.LDAPError:
        conn.unbind_s()
        return None
