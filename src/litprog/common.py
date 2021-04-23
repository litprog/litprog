# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import typing as typ
import pathlib as pl

from . import parse


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

    # TODO (mb 2021-02-26): These ids are not namespaced (yet)
    #   see litprog.build._namespaced_lp_id and litprog.parse.MarkdownFile.block_namespace()
    provides_id         : typ.Optional[str]
    requires_ids        : typ.Set[str]
    timeout             : float
    input_delay         : float
    expected_exit_status: int

    is_stdin_writable: bool
    is_debug         : bool
    keepends         : bool

    fmt: FormatOptions


class TaskBlockOpts(typ.NamedTuple):
    block: parse.Block
    opts : SessionBlockOptions


ElemIndex = int


class BlockTask(typ.NamedTuple):
    md_path: pl.Path
    command: str
    block  : parse.Block
    opts   : SessionBlockOptions
    # block to which the captured output belongs
    capture_index: ElemIndex
