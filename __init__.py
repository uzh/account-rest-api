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
import signal
import sys
from logging.handlers import RotatingFileHandler

from os.path import exists, expandvars, expanduser

import click
import click_log
import psutil
from daemon import daemon

from gunicorn.app.base import BaseApplication

from app import AccountRestService
from config import Config


logger = logging.getLogger()
click_log.basic_config(logger)


class GunicornApp(BaseApplication):
    """ Gunicorn application loader """
    log = logging.getLogger(__name__)

    def __init__(self, application, options=None):
        self.options = options or {}
        self.application = application
        super(GunicornApp, self).__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def check_pid(pid_file):
    if pid_file and exists(expandvars(expanduser(pid_file))):
        with open(expandvars(expanduser(pid_file)), "r") as pfp:
            pid = int(pfp.read())
        if psutil.pid_exists(pid):
            return pid
    return None


@click.group()
@click.option('-c', '--config-file', default='~/.acpy/api.config', help='Specify configuration file path (creates if not exists)')
@click.pass_context
@click_log.simple_verbosity_option(logger)
def cli(ctx, config_file):
    """
    This CLI allows you to manage the Accounting Center API, this service will run in the background.
    The service is wrapped by gunicorn, and these commands allow you to control the gunicorn master process.
    Check your config file for settings, the default location is in your home folder under `~/.acpy/api.config`.
    """
    ctx.obj = {}

    def set_level(level):
        for l in "sqlalchemy", "connexion", "gunicorn", "meinheld":
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
        logger.addHandler(handler)

    ctx.obj["CONFIG"] = config_file


def _start_direct_(srv_config, no_auth, direct, ui, background):
    if background:
        with daemon.DaemonContext():
            AccountRestService(srv_config, no_auth=no_auth, direct=direct, ui=ui).start()
    else:
        AccountRestService(srv_config, no_auth=no_auth, direct=direct, ui=ui).start()
        signal.signal(signal.SIGINT, signal_handler)
        signal.pause()
        runtime = expandvars(expanduser(srv_config.general().get("run_time")))
        if exists(runtime):
            os.remove(runtime)


def _stop_direct_(srv_config, no_auth, direct, ui):
    AccountRestService(srv_config, no_auth=no_auth, direct=direct, ui=ui).stop(signal.SIGTERM)


def _start_gu_(srv_config, no_auth, direct, ui, background):
    if background:
        with daemon.DaemonContext():
            GunicornApp(AccountRestService(srv_config, no_auth=no_auth, direct=direct, ui=ui).app.app, srv_config.gunicorn()).run()
    else:
        GunicornApp(AccountRestService(srv_config, no_auth=no_auth, direct=direct, ui=ui).app.app, srv_config.gunicorn()).run()
        signal.signal(signal.SIGINT, signal_handler)
        signal.pause()
        runtime = expandvars(expanduser(srv_config.general().get("run_time")))
        if exists(runtime):
            os.remove(runtime)


def _reload_gu_(srv_config, no_auth, direct, ui, background):
    if background:
        with daemon.DaemonContext():
            GunicornApp(AccountRestService(srv_config, no_auth=no_auth, direct=direct, ui=ui).app.app, srv_config.gunicorn()).reload()
    else:
        GunicornApp(AccountRestService(srv_config, no_auth=no_auth, direct=direct, ui=ui).app.app, srv_config.gunicorn()).reload()


def _stop_gu_(pid_file, force=False):
    pid = check_pid(pid_file)
    if pid:
        try:
            if force == 0:
                os.kill(pid, signal.SIGTERM)
            elif force == 1:
                os.kill(pid, signal.SIGKILL)
            logger.info("stop finished")
        except OSError as e:
            logger.error("failed to stop rest service: {0}".format(e))


def _restart_direct_(srv_config, auth, direct, ui, background):
    _stop_direct_(srv_config, auth, direct, ui)
    _start_direct_(srv_config, auth, direct, ui, background)


def _restart_gu_(srv_config, auth, direct, ui, pid_file, background):
    _stop_gu_(pid_file)
    _start_gu_(srv_config, auth, direct, ui, background)


@cli.command(help="start api")
@click.option('-d', '--direct', is_flag=True, help='do not use gunicorn wrapper')
@click.option('-u', '--ui', is_flag=True, help='enable swagger ui (url/api/v1/ui)')
@click.option('-b', '--background', is_flag=True, help='start as a background process')
@click.option('-n', '--no-auth', is_flag=True, help='disable authentication')
@click.option('-f', '--force', is_flag=True, help='force start ignoring recorded state')
@click.pass_context
def start(ctx, direct, ui, background, no_auth, force):
    runtime_config = dict(direct=direct, ui=ui, background=background, no_auth=no_auth)
    runtime = expandvars(expanduser(ctx.obj["CONFIG"].general().get("run_time")))
    if direct:
        if not exists(runtime) or force:
            with open(runtime, 'wb') as f:
                runtime_config['mode'] = 'direct'
                pickle.dump(runtime_config, f)
            runtime_config.pop('mode', None)
            _start_direct_(ctx.obj["CONFIG"], **runtime_config)
        else:
            logger.error("already detected running instance, please check if the process is still running")
    else:
        if not exists(runtime) or force:
            with open(runtime, 'wb') as f:
                runtime_config['mode'] = 'gunicorn'
                pickle.dump(runtime_config, f)
            runtime_config.pop('mode', None)
            _start_gu_(ctx.obj["CONFIG"], **runtime_config)
        else:
            logger.error("already detected running instance, please check if the process is still running")


@cli.command(help="stop api")
@click.option("--force/--no-force", default=False, help="force kill service")
@click.pass_context
def stop(ctx, force):
    runtime = expandvars(expanduser(ctx.obj["CONFIG"].general().get("run_time")))
    if not exists(runtime):
        logger.error("no previous instance detected")
    else:
        with open(runtime, 'rb') as f:
            runtime_config = pickle.load(f)
        if runtime_config['direct']:
            runtime_config.pop('mode', None)
            runtime_config.pop('background', None)
            _stop_direct_(ctx.obj["CONFIG"], **runtime_config)
        else:
            _stop_gu_(ctx.obj["CONFIG"].gunicorn().get("pidfile"), force)
        runtime = expandvars(expanduser(ctx.obj["CONFIG"].general().get("run_time")))
        if exists(runtime):
            os.remove(runtime)


@cli.command(help="reload api")
@click.pass_context
def reload(ctx):
    runtime = expandvars(expanduser(ctx.obj["CONFIG"].general().get("run_time")))
    if not exists(runtime):
        logger.error("no previous instance detected")
    else:
        with open(runtime, 'rb') as f:
            runtime_config = pickle.load(f)
        if runtime_config['mode'] == 'direct':
            logger.warning("cannot reload instance that has been started directly")
        else:
            runtime_config.pop('direct', None)
            _reload_gu_(ctx.obj["CONFIG"], **runtime_config)


@cli.command(help="restart api")
@click.pass_context
def restart(ctx):
    runtime = expandvars(expanduser(ctx.obj["CONFIG"].general().get("run_time")))
    if not exists(runtime):
        logger.error("no previous instance detected, cannot determine restart parameters")
    else:
        with open(runtime, 'rb') as f:
            runtime_config = pickle.load(f)
        if runtime_config['mode'] == 'direct':
            _restart_direct_(ctx.obj["CONFIG"], **runtime_config)
        else:
            _restart_gu_(ctx.obj["CONFIG"], **runtime_config)


@cli.command(help="rest service information")
@click.pass_context
def info(ctx):
    runtime = expandvars(expanduser(ctx.obj["CONFIG"].general().get("run_time")))
    if not exists(runtime):
        logger.warning("no previous instance detected, cannot determine restart parameters")
    else:
        with open(runtime, 'rb') as f:
            runtime_config = pickle.load(f)
        logger.info("*" * 33)
        for key in runtime_config:
            logger.info("{0} : {1}".format(key, runtime_config[key]))

        pid = check_pid(ctx.obj["CONFIG"].gunicorn().get("pidfile"))
        if pid:
            logger.info("service running at {0}".format(ctx.obj["CONFIG"].gunicorn().get("bind")))
            logger.info("*" * 33)
            gup = psutil.Process(pid).as_dict(attrs=['pid', 'username', 'cpu_percent', 'name', 'memory_info', 'connections'])
            logger.info("CPU usage: {0}%".format(gup['cpu_percent']))
            logger.info("-" * 20)
            logger.info("memory info\n"
                        "- rss         : {0}\n"
                        "- vms         : {1}\n"
                        "- page faults : {2}\n"
                        "- page ins    : {3}".format(gup['memory_info'].rss,
                                                     gup['memory_info'].vms,
                                                     gup['memory_info'].pfaults,
                                                     gup['memory_info'].pageins))
            logger.info("-" * 20)
            logger.info("connections")
            for connection in gup['connections']:
                logger.info("- {0}".format(connection))
        logger.info("*" * 33)


if __name__ == "__main__":
    cli()
