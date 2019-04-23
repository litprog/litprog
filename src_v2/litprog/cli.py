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
import logging

log = logging.getLogger(__name__)
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


import hashlib

import click

import watchdog.events
import watchdog.observers

import litprog.parse
import litprog.build

# import litprog.watch
import litprog.session
import litprog.lptyp as lptyp

click.disable_unicode_literals_warning = True
verbosity_option                       = click.option(
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
    # TODO: figure out how to share this code between sub-commands
    md_paths = sorted(_iter_markdown_filepaths(input_paths))
    if len(md_paths) == 0:
        log.error("No markdown files found for {input_paths}.")
        click.secho("No markdown files found", fg='red')
        sys.exit(1)

    ctx = litprog.parse.parse_context(md_paths)
    try:
        sys.exit(litprog.build.build(ctx))
    except litprog.session.SessionException:
        sys.exit(1)


@cli.command()
@click.argument('input_paths', nargs=-1, type=click.Path(exists=True))
@verbosity_option
def watch(input_paths: InputPaths, verbose: int = 0) -> None:
    _configure_logging(verbose)
    # TODO: figure out how to share this code between sub-commands
    md_paths = sorted(_iter_markdown_filepaths(input_paths))
    if len(md_paths) == 0:
        log.error("No markdown files found for {input_paths}.")
        click.secho("No markdown files found", fg='red')
        sys.exit(1)

    sys.exit(_watch(input_paths, md_paths))


@cli.command()
@click.argument('input_paths', nargs=-1, type=click.Path(exists=True))
@verbosity_option
def sync_manifest(input_paths: InputPaths, verbose: int = 0) -> None:
    _configure_logging(verbose)
    # TODO: figure out how to share this code between sub-commands
    md_paths = sorted(_iter_markdown_filepaths(input_paths))
    if len(md_paths) == 0:
        log.error("No markdown files found for {input_paths}.")
        click.secho("No markdown files found", fg='red')
        sys.exit(1)

    ctx = litprog.parse.parse_context(md_paths)

    maybe_manifest = _parse_manifest(ctx)
    if maybe_manifest is None:
        return _init_manifest(ctx)
    else:
        return _sync_manifest(ctx, maybe_manifest)


def _watch(input_paths: InputPaths, md_paths: FilePaths) -> ExitCode:
    valid_md_paths = set(md_paths)
    observer       = watchdog.observers.Observer()
    handler        = WatchHandler()

    for path in input_paths:
        observer.schedule(handler, str(path))

    observer.start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


FSEvent = watchdog.events.FileSystemEvent


class WatchHandler(watchdog.events.FileSystemEventHandler):
    def on_modified(self, event: FSEvent) -> None:
        path = pl.Path(event.src_path)
        if path.is_file:
            _handle_modified(path)


AUTOFIX_PATTERNS = {
    r"\bapi\b"                : "API",
    r"\bhtml/pdf\b"           : "HTML/PDF",
    r"\b(B|b)urdon\b"         : r"\1urden",
    r"\b(P|p)receed\b"        : r"\1recede",
    r"\b(E|e)xtreem\b"        : r"\1xtreme",
    r"\b(N|n)ecessarry\b"     : r"\1ecessary",
    r"\b(N|n)ecessarilly\b"   : r"\1ecessarily",
    r"\b(P|p)rimarilly\b"     : r"\1rimarily",
    r"\b(P|p)rograming\b"     : r"\1rogramming",
    r"\b(A|a)sside\b"         : r"\1side",
    r"\b(S|s)entance\b"       : r"\1entence",
    r"\b(D|d)ependancy\b"     : r"\1ependency",
    r"\b(A|a)ppropriatly\b"   : r"\1ppropriately",
    r"\b(P|p)rogramatically\b": r"\1rogrammatically",
    r"\b(A|a)ccuratly"        : r"\1ccurately",
}

AUTOFIX_REGEXPS = {}


def _init_autofix_regexps():
    for search, repl in AUTOFIX_PATTERNS.items():
        AUTOFIX_REGEXPS[re.compile(search)] = repl


WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


def _iter_fixed_elements(ctx: lptyp.ParseContext) -> typ.Iterable[lptyp.MardownElement]:
    for elem in ctx.elements:
        if isinstance(elem, lptyp.FencedBlockMeta):
            yield elem
        elif isinstance(elem, lptyp.FencedBlockData):
            yield elem
        else:
            text       = "".join(l.val for l in elem.lines)
            fixed_text = _autofix(text)
            if text == fixed_text:
                yield elem
                continue

            keepends        = True
            fixed_line_vals = fixed_text.splitlines(keepends)
            # TODO: so what if they're different,?
            #   well, we would at least have to make sure
            #   we write all the fixed lines (maybe zip_longest).
            assert len(fixed_line_vals) == len(elem.lines)
            line_pairs  = zip(elem.lines, fixed_line_vals)
            fixed_lines = [
                lptyp.Line(old_line.line_no, fixed_line_val)
                for old_line, fixed_line_val in line_pairs
            ]
            yield lptyp.RawElement(elem.file_path, fixed_lines)


def file_id(path: pl.Path) -> bytes:
    stat      = path.stat()
    stat_data = f"{stat.st_ino}_{stat.st_size}_{stat.st_mtime}"

    id_sum = hashlib.new('sha1')
    id_sum.update(stat_data.encode('ascii'))
    with path.open(mode="rb") as fh:
        id_sum.update(fh.read())
    return id_sum.digest()


def _handle_modified(path: pl.Path) -> None:
    if path.is_dir() or path.suffix != ".md":
        return

    _init_autofix_regexps()
    old_file_id = file_id(path)
    ctx         = litprog.parse.parse_context([path])

    fixed_elements = list(_iter_fixed_elements(ctx))
    if fixed_elements == ctx.elements:
        return

    fixed_content = "".join(
        # line number prefix for debugging
        # "".join(f"{l.line_no:03d} " +  l.val for l in elem.lines)
        "".join(l.val for l in elem.lines)
        for elem in fixed_elements
    )

    tmp_path = pl.Path(path.parent, path.name + ".tmp")
    with tmp_path.open(mode="w") as fh:
        fh.write(fixed_content)

    new_file_id = file_id(path)
    if old_file_id == new_file_id:
        # nothing changed -> we can update with the fix
        tmp_path.rename(path)
    else:
        tmp_path.unlink()
    print("updated", path)


def _autofix(text: str) -> str:
    for regexp, repl in AUTOFIX_REGEXPS.items():
        text, n = regexp.subn(repl, text)
    return text


FileId     = str
PartId     = str
ChapterId  = str
ChapterNum = str  # eg. "00"

Manifest = typ.List[FileId]


class ChapterItem(typ.NamedTuple):
    num       : ChapterNum
    part_id   : PartId
    chapter_id: ChapterId
    md_path   : pl.Path


ChapterKey    = typ.Tuple[PartId, ChapterId]
ChaptersByKey = typ.Dict[ChapterKey, ChapterItem]


def _sync_manifest(ctx: lptyp.ParseContext, manifest: Manifest) -> ExitCode:
    chapters: ChaptersByKey = _parse_chapters(ctx)

    # TODO: probably it's better to put the manifest in a config file
    #   and keep the markdown files a little bit cleaner.
    chapters_by_file_id: typ.Dict[FileId, ChapterItem] = {}

    for file_id in manifest:
        if "::" not in file_id:
            errmsg = f"Invalid file id in manifest {file_id}"
            click.secho(errmsg, fg='red')
            return 1

        part_id, chapter_id = file_id.split("::", 1)
        chapter_key  = (part_id, chapter_id)
        chapter_item = chapters.get(chapter_key)
        if chapter_item is None:
            # TODO: deal with renaming,
            #   maybe best guess based on ordering
            raise KeyError(chapter_key)
        else:
            chapters_by_file_id[file_id] = chapter_item

    renames: typ.List[typ.Tuple[pl.Path, pl.Path]] = []

    # TODO: padding when indexes are > 9

    part_index    = 1
    chapter_index = 1
    prev_part_id  = ""

    for file_id in manifest:
        part_id, chapter_id = file_id.split("::", 1)

        if prev_part_id and part_id != prev_part_id:
            part_index += 1
            chapter_index = 1

        chapter_item = chapters_by_file_id[file_id]

        path = chapter_item.md_path
        ext  = path.name.split(".", 1)[-1]

        new_chapter_num = f"{part_index}{chapter_index}"
        new_filename    = f"{new_chapter_num}_{chapter_id}.{ext}"
        new_filepath    = path.parent / new_filename

        if new_filepath != path:
            renames.append((path, new_filepath))

        chapter_index += 1
        prev_part_id = part_id

    if not any(renames):
        return 0

    for src, tgt in renames:
        print(f"    {str(src):<35} -> {str(tgt):<35}")

    # TODO: perhaps rename should check for git and
    #   do git mv src tgt

    prompt = "Do you want to perform these renaming(s)?"
    if click.confirm(prompt):
        for src, tgt in renames:
            src.rename(tgt)

    return 0


CHAPTER_NUM_RE = re.compile(r"^[0-9A-Za-z]{2,3}_")


def _parse_chapters(ctx: lptyp.ParseContext) -> ChaptersByKey:
    chapters: ChaptersByKey = {}

    part_index    = "1"
    chapter_index = "1"

    # first chapter_id is the first part_id
    part_id = ""

    for path in sorted(ctx.md_paths):
        basename = path.name.split(".", 1)[0]
        if "_" in basename and CHAPTER_NUM_RE.match(basename):
            chapter_num, chapter_id = basename.split("_", 1)
            this_part_index = chapter_num[0]
            if this_part_index != part_index:
                part_id    = chapter_id
                part_index = this_part_index
            chapter_index = chapter_num[1]
        else:
            chapter_id = basename
            # auto generate chapter number
            chapter_num   = part_index + chapter_index
            chapter_index = chr(ord(chapter_index) + 1)

        if part_id == "":
            part_id = chapter_id

        chapter_key  = (part_id, chapter_id)
        chapter_item = ChapterItem(chapter_num, part_id, chapter_id, path)
        chapters[chapter_key] = chapter_item

    return chapters


def _parse_manifest(ctx: lptyp.ParseContext) -> typ.Optional[Manifest]:
    for elem in ctx.elements:
        if not isinstance(elem, lptyp.FencedBlockMeta):
            continue

        meta_block = elem
        manifest   = meta_block.options.get('manifest')
        if manifest is None:
            continue

        return manifest

    return None


def _init_manifest(ctx: lptyp.ParseContext) -> ExitCode:
    first_md_filepath = min(ctx.md_paths)
    print(f"Manifest not found. ", f"Would you like to create one in", first_md_filepath)
    print("_init_manifest() not implemented")
    return 1


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
