# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import typing as typ
import logging

import markdown as md

log = logging.getLogger(__name__)

MarkdownText = str

HTMLText = str

# https://python-markdown.github.io/extensions/toc/
TocHTML   = str
TocTokens = typ.List[typ.Dict[str, typ.Any]]


class HTMLResult(typ.NamedTuple):

    raw_html  : HTMLText
    toc_html  : TocHTML
    toc_tokens: TocTokens
    filename  : str


def init_md_ctx() -> md.Markdown:
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

    extension_configs: typ.Dict[str, typ.Any] = {
        'markdown_svgbob': {
            'tag_type'      : "img_base64_svg",
            'bg_color'      : "transparent",
            'fg_color'      : "black",
            'min_char_width': 70,
        },
        'markdown_katex'                : {'no_inline_svg': True, 'insert_fonts_css': False},
        "markdown.extensions.codehilite": {
            # NOTE (mb 2020-06-05): The default guess_lexer=True can detect the
            #   wrong language for certain blocks and colour everything as an
            #   error. The explicit language of the blocks appears to override
            #   this regardless, so this hopefully only affects blocks without
            #   a language in their info string.
            'guess_lang': False,
        },
    }
    return md.Markdown(extensions=extensions, extension_configs=extension_configs)


def md2html(md_text: MarkdownText, filename: str = "<markdown_blob>") -> HTMLResult:
    md_ctx        = init_md_ctx()
    raw_html_text = md_ctx.convert(md_text)
    return HTMLResult(raw_html_text, md_ctx.toc, md_ctx.toc_tokens, filename)  # type: ignore
