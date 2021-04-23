# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import sys
import logging
import pathlib as pl


def html2pdf(html_text: str, out_path: pl.Path, html_dir: pl.Path) -> None:
    # pylint: disable=import-outside-toplevel ; lazy import since we don't always need it
    #   the lazy import makes for a better cli experience
    import weasyprint

    logging.getLogger('weasyprint').setLevel(logging.ERROR)

    wp_ctx = weasyprint.HTML(string=html_text, base_url=str(html_dir))
    with out_path.open(mode="wb") as fobj:
        wp_ctx.write_pdf(fobj)


def main(in_path: pl.Path, out_path: pl.Path) -> None:
    with in_path.open(mode="rt") as in_fobj:
        html2pdf(in_fobj.read(), out_path, in_path.parent)


if __name__ == '__main__':
    main(pl.Path(sys.argv[1]), pl.Path(sys.argv[2]))
