
# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

###################################
#    This is a generated file.    #
# This file should not be edited. #
#  Changes will be overwritten!   #
###################################
import os
import io
import re
import sys
import math
import time
import enum
import os.path
import collections
import typing as typ
import pathlib2 as pl
import operator as op
import datetime as dt
import itertools as it
import functools as ft

InputPaths = typ.Sequence[str]
FilePaths = typ.Iterable[pl.Path]

ExitCode = int
import logging

log = logging.getLogger(__name__)
import json
import toml
import yaml
import uuid

import litprog.types as lptyp

VALID_OPTION_KEYS = {'lptype', 'lpid'}


class ParseError(Exception):
    def __init__(self, msg: str, block: lptyp.Block) -> None:
        file_path  = block.file_path
        first_line = block.lines[0]
        line_no    = first_line.line_no

        self.msg       = msg
        self.file_path = file_path
        self.line_no   = line_no

        msg += f" on line {line_no} of {file_path}"
        super(ParseError, self).__init__(msg)


def parse_context(md_paths: FilePaths) -> lptyp.ParseContext:
    ctx = lptyp.ParseContext()
    ctx.md_paths.extend(md_paths)

    for path in ctx.md_paths:
        log.debug(f"parsing {path}")
        for rfb in _iter_raw_fenced_blocks(path):
            code_block = _parse_code_block(rfb)
            _add_to_context(ctx, code_block)

    return ctx


def _iter_raw_fenced_blocks(
    input_path: pl.Path
) -> typ.Iterable[lptyp.RawFencedBlock]:
    with input_path.open(mode="r", encoding="utf-8") as fh:
        input_lines = enumerate(fh)
        for i, line_val in input_lines:
            is_fence = (
                line_val.startswith("~~~")
                or line_val.startswith("```")
            )
            if not is_fence:
                continue

            fence_str   = line_val[:3]
            info_string = line_val[3:].strip()
            block_lines = list(_iter_fenced_block_lines(fence_str, input_lines))
            yield lptyp.RawFencedBlock(input_path, info_string, block_lines)


def _iter_fenced_block_lines(
    fence_str: str, input_lines: typ.Iterable[typ.Tuple[int, str]]
) -> typ.Iterable[lptyp.Line]:
    for i, line_val in input_lines:
        line_no     = i + 1
        maybe_fence = line_val.rstrip()

        is_closing_fence = maybe_fence.startswith(fence_str)
        if is_closing_fence:
            last_line_val = line_val.rstrip()[: -len(fence_str)]
            if last_line_val:
                yield lptyp.Line(line_no, last_line_val)
            break
        else:
            yield lptyp.Line(line_no, line_val)

LANGUAGE_COMMENT_PATTERNS = {
    "c++"          : (r"^//" , r"$"),
    'actionscript' : (r"^//" , r"$"),
    'actionscript3': (r"^//" , r"$"),
    'bash'         : (r"^#"  , r"$"),
    'c'            : (r"^//" , r"$"),
    'd'            : (r"^//" , r"$"),
    'elixir'       : (r"^#"  , r"$"),
    'erlang'       : (r"^%"  , r"$"),
    'go'           : (r"^//" , r"$"),
    'java'         : (r"^//" , r"$"),
    'javascript'   : (r"^//" , r"$"),
    'json'         : (r"^//" , r"$"),
    'swift'        : (r"^//" , r"$"),
    'r'            : (r"^//" , r"$"),
    'php'          : (r"^//" , r"$"),
    'svg'          : (r"<!--", r"-->"),
    'html'         : (r"<!--", r"-->"),
    'css'          : (r"^/\*", r"\*/"),
    'csharp'       : (r"^//" , r"$"),
    'fsharp'       : (r"^//" , r"$"),
    'kotlin'       : (r"^//" , r"$"),
    'make'         : (r"^#"  , r"$"),
    'nim'          : (r"^#"  , r"$"),
    'perl'         : (r"^#"  , r"$"),
    'php'          : (r"^#"  , r"$"),
    'yaml'         : (r"^#"  , r"$"),
    'prolog'       : (r"^%"  , r"$"),
    'scheme'       : (r"^;"  , r"$"),
    'clojure'      : (r"^;"  , r"$"),
    'lisp'         : (r"^;"  , r"$"),
    'coffee-script': (r"^#"  , r"$"),
    'python'       : (r"^#"  , r"$"),
    'ruby'         : (r"^#"  , r"$"),
    'rust'         : (r"^//" , r"$"),
    'scala'        : (r"^//" , r"$"),
    'sh'           : (r"^#"  , r"$"),
    'shell'        : (r"^#"  , r"$"),
    'sql'          : (r"^--" , r"$"),
    'typescript'   : (r"^//" , r"$"),
}


LANGUAGE_COMMENT_TEMPLATES = {
    "c++"          : "// {}",
    'actionscript' : "// {}",
    'actionscript3': "// {}",
    'bash'         : "# {}",
    'c'            : "// {}",
    'd'            : "// {}",
    'elixir'       : "# {}",
    'erlang'       : "% {}",
    'go'           : "// {}",
    'java'         : "// {}",
    'javascript'   : "// {}",
    'json'         : "// {}",
    'swift'        : "// {}",
    'r'            : "// {}",
    'php'          : "// {}",
    'svg'          : "<!-- {} -->",
    'html'         : "<!-- {} -->",
    'css'          : "/* {} */",
    'csharp'       : "// {}",
    'fsharp'       : "// {}",
    'kotlin'       : "// {}",
    'make'         : "# {}",
    'nim'          : "# {}",
    'perl'         : "# {}",
    'php'          : "# {}",
    'yaml'         : "# {}",
    'prolog'       : "% {}",
    'scheme'       : "; {}",
    'clojure'      : "; {}",
    'lisp'         : "; {}",
    'coffee-script': "# {}",
    'python'       : "# {}",
    'ruby'         : "# {}",
    'rust'         : "// {}",
    'scala'        : "// {}",
    'sh'           : "# {}",
    'shell'        : "# {}",
    'sql'          : "-- {}",
    'typescript'   : "// {}",
}


def _parse_comment_options(
    maybe_lang: lptyp.MaybeLang, raw_lines: lptyp.Lines
) -> typ.Tuple[lptyp.BlockOptions, lptyp.Lines]:
    # NOTE (2019-03-02 mb): In the case of
    #   options, each one is on it's own line and
    #   the first line to not declare an option
    #   terminates the options preamble of a
    #   fenced block.

    options: lptyp.BlockOptions = {}
    if not (maybe_lang and maybe_lang in LANGUAGE_COMMENT_PATTERNS):
        return options, raw_lines

    assert maybe_lang is not None
    language = maybe_lang

    key_val_pattern = r"(?P<key>lp\w+)\s*=\s*(?P<val>[^\s,]+?)?\s*$"
    key_val_re      = re.compile(key_val_pattern)

    comment_start_pattern, comment_end_pattern = LANGUAGE_COMMENT_PATTERNS[language]
    options_pattern = comment_start_pattern + r"\s*(.+?)\s*" + comment_end_pattern
    options_re      = re.compile(options_pattern)

    last_options_line = 0

    for line in raw_lines:
        match = options_re.match(line.val)
        if match is None:
            break

        maybe_option_str = match.group(1)
        kv_match         = key_val_re.match(maybe_option_str)
        if kv_match is None:
            break

        kv  = kv_match.groupdict()
        key = kv['key']
        val = kv['val']

        if key not in VALID_OPTION_KEYS:
            break

        options[key] = val
        last_options_line += 1

    filtered_lines = raw_lines[last_options_line:]

    return options, filtered_lines


def _parse_language(info_string: str) -> lptyp.MaybeLang:
    info_string = info_string.strip()

    if info_string:
        return info_string.split(" ", 1)[0]
    else:
        return None


def _parse_maybe_options(
    lang: lptyp.Lang, raw_lines: lptyp.Lines
) -> typ.Optional[lptyp.BlockOptions]:
    if len(raw_lines) == 0:
        return None

    first_line = raw_lines[0].val

    maybe_options: typ.Any = None
    if lang in ('toml', 'yaml', 'json'):
        maybe_options_data = "".join(line.val for line in raw_lines)

        if lang == 'toml':
            maybe_options = toml.loads(maybe_options_data)
        elif lang == 'yaml':
            maybe_options = yaml.safe_load(io.StringIO(maybe_options_data))
        elif lang == 'json':
            maybe_options = json.loads(maybe_options_data)
        else:
            return None
    else:
        return None

    if not isinstance(maybe_options, dict):
        return None

    has_filepath = 'filepath' in maybe_options

    if has_filepath and 'lptype' not in maybe_options:
        maybe_options['lptype'] = 'out_file'

    if has_filepath and 'lpid' not in maybe_options:
        maybe_options['lpid'] = maybe_options['filepath']

    if 'lptype' in maybe_options:
        # TODO (2019-03-02 mb): Probably we should validate the parsed options
        #   and raise an error if the options are invalid.
        return maybe_options
    else:
        return None


def _parse_code_block(raw_fenced_block: lptyp.RawFencedBlock) -> lptyp.FencedBlock:
    maybe_lang = _parse_language(raw_fenced_block.info_string)
    raw_lines  = raw_fenced_block.lines

    if maybe_lang:
        maybe_options = _parse_maybe_options(maybe_lang, raw_lines)
    else:
        maybe_options = None

    filtered_lines: lptyp.Lines

    if maybe_options is None:
        options, filtered_lines = _parse_comment_options(maybe_lang, raw_lines)
    else:
        options        = typ.cast(lptyp.BlockOptions, maybe_options)
        filtered_lines = []

    filtered_content = "".join(line.val for line in filtered_lines)

    lpid: LitprogID
    if 'lpid' in options:
        lpid = options['lpid']
    elif 'filepath' in options:
        lpid = options['filepath']
    else:
        lpid = str(uuid.uuid4())

    if 'lptype' not in options:
        options['lptype'] = 'raw_block'

    return lptyp.FencedBlock(
        raw_fenced_block.file_path,
        raw_fenced_block.info_string,
        filtered_lines,
        lpid,
        maybe_lang,
        options,
        filtered_content,
    )


def _add_to_context(ctx: lptyp.ParseContext, code_block: lptyp.FencedBlock) -> None:
    is_duplicate_lpid = (
        code_block.lpid in ctx.blocks
        and code_block.options['lptype'] != 'raw_block'
    )
    if is_duplicate_lpid:
        err_msg = f"Duplicated definition of {code_block.lpid}"
        raise ParseError(err_msg)

    ctx.blocks[code_block.lpid].append(code_block)

    if code_block.lpid in ctx.options:
        prev_options = ctx.options[code_block.lpid]
        for key, val in code_block.options.items():
            is_redeclared_key = (
                key in prev_options and prev_options[key] != val
            )

            is_block_continuation = (
                is_redeclared_key 
                and key == 'lptype' 
                and val == 'raw_block'
            )
            if is_block_continuation:
                valid_continuation_options = {
                    'lpid': code_block.lpid,
                    'lptype': 'raw_block'
                }
                assert code_block.options == valid_continuation_options
                continue
            elif is_redeclared_key:
                err_msg = f"Redeclaration of option {key} for lpid={code_block.lpid}"
                raise ParseError(err_msg, code_block)
            else:
                prev_options[key] = val
    else:
        ctx.options[code_block.lpid] = code_block.options
