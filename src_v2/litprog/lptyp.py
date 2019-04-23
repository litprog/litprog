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

Lang = str

MaybeLang = typ.Optional[Lang]

LitProgId  = str
LitProgIds = typ.List[LitProgId]


class Line(typ.NamedTuple):

    line_no: int
    val    : str


Lines = typ.List[Line]

BlockOptions = typ.Dict[str, typ.Any]


class RawElement(typ.NamedTuple):

    file_path: pl.Path
    lines    : Lines


class RawFencedBlock(typ.NamedTuple):

    file_path  : pl.Path
    lines      : Lines
    info_string: str


RawMarkdown = typ.Union[RawElement, RawFencedBlock]


class FencedBlockData(typ.NamedTuple):

    file_path  : pl.Path
    lines      : Lines
    info_string: str
    lpid       : LitProgId
    language   : MaybeLang
    options    : BlockOptions
    content    : str


class FencedBlockMeta(typ.NamedTuple):

    file_path  : pl.Path
    lines      : Lines
    info_string: str
    lpid       : LitProgId
    language   : MaybeLang
    options    : BlockOptions


FencedBlock = typ.Union[FencedBlockData, FencedBlockMeta]
Block       = typ.Union[RawFencedBlock , FencedBlockData, FencedBlockMeta]


MardownElement = typ.Union[RawElement, RawFencedBlock]

OptionsById = typ.Dict[LitProgId, BlockOptions]


class ParseContext:

    md_paths  : FilePaths
    elements  : typ.List[MardownElement]
    options   : OptionsById
    prev_block: typ.Optional[FencedBlockData]

    def __init__(self) -> None:
        self.md_paths   = []
        self.elements   = []
        self.options    = {}
        self.prev_block = None


class CapturedLine(typ.NamedTuple):
    ts  : float
    line: str


class ProcResult(typ.NamedTuple):
    exit_code: int
    stdout   : typ.List[CapturedLine]
    stderr   : typ.List[CapturedLine]


OutputsById     = typ.Dict[LitProgId, str]
ProgResultsById = typ.Dict[LitProgId, ProcResult]


class BuildContext:

    md_paths        : FilePaths
    elements        : typ.List[MardownElement]
    options         : OptionsById
    captured_outputs: OutputsById
    captured_procs  : ProgResultsById

    def __init__(self, pctx: ParseContext) -> None:
        self.md_paths         = pctx.md_paths
        self.elements         = pctx.elements
        self.options          = pctx.options
        self.captured_outputs = {}
        self.captured_procs   = {}
