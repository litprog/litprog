# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import typing as typ
import pathlib2 as pl

Paths = typ.Iterable[pl.Path]
import logging

log           = logging.getLogger(__name__)
InputPaths    = typ.Sequence[str]
MarkdownPaths = typ.Iterable[pl.Path]


def iter_markdown_filepaths(input_paths: InputPaths) -> MarkdownPaths:
    for in_path_str in input_paths:
        in_path = pl.Path(in_path_str)
        if in_path.is_dir():
            for in_filepath in in_path.glob("**/*.md"):
                yield in_filepath
        else:
            yield in_path


class Line(typ.NamedTuple):

    line_no: int
    val    : str


Lines = typ.List[Line]


class RawFencedBlock(typ.NamedTuple):

    file_path  : pl.Path
    info_string: str
    lines      : Lines


LitprogID = str

Lang = str

MaybeLang = typ.Optional[Lang]

BlockOptions = typ.Dict[str, typ.Any]


class FencedBlock(typ.NamedTuple):

    file_path  : pl.Path
    info_string: str
    lines      : Lines
    lpid       : LitprogID
    language   : MaybeLang
    options    : BlockOptions
    content    : str


Block = typ.Union[RawFencedBlock, FencedBlock]
