# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import logging
import typing as typ
import pathlib2 as pl

from . import parse
from . import md2html
from . import html2pdf
from . import join_pdf
from . import html_postproc

log = logging.getLogger(__name__)

MarkdownText = str

HTMLText = str


class Replacement(typ.NamedTuple):

    target  : str
    filename: str


REPLACEMENTS = [
    Replacement('all'   , "codehilite.css"),
    Replacement('all'   , "general.css"),
    Replacement('all'   , "katex.css"),
    Replacement('screen', "fonts.css"),
    Replacement('screen', "screen.css"),
    Replacement('screen', "check_reloaded.js"),
    Replacement('screen', "pdf_modal.css"),
    Replacement('screen', "navigation.css"),
    Replacement('screen', "navigation.js"),
    # print styles
    Replacement('print'                   , "print.css"),
    Replacement('print_a6'                , "print_a6.css"),
    Replacement('print_booklet'           , "print_booklet.css"),
    Replacement('print_booklet_a5'        , "print_booklet_a5.css"),
    Replacement('print_booklet_halfletter', "print_booklet_halfletter.css"),
    Replacement('print_tallcol'           , "print_tallcol.css"),
    Replacement('print_tallcol_a4'        , "print_tallcol_a4.css"),
    Replacement('print_tallcol_letter'    , "print_tallcol_letter.css"),
]


PRINT_TARGETS = [
    # 'print_a6',
    'print_booklet_a5',
    # 'print_booklet_halfletter',
    # 'print_tallcol_a4',
    # 'print_tallcol_letter',
]


STATIC_DIR = pl.Path(__file__).parent / "static"


def read_static(fname: str) -> str:
    fpath = STATIC_DIR / fname
    with fpath.open(mode="r", encoding="utf-8") as fobj:
        return fobj.read()


def wrap_content_html(content: HTMLText, target: str) -> HTMLText:
    assert target == 'screen' or target.startswith('print_')

    styles  = ""
    scripts = ""

    result = read_static("template.html")
    for repl in REPLACEMENTS:
        if repl.target == 'all' or target.startswith(repl.target):
            search    = "{{" + repl.filename + "}}"
            repl_text = read_static(repl.filename)

            if search in result:
                result = result.replace(search, repl_text)
            elif repl.filename.endswith(".css"):
                styles += repl_text
            elif repl.filename.endswith(".js"):
                scripts += repl_text
            else:
                err_msg = f"Invalid replacement: {repl.filename}"
                raise Exception(err_msg)

    result = result.replace("{{styles}}" , styles)
    result = result.replace("{{scripts}}", scripts)

    return result.replace("{{content}}", content)


def gen_html(ctx: parse.Context, html_dir: pl.Path) -> None:
    log.info(f"Writing html to '{html_dir}'")
    if not html_dir.exists():
        html_dir.mkdir(parents=True)

    mdfile: parse.MarkdownFile

    for md_file in ctx.files:
        html_fname = md_file.md_path.stem + ".html"
        html_fpath = html_dir / html_fname
        log.info(f"converting '{md_file.md_path}' -> '{html_fpath}'")

        md_text     : MarkdownText = str(md_file)
        content_html: HTMLText     = md2html.md2html(md_text)
        content_html = html_postproc.postproc4all(content_html)
        content_html = html_postproc.postproc4screen(content_html)
        wrapped_html = wrap_content_html(content_html, 'screen')
        with html_fpath.open(mode="w") as fobj:
            fobj.write(wrapped_html)


def gen_pdf(ctx: parse.Context, html_dir: pl.Path, pdf_dir: pl.Path) -> None:
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True)

    all_md_texts = []
    for md_file in ctx.files:
        md_text: MarkdownText = str(md_file)
        all_md_texts.append(md_text)

    full_md_text = "\n\n".join(all_md_texts)
    content_html: HTMLText = md2html.md2html(md_text)
    content_html = html_postproc.postproc4all(content_html)
    content_html = html_postproc.postproc4print(content_html)

    for target in PRINT_TARGETS:
        wrapped_html = wrap_content_html(content_html, target)
        html_fpath   = html_dir / (target + ".html")
        pdf_fpath    = html_dir / (target + ".pdf")
        with html_fpath.open(mode="w") as fobj:
            fobj.write(wrapped_html)

        log.info(f"converting '{html_fpath}' -> '{pdf_fpath}'")
        html2pdf.html2pdf(wrapped_html, pdf_fpath)
