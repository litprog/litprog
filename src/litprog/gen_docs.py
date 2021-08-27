# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import re
import time
import shutil
import typing as typ
import hashlib
import logging
import pathlib as pl
import datetime as dt

import jinja2

from . import vcs
from . import parse
from . import md2html
from . import html2pdf
from . import __version__
from . import common_types as ct
from . import package_data
from . import vcs_timeline
from . import html_postproc
from .simple_cache import SimpleCache  # type: ignore

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

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head> <meta http-equiv="refresh" content="0; URL='{}'" /> </head>
<body></body>
</html>
"""


Metadata = dict[str, typ.Any]

METADATA_DEFAULTS = {'lang': "en-US", 'title': "-"}


class FileItem(typ.NamedTuple):
    filename_html   : str
    meta            : Metadata
    html_res        : md2html.HTMLResult
    block_line_infos: list[ct.BlockLineInfo]


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


def _deep_update(src: dict, dest: dict) -> None:
    for key, src_v in src.items():
        if isinstance(src_v, dict):
            dest_v = dest.get(key, {})
            _deep_update(src=src_v, dest=dest_v)
            dest[key] = dest_v
        else:
            dest[key] = src_v


def _init_meta(chapter_metas: list[Metadata]) -> Metadata:
    build_tt = time.localtime()
    meta: Metadata = {
        'litprog_version'   : __version__,
        'build_timestamp'   : time.strftime("%a %Y-%m-%d %H:%M:%S %Z", build_tt),
        'vcs_name'          : "",
        'vcs_revision'      : "",
        'vcs_revision_short': "",
        'vcs_dirty_files'   : set(),
        'pdf_formats'       : PRINT_FORMATS,
        'configuration'     : {
            'concurrent': True,
        },
    }

    for file_meta in chapter_metas:
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


StaticPaths = set[tuple[str, str]]


HEADLINE_RE = re.compile(r'<h([1-9]+) id="([^"]+)">')


def _iter_file_nav_htmls(file_items: list[FileItem]) -> typ.Iterable[str]:
    top_level_toc = []
    for file_item in file_items:
        for toc in file_item.html_res.toc_tokens:
            if toc['level'] <= 2:
                file_nav_id = file_item.filename_html + "#" + toc['id']
                top_level_toc.append((file_nav_id, toc['id'], toc['name']))

    for file_item in file_items:
        content_html = file_item.html_res.raw_html
        headline     = HEADLINE_RE.search(content_html)
        if headline is None:
            continue

        level      = int(headline.group(1))
        cur_nav_id = headline.group(2)

        if level <= 2:
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


def _write_screen_html(file_items: list[FileItem], html_dir: pl.Path) -> None:
    inital_url = ""

    nav_htmls = list(_iter_file_nav_htmls(file_items))

    with SimpleCache() as _cache:
        _postproc4screen   = _cache.decorate()(html_postproc.postproc4screen)
        _wrap_content_html = _cache.decorate()(wrap_content_html)

        for nav_html, (html_fname, meta, html_res, block_line_infos) in zip(nav_htmls, file_items):
            html_fpath = html_dir / html_fname
            logger.info(f"writing '{html_fpath}'")

            htmls        = _postproc4screen(html_res, block_line_infos, nav_html)
            wrapped_html = _wrap_content_html(htmls.content, 'screen', meta, htmls)

            with html_fpath.open(mode="w") as fobj:
                fobj.write(wrapped_html)

            if inital_url:
                inital_url = min(inital_url, html_fname)
            else:
                inital_url = html_fname

    if inital_url:
        with (html_dir / "index.html").open(mode="w") as fobj:
            fobj.write(INDEX_HTML.format(inital_url))


def _write_static_files(captured_static_paths: StaticPaths, html_dir: pl.Path) -> None:
    # copy/update static dependencies references in markdown files
    for src_path_str, tgt_path_str in sorted(captured_static_paths):
        # logger.info(f"copy {src_path_str} -> {tgt_path_str}")
        shutil.copy(src_path_str, tgt_path_str)

    out_static_dir = html_dir / "static"
    out_static_dir.mkdir(parents=True, exist_ok=True)

    for _pkg, pkg_fname, pkg_path_ctx in package_data.iter_paths():
        out_fpath = out_static_dir / pkg_fname
        with pkg_path_ctx as in_path:
            is_ouptut_newer = out_fpath.exists() and out_fpath.stat().st_mtime >= in_path.stat().st_mtime
            if not is_ouptut_newer:
                logger.debug(f"copy {in_path} -> {out_fpath}")
                with in_path.open(mode="rb") as in_fobj:
                    with out_fpath.open(mode="wb") as out_fobj:
                        shutil.copyfileobj(in_fobj, out_fobj)


GroupedChapters = dict[tuple[str, str], list[parse.Chapter]]


def _grouped_md_files(ctx: parse.Context) -> GroupedChapters:
    res: GroupedChapters = {}
    for chapter in ctx.chapters:
        key = (chapter.chapnum, chapter.namespace)
        if key in res:
            res[key].append(chapter)
        else:
            res[key] = [chapter]
    return res


def _make_html_chunk_cache_key(html_dir: pl.Path, meta: Metadata, chapters: list[parse.Chapter]) -> str:
    digester = hashlib.sha1()
    digester.update(str(html_dir).encode("utf-8"))

    for key in sorted(meta):
        if key == 'build_timestamp':
            continue
        digester.update(key.encode("utf-8"))
        val = meta[key]
        if isinstance(val, set):
            digester.update(str(sorted(val)).encode("utf-8"))
        elif isinstance(val, dict):
            digester.update(str(sorted(val.items())).encode("utf-8"))
        else:
            digester.update(str(val).encode("utf-8"))

    for chapter in chapters:
        for md_path in chapter.md_paths:
            digester.update(str(md_path).encode("utf-8"))
            mtime = md_path.stat().st_mtime
            digester.update(str(mtime).encode("utf-8"))

    return digester.hexdigest()


def _gen_html_chunk(
    html_dir: pl.Path,
    meta    : Metadata,
    chapters: list[parse.Chapter],
) -> tuple[Metadata, md2html.HTMLResult, list[ct.BlockLineInfo], StaticPaths]:
    meta             = meta.copy()
    html_res         = md2html.HTMLResult("", "", [], "")
    block_line_infos = []

    static_paths: StaticPaths = set()
    for chapter in chapters:
        meta.update(chapter.parse_front_matter_meta())

        md_path = chapter.md_paths[0]
        logger.info(f"processing '{md_path}'")

        md_text: MarkdownText = "\n\n".join(
            [chapter.md_content(_md_path, front_matter=False) for _md_path in chapter.md_paths]
        )

        md_filepath = str(md_path)
        meta['md_filepath'  ] = md_filepath
        meta['is_file_dirty'] = md_filepath in meta['vcs_dirty_files']

        if meta.get('stats_by_file') and md_filepath in meta['stats_by_file']:
            base_name, _ = re.subn(r"[^\w]", "_", str(md_path.name))
            svg_name = base_name + "_authors_timeline.svg"
            svg_path = html_dir / svg_name
            stats    = meta['stats_by_file'][md_filepath]
            vcs_timeline.write_stats_svg(stats, svg_path)
            meta['authors_timeline_svg'] = svg_name

        for img_tag in chapter.image_tags():
            src_path = md_path.parent / img_tag.url
            if src_path.exists():
                tgt_path = html_dir / img_tag.url
                static_paths.add((str(src_path), str(tgt_path)))

        partial_html_res: md2html.HTMLResult = md2html.md2html(md_text, md_filepath)

        if partial_html_res.raw_html:
            if html_res.toc_tokens:
                # TODO (mb 2021-07-25): fix toc merge with bad headers
                html_res.toc_tokens[-1]['children'].append(partial_html_res.toc_tokens)
                logger.error("error merging toc_tokens")
            else:
                toc_tokens = partial_html_res.toc_tokens

            html_res = md2html.HTMLResult(
                html_res.raw_html + partial_html_res.raw_html,
                html_res.toc_html + partial_html_res.toc_html,
                toc_tokens,
                md_filepath,
            )
            block_line_infos.extend(list(chapter.iter_block_linenos()))

    return (meta, html_res, block_line_infos, static_paths)


def gen_html(ctx: parse.Context, html_dir: pl.Path) -> None:
    logger.info(f"Writing html to '{html_dir}'")
    if not html_dir.exists():
        html_dir.mkdir(parents=True)

    chapter_metas = [chapter.parse_front_matter_meta() for chapter in sorted(ctx.chapters)]
    base_meta     = _init_meta(chapter_metas)

    captured_static_paths: StaticPaths = set()
    file_items           : list[FileItem] = []

    with SimpleCache() as cache:
        __gen_html_chunk = cache.decorate(make_key=_make_html_chunk_cache_key)(_gen_html_chunk)
        for (chapnum, namespace), chapters in _grouped_md_files(ctx).items():
            html_chunk_res = __gen_html_chunk(html_dir, base_meta, chapters)

            file_meta, html_res, block_line_infos, static_paths = html_chunk_res
            captured_static_paths.update(static_paths)

            if html_res.raw_html:
                filename_html = chapnum + "_" + namespace + ".html"
                file_item     = FileItem(
                    filename_html,
                    file_meta,
                    html_res,
                    block_line_infos,
                )
                file_items.append(file_item)

    _write_screen_html(file_items, html_dir)
    _write_static_files(captured_static_paths, html_dir)


def gen_pdf(
    ctx     : parse.Context,
    html_dir: pl.Path,
    pdf_dir : pl.Path,
) -> None:
    # pylint: disable=import-outside-toplevel ; improves import time
    from . import pdf_booklet

    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True)

    # TODO (mb 2021-01-21): cover page with title and author(s)
    #   timeline for whole project

    chapter_metas = [chapter.parse_front_matter_meta() for chapter in ctx.chapters]
    cur_meta      = _init_meta(chapter_metas)

    default_basename = dt.date.today().strftime("%Y%m%d")
    pdf_basename     = cur_meta.get('pdf_basename', default_basename).rstrip("_") + "_"

    pdf_formats = [(fmt if fmt.startswith("print_") else "print_" + fmt) for fmt in cur_meta['pdf_formats']]

    all_md_texts    : list[MarkdownText    ] = []
    block_line_infos: list[ct.BlockLineInfo] = []
    for file_meta, chapter in zip(chapter_metas, ctx.chapters):
        cur_meta.update(file_meta)
        for md_path in chapter.md_paths:
            md_text = chapter.md_content(md_path, front_matter=False)
            all_md_texts.append(md_text)
        block_line_infos.extend(chapter.iter_block_linenos())

    full_md_text = "\n\n".join(all_md_texts)

    html_res: md2html.HTMLResult = md2html.md2html(full_md_text, "<concat.md>")
    multipage_formats = {fmt for fmt in pdf_formats if fmt in MULTIPAGE_FORMATS}
    onepage_formats   = set(pdf_formats) - set(multipage_formats)
    for fmt in multipage_formats:
        part_page_fmt = MULTIPAGE_FORMATS[fmt]
        onepage_formats.add(part_page_fmt)

    for fmt in onepage_formats:
        print_html   = html_postproc.postproc4print(html_res, fmt, block_line_infos)
        wrapped_html = wrap_content_html(print_html, fmt, cur_meta)
        html_fpath   = pdf_dir / (pdf_basename + fmt[6:] + ".html")
        pdf_fpath    = pdf_dir / (pdf_basename + fmt[6:] + ".pdf")
        with html_fpath.open(mode="w") as fobj:
            fobj.write(wrapped_html)

        logger.info(f"converting '{html_fpath}' -> '{pdf_fpath}'")
        html2pdf.html2pdf(wrapped_html, pdf_fpath, html_dir)

    for fmt in multipage_formats:
        part_page_fmt       = MULTIPAGE_FORMATS[fmt]
        part_page_pdf_fpath = pdf_dir / (pdf_basename + part_page_fmt[6:] + ".pdf")
        booklet_pdf_fpath   = pdf_dir / (pdf_basename + fmt[6:] + ".pdf")
        logger.info(f"creating booklet '{part_page_pdf_fpath}' -> '{booklet_pdf_fpath}'")
        pdf_booklet.create(in_path=part_page_pdf_fpath, out_path=booklet_pdf_fpath)
