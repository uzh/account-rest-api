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

import connexion
from flask_cors import CORS


class AccountRestService(object):
    logger = logging.getLogger(__name__)

    def __init__(self, config, https=True, auth=True, direct=False):
        """
        Service wrapper for our Gunicorn and Flask
        :param config: our configuration object
        :param https: enable/disable https
        :param auth: enable/disable authorization
        :param direct: direct start API (don't use Gunicorn)
        """
        self.config = config
        self.direct = direct
        self.logger.debug("initializing routes")
        # Initialize framework
        if direct:
            self.app = connexion.FlaskApp(__name__, specification_dir='swagger/')
        else:
            self.app = connexion.FlaskApp(__name__,
                                          port=self.config.flask.get('port'),
                                          specification_dir='swagger/',
                                          server='gunicorn')
        # Build routes
        self.app.add_api('api.yaml')
        # add CORS support
        if self.config.general().get("CORS"):
            CORS(self.app.app)

    def start(self):
        """ A hook to when a Gunicorn worker calls run()."""
        self.logger.info("started accounting rest api")
        if self.direct:
            self.app.run(port=self.config.flask().get('port'), debug=self.config.flask().get('debug'))
        else:
            self.app.run(debug=self.config.flask().get('debug'))

    def stop(self, signal):
        """ A hook to when a Gunicorn worker starts shutting down. """
        self.logger.info("stopped accounting rest api")
