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
import shlex
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
    if verbosity == 0:
        log_format = "%(levelname)-7s - %(message)s"
        log_level  = logging.WARNING
    else:
        log_format = (
            "%(asctime)s.%(msecs)03d %(levelname)-7s " + "%(name)-15s - %(message)s"
        )
        if verbosity == 1:
            log_level = logging.INFO
        else:
            assert verbosity >= 2
            log_level = logging.DEBUG

    logging.basicConfig(level=log_level, format=log_format, datefmt="%Y-%m-%dT%H:%M:%S")


import click

click.disable_unicode_literals_warning = True


@click.group()
@click.version_option(version="v201901.0001-alpha")
@click.option(
    '-v', '--verbose', count=True, help="Control log level. -vv for debug level."
)
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
    is_duplicate_lpid = (
        code_block.lpid in context.blocks_by_id
        and code_block.options['lptype'] != 'raw_block'
    )
    if is_duplicate_lpid:
        err_msg = f"Duplicated definition of {code_block.lpid}"
        raise ParseError(err_msg)

    context.blocks_by_id[code_block.lpid].append(code_block)

    if code_block.lpid in context.options_by_id:
        prev_options = context.options_by_id[code_block.lpid]
        for key, val in code_block.options.items():
            is_redeclared_key     = key in prev_options and prev_options[key] != val
            is_block_continuation = (
                is_redeclared_key and key == 'lptype' and val == 'raw_block'
            )
            if is_block_continuation:
                valid_continuation_options = {
                    'lpid'  : code_block.lpid,
                    'lptype': 'raw_block',
                }
                assert code_block.options == valid_continuation_options
                continue
            elif is_redeclared_key:
                err_msg = f"Redeclaration of option {key} for lpid={code_block.lpid}"
                raise ParseError(err_msg, code_block)
            else:
                prev_options[key] = val
    else:
        context.options_by_id[code_block.lpid] = code_block.options


class CapturedLine(typ.NamedTuple):

    us_ts: float
    line : str


class ProcResult(typ.NamedTuple):
    exit_code: int
    stdout   : typ.List[CapturedLine]
    stderr   : typ.List[CapturedLine]


class SessionException(Exception):
    pass


ExitCode = int


def _build(context: Context) -> ExitCode:
    captured_outputs: typ.Dict[LitprogID, str       ] = {}
    captured_procs  : typ.Dict[LitprogID, ProcResult] = {}

    all_ids = set(context.options_by_id.keys()) | set(context.blocks_by_id.keys())

    while len(captured_outputs) < len(all_ids):

        assert len(context.options_by_id) == len(all_ids)

        prev_len_completed = len(captured_outputs)
        for lpid, options in context.options_by_id.items():
            if lpid in captured_outputs:
                continue

            litprog_type: str = options['lptype']
            if litprog_type == 'out_file':
                required_inputs   = set(options['inputs'])
                completed_outputs = set(captured_outputs.keys())
                missing_inputs    = required_inputs - completed_outputs
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
                log.debug(f"{litprog_type:>9} block {lpid:>25} done.")
            elif litprog_type == 'raw_block':
                captured_outputs[lpid] = "".join(
                    "".join(l.val for l in block.lines)
                    for block in context.blocks_by_id[lpid]
                )
                log.debug(f"{litprog_type:>9} block {lpid:>25} done.")
            elif litprog_type == 'session':
                required_blocks = set(options.get('requires', []))
                captured_blocks = set(captured_outputs.keys())
                missing_blocks  = required_blocks - captured_blocks
                if any(missing_blocks):
                    log.debug(f"deferring {lpid} until {missing_blocks} are completed")
                    continue

                cmd_parts: typ.List[str]
                command = options.get('command', "bash")

                if isinstance(command, str):
                    cmd_parts = shlex.split(command)
                elif isinstance(command, list):
                    cmd_parts = command
                else:
                    err_msg = f"Invalid command: {command}"
                    raise Exception(err_msg)
                log.info(f"starting session {lpid}. cmd: {cmd_parts}")
                isession = session.InteractiveSession(cmd_parts)

                for block in context.blocks_by_id[lpid]:
                    for line in block.lines:
                        isession.send(line.val)

                exit_code = isession.wait(timeout=2)
                output    = "\n".join(iter(isession))

                expected_exit_code = options.get('expected_exit_code', 0)
                if exit_code == expected_exit_code:
                    # TODO (mb): better output capture for sessions
                    captured_outputs[lpid] = output
                    log.info(
                        f"{litprog_type:>9} block {lpid:<15} done. RETCODE: {exit_code} ok."
                    )
                else:
                    log.info(
                        f"{litprog_type:>9} block {lpid:<15} fail. RETCODE: {exit_code} invalid!"
                    )
                    sys.stderr.write(output)
                    err_msg = f"Error processing block {lpid}"
                    log.error(err_msg)
                    return 1
            elif litprog_type == 'meta':
                captured_outputs[lpid] = ""
                log.warning("lptype=meta not implemented")
            else:
                log.error(f"Unhandled litprog type={litprog_type} for lpid={lpid}")
                return 1

            if lpid not in captured_outputs:
                continue

            filepath = options.get('filepath')
            if filepath is None:
                continue

            encoding = options.get('encoding', "utf-8")
            file     = pl.Path(filepath)
            with file.open(mode="w", encoding=encoding) as fh:
                fh.write(captured_outputs[lpid])

            if options.get('is_executable'):
                file.chmod(file.stat().st_mode | 0o100)

            log.info(f"wrote to '{file}'")

        if prev_len_completed == len(captured_outputs):
            captured_blocks = list(captured_outputs.keys())
            log.error(f"Captured blocks: {captured_blocks}")
            log.error(f"Build failed: No progress/unresolved requirements.")
            return 1
    return 0


InputPaths = typ.Sequence[str]

MarkdownPaths = typ.Iterable[pl.Path]


def iter_markdown_filepaths(input_paths: InputPaths) -> MarkdownPaths:
    for in_path_str in input_paths:
        in_path = pl.Path(in_path_str)
        if in_path.is_dir():
            for in_filepath in in_path.glob("**/*.md"):
                yield in_filepath
        else:
            yield in_path


def _parse_context(input_paths: InputPaths) -> Context:
    input_filepaths = sorted(iter_markdown_filepaths(input_paths))

    context = Context()

    for path in input_filepaths:
        log.debug(f"parsing {path}")
        for rfb in _iter_raw_fenced_blocks(path):
            code_block = _parse_code_block(rfb)
            _add_to_context(context, code_block)
    return context


@cli.command()
@click.argument('input_paths', nargs=-1, type=click.Path(exists=True))
@click.option(
    '-v', '--verbose', count=True, help="Control log level. -vv for debug level."
)
def build(input_paths: InputPaths, verbose: int = 0) -> None:
    _configure_logging(verbose)
    context = _parse_context(input_paths)
    try:
        sys.exit(_build(context))
    except SessionException:
        sys.exit(1)
