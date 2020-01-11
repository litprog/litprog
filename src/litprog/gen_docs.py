# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import shutil
import logging
import typing as typ
import pathlib2 as pl

import yaml
import jinja2

from . import parse
from . import md2html
from . import html2pdf
from . import pdf_booklet
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
    Replacement('all'   , "fonts.css"),
    Replacement('screen', "screen.css"),
    Replacement('screen', "check_reloaded.js"),
    Replacement('screen', "pdf_modal.css"),
    Replacement('screen', "navigation.css"),
    Replacement('screen', "navigation.js"),
    # print styles
    Replacement('print'                   , "print.css"),
    Replacement('print_ereader'           , "print_ereader.css"),
    Replacement('print_booklet'           , "print_booklet.css"),
    Replacement('print_booklet_a5'        , "print_booklet_a5.css"),
    Replacement('print_booklet_halfletter', "print_booklet_halfletter.css"),
    Replacement('print_tallcol'           , "print_tallcol.css"),
    Replacement('print_tallcol_a4'        , "print_tallcol_a4.css"),
    Replacement('print_tallcol_letter'    , "print_tallcol_letter.css"),
]


PRINT_FORMATS = [
    'print_ereader',
    'print_a5',
    'print_booklet_a5',
    'print_halfletter',
    'print_booklet_halfletter',
    # 'print_tallcol_a4',
    # 'print_tallcol_letter',
]


STATIC_DIR = pl.Path(__file__).parent / "static"
FONTS_DIR  = STATIC_DIR.parent.parent.parent / "fonts"

STATIC_DEPS = {
    STATIC_DIR / "fonts.css",
    STATIC_DIR / "katex.css",
    STATIC_DIR / "codehilite.css",
    STATIC_DIR / "general_v2.css",
    STATIC_DIR / "screen_v2.css",
    STATIC_DIR / "slideout.js",
    STATIC_DIR / "app.js",
    STATIC_DIR / "print.css",
    STATIC_DIR / "print_a5.css",
    STATIC_DIR / "print_ereader.css",
    STATIC_DIR / "print_halfletter.css",
}

STATIC_DEPS.update(FONTS_DIR.glob("*.woff2"))
STATIC_DEPS.update(FONTS_DIR.glob("*.woff" ))
STATIC_DEPS.update(FONTS_DIR.glob("*.ttf"  ))


def read_static(fname: str) -> str:
    fpath = STATIC_DIR / fname
    with fpath.open(mode="r", encoding="utf-8") as fobj:
        return fobj.read()


DEBUG_NAVIGATION_OUTLINE = """
<div class="toc">
<ul>
    <li><a href="">1. Headline</a></li>
    <li>
        <a href="">2. Headline</a>
        <ul>
            <li><a href="">
            2.1 Subsection with a longer title than can fit on
            just one line by itself
            1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6</a></li>
            <li><a href="">2.2 Subsection</a></li>
            <li><a href="">2.3 Subsection</a></li>
            <li><a href="">2.4 Subsection</a></li>
        </ul>
    </li>
    <li>
        <a href="">3. Headline</a>
        <ul>
            <li><a href="">3.1 Subsection</a></li>
            <li><a href="">3.2 Subsection</a></li>
            <li><a href="">3.3 Subsection</a></li>
            <li><a href="">3.4 Subsection</a></li>
        </ul>
    </li>
    <li>
        <a href="">4. Headline</a>
        <ul>
            <li><a href="">4.1 Subsection</a></li>
            <li><a href="">4.2 Subsection</a></li>
            <li><a href="">4.3 Subsection</a></li>
            <li><a href="">4.4 Subsection</a></li>
            <li><a href="">4.5 Subsection</a></li>
            <li><a href="">4.6 Subsection</a></li>
        </ul>
    </li>
    <li>
        <a href="">5. Headline</a>
        <ul>
            <li><a href="">5.1 Subsection</a></li>
            <li><a href="">5.2 Subsection</a></li>
            <li><a href="">5.3 Subsection</a></li>
            <li><a href="">5.4 Subsection</a></li>
            <li><a href="">5.5 Subsection</a></li>
            <li><a href="">5.6 Subsection</a></li>
        </ul>
    </li>
    <li>
        <a href="">6. Headline</a>
        <ul>
            <li><a href="">6.1 Subsection</a></li>
            <li><a href="">6.2 Subsection</a></li>
            <li><a href="">6.3 Subsection</a></li>
            <li><a href="">6.4 Subsection</a></li>
            <li><a href="">6.5 Subsection</a></li>
            <li><a href="">6.6 Subsection</a></li>
        </ul>
    </li>
    <li>
        <a href="">7. Headline</a>
        <ul>
            <li><a href="">7.1 Subsection</a></li>
            <li><a href="">7.2 Subsection</a></li>
            <li><a href="">7.3 Subsection</a></li>
            <li><a href="">7.4 Subsection</a></li>
            <li><a href="">7.5 Subsection</a></li>
            <li><a href="">7.6 Subsection</a></li>
        </ul>
    </li>
    <li>
        <a href="">8. Headline</a>
        <ul>
            <li><a href="">8.1 Subsection</a></li>
            <li><a href="">8.2 Subsection</a></li>
            <li><a href="">8.3 Subsection</a></li>
            <li><a href="">8.4 Subsection</a></li>
            <li><a href="">8.5 Subsection</a></li>
            <li><a href="">8.6 Subsection</a></li>
        </ul>
    </li>
    <li>
        <a href="">4. Headline</a>
        <ul>
            <li><a href="">4.1 Subsection</a></li>
            <li><a href="">4.2 Subsection</a></li>
            <li><a href="">4.3 Subsection</a></li>
            <li><a href="">4.4 Subsection</a></li>
            <li><a href="">4.5 Subsection</a></li>
            <li><a href="">4.6 Subsection</a></li>
        </ul>
    </li>
    <li>
        <a href="">4. Headline</a>
        <ul>
            <li><a href="">4.1 Subsection</a></li>
            <li><a href="">4.2 Subsection</a></li>
            <li><a href="">4.3 Subsection</a></li>
            <li><a href="">4.4 Subsection</a></li>
            <li><a href="">4.5 Subsection</a></li>
            <li><a href="">4.6 Subsection</a></li>
        </ul>
    </li>
</ul>
</div>
"""


Metadata = typ.Dict[str, str]


def wrap_content_html(
    content: HTMLText, target: str, meta: Metadata, toc: typ.Optional[HTMLText]
) -> HTMLText:
    assert target == 'screen' or target.startswith('print_')
    meta['target'] = target

    fmt = {
        'page_size'        : target.split("_")[-1],
        'is_print_target'  : target.startswith('print_'),
        'is_web_target'    : not target.startswith('print_'),
        'is_booklet_target': "_booklet" in target,
    }

    nav = {'outline_html': toc}

    ctx = {'meta': meta, 'fmt': fmt, 'nav': nav, 'content': content}

    tmpl   = jinja2.Template(read_static("template_v2.html"))
    result = tmpl.render(**ctx)

    # styles  = ""
    # scripts = ""

    # for repl in REPLACEMENTS:
    #     search    = "{{" + repl.filename + "}}"
    #     if repl.target == 'all' or target.startswith(repl.target):
    #         repl_text = read_static(repl.filename)

    #         if search in result:
    #             result = result.replace(search, repl_text)
    #         elif repl.filename.endswith(".css"):
    #             styles += repl_text
    #         elif repl.filename.endswith(".js"):
    #             scripts += repl_text
    #         else:
    #             err_msg = f"Invalid replacement: {repl.filename}"
    #             raise Exception(err_msg)
    #     elif search in result:
    #         # remove placeholder
    #         result = result.replace(search, "")

    # result = result.replace("{{styles}}" , styles)
    # result = result.replace("{{scripts}}", scripts)

    return result


def parse_front_matter(md_text: MarkdownText) -> typ.Tuple[Metadata, MarkdownText]:
    meta = {'lang': "en-US", 'title': "-"}
    if md_text.lstrip().startswith("---"):
        _, front_matter, md_text = md_text.split("---", 2)
        meta = yaml.safe_load(front_matter)
    return meta, md_text


def gen_html(ctx: parse.Context, html_dir: pl.Path) -> None:
    log.info(f"Writing html to '{html_dir}'")
    if not html_dir.exists():
        html_dir.mkdir(parents=True)

    md_file: parse.MarkdownFile
    meta = {}

    for md_file in ctx.files:
        html_fname = md_file.md_path.stem + ".html"
        html_fpath = html_dir / html_fname
        log.info(f"converting '{md_file.md_path}' -> '{html_fpath}'")

        md_text: MarkdownText = str(md_file)
        new_meta, md_text = parse_front_matter(md_text)
        meta.update(new_meta)

        html_res: md2html.HTMLResult = md2html.md2html(md_text)
        content_html = html_postproc.postproc4screen(html_res)
        wrapped_html = wrap_content_html(content_html, 'screen', meta, html_res.toc)
        with html_fpath.open(mode="w") as fobj:
            fobj.write(wrapped_html)

    # copy/update static dependencies
    # TODO: copy only ttf for print target
    #       copy only woff for screen target
    out_static_dir = html_dir / "static"
    out_static_dir.mkdir(parents=True, exist_ok=True)
    for in_fpath in STATIC_DEPS:
        in_fname     = in_fpath.name
        out_fpath    = out_static_dir / in_fname
        is_out_older = (
            not out_fpath.exists() or out_fpath.stat().st_mtime <= in_fpath.stat().st_mtime
        )
        if is_out_older:
            # log.info(f"copy {in_fpath} -> {out_fpath}")
            shutil.copy(str(in_fpath), str(out_fpath))


def gen_pdf(
    ctx     : parse.Context,
    html_dir: pl.Path,
    pdf_dir : pl.Path,
    formats : typ.Sequence[str] = PRINT_FORMATS,
) -> None:
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True)

    meta = {}

    all_md_texts = []
    for md_file in ctx.files:
        md_text: MarkdownText = str(md_file)
        new_meta, md_text = parse_front_matter(md_text)
        meta.update(new_meta)
        all_md_texts.append(md_text)

    full_md_text = "\n\n".join(all_md_texts)

    html_res: md2html.HTMLResult = md2html.md2html(full_md_text)
    onepage_formats = {fmt.replace("_booklet", "") for fmt in formats}

    for fmt in onepage_formats:
        print_html   = html_postproc.postproc4print(html_res, fmt)
        wrapped_html = wrap_content_html(print_html, fmt, meta, html_res.toc)
        html_fpath   = pdf_dir / (fmt + ".html")
        pdf_fpath    = pdf_dir / (fmt + ".pdf")
        with html_fpath.open(mode="w") as fobj:
            fobj.write(wrapped_html)

        log.info(f"converting '{html_fpath}' -> '{pdf_fpath}'")
        html2pdf.html2pdf(wrapped_html, pdf_fpath, html_dir)

    booklet_formats = set(formats) - onepage_formats

    for fmt in booklet_formats:
        onepage_fmt       = fmt.replace("_booklet", "")
        onepage_pdf_fpath = pdf_dir / (onepage_fmt + ".pdf")
        booklet_pdf_fpath = pdf_dir / (fmt         + ".pdf")
        log.info(f"creating booklet '{onepage_pdf_fpath}' -> '{booklet_pdf_fpath}'")
        pdf_booklet.create(in_path=onepage_pdf_fpath, out_path=booklet_pdf_fpath)
