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
import signal
import time

from os.path import exists, expandvars

import click
import click_log
import psutil

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


def check_pid(pid_file):
    if pid_file and exists(expandvars(pid_file)):
        with open(expandvars(pid_file), "r") as pfp:
            pid = int(pfp.read())
        if psutil.pid_exists(pid):
            return pid
    return None


@click.group()
@click.option("-c", "--config-file", default="/etc/accounting-rest/api.confg", help="Specify configuration file path (creates if not exists)")
@click.option("--spew/--no-spew", default=False, help="spew all messages, really noisy (default --no-spew)")
@click.option("--auth/--no-auth", default=True, help="disable authentication (default --auth)")
@click.option("--direct", is_flag=True, help="don't use gunicorn wrapper")
@click.pass_context
@click_log.simple_verbosity_option(logger)
def cli(ctx, config_file, spew, auth, direct):
    """
    This CLI allows you to manage the Accounting Rest API, this service will run in the background.
    The service is wrapped by gunicorn, and these commands allow you to control the gunicorn master process.
    Check your config file for settings, the default location is in your home folder under `.accounting-rest`.
    This service enables HTTPS by default, so stick it behind a proxy (we recommend nginx).
    Use the --no-https flag only for testing, never in production!
    :param ctx: our context
    :param config_file: our configuration file
    :param spew: very noisy debugging
    :param auth: enable/disable authentication mechanism
    :param direct: don't user Gunicorn
    """
    ctx.obj = {}

    def set_level(level):
        for l in "sqlalchemy", "connexion", "gunicorn", "meinheld":
            li = logging.getLogger(l)
            if li:
                li.setLevel(level)

    if spew:
        logger.setLevel(logging.DEBUG)
        set_level(logging.DEBUG)
    if logger.getEffectiveLevel() == logging.DEBUG:
        set_level(logging.INFO)
    elif logger.getEffectiveLevel() == logging.INFO:
        set_level(logging.WARNING)
    elif logger.getEffectiveLevel() == logging.WARNING:
        set_level(logging.ERROR)
    elif logger.getEffectiveLevel() == logging.ERROR:
        set_level(logging.CRITICAL)

    config_file = Config(config_file)

    ctx.obj["CONFIG"] = config_file
    ctx.obj["SRV"] = AccountRestService(config_file, auth=auth, direct=direct)
    gu_config = config_file.gunicorn()
    gu_config["spew"] = spew
    if not direct:
        ctx.obj["APP"] = GunicornApp(ctx.obj["SRV"], gu_config)


@cli.command(help="start accounting-rest api")
@click.pass_context
def start(ctx):
    pid = check_pid(ctx.obj["CONFIG"].gunicorn().get("pidfile"))
    if pid:
        logger.info("rest service already running")
    else:
        logger.info("starting rest service")
        if ctx.obj["APP"]:
            ctx.obj["APP"].run()
        else:
            ctx.obj["SRV"].start()


@cli.command(help="rest service information")
@click.pass_context
def info(ctx):
    pid = check_pid(ctx.obj["CONFIG"].gunicorn().get("pidfile"))
    if pid:
        logger.info("service running at {0}".format(ctx.obj["CONFIG"].gunicorn().get("bind")))
        logger.info("*" * 33)
        gup = psutil.Process(pid)
        logger.info("number of cpu's: {0} ({1}%)".format(gup.cpu_num(), gup.cpu_percent()))
        logger.info("memory info\n"
                    "- rss    : {0}\n"
                    "- vms    : {1}\n"
                    "- shared : {2}\n"
                    "- text   : {3}\n"
                    "- lib    : {4}\n"
                    "- data   : {5}\n"
                    "- dirty  : {6}".format(gup.memory_info().rss,
                                            gup.memory_info().vms,
                                            gup.memory_info().shared,
                                            gup.memory_info().text,
                                            gup.memory_info().lib,
                                            gup.memory_info().data,
                                            gup.memory_info().dirty))
        logger.info("connections")
        for connection in gup.connections():
            logger.info("- {0}".format(connection))
        logger.info("*" * 33)
    else:
        if ctx.obj["APP"]:
            logger.warning("rest service not running, could not find pid")
        else:
            logger.info("started in direct mode, can't determine pid")


@cli.command(help="reload rest service")
@click.pass_context
def reload(ctx):
    logger.info("reloading rest service")
    if ctx.obj["APP"]:
        ctx.obj["APP"].reload()
    else:
        ctx.obj["SRV"].stop()
        ctx.obj["SRV"].start()
    logger.info("reload finished")


@cli.command(help="stop rest service")
@click.option("--force/--no-force", default=False, help="force kill service")
@click.pass_context
def stop(ctx, force):
    logger.info("stopping rest service")
    pid = check_pid(ctx.obj["CONFIG"].gunicorn().get("pidfile"))
    if pid:
        try:
            if force == 0:
                os.kill(pid, signal.SIGTERM)
            elif force == 1:
                os.kill(pid, signal.SIGKILL)
            logger.info("stop finished")
        except OSError as e:
            logger.error("failed to stop rest service: {0}".format(e))
    else:
        if ctx.obj["APP"]:
            logger.warning("could not find pid")
        else:
            ctx.obj["SRV"].stop()


@cli.command(help="restart rest service")
@click.pass_context
def restart(ctx):
    if ctx.obj["APP"]:
        pid = check_pid(ctx.obj["CONFIG"].gunicorn().get("pidfile"))
        if pid:
            logger.info("stopping rest service")
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(3)
                logger.info("stop finished, restarting rest service")
                ctx.obj["APP"].run()
            except OSError as e:
                logger.error("failed to restart rest service: {0}".format(e))
        else:
            logging.info("rest service not running, starting it.")
            ctx.obj["APP"].run()
    else:
        ctx.obj["SRV"].stop()
        ctx.obj["SRV"].start()
        logger.info("restart finished")


if __name__ == "__main__":
    cli()
