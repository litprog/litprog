#!/usr/bin/env python
# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2018 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import click
import litprog

try:
    import backtrace

    # To enable pretty tracebacks:
    #   echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc
    backtrace.hook(align=True, strip_path=True, enable_on_envvar_only=True)
except ImportError:
    pass


click.disable_unicode_literals_warning = True


@click.group()
def cli() -> None:
    """litprog cli."""


@cli.command()
def version() -> None:
    """Show version number."""
    print(f"litprog version: {litprog.__version__}")
