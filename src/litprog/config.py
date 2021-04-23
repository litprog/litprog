# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import os
import pathlib as pl

HOME = os.path.expanduser("~")

FALLBACK_CONFIG_HOME = os.path.join(HOME, ".config")
FALLBACK_CACHE_HOME  = os.path.join(HOME, ".cache")
FALLBACK_DATA_HOME   = os.path.join(HOME, ".local", "share")

CONFIG_HOME = pl.Path(os.getenv('XDG_CONFIG_HOME', FALLBACK_CONFIG_HOME))
CACHE_HOME  = pl.Path(os.getenv('XDG_CACHE_HOME' , FALLBACK_CACHE_HOME ))
DATA_HOME   = pl.Path(os.getenv('XDG_DATA_HOME'  , FALLBACK_DATA_HOME  ))

CONFIG_DIR  = CONFIG_HOME / "litprog"
CACHE_DIR   = CACHE_HOME  / "litprog"
ENVDIR_BASE = DATA_HOME   / "litprog"
