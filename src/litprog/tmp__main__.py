#!/usr/bin/env python
# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import typing as typ
import pathlib2 as pl

InputPaths = typ.Sequence[str]
Paths      = typ.Iterable[pl.Path]
import yaml
import toml
import json
import uuid
import collections

# To enable pretty tracebacks:
#   echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc
if os.environ.get('ENABLE_BACKTRACE') == '1':
    import backtrace

    backtrace.hook(align=True, strip_path=True, enable_on_envvar_only=True)
import logging

log = logging.getLogger("litprog.cli")


def _configure_logging(verbosity: int = 0) -> None:
    if verbosity >= 2:
        log_format = (
            "%(asctime)s.%(msecs)03d %(levelname)-7s " + "%(name)-15s - %(message)s"
        )
        log_level = logging.DEBUG
    elif verbosity == 2:
        log_format = "%(levelname)-7s - %(message)s"
        log_level  = logging.INFO
    else:
        log_format = "%(levelname)-7s - %(message)s"
        log_level  = logging.WARNING

    logging.basicConfig(level=log_level, format=log_format, datefmt="%Y-%m-%dT%H:%M:%S")


import click

click.disable_unicode_literals_warning = True


@click.group()
@click.version_option(version="v201901.0001-alpha")
@click.option(
    '-v', '--verbose', count=True, help="Control log level. -vv for debug level."
)
def cli(verbose: int = 0) -> None:
    """litprog cli."""
    _configure_logging(verbose=verbose)


InputPaths = typ.Sequence[str]


@cli.command()
@click.argument('input_paths', nargs=-1, type=click.Path(exists=True))
@click.option(
    '-v', '--verbose', count=True, help="Control log level. -vv for debug level."
)
def build(input_paths: InputPaths, verbose: int = 0) -> None:
    _configure_logging(verbose)
    context = _prepare_context(input_paths)
    _build(context)


MarkdownPaths = typ.Iterable[pl.Path]


def _iter_markdown_filepaths(input_paths: InputPaths) -> MarkdownPaths:
    for in_path_str in input_paths:
        in_path = pl.Path(in_path_str)
        if in_path.is_dir():
            for in_filepath in in_path.glob("**/*.md"):
                yield in_filepath
        else:
            yield in_path
