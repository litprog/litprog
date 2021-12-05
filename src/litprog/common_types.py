# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import typing as typ
from pathlib import Path


class FormatOptions(typ.NamedTuple):

    out : str
    err : str
    info: str

    out_prefix: str
    err_prefix: str


class SessionBlockOptions(typ.NamedTuple):
    """A Session Block based on an 'exec', 'run' or 'out' directive.

    If it is an exec or run directive a session is run and the output is
    captured for later use. If it is an out directive, output from a previous
    capture is used.
    """

    command  : typ.Optional[str]
    directive: str

    provides_id         : typ.Optional[str]
    requires_ids        : set[str]
    timeout             : float
    input_delay         : float
    expected_exit_status: int

    capture_file: typ.Optional[Path]

    is_stdin_writable: bool
    is_debug         : bool
    keepends         : bool

    fmt: FormatOptions


class BlockLineInfo(typ.NamedTuple):
    md_path     : Path
    first_lineno: int
    num_lines   : int


BlockLineInfos = list[BlockLineInfo]


class Headline(typ.NamedTuple):

    md_path   : Path
    elem_index: int
    text      : str
    level     : int


InfoString = str


class Directive(typ.NamedTuple):

    name : str
    value: str

    raw_text: str


class Block(typ.NamedTuple):

    md_path           : Path
    namespace         : str
    first_line        : int
    elem_index        : int
    info_string       : InfoString
    directives        : list[Directive]
    content           : str
    inner_content     : str
    includable_content: str


class TaskBlockOpts(typ.NamedTuple):
    block: Block
    opts : SessionBlockOptions


ElemIndex = int


class BlockTask(typ.NamedTuple):
    md_path: Path
    command: str
    block  : Block
    opts   : SessionBlockOptions
    # block to which the captured output belongs
    capture_index: ElemIndex
