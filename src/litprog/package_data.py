# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import re
import typing as typ

try:
    import importlib.resources as importlib_resources
except ImportError:
    # compat for py36 and lower
    import importlib_resources  # type: ignore


SELECTED_STATIC_DEPS = {
    r"static/fonts_screen\.css",
    r"static/fonts_print\.css",
    r"static/katex\.css",
    r"static/codehilite\.css",
    r"static/general_v2\.css",
    # r"static/screen_v2\.css",
    r"static/screen_v3\.css",
    # r"static/slideout.js",
    r"static/popper.js",
    # r"static/popper.min.js",
    r"static/app.js",
    r"static/print\.css",
    r"static/print_a4\.css",
    r"static/print_a5\.css",
    r"static/print_letter\.css",
    r"static/print_ereader\.css",
    r"static/print_halfletter\.css",
    r"static/print_tallcol\.css",
    r"static/print_tallcol_a4\.css",
    r"static/print_tallcol_letter\.css",
    r"static/.+\.css",
    r"static/.+\.svg",
    r"static/fonts/.+\.woff2",
    r"static/fonts/.+\.woff",
    r"static/fonts/.+\.ttf",
}


Package = typ.NewType('Package', str)


def iter_paths() -> typ.Iterator[tuple[Package, str, typ.ContextManager]]:
    available_filepaths = {
        package: list(importlib_resources.contents(package))
        for package in ["litprog.static", "litprog.static.fonts"]
    }

    for static_fpath in SELECTED_STATIC_DEPS:
        dirpath, fname = static_fpath.rsplit("/", 1)
        package = Package("litprog." + dirpath.replace("/", "."))

        pkg_fname_re = re.compile(fname)
        for pkg_fname in available_filepaths[package]:
            if pkg_fname_re.match(pkg_fname):
                pkg_path_ctx = importlib_resources.path(package, pkg_fname)
                yield package, pkg_fname, pkg_path_ctx
