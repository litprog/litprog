# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

###################################
#    This is a generated file.    #
# This file should not be edited. #
#  Changes will be overwritten!   #
###################################
import os
import io
import re
import sys
import math
import time
import enum
import os.path
import collections
import typing as typ
import pathlib2 as pl
import operator as op
import datetime as dt
import itertools as it
import functools as ft

InputPaths = typ.Sequence[str]
FilePaths  = typ.Iterable[pl.Path]

ExitCode = int
import logging

log = logging.getLogger(__name__)
# To enable pretty tracebacks:
#   echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc
if os.environ.get('ENABLE_BACKTRACE') == '1':
    import backtrace

    backtrace.hook(align=True, strip_path=True, enable_on_envvar_only=True)


class LogConfig(typ.NamedTuple):
    fmt: str
    lvl: int


def _parse_logging_config(verbosity: int) -> LogConfig:
    if verbosity == 0:
        return LogConfig("%(levelname)-7s - %(message)s", logging.WARNING)

    log_format = "%(asctime)s.%(msecs)03d %(levelname)-7s " + "%(name)-15s - %(message)s"
    if verbosity == 1:
        return LogConfig(log_format, logging.INFO)

    assert verbosity >= 2
    return LogConfig(log_format, logging.DEBUG)


def _configure_logging(verbosity: int = 0) -> None:
    _prev_verbosity: int = getattr(_configure_logging, '_prev_verbosity', -1)

    if verbosity <= _prev_verbosity:
        return

    _configure_logging._prev_verbosity = verbosity

    # remove previous logging handlers
    for handler in list(logging.root.handlers):
        logging.root.removeHandler(handler)

    log_cfg = _parse_logging_config(verbosity)
    logging.basicConfig(level=log_cfg.lvl, format=log_cfg.fmt, datefmt="%Y-%m-%dT%H:%M:%S")


import click

import litprog.parse
import litprog.build
import litprog.session

click.disable_unicode_literals_warning = True

verbosity_option = click.option(
    '-v', '--verbose', count=True, help="Control log level. -vv for debug level."
)


@click.group()
@click.version_option(version="v201901.0001-alpha")
@verbosity_option
def cli(verbose: int = 0) -> None:
    """litprog cli."""
    _configure_logging(verbose)


@cli.command()
@click.argument('input_paths', nargs=-1, type=click.Path(exists=True))
@verbosity_option
def build(input_paths: InputPaths, verbose: int = 0) -> None:
    _configure_logging(verbose)
    md_filepaths = sorted(_iter_markdown_filepaths(input_paths))
    context      = litprog.parse.parse_context(md_filepaths)
    try:
        sys.exit(litprog.build.build(context))
    except litprog.session.SessionException:
        sys.exit(1)


MARKDOWN_FILE_EXTENSIONS = {
    "markdown",
    "mdown",
    "mkdn",
    "md",
    "mkd",
    "mdwn",
    "mdtxt",
    "mdtext",
    "text",
    "Rmd",
}


def _iter_markdown_filepaths(input_paths: InputPaths) -> FilePaths:
    for path_str in input_paths:
        path = pl.Path(path_str)
        if path.is_file():
            yield path
        else:
            for ext in MARKDOWN_FILE_EXTENSIONS:
                for fpath in path.glob(f"**/*.{ext}"):
                    yield fpath
