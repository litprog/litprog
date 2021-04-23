# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import re
import time
import shutil
import typing as typ
import logging
import pathlib as pl

import jinja2

try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources  # type: ignore

from . import vcs
from . import parse
from . import md2html
from . import html2pdf
from . import __version__
from . import pdf_booklet
from . import vcs_timeline
from . import html_postproc

logger = logging.getLogger("litprog.gen_docs")

MarkdownText = str

HTMLText = str


class Replacement(typ.NamedTuple):

    target  : str
    filename: str


PRINT_FORMATS = (
    'print_ereader',
    'print_a4',
    'print_a5',
    'print_booklet_a4',
    'print_halfletter',
    'print_booklet_letter',
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


INDEX_HTML = """
<!DOCTYPE html>
<html>
<head> <meta http-equiv="refresh" content="0; URL='{}'" /> </head>
<body></body>
</html>
"""


Metadata = typ.Dict[str, typ.Any]

METADATA_DEFAULTS = {'lang': "en-US", 'title': "-"}


class FileItem(typ.NamedTuple):
    md_path : pl.Path
    meta    : Metadata
    html_res: md2html.HTMLResult

    block_linenos: typ.List[typ.Tuple[int, int]]


FOOTNOTES_RE = re.compile(r'\<h\d\s+id="references"\s*\>')


def wrap_content_html(
    content_html: HTMLText,
    target      : str,
    meta        : Metadata,
    htmls       : typ.Optional[html_postproc.HTMLTexts] = None,
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
    if htmls:
        if htmls.chapters:
            nav['chapters_html'] = htmls.chapters
        if htmls.sections:
            nav['sections_html'] = htmls.sections
        if htmls.chapter_prev_href:
            nav['chapter_prev_href'] = htmls.chapter_prev_href
            nav['chapter_prev_text'] = htmls.chapter_prev_text
        if htmls.chapter_next_href:
            nav['chapter_next_href'] = htmls.chapter_next_href
            nav['chapter_next_text'] = htmls.chapter_next_text

    ctx = {'meta': meta, 'fmt': fmt, 'nav': nav, 'content': content_html}

    env    = jinja2.Environment(loader=jinja2.PackageLoader('litprog', package_path="static"))
    tmpl   = env.get_template("template_v2.html")
    result = tmpl.render(**ctx)
    return result


def _deep_update(src: typ.Dict, dest: typ.Dict) -> None:
    for key, src_v in src.items():
        if isinstance(src_v, dict):
            dest_v = dest.get(key, {})
            _deep_update(src=src_v, dest=dest_v)
            dest[key] = dest_v
        else:
            dest[key] = src_v


def _init_meta(file_metas: typ.List[Metadata]) -> Metadata:
    build_tt = time.localtime()
    meta: Metadata = {
        'litprog_version'   : __version__,
        'build_timestamp'   : time.strftime("%a %Y-%m-%d %H:%M:%S %Z", build_tt),
        'vcs_name'          : "",
        'vcs_revision'      : "",
        'vcs_revision_short': "",
        'vcs_dirty_files'   : set(),
        'configuration'     : {
            'concurrent': True,
        },
    }

    for file_meta in file_metas:
        if file_meta:
            _deep_update(src=file_meta, dest=meta)

    author_aliases = {}
    for raw_alias in meta.get('vcs_author_alias', []):
        alias_re = re.compile(raw_alias['alias_regex'])
        author_aliases[alias_re] = (raw_alias['real_name'], raw_alias['real_email'])

    vcs_api = vcs.get_vcs_api()
    if vcs_api:
        head_rev      = vcs_api.head_rev()
        commits       = vcs_api.commits()
        stats_by_file = vcs_timeline.stats_by_file(commits, author_aliases)
        overall_stats = vcs_timeline.calc_overall_stats(commits, author_aliases)
        meta.update(
            {
                'overall_stats'     : overall_stats,
                'stats_by_file'     : stats_by_file,
                'vcs_name'          : vcs_api.name,
                'vcs_revision'      : head_rev,
                'vcs_revision_short': head_rev[:10],
                'vcs_dirty_files'   : set(vcs_api.status()),
            }
        )

    return meta


StaticPaths = typ.Set[typ.Tuple[str, str]]


HEADLINE_RE = re.compile('<h1 id="([^"]+)">')


def _iter_file_nav_htmls(file_items: typ.List[FileItem]) -> typ.Iterable[str]:
    top_level_toc = []
    for file_item in file_items:
        for toc in file_item.html_res.toc_tokens:
            if toc['level'] == 1:
                filename_md   = str(file_item.md_path.name)
                filename_html = filename_md[: -len(file_item.md_path.suffix)] + ".html"
                file_nav_id   = filename_html + "#" + toc['id']
                top_level_toc.append((file_nav_id, toc['id'], toc['name']))

    for file_item in file_items:
        content_html = file_item.html_res.raw_html
        headline     = HEADLINE_RE.search(content_html)
        if headline is None:
            continue

        cur_nav_id = headline.group(1)

        nav_html_parts = ['<div class="toc"><ul>']
        for file_nav_id, nav_id, nav_name in top_level_toc:
            if nav_id == cur_nav_id:
                subnav_html = file_item.html_res.toc_html
                l_index     = subnav_html.find("<ul>")
                r_index     = subnav_html.rfind("</ul>")
                subnav_html = subnav_html[l_index + 4 : r_index]
                html_part   = f"<li><ul>{subnav_html}</ul></li>"
                html_part   = html_part.replace("#" + nav_id, file_nav_id, 1)
                nav_html_parts.append(html_part)
            else:
                nav_html_parts.append(f'<li><a href="{file_nav_id}">{nav_name}</a></li>')
        nav_html_parts.append("</ul></div>")

        nav_html = "\n".join(nav_html_parts)

        has_footnotes = bool(FOOTNOTES_RE.search(content_html))
        nav_html      = html_postproc.postproc_nav_html(nav_html, has_footnotes)

        yield nav_html


def _write_screen_html(file_items: typ.List[FileItem], html_dir: pl.Path) -> None:
    inital_url = ""

    nav_htmls = list(_iter_file_nav_htmls(file_items))
    for nav_html, (md_path, meta, html_res, block_linenos) in zip(nav_htmls, file_items):
        html_fname = md_path.stem + ".html"
        html_fpath = html_dir / html_fname
        logger.info(f"writing '{md_path}' -> '{html_fpath}'")
        htmls        = html_postproc.postproc4screen(html_res, block_linenos, nav_html)
        wrapped_html = wrap_content_html(htmls.content, 'screen', meta, htmls)
        with html_fpath.open(mode="w") as fobj:
            fobj.write(wrapped_html)

        if inital_url:
            inital_url = min(inital_url, html_fname)
        else:
            inital_url = html_fname

    if inital_url:
        with (html_dir / "index.html").open(mode="w") as fobj:
            fobj.write(INDEX_HTML.format(inital_url))


Package = typ.NewType('Package', str)


def _iter_package_paths() -> typ.Iterator[tuple[Package, str]]:
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
                yield package, pkg_fname


def _write_static_files(captured_static_paths: StaticPaths, html_dir: pl.Path) -> None:
    # copy/update static dependencies references in markdown files
    for src_path_str, tgt_path_str in sorted(captured_static_paths):
        # logger.info(f"copy {src_path_str} -> {tgt_path_str}")
        shutil.copy(src_path_str, tgt_path_str)

    out_static_dir = html_dir / "static"
    out_static_dir.mkdir(parents=True, exist_ok=True)

    for package, pkg_fname in _iter_package_paths():
        out_fpath = out_static_dir / pkg_fname
        with importlib_resources.path(package, pkg_fname) as in_path:
            if out_fpath.exists() and in_path.stat().st_mtime < out_fpath.stat().st_mtime:
                continue
            logger.debug(f"copy {in_path} -> {out_fpath}")
            with in_path.open(mode="rb") as in_fobj:
                with out_fpath.open(mode="wb") as out_fobj:
                    shutil.copyfileobj(in_fobj, out_fobj)


def gen_html(ctx: parse.Context, html_dir: pl.Path) -> None:
    logger.info(f"Writing html to '{html_dir}'")
    if not html_dir.exists():
        html_dir.mkdir(parents=True)

    md_file: parse.MarkdownFile

    file_metas = [md_file.parse_front_matter_meta() for md_file in ctx.files]
    cur_meta   = _init_meta(file_metas)

    captured_static_paths: StaticPaths = set()

    file_items: typ.List[FileItem] = []
    for file_meta, md_file in zip(file_metas, ctx.files):
        logger.info(f"processing '{md_file.md_path}'")
        md_text: MarkdownText = str(md_file)
        cur_meta.update(file_meta)
        md_filepath = str(md_file.md_path)
        cur_meta['md_filepath'  ] = md_filepath
        cur_meta['is_file_dirty'] = md_filepath in cur_meta['vcs_dirty_files']

        if cur_meta.get('stats_by_file') and md_filepath in cur_meta['stats_by_file']:
            base_name, _ = re.subn(r"[^\w]", "_", str(md_file.md_path.name))
            svg_name = base_name + "_authors_timeline.svg"
            svg_path = html_dir / svg_name
            stats    = cur_meta['stats_by_file'][md_filepath]
            vcs_timeline.write_stats_svg(stats, svg_path)
            cur_meta['authors_timeline_svg'] = svg_name

        for img_tag in md_file.image_tags():
            src_path = md_file.md_path.parent / img_tag.url
            if src_path.exists():
                tgt_path = html_dir / img_tag.url
                captured_static_paths.add((str(src_path), str(tgt_path)))

        html_res: md2html.HTMLResult = md2html.md2html(md_text, filename=str(md_file.md_path))

        if html_res.raw_html:
            block_linenos = list(md_file.iter_block_linenos())
            file_item     = FileItem(
                md_file.md_path,
                cur_meta.copy(),
                html_res,
                block_linenos,
            )
            file_items.append(file_item)

    _write_screen_html(file_items, html_dir)
    _write_static_files(captured_static_paths, html_dir)


def gen_pdf(
    ctx     : parse.Context,
    html_dir: pl.Path,
    pdf_dir : pl.Path,
    formats : typ.Sequence[str] = PRINT_FORMATS,
) -> None:
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True)

    # TODO (mb 2021-01-21): cover page with title and author(s)
    #   timeline for whole project

    file_metas = [md_file.parse_front_matter_meta() for md_file in ctx.files]
    cur_meta   = _init_meta(file_metas)

    all_md_texts = []
    block_linenos: typ.List[typ.Tuple[int, int]] = []
    for file_meta, md_file in zip(file_metas, ctx.files):
        md_text: MarkdownText = str(md_file)
        cur_meta.update(file_meta)
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
