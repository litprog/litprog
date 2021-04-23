# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import os
import sys
import glob
import shutil
import typing as typ
import logging
import pathlib as pl
import tempfile

import click

import litprog.build as lp_build
import litprog.parse as lp_parse
import litprog.watch as lp_watch

try:
    import pretty_traceback

    pretty_traceback.install()
except ImportError:
    pass  # no need to fail because of missing dev dependency


logger = logging.getLogger(__name__)


InputPaths = typ.Sequence[str]

click.disable_unicode_literals_warning = True


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
    # pylint: disable=global-statement
    global _PREV_VERBOSITY

    if verbosity <= _PREV_VERBOSITY:
        # allow function to be called multiple times
        return

    _PREV_VERBOSITY = verbosity

    # remove previous logging handlers
    for handler in list(logging.root.handlers):
        logging.root.removeHandler(handler)

    log_cfg = _parse_logging_config(verbosity)
    logging.basicConfig(level=log_cfg.lvl, format=log_cfg.fmt, datefmt="%Y-%m-%dT%H:%M:%S")


def _iter_markdown_filepaths(input_paths: InputPaths) -> typ.Iterable[pl.Path]:
    for path_str in input_paths:
        path = pl.Path(path_str)
        if path.is_file():
            yield path
        elif path.is_dir():
            for ext in MARKDOWN_FILE_EXTENSIONS:
                for fpath in path.glob(f"**/*.{ext}"):
                    yield fpath
        else:
            glob_path_strs = glob.glob(path_str)
            if glob_path_strs:
                for glob_path_str in glob_path_strs:
                    glob_path = pl.Path(glob_path_str)
                    if glob_path.is_file():
                        yield glob_path
                # TODO (mb 2021-01-01): support globs
            else:
                logger.warning(f"Invalid path: '{path_str}'")


def _get_md_paths(input_paths: InputPaths) -> typ.List[pl.Path]:
    if len(input_paths) == 0:
        click.secho("No markdown files given.", fg='red')
        sys.exit(1)

    md_paths = sorted(_iter_markdown_filepaths(input_paths))
    if len(md_paths) == 0:
        msg = f"No markdown files found for {' '.join(input_paths)}"
        logger.error(msg)
        click.secho(msg, fg='red')
        sys.exit(1)

    return md_paths


# TODO (mb 2021-01-28): These should be parsed from the front matter
SELECTED_FORMATS = [
    'print_a4',
    'print_letter',
    'print_ereader',
    'print_a5',
    'print_booklet_a4',
    'print_halfletter',
    'print_booklet_letter',
    # 'print_twocol_letter',
    # 'print_twocol_a4',
]


def _num_cpus() -> int:
    try:
        # pylint: disable=no-member;    not available on all platforms
        return len(os.sched_getaffinity(0))
    except AttributeError:
        return os.cpu_count() or 1


DEFAULT_CONCURRENCY = max(2, _num_cpus())


def _build(
    input_paths    : InputPaths,
    html           : typ.Optional[str],
    pdf            : typ.Optional[str],
    exitfirst      : bool = False,
    in_place_update: bool = False,
    cache_enabled  : bool = True,
    concurrency    : int  = DEFAULT_CONCURRENCY,
) -> None:
    build_opts = lp_build.BuildOptions(
        exitfirst=exitfirst,
        in_place_update=in_place_update,
        cache_enabled=cache_enabled,
        concurrency=concurrency,
    )

    md_paths = _get_md_paths(input_paths)

    parse_ctx = lp_parse.parse_context(md_paths)
    built_ctx = lp_build.build(parse_ctx, build_opts)

    logger.info("build completed")

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

    # pylint: disable=import-outside-toplevel ; lazy import since we don't always need it
    #   if we were to eagerly import this, then it would slow down every cli invokation,
    #   even those which don't generate --html or --pdf output.
    import litprog.gen_docs as lp_gen_docs

    lp_gen_docs.gen_html(built_ctx, html_dir)

    if pdf:
        pdf_dir = pl.Path(pdf)
        lp_gen_docs.gen_pdf(built_ctx, html_dir, pdf_dir, formats=SELECTED_FORMATS)

    if is_html_tmp_dir:
        shutil.rmtree(html_dir)


_in_path_arg = click.Path(readable=True)
_out_dir_arg = click.Path(file_okay=False, writable=True)

_arg_input_paths = click.argument('input_paths', nargs=-1, type=_in_path_arg)

_opt_html = click.option('--html', nargs=1, type=_out_dir_arg)
_opt_pdf  = click.option('--pdf' , nargs=1, type=_out_dir_arg)

_opt_existfirst = click.option(
    '-e',
    "--exitfirst/--no-exitfirst",
    default=False,
    help="Exit instantly on first error.",
)

_opt_in_place = click.option(
    '-i',
    "--in-place-update",
    is_flag=True,
    default=False,
    help="In place update of lp_out and lp_run blocks in markdown files.",
)

_opt_concurrency = click.option(
    '-n',
    "--concurrency",
    default=DEFAULT_CONCURRENCY,
    help="Number of concurrent processes to execute.",
)

_opt_cache_enabled = click.option(
    "--cache-enabled/--no-cache",
    is_flag=True,
    default=True,
    help="Enable/disable block result cache. Default: enabled",
)

_opt_verbose = click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")


@click.group()
@click.version_option(version="2021.1005-alpha")
@_opt_verbose
def cli(verbose: int = 0) -> None:
    """CLI for litprog."""
    _configure_logging(verbose)


@cli.command()
@_arg_input_paths
@_opt_html
@_opt_pdf
@_opt_existfirst
@_opt_in_place
@_opt_concurrency
@_opt_cache_enabled
@_opt_verbose
def build(
    input_paths    : InputPaths,
    html           : typ.Optional[str],
    pdf            : typ.Optional[str],
    exitfirst      : bool = False,
    in_place_update: bool = False,
    concurrency    : int  = DEFAULT_CONCURRENCY,
    cache_enabled  : bool = True,
    verbose        : int  = 0,
) -> None:
    _configure_logging(verbose)
    _build(input_paths, html, pdf, exitfirst, in_place_update, cache_enabled, concurrency)


@cli.command()
@_arg_input_paths
@_opt_html
@_opt_pdf
@_opt_existfirst
@_opt_in_place
@_opt_concurrency
@_opt_cache_enabled
@_opt_verbose
def watch(
    input_paths    : InputPaths,
    html           : typ.Optional[str],
    pdf            : typ.Optional[str],
    exitfirst      : bool = False,
    in_place_update: bool = False,
    concurrency    : int  = DEFAULT_CONCURRENCY,
    cache_enabled  : bool = True,
    verbose        : int  = 0,
) -> None:
    _configure_logging(verbose)

    if len(input_paths) == 0:
        click.secho("No paths given.", fg='red')
        sys.exit(1)

    # initial build
    try:
        _build(input_paths, html, pdf, exitfirst, in_place_update, cache_enabled, concurrency)
    except lp_build.BlockExecutionError:
        pass

    watcher = lp_watch.Watcher(input_paths)

    def _build_cb(changes) -> None:
        try:
            _build(input_paths, html, pdf, exitfirst, in_place_update, cache_enabled, concurrency)
        except lp_build.BlockExecutionError:
            pass
        # refresh mtimes after build, as they may have changed in the meantime
        watcher.refresh_mtimes()

    watcher.watch(callback=_build_cb)


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


if __name__ == '__main__':
    cli()
