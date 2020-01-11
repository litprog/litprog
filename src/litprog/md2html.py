# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import logging
import typing as typ

import markdown as md


log = logging.getLogger(__name__)

MarkdownText = str

HTMLText = str

# https://python-markdown.github.io/extensions/toc/
TocHTML   = str
TocTokens = typ.List[typ.Dict[str, typ.Any]]


class HTMLResult(typ.NamedTuple):

    raw_html  : HTMLText
    toc       : TocHTML
    toc_tokens: TocTokens


def md2html(md_text: MarkdownText) -> HTMLResult:
    # https://python-markdown.github.io/extensions/
    extensions = [
        "markdown.extensions.toc",
        "markdown.extensions.extra",
        "markdown.extensions.abbr",
        "markdown.extensions.attr_list",
        "markdown.extensions.def_list",
        "markdown.extensions.fenced_code",
        "markdown.extensions.footnotes",
        "markdown.extensions.tables",
        "markdown.extensions.admonition",
        "markdown.extensions.codehilite",
        "markdown.extensions.meta",
        "markdown.extensions.sane_lists",
        "markdown.extensions.wikilinks",
        "markdown_aafigure",
        "markdown_blockdiag",
        "markdown_svgbob",
        "markdown_katex",
        #####
        # "markdown.extensions.legacy_attr",
        # "markdown.extensions.legacy_em",
        # "markdown.extensions.nl2br",
        # "markdown.extensions.smarty",
    ]

    md_ctx = md.Markdown(
        extensions=extensions,
        extension_configs={
            'markdown_svgbob': {
                'tag_type'      : "img_base64_svg",
                'bg_color'      : "transparent",
                'fg_color'      : "black",
                'min_char_width': 70,
            },
            'markdown_katex': {'no_inline_svg': True, 'insert_fonts_css': False},
        },
    )
    raw_html_text = md_ctx.convert(md_text)
    return HTMLResult(raw_html_text, md_ctx.toc, md_ctx.toc_tokens)
