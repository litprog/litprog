# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import sys
import shutil
import typing as typ
import logging
import tempfile

import click
import pathlib2 as pl

import litprog.build as lp_build
import litprog.parse as lp_parse

try:
    import pretty_traceback

    pretty_traceback.install()
except ImportError:
    pass  # no need to fail because of missing dev dependency


logger = logging.getLogger(__name__)


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
@click.option(
    '-e', "--exitfirst/--no-exitfirst", default=False, help="Exit instantly on first error."
)
@click.option(
    '-i',
    "--in-place-update",
    is_flag=True,
    default=False,
    help="In place update of lp_out and lp_run blocks in markdown files.",
)
@verbosity_option
def build(
    input_paths    : InputPaths,
    html           : typ.Optional[str],
    pdf            : typ.Optional[str],
    exitfirst      : bool = False,
    in_place_update: bool = False,
    verbose        : int  = 0,
) -> None:
    _configure_logging(verbose)

    if len(input_paths) == 0:
        click.secho("No markdown files given.", fg='red')
        sys.exit(1)

    md_paths = sorted(_iter_markdown_filepaths(input_paths))
    if len(md_paths) == 0:
        msg = f"No markdown files found for {' '.join(input_paths)}"
        logger.error(msg)
        click.secho(msg, fg='red')
        sys.exit(1)

    ctx       = lp_parse.parse_context(md_paths)
    built_ctx = lp_build.build(ctx, exitfirst=exitfirst, in_place_update=in_place_update)

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
    import litprog.gen_docs as lp_gen_docs

    lp_gen_docs.gen_html(built_ctx, html_dir)

    if pdf:
        pdf_dir          = pl.Path(pdf)
        selected_formats = [
            # 'print_letter',
            # 'print_halfletter',
            # 'print_booklet_letter',
            # 'print_twocol_letter',
            # 'print_a4',
            'print_a5',
            # 'print_booklet_a4',
            # 'print_twocol_a4',
            # 'print_ereader',
        ]
        lp_gen_docs.gen_pdf(built_ctx, html_dir, pdf_dir, formats=selected_formats)

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
