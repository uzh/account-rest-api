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

import os
import logging
import pickle
import psutil
import signal
from logging.handlers import RotatingFileHandler

from os.path import exists, expandvars, expanduser

import click
import click_log
import connexion
from flask_cors import CORS

from sqlalchemy.exc import SQLAlchemyError

from auth import NoAuth
from auth.access_secret import AccessSecretToken
from config import Config
from db.group import Group
from db.handler import init_db
from db.service import Service

logger = logging.getLogger()
click_log.basic_config(logger)

auth = NoAuth()
service_auth = NoAuth()

config = None


def application(application_config, no_auth, gevent=False, ui=False, debug=False):
    global config
    global auth
    global service_auth
    port = int(application_config.general().get('port'))
    logger.debug("initializing database")
    config = application_config
    session = init_db(application_config.database().get('connection'))
    if ui:
        logger.warning("enabling UI")
    options = {"swagger_ui": ui}
    if gevent:
        logger.info("gunicorn application")
        app = connexion.FlaskApp(__name__, port=port, debug=debug, specification_dir='swagger/', server='gevent', options=options)
    else:
        logger.info("direct request")
        app = connexion.FlaskApp(__name__, port=port, debug=debug, specification_dir='swagger/', options=options)
    app.app.secret_key = application_config.general().get('secret')
    # primary authentication tables
    try:
        s = session.query(Service)
        if not s.filter(Service.name == 'admin').one_or_none():
            admin_service = Service(name='admin', access=application_config.admin().get('access'), secret=application_config.admin().get('secret'))
            session.add(admin_service)
            session.commit()
    except SQLAlchemyError:
        logger.exception('failed to add admin service')
    try:
        g = session.query(Group)
        if not g.filter(Group.name == 'admins').one_or_none():
            admin_group = Group(name='admins', active=True)
            session.add(admin_group)
            session.commit()
    except SQLAlchemyError:
        logger.exception('failed to add admin group')
    if no_auth:
        logger.warning("authorization disabled")
    else:
        auth = NoAuth()
        service_auth = AccessSecretToken()
    app.add_api('api.yaml')
    if application_config.general().get('CORS'):
        CORS(app.app)
    return app


@click.group()
@click.option('-c', '--config-file', default='~/.acpy/api.config', help='Specify configuration file path (creates if not exists)')
@click.pass_context
@click_log.simple_verbosity_option(logger)
def cli(ctx, config_file):
    """
    This CLI allows you to manage the Accounting Center API, this service will run in the background. The service is
    wrapped by gevent by default. Check your config file for settings, the default location is in your home folder
    under `~/.acpy/api.config`.
    """
    ctx.obj = {}

    def set_level(level):
        for l in 'sqlalchemy', 'connexion', 'gunicorn', 'meinheld':
            li = logging.getLogger(l)
            if li:
                li.setLevel(level)

    if logger.getEffectiveLevel() == logging.DEBUG:
        set_level(logging.INFO)
    elif logger.getEffectiveLevel() == logging.INFO:
        set_level(logging.WARNING)
    elif logger.getEffectiveLevel() == logging.WARNING:
        set_level(logging.ERROR)
    else:
        set_level(logging.CRITICAL)

    config_file = Config(config_file)

    if config_file.logging().get('log_file'):
        handler = RotatingFileHandler(config_file.logging().get('log_file'),
                                      mode='a',
                                      maxBytes=int(config_file.logging().get('max_bytes')),
                                      backupCount=int(config_file.logging().get('backup_count')))
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s [%(funcName)s] %(message)s"))
        logger.addHandler(handler)

    ctx.obj['CONFIG'] = config_file


@cli.command(help='start api')
@click.option('-n', '--no-auth', is_flag=True, help='disable authentication')
@click.option('-g', '--gevent', is_flag=True, help='use gevent as server')
@click.option('-u', '--ui', is_flag=True, help='enable swagger ui (url/api/v1/ui)')
@click.option('-d', '--debug', is_flag=True, help='enable debug mode')
@click.option('-f', '--force', is_flag=True, help='force start ignoring recorded state')
@click.pass_context
def start(ctx, no_auth, gevent, ui, debug, force):
    runtime_config = dict(no_auth=no_auth, gevent=gevent, ui=ui, debug=debug)
    application_config = ctx.obj["CONFIG"]
    runtime = expandvars(expanduser(application_config.general().get("run_time")))
    if not exists(runtime) or debug or force:
        app = application(application_config, no_auth, gevent, ui, debug)
        runtime_config['pid'] = os.getpid()
        with open(runtime, 'wb') as f:
            pickle.dump(runtime_config, f)
        if gevent:
            app.run()
        else:
            def signal_handler(sig, frame):
                logger.debug("crtl+c detected, terminating")
                if exists(runtime):
                    os.remove(runtime)
                os.kill(runtime_config['pid'], signal.SIGKILL)
            signal.signal(signal.SIGINT, signal_handler)
            app.run()
            signal.pause()
    else:
        logger.warning("already detected running instance, please check if the process is still running")


@cli.command(help='stop api')
@click.option('-f', '--force', is_flag=True, help='kill instead of terminate')
@click.pass_context
def stop(ctx, force):
    runtime = expandvars(expanduser(ctx.obj['CONFIG'].general().get('run_time')))
    if not exists(runtime):
        logger.error("no previous instance detected")
    else:
        with open(runtime, 'rb') as f:
            runtime_config = pickle.load(f)
        if 'pid' in runtime_config:
            if psutil.pid_exists(runtime_config['pid']):
                try:
                    if force:
                        os.kill(runtime_config['pid'], signal.SIGTERM)
                    else:
                        os.kill(runtime_config['pid'], signal.SIGKILL)
                    logger.info("stop finished")
                except OSError as e:
                    logger.error("failed to stop rest service: {0}".format(e))

            else:
                logger.warning("could not find process for service under pid {0}, clearing stale state".format(runtime_config['pid']))
        else:
            logger.error("could not find process id, clearing stale state")
        os.remove(runtime)


@cli.command(help='rest service information')
@click.pass_context
def info(ctx):
    runtime = expandvars(expanduser(ctx.obj['CONFIG'].general().get('run_time')))
    if not exists(runtime):
        logger.warning("no previous instance detected, cannot determine restart parameters")
    else:
        with open(runtime, 'rb') as f:
            runtime_config = pickle.load(f)
        logger.info("*" * 33)
        for key in runtime_config:
            logger.info("{0} : {1}".format(key, runtime_config[key]))
        logger.info("*" * 33)


if __name__ == '__main__':
    cli()
