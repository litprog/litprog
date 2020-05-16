# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import io
import os
import re
import sys
import enum
import math
import time
import shutil
import typing as typ
import logging
import os.path
import datetime as dt
import operator as op
import tempfile
import functools as ft
import itertools as it
import collections

import click
import pathlib2 as pl

import litprog.build
import litprog.parse

log = logging.getLogger(__name__)


if os.environ.get('ENABLE_BACKTRACE') == '1':
    import backtrace

    backtrace.hook(align=True, strip_path=True, enable_on_envvar_only=True)

InputPaths = typ.Sequence[str]
FilePaths  = typ.Iterable[pl.Path]

click.disable_unicode_literals_warning = True

verbosity_option = click.option(
    '-v', '--verbose', count=True, help="Control log level. -vv for debug level."
)


class LogConfig(typ.NamedTuple):
    fmt: str
    lvl: int


def _parse_logging_config(verbosity: int) -> LogConfig:
    if verbosity == 0:
        return LogConfig("%(levelname)-7s - %(message)s", logging.WARNING)

    log_format = "%(asctime)s.%(msecs)03d %(levelname)-7s " + "%(name)-16s - %(message)s"
    if verbosity == 1:
        return LogConfig(log_format, logging.INFO)

    assert verbosity >= 2
    return LogConfig(log_format, logging.DEBUG)


_PREV_VERBOSITY: int = -1


def _configure_logging(verbosity: int = 0) -> None:
    global _PREV_VERBOSITY

    if verbosity <= _PREV_VERBOSITY:
        return

    _PREV_VERBOSITY = verbosity

    # remove previous logging handlers
    for handler in list(logging.root.handlers):
        logging.root.removeHandler(handler)

    log_cfg = _parse_logging_config(verbosity)
    logging.basicConfig(level=log_cfg.lvl, format=log_cfg.fmt, datefmt="%Y-%m-%dT%H:%M:%S")


@click.group()
@click.version_option(version="2020.1001-alpha")
@verbosity_option
def cli(verbose: int = 0) -> None:
    """litprog cli."""
    _configure_logging(verbose)


_in_path_arg = click.Path(readable=True)
_out_dir_arg = click.Path(file_okay=False, writable=True)


@cli.command()
@click.argument('input_paths', nargs=-1, type=_in_path_arg)
@click.option('--html', nargs=1, type=_out_dir_arg)
@click.option('--pdf' , nargs=1, type=_out_dir_arg)
@verbosity_option
def build(
    input_paths: InputPaths, html: typ.Optional[str], pdf: typ.Optional[str], verbose: int = 0
) -> None:
    _configure_logging(verbose)
    # TODO: figure out how to share this code between sub-commands
    md_paths = sorted(_iter_markdown_filepaths(input_paths))
    if len(md_paths) == 0:
        log.error("No markdown files found for {input_paths}.")
        click.secho("No markdown files found", fg='red')
        sys.exit(1)

    ctx       = litprog.parse.parse_context(md_paths)
    built_ctx = litprog.build.build(ctx)

    if pdf is None and html is None:
        return

    # NOTE: Since the html is the input for the pdf generation, the
    #   html is generated either way, the only question is if the
    #   output goes to a user specified or to a temporary directory.

    if html is None:
        html            = tempfile.mkdtemp(prefix="litprog_")
        is_html_tmp_dir = True
    else:
        is_html_tmp_dir = False

    html_dir = pl.Path(html)

    # lazy import since we don't always need it
    import litprog.gen_docs

    litprog.gen_docs.gen_html(built_ctx, html_dir)

    if pdf:
        pdf_dir          = pl.Path(pdf)
        selected_formats = [
            'print_letter',
            'print_halfletter',
            'print_booklet_letter',
            'print_twocol_letter',
            'print_a4',
            'print_a5',
            'print_booklet_a4',
            'print_twocol_a4',
            'print_ereader',
        ]
        litprog.gen_docs.gen_pdf(built_ctx, html_dir, pdf_dir, formats=selected_formats)

    if is_html_tmp_dir:
        shutil.rmtree(html_dir)


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


if __name__ == '__main__':
    cli()
