# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import logging
import pathlib2 as pl

import weasyprint


log = logging.getLogger(__name__)

logging.getLogger('weasyprint').setLevel(logging.ERROR)


def html2pdf(html_text: str, out_path: pl.Path) -> None:
    wp_ctx = weasyprint.HTML(string=html_text)
    with out_path.open(mode="wb") as fobj:
        wp_ctx.write_pdf(fobj)
