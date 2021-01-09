# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import time
import shutil
import typing as typ
import logging
import pathlib as pl

import yaml
import jinja2

from . import __version__
from . import parse
from . import md2html
from . import html2pdf
from . import pdf_booklet
from . import html_postproc
from . import vcs

logger = logging.getLogger("litprog.gen_docs")

MarkdownText = str

HTMLText = str


class Replacement(typ.NamedTuple):

    target  : str
    filename: str


PRINT_FORMATS = (
    'print_ereader',
    'print_a5',
    'print_booklet_a4',
    # 'print_halfletter',
    # 'print_booklet_letter',
    # 'print_tallcol_a4',
    # 'print_tallcol_letter',
    # 'print_twocol_a4',
    # 'print_twocol_letter',
)

MULTIPAGE_FORMATS = {
    'print_booklet_a4'    : "print_a5",
    'print_booklet_letter': "print_halfletter",
    'print_twocol_a4'     : "print_tallcol_a4",
    'print_twocol_letter' : "print_tallcol_letter",
}

PART_PAGE_SIZES = {
    'screen'              : "screen",
    'print_ereader'       : "ereader",
    'print_a5'            : "a5",
    'print_a4'            : "a4",
    'print_booklet_a4'    : "a5",
    'print_letter'        : "letter",
    'print_halfletter'    : "halfletter",
    'print_booklet_letter': "halfletter",
    'print_tallcol_a4'    : "tallcol_a4",
    'print_tallcol_letter': "tallcol_letter",
    'print_twocol_a4'     : "tallcol_a4",
    'print_twocol_letter' : "tallcol_letter",
}


STATIC_DIR = pl.Path(__file__).parent / "static"
FONTS_DIR  = STATIC_DIR.parent.parent.parent / "fonts"

STATIC_DEPS = {
    STATIC_DIR / "fonts.css",
    STATIC_DIR / "katex.css",
    STATIC_DIR / "codehilite.css",
    STATIC_DIR / "general_v2.css",
    STATIC_DIR / "screen_v2.css",
    STATIC_DIR / "slideout.js",
    STATIC_DIR / "popper.js",
    STATIC_DIR / "popper.min.js",
    STATIC_DIR / "app.js",
    STATIC_DIR / "print.css",
    STATIC_DIR / "print_a4.css",
    STATIC_DIR / "print_a5.css",
    STATIC_DIR / "print_letter.css",
    STATIC_DIR / "print_ereader.css",
    STATIC_DIR / "print_halfletter.css",
    STATIC_DIR / "print_tallcol.css",
    STATIC_DIR / "print_tallcol_a4.css",
    STATIC_DIR / "print_tallcol_letter.css",
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


class FileItem(typ.NamedTuple):
    md_path : pl.Path
    meta    : Metadata
    toc     : md2html.TocHTML
    html_res: md2html.HTMLResult

    block_linenos: typ.List[typ.Tuple[int, int]]


def wrap_content_html(
    content: HTMLText, target: str, meta: Metadata, nav_html: typ.Optional[HTMLText] = None
) -> HTMLText:
    assert target == 'screen' or target.startswith('print_')
    meta['target'] = target

    fmt = {
        'page_size'        : PART_PAGE_SIZES[target],
        'is_print_target'  : target.startswith('print_'),
        'is_web_target'    : not target.startswith('print_'),
        'is_tallcol_target': "_tallcol_" in target,
    }

    nav = {}

    if nav_html:
        nav['outline_html'] = html_postproc.postproc_nav_html(nav_html)

    # nav['outline_html'] = DEBUG_NAVIGATION_OUTLINE

    ctx = {'meta': meta, 'fmt': fmt, 'nav': nav, 'content': content}

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STATIC_DIR.absolute()))
        # loader=jinja2.PackageLoader('litprog'),
    )
    tmpl   = env.get_template("template_v2.html")
    result = tmpl.render(**ctx)
    return result


def parse_front_matter(md_text: MarkdownText) -> typ.Tuple[Metadata, MarkdownText]:
    meta = {'lang': "en-US", 'title': "-"}
    if md_text.lstrip().startswith("---"):
        _, front_matter, md_text = md_text.split("---", 2)
        meta = yaml.safe_load(front_matter)
    return meta, md_text


def _init_meta() -> typ.Dict[str, str]:
    build_tt = time.localtime()
    meta = {
        # TODO (mb 2021-01-08): parse from front matter
        'copyright_url'  : "https://gitlab.com/mbarkhau/litprog/-/blob/master/LICENSE",
        'copyright'      : "2019-2021 Manuel Barkhau - MIT License",
        'repo_url'       : "https://gitlab.com/mbarkhau/litprog/-/blob/",
        'litprog_version': __version__,
        'build_timestamp': time.strftime("%a %Y-%m-%d %H:%M:%S %Z", build_tt),
        'vcs_dirty_files': set(),
        'vcs_revision'   : "",
        'vcs_revision_short': "",
    }
    vcs_api = vcs.get_vcs_api()
    if vcs_api:
        head_rev = vcs_api.head_rev()
        meta.update({
            'vcs_name'          : vcs_api.name,
            'vcs_revision'      : head_rev,
            'vcs_revision_short': head_rev[:10],
            'vcs_dirty_files'   : set(vcs_api.status()),
        })
    return meta


def gen_html(ctx: parse.Context, html_dir: pl.Path) -> None:
    logger.info(f"Writing html to '{html_dir}'")
    if not html_dir.exists():
        html_dir.mkdir(parents=True)

    md_file: parse.MarkdownFile

    # NOTE (mb): In order to do linking between documents, we need
    #   the full toc. This is why there are two passes.

    cur_meta = _init_meta()

    file_items: typ.List[FileItem] = []

    static_paths: typ.Set[typ.Tuple[str, str]] = set()

    for md_file in ctx.files:
        logger.info(f"processing '{md_file.md_path}'")
        md_text: MarkdownText = str(md_file)
        new_meta, md_text = parse_front_matter(md_text)
        cur_meta = cur_meta.copy()
        cur_meta.update(new_meta)
        md_filepath = str(md_file.md_path)
        cur_meta['md_filepath']   = md_filepath
        cur_meta['is_file_dirty'] = md_filepath in cur_meta['vcs_dirty_files']

        for img_tag in md_file.image_tags:
            src_path = md_file.md_path.parent / img_tag.url
            if src_path.exists():
                tgt_path = html_dir / img_tag.url
                static_paths.add((src_path, tgt_path))

        html_res: md2html.HTMLResult = md2html.md2html(md_text)

        if html_res.raw_html:
            block_linenos = list(md_file.iter_block_linenos())
            file_item = FileItem(
                md_file.md_path,
                cur_meta,
                html_res.toc,
                html_res,
                block_linenos,
            )
            file_items.append(file_item)

    for md_path, meta, toc, html_res, block_linenos in file_items:
        html_fname = md_path.stem + ".html"
        html_fpath = html_dir / html_fname
        logger.info(f"writing '{md_path}' -> '{html_fpath}'")
        content_html = html_postproc.postproc4screen(html_res, block_linenos)
        wrapped_html = wrap_content_html(content_html, 'screen', meta, toc)
        with html_fpath.open(mode="w") as fobj:
            fobj.write(wrapped_html)

    # copy/update static dependencies
    for src_path, tgt_path in sorted(static_paths):
        # logger.info(f"copy {src_path} -> {tgt_path}")
        shutil.copy(str(src_path), str(tgt_path))

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
            # logger.info(f"copy {in_fpath} -> {out_fpath}")
            shutil.copy(str(in_fpath), str(out_fpath))


def gen_pdf(
    ctx     : parse.Context,
    html_dir: pl.Path,
    pdf_dir : pl.Path,
    formats : typ.Sequence[str] = PRINT_FORMATS,
) -> None:
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True)

    # TODO (mb 2021-01-06): This should probably
    #   be more unified with gen_html.
    cur_meta = _init_meta()

    all_md_texts = []
    block_linenos = []
    for md_file in ctx.files:
        md_text: MarkdownText = str(md_file)
        new_meta, md_text = parse_front_matter(md_text)
        cur_meta.update(new_meta)
        all_md_texts.append(md_text)
        block_linenos.extend(md_file.iter_block_linenos())

    full_md_text = "\n\n".join(all_md_texts)

    html_res: md2html.HTMLResult = md2html.md2html(full_md_text)
    multipage_formats = {fmt for fmt in formats if fmt in MULTIPAGE_FORMATS}
    onepage_formats   = set(formats) - set(multipage_formats)
    for fmt in multipage_formats:
        part_page_fmt = MULTIPAGE_FORMATS[fmt]
        onepage_formats.add(part_page_fmt)

    for fmt in onepage_formats:
        print_html   = html_postproc.postproc4print(html_res, fmt, block_linenos)
        wrapped_html = wrap_content_html(print_html, fmt, cur_meta)
        html_fpath   = pdf_dir / (fmt + ".html")
        pdf_fpath    = pdf_dir / (fmt + ".pdf")
        with html_fpath.open(mode="w") as fobj:
            fobj.write(wrapped_html)

        logger.info(f"converting '{html_fpath}' -> '{pdf_fpath}'")
        html2pdf.html2pdf(wrapped_html, pdf_fpath, html_dir)

    for fmt in multipage_formats:
        part_page_fmt       = MULTIPAGE_FORMATS[fmt]
        part_page_pdf_fpath = pdf_dir / (part_page_fmt + ".pdf")
        booklet_pdf_fpath   = pdf_dir / (fmt           + ".pdf")
        logger.info(f"creating booklet '{part_page_pdf_fpath}' -> '{booklet_pdf_fpath}'")
        pdf_booklet.create(in_path=part_page_pdf_fpath, out_path=booklet_pdf_fpath)
