# -*- coding: utf-8 -*-
"""entry point for zazu"""
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import click
import os
import git_helper
import zazu.build
import zazu.config
import zazu.dev.commands
import zazu.repo.commands
import zazu.style
import zazu.tool.commands
import zazu.upgrade


@click.group()
@click.version_option(version=zazu.__version__)
@click.pass_context
def cli(ctx):
    ctx.obj = zazu.config.Config(git_helper.get_repo_root(os.getcwd()))

cli.add_command(zazu.upgrade.upgrade)
cli.add_command(zazu.style.style)
cli.add_command(zazu.build.build)
cli.add_command(zazu.dev.commands.dev)
cli.add_command(zazu.repo.commands.repo)
cli.add_command(zazu.tool.commands.tool)
