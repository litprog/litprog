# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import logging
import pathlib2 as pl

import weasyprint as wp


log = logging.getLogger(__name__)


def html2pdf(html_text: str, out_path: pl.Path) -> None:
    wp_ctx = wp.HTML(string=html_text)
    with out_path.open(mode="wb") as fh:
        wp_ctx.write_pdf(fh)
