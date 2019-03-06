#!/usr/bin/env python
# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import os
import re
import io
import sys
import json
import yaml
import toml
import uuid
import collections
import typing as typ
import pathlib2 as pl

from . import session

# To enable pretty tracebacks:
#   echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc
if os.environ.get('ENABLE_BACKTRACE') == '1':
    import backtrace

    backtrace.hook(align=True, strip_path=True, enable_on_envvar_only=True)


import logging

log = logging.getLogger("litprog.cli")


def _configure_logging(verbosity: int = 0) -> None:
    if verbosity >= 2:
        log_format = "%(asctime)s.%(msecs)03d %(levelname)-7s " + "%(name)-15s - %(message)s"
        log_level  = logging.DEBUG
    elif verbosity == 2:
        log_format = "%(levelname)-7s - %(message)s"
        log_level  = logging.INFO
    else:
        log_format = "%(levelname)-7s - %(message)s"
        log_level  = logging.WARNING

    logging.basicConfig(level=log_level, format=log_format, datefmt="%Y-%m-%dT%H:%M:%S")


import click

click.disable_unicode_literals_warning = True


@click.group()
@click.version_option(version="v201901.0001-alpha")
@click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")
def cli(verbose: int = 0) -> None:
    """litprog cli."""
    _configure_logging(verbose)


@cli.command()
def version() -> None:
    """Show version number."""
    print("litprog version: v201901.0001-alpha")


VALID_OPTION_KEYS = {'lptype', 'lpid'}


class Line(typ.NamedTuple):

    line_no: int
    val    : str


Lines = typ.List[Line]


class RawFencedBlock(typ.NamedTuple):

    file_path  : pl.Path
    info_string: str
    lines      : Lines


LitprogID = str

Lang = str

MaybeLang = typ.Optional[Lang]

BlockOptions = typ.Dict[str, typ.Any]


class FencedBlock(typ.NamedTuple):

    file_path  : pl.Path
    info_string: str
    lines      : Lines
    lpid       : LitprogID
    language   : MaybeLang
    options    : BlockOptions
    content    : str


Block = typ.Union[RawFencedBlock, FencedBlock]


class ParseError(Exception):
    def __init__(self, msg: str, block: Block) -> None:
        file_path  = block.file_path
        first_line = block.lines[0]
        line_no    = first_line.line_no

        self.msg       = msg
        self.file_path = file_path
        self.line_no   = line_no

        msg += f" on line {line_no} of {file_path}"
        super(ParseError, self).__init__(msg)


class Context:

    blocks_by_id : typ.Dict[LitprogID, typ.List[FencedBlock]]
    options_by_id: typ.Dict[LitprogID, BlockOptions]

    def __init__(self) -> None:
        self.blocks_by_id  = collections.defaultdict(list)
        self.options_by_id = {}


def _iter_fenced_block_lines(
    fence_str: str, input_lines: typ.Iterable[typ.Tuple[int, str]]
) -> typ.Iterable[Line]:
    for i, line_val in input_lines:
        line_no     = i + 1
        maybe_fence = line_val.rstrip()

        is_closing_fence = maybe_fence.startswith(fence_str)
        if is_closing_fence:
            last_line_val = line_val.rstrip()[: -len(fence_str)]
            if last_line_val:
                yield Line(line_no, last_line_val)
            break
        else:
            yield Line(line_no, line_val)


def _iter_raw_fenced_blocks(input_path: pl.Path) -> typ.Iterable[RawFencedBlock]:
    with input_path.open(mode="r", encoding="utf-8") as fh:
        input_lines = enumerate(fh)
        for i, line_val in input_lines:
            is_fence = line_val.startswith("~~~") or line_val.startswith("```")
            if not is_fence:
                continue

            fence_str   = line_val[:3]
            info_string = line_val[3:].strip()
            block_lines = list(_iter_fenced_block_lines(fence_str, input_lines))
            yield RawFencedBlock(input_path, info_string, block_lines)


import re

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
    maybe_lang: MaybeLang, raw_lines: Lines
) -> typ.Tuple[BlockOptions, Lines]:
    # NOTE (2019-03-02 mb): In the case of
    #   options, each one is on it's own line and
    #   the first line to not declare an option
    #   terminates the options preamble of a
    #   fenced block.

    options: BlockOptions = {}
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


# Old parser for options from info_string. In order
# make the info string still be valid for various editors
# which only understand the language declaration, the
# options string is moved into the block
#
# def _parse_options_str(options_str: str) -> BlockOptions:
#     options     : BlockOptions = {}
#     option_key  : str
#     option_value: typ.Optional[str]
#
#     if options_str.startswith("{"):
#         options_str = options_str[1:]
#     if options_str.endswith("}"):
#         options_str = options_str[:-1]
#
#     for option_kv in options_str.split():
#         if "=" in option_kv:
#             option_key, option_value = option_kv.split("=", 1)
#         else:
#             option_key   = option_kv
#             option_value = "1"
#         options[option_key] = option_value
#
#     return options


def _parse_language(info_string: str) -> MaybeLang:
    info_string = info_string.strip()

    if info_string:
        return info_string.split(" ", 1)[0]
    else:
        return None


def _parse_maybe_options(lang: Lang, raw_lines: Lines) -> typ.Optional[BlockOptions]:
    if len(raw_lines) == 0:
        return None

    first_line = raw_lines[0].val

    maybe_options: typ.Any = None
    if 'lptype' in first_line and lang in ('toml', 'yaml', 'json'):
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

    if isinstance(maybe_options, dict) and 'lptype' in maybe_options:
        # TODO (2019-03-02 mb): Probably we should validate the parsed options
        #   and raise an error if the options are invalid.
        return maybe_options
    else:
        return None


def _parse_code_block(raw_fenced_block: RawFencedBlock) -> FencedBlock:
    maybe_lang = _parse_language(raw_fenced_block.info_string)
    raw_lines  = raw_fenced_block.lines

    if maybe_lang:
        maybe_options = _parse_maybe_options(maybe_lang, raw_lines)
    else:
        maybe_options = None

    filtered_lines: Lines

    if maybe_options is None:
        options, filtered_lines = _parse_comment_options(maybe_lang, raw_lines)
    else:
        options        = typ.cast(BlockOptions, maybe_options)
        filtered_lines = raw_lines

    if isinstance(maybe_options, dict) and 'lptype' in maybe_options:
        options        = maybe_options
        filtered_lines = raw_lines
    else:
        options, filtered_lines = _parse_comment_options(maybe_lang, raw_lines)

    filtered_content = "".join(line.val for line in filtered_lines)

    lpid: LitprogID = options['lpid'] if 'lpid' in options else str(uuid.uuid4())

    return FencedBlock(
        raw_fenced_block.file_path,
        raw_fenced_block.info_string,
        filtered_lines,
        lpid,
        maybe_lang,
        options,
        filtered_content,
    )


def _add_to_context(context: Context, code_block: FencedBlock) -> None:
    context.blocks_by_id[code_block.lpid].append(code_block)

    if code_block.lpid in context.options_by_id:
        prev_options = context.options_by_id[code_block.lpid]
        for key, val in code_block.options.items():
            if key in prev_options and prev_options[key] != val:
                err_msg = f"Redeclaration of option {key} for lpid={lpid}"
                raise ParseError(err_msg, code_block)
            else:
                prev_options[key] = val
    else:
        context.options_by_id[code_block.lpid] = code_block.options


class OutputLine(typ.NamedTuple):

    microtime: float
    line     : str


class ProcResult(typ.NamedTuple):
    exit_code: int
    stdout   : typ.List[OutputLine]
    stderr   : typ.List[OutputLine]


def _build(context: Context) -> None:
    captured_outputs: typ.Dict[LitprogID, str       ] = {}
    captured_procs  : typ.Dict[LitprogID, ProcResult] = {}

    # for lpid, blocks in context.blocks_by_id.items():
    #     if lpid in context.options_by_id:
    #         # requires further processing
    #         continue
    #     else:
    #         # TODO: this should not be done here. In order to preserve
    #         #   information about which block came from where, this should
    #         #   be done later.
    #         captured_outputs[lpid] = "".join(block.content for block in blocks)

    for lpid, blocks in context.blocks_by_id.items():
        options = context.options_by_id[lpid]
        if 'lptype' not in options:
            context.options_by_id[lpid]['lptype'] = 'raw_block'

    all_ids = set(context.options_by_id.keys()) | set(context.blocks_by_id.keys())

    while len(captured_outputs) < len(all_ids):

        assert len(context.options_by_id) == len(all_ids)

        prev_len_completed = len(captured_outputs)
        for lpid, options in context.options_by_id.items():
            if lpid in captured_outputs:
                continue

            litprog_type: str = options['lptype']
            if litprog_type == 'out_file':
                missing_inputs = set(options['inputs']) - set(captured_outputs.keys())
                if any(missing_inputs):
                    continue

                output_parts = []
                # prelude_tmpl    = options.get('block_prelude')
                # postscript_tmpl = options.get('block_postscript')

                for input_lpid in options['inputs']:
                    # if input_lpid in context.blocks_by_id:
                    #     block      = context.blocks_by_id[input_lpid][0]
                    #     input_path = str(block.file_path)
                    # else:
                    #     input_path = "<generated>"

                    # if prelude_tmpl:
                    #     prelude = prelude_tmpl.format(path=input_path, lpid=input_lpid)
                    #     output_parts.append(prelude)

                    output_parts.append(captured_outputs[input_lpid])

                    # if postscript_tmpl:
                    #     postscript = postscript_tmpl.format(path=input_path, lpid=input_lpid)
                    #     output_parts.append(postscript)

                captured_outputs[lpid] = "".join(output_parts)
                log.info(f"completed {litprog_type:>9} block {lpid}")
            elif litprog_type == 'raw_block':
                captured_outputs[lpid] = "".join(
                    "".join(l.val for l in block.lines) for block in context.blocks_by_id[lpid]
                )
                log.info(f"completed {litprog_type:>9} block {lpid}")
            elif litprog_type == 'session':
                isession = session.InteractiveSession(options.get('command', "bash"))

                for block in context.blocks_by_id[lpid]:
                    for line in block.ines:
                        session.send(line.val + "\n")

                returncode = isession.exit()

                out_lines = sorted([(ts, "out", line) for ts, line in isession.stdout_lines])
                err_lines = sorted([(ts, "err", line) for ts, line in isession.stderr_lines])
                all_lines = sorted(out_lines + err_lines)
                output = "\n".join(line for ts, out, line in all_lines)

                if returncode != options.get('expected_exit_code', 0):
                    sys.stderr.write(output)
                    err_msg = f"Error processing block {lpid}"
                    raise Exception(err_msg)

                captured_outputs[lpid] = output
                log.info(f"completed {litprog_type:>9} block {lpid}")
            else:
                log.error(f"Unhandled litprog type={litprog_type} for lpid={lpid}")
                return

        if prev_len_completed == len(captured_outputs):
            log.error(f"Build failed: No progress on/unresolved requirements.")
            return

    for lpid, output in captured_outputs.items():
        options = context.options_by_id[lpid]
        print(f"captured {lpid:<40} {options}")
        filepath = options.get('filepath')
        if filepath is None:
            continue

        encoding = options.get('encoding', "utf-8")
        file     = pl.Path(filepath)
        print("write to", file)
        with file.open(mode="w", encoding=encoding) as fh:
            fh.write(output)

        if options.get('is_executable'):
            file.chmod(file.stat().st_mode | 0o100)

        log.info(f"Created {file}")


InputPaths = typ.Sequence[str]

MarkdownPaths = typ.Iterable[pl.Path]


def _iter_markdown_filepaths(input_paths: InputPaths) -> MarkdownPaths:
    for in_path_str in input_paths:
        in_path = pl.Path(in_path_str)
        if in_path.is_dir():
            for in_filepath in in_path.glob("**/*.md"):
                yield in_filepath
        else:
            yield in_path


def _prepare_context(input_paths: InputPaths) -> Context:
    input_filepaths = sorted(_iter_markdown_filepaths(input_paths))

    context = Context()

    for path in input_filepaths:
        log.info(f"parsing {path}")
        for rfb in _iter_raw_fenced_blocks(path):
            code_block = _parse_code_block(rfb)
            _add_to_context(context, code_block)
    return context


@cli.command()
@click.argument('input_paths', nargs=-1, type=click.Path(exists=True))
@click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")
def build(input_paths: InputPaths, verbose: int = 0) -> None:
    _configure_logging(verbose)
    context = _prepare_context(input_paths)
    _build(context)
