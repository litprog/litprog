# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

# pylint: disable=protected-access

import pathlib as pl

import litprog.cli


def test_fs_scanning():
    lit_paths = list(litprog.cli._iter_markdown_filepaths(["lit_v3/"]))

    assert len(lit_paths) > 0
    assert all(isinstance(p, pl.Path) for p in lit_paths)
    assert all(p.suffix == ".md" for p in lit_paths)
