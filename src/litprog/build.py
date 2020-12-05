# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import io
import os
import re
import sys
import enum
import math
import time
import typing as typ
import logging
import os.path
import datetime as dt
import operator as op
import functools as ft
import itertools as it
import collections

import pathlib2 as pl

from litprog.parse import Block
from litprog.parse import Context
from litprog.parse import Headline
from litprog.parse import Directive
from litprog.parse import ParseError
from litprog.parse import MarkdownFile
from litprog.parse import MarkdownElement

from . import parse
from . import session

log = logging.getLogger(__name__)


COLOR_CODE_RE = re.compile(r"\d+(;\d)?")


TERM_COLORS = {
    'black'  : "30",
    'red'    : "31",
    'green'  : "32",
    'yellow' : "33",
    'blue'   : "34",
    'magenta': "35",
    'cyan'   : "36",
    'white'  : "37",
}


MarkdownFiles = typ.Iterable[MarkdownFile]

# The expanded files are structurally no different, it's just that
# their elements are expanded.
ExpandedMarkdownFile  = MarkdownFile
ExpandedMarkdownFiles = typ.Iterable[ExpandedMarkdownFile]

CapturedLine = session.CapturedLine


class Capture(typ.NamedTuple):
    command    : str
    exit_status: int
    runtime    : float
    lines      : typ.List[CapturedLine]


class BlockError(Exception):

    block           : Block
    include_contents: typ.List[str]

    def __init__(self, msg: str, block: Block, include_contents: typ.Optional[str] = None) -> None:
        self.block            = block
        self.include_contents = include_contents or []
        loc                   = parse.location(block).strip()
        super().__init__(f"{loc} - " + msg)


def get_directive(
    block: Block, name: str, missing_ok: bool = True, many_ok: bool = True
) -> typ.Optional[Directive]:
    found: typ.List[Directive] = []
    for directive in block.directives:
        if directive.name == name:
            if many_ok:
                return directive
            else:
                found.append(directive)

    if len(found) == 0:
        if missing_ok:
            return None
        else:
            errmsg = f"Could not find block with expected '{name}'"
            raise BlockError(errmsg, block)

    if len(found) > 1 and not many_ok:
        errmsg = f"Block with multiple '{name}'"
        raise BlockError(errmsg, block)

    return found[0]


def has_directive(block: Block, name: str) -> bool:
    return get_directive(block, name, missing_ok=True) is not None


def iter_directives(block: Block, name: str) -> typ.Iterable[Directive]:
    for directive in block.directives:
        if directive.name == name:
            yield directive


# CONSTANT_RE = re.compile(r"`lp_const:\s*(?P<name>\w+)\s*=(?P<value>.*)`")
#
#
# class ConstItem(typ.NamedTuple):
#     decl_path: pl.Path
#     name     : str
#     value    : str
#
#
# def _parse_constants(build_ctx: Context) -> typ.List[ConstItem]:
#     constants: typ.List[ConstItem] = []
#     for md_file in build_ctx.files:
#         decl_path = md_file.md_path
#         for elem in md_file.elements:
#             for match in CONSTANT_RE.finditer(elem.content):
#                 name  = match.group('name')
#                 value = match.group('value')
#                 constants.append(ConstItem(decl_path, name, value))
#
#     # Expand longer constants first, so constants that
#     # are substrings of others don't clobber the longer
#     # constant. This is not an ideal solution, but since
#     # we are restricted to textual replacement with any
#     # conceivable language this may be adequate.
#     constants.sort(key=lambda item: len(item.name))
#
#     return constants
#
#
# def _expand_constants(build_ctx: Context) -> Context:
#     constants = _parse_constants(build_ctx)
#
#     done = False
#     while not done:
#         done         = True
#         new_md_files = []
#         for md_file in build_ctx.files:
#             cur_path = md_file.md_path
#
#             new_elements = list(md_file.elements)
#
#             for block in md_file.blocks:
#                 new_content = block.content
#                 for decl_path, name, const_val in constants:
#                     namespace   = decl_path.name[: -len(decl_path.suffix)]
#                     new_content = new_content.replace(name, const_val)
#                     if decl_path == cur_path:
#                         new_content = new_content.replace(name, const_val)
#
#                 # TODO: There may a bug here that relates to the order
#                 #   of expanding blocks. Since the addable_val is based
#                 #   on block.inner_content, there may be issues with
#                 #   recursive includes
#
#                 if new_content == block.content:
#                     continue
#
#                 done = False
#
#                 elem = md_file.elements[block.elem_index]
#                 new_elements[block.elem_index] = MarkdownElement(
#                     elem.md_path, elem.first_line, elem.elem_index, elem.md_type, new_content, None
#                 )
#
#             new_md_file = MarkdownFile(md_file.md_path, new_elements)
#             new_md_files.append(new_md_file)
#
#         build_ctx = Context(new_md_files)
#
#     return build_ctx


# # TODO (mb 2020-06-01): maybe use for lp_include_match
# def find_include(block_contents: typ.List[str], include_directive: Directive) -> typ.Optional[str]:
#     query = include_directive.value.strip()
#     for content in block_contents:
#         if query in content:
#             return content
#     return None


def _indented_include(content, raw_text, include_val) -> str:
    unindented = raw_text.lstrip()
    indent     = raw_text[: -len(unindented)]
    if indent:
        include_val = "\n".join(indent + line for line in include_val.splitlines())
    return content.replace(raw_text, include_val)


# TODO: this should be part of the parsing of all directives
def _parse_prefix(directive: Directive) -> str:
    val = directive.value.strip()
    if val.startswith("'") and val.endswith("'"):
        val = val[1:-1]
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return val


BlockId     = str
BlocksById  = typ.Dict[BlockId, typ.List[Block]]
ParentsById = typ.Dict[BlockId, typ.Set[BlockId]]


def _get_include_loop(
    lp_id: BlockId, include_parents: ParentsById, root_id: typ.Optional[BlockId] = None, n: int = 0
) -> typ.Optional[typ.List[str]]:
    if root_id is None:
        return _get_include_loop(lp_id, include_parents, lp_id, n + 1)

    parent_ids = include_parents.get(lp_id, [])
    for parent_id in parent_ids:
        if parent_id == root_id:
            return [parent_id]  # found loop

    for parent_id in parent_ids:
        loop = _get_include_loop(parent_id, include_parents, root_id, n + 1)
        if loop:
            return [parent_id] + loop
    return None


def _err_on_include_loop(
    block          : Block,
    lp_id          : BlockId,
    blocks_by_id   : BlocksById,
    include_parents: ParentsById,
    root_id        : typ.Optional[BlockId] = None,
) -> None:
    loop_ids = _get_include_loop(lp_id, include_parents, root_id=root_id)
    if not loop_ids or len(loop_ids) < 2:
        return

    for loop_id in loop_ids:
        loop_block = blocks_by_id[loop_id][0]
        loc        = parse.location(loop_block).strip()
        log.warning(f"{loc} - {loop_id} (trace for include loop)")

    path   = " -> ".join(f"'{loop_id}'" for loop_id in loop_ids)
    errmsg = f"Include loop {path}"
    raise BlockError(errmsg, block)


def _namespaced_lp_id(block: Block, lp_id: BlockId) -> BlockId:
    if "." in lp_id:
        return lp_id.strip()
    else:
        return block.namespace + "." + lp_id.strip()


def _expand_directives(blocks_by_id: BlocksById, md_file: MarkdownFile) -> MarkdownFile:
    new_md_file = md_file.copy()
    include_parents: ParentsById = {}

    is_done = False
    while not is_done:
        is_done = True
        blocks  = list(new_md_file.blocks)
        for block in blocks:
            lp_def = get_directive(block, 'lp_def', missing_ok=True, many_ok=False)
            if lp_def is None:
                lp_def_id = None
            else:
                lp_def_id = _namespaced_lp_id(block, lp_def.value) if lp_def else None

            new_content = block.content
            for lp_include in iter_directives(block, 'lp_include'):
                content_chunks: typ.List[str] = []
                lp_include_ids = [
                    _namespaced_lp_id(block, lp_id) for lp_id in lp_include.value.split(",")
                ]

                for lp_id in lp_include_ids:
                    if lp_id not in blocks_by_id:
                        errmsg = f"Unknown block id: {lp_id}"
                        raise BlockError(errmsg, block, content_chunks)

                    if lp_id not in include_parents:
                        include_parents[lp_id] = set()

                    if lp_def_id:
                        include_parents[lp_id].add(lp_def_id)

                    _err_on_include_loop(
                        block, lp_id, blocks_by_id, include_parents, root_id=lp_def_id
                    )

                    content_chunks.extend(
                        [b.includable_content + "\n" for b in blocks_by_id[lp_id]]
                    )

                include_content = "".join(content_chunks)
                new_content     = _indented_include(new_content, lp_include.raw_text, include_content)

            if new_content != block.content:
                is_done = False  # may need more recursive includes

                elem = new_md_file.elements[block.elem_index]
                new_md_file.elements[block.elem_index] = MarkdownElement(
                    elem.md_path, elem.first_line, elem.elem_index, elem.md_type, new_content, None
                )

    return new_md_file


def _get_blocks_by_id(md_files: MarkdownFiles) -> BlocksById:
    blocks_by_id: BlocksById = {}

    for md_file in md_files:
        for block in md_file.blocks:
            lp_def = get_directive(block, 'lp_def', missing_ok=True, many_ok=False)
            if lp_def:
                lp_def_id = lp_def.value
                if "." in lp_def_id:
                    errmsg = f"Invalid block id: {lp_def_id}"
                    raise BlockError(errmsg, block)

                block_id = _namespaced_lp_id(block, lp_def_id)
                if block_id in blocks_by_id:
                    prev_block = blocks_by_id[block_id][0]
                    prev_loc   = parse.location(prev_block).strip()
                    errmsg     = f"Block already defined: {lp_def_id} at {prev_loc}"
                    raise BlockError(errmsg, block)

                blocks_by_id[block_id] = [block]

            for lp_addto in iter_directives(block, 'lp_addto'):
                lp_addto_id = _namespaced_lp_id(block, lp_addto.value)
                if lp_addto_id not in blocks_by_id:
                    errmsg = f"Unknown block id: {lp_addto_id}"
                    raise BlockError(errmsg, block)

                blocks_by_id[lp_addto_id].append(block)

    return blocks_by_id


def _iter_expanded_files(md_files: MarkdownFiles) -> ExpandedMarkdownFiles:
    # NOTE (mb 2020-05-24): To do the expansion, we have to first
    #   build a graph so that we can resolve blocks for each include.

    # pass 1. collect all blocks (globally) with lp_def directives
    # NOTE (mb 2020-05-31): block ids are always absolute
    blocks_by_id = _get_blocks_by_id(md_files)

    # pass 2. expand lp_include directives in file
    for md_file in md_files:
        yield _expand_directives(blocks_by_id, md_file)


def _iter_block_errors(orig_ctx: Context, build_ctx: Context) -> typ.Iterable[str]:
    """Validate that expansion worked correctly."""
    # NOTE: the main purpose of the orig_ctx is to produce
    #   better error messages. It allows us to point at the
    #   original block, whereas the build_ctx has been
    #   modified and line numbers no longer correspond to
    #   the original file.
    assert len(orig_ctx.files) == len(build_ctx.files)
    for orig_md_file, md_file in zip(orig_ctx.files, build_ctx.files):
        assert orig_md_file.md_path == md_file.md_path
        assert len(orig_md_file.elements) == len(md_file.elements)

        for block in md_file.blocks:
            orig_elem = orig_md_file.elements[block.elem_index]
            for directive in iter_directives(block, 'lp_include'):
                elem = md_file.elements[block.elem_index]

                rel_line_no = 0
                for line in orig_elem.content.splitlines():
                    if directive.raw_text in line:
                        break
                    else:
                        rel_line_no += 1

                line_no = elem.first_line + rel_line_no
                yield f"Error processing {md_file.md_path}"
                yield f"Could not expend '{directive.raw_text}' on line {line_no}"


def _dump_files(build_ctx: Context) -> None:
    for md_file in build_ctx.files:
        for block in md_file.blocks:
            file_directive = get_directive(block, 'lp_file')
            if file_directive is None:
                continue

            path = pl.Path(file_directive.value)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open(mode="w", encoding="utf-8") as fh:
                fh.write(block.includable_content)


class SessionBlockOptions(typ.NamedTuple):
    """A Session Block based on an 'lp_exec', 'lp_run' or 'lp_out' directive.

    If it is an lp_exec or lp_run directive a session is run and the output is
    captured for later use. If it is an lp_out directive, output from a previous
    capture is used.
    """

    command  : typ.Optional[str]
    directive: str

    is_stdin_writable   : bool
    is_debug            : bool
    keepends            : bool
    timeout             : float
    input_delay         : float
    debug_prefix        : str
    expected_exit_status: int

    out_fmt : str
    err_fmt : str
    info_fmt: str

    out_prefix: str
    err_prefix: str


def _parse_session_block_options(block: Block) -> typ.Optional[SessionBlockOptions]:
    exec_directive = get_directive(block, 'lp_exec')
    run_directive  = get_directive(block, 'lp_run')
    out_directive  = get_directive(block, 'lp_out')

    command          : typ.Optional[str]
    is_stdin_writable: bool

    if exec_directive:
        directive         = 'lp_exec'
        command           = exec_directive.value
        is_stdin_writable = True
    elif run_directive:
        directive         = 'lp_run'
        command           = run_directive.value
        is_stdin_writable = True
    elif out_directive:
        directive         = 'lp_out'
        command           = None
        is_stdin_writable = False
    else:
        return None

    debug_directive = get_directive(block, 'lp_debug')
    if debug_directive:
        is_debug     = True
        debug_prefix = _parse_prefix(debug_directive) or "{lineno:>3}: "
    else:
        is_debug     = False
        debug_prefix = "{lineno:>3}: "

    timeout = get_directive(block, 'lp_timeout')
    if timeout is None:
        timeout_val = 1.0
    else:
        timeout_val = float(timeout.value)

    input_delay = get_directive(block, 'lp_input_delay')
    if input_delay is None:
        input_delay_val = 0.0
    else:
        input_delay_val = float(input_delay.value)

    keepends = True

    # TODO: parse out_color
    out_color = get_directive(block, 'lp_out_color')
    err_color = get_directive(block, 'lp_err_color')

    if err_color is None:
        color_code = TERM_COLORS['red']
        err_fmt    = "\u001b[" + color_code + "m{0}\u001b[0m"
    else:
        color_val = err_color.value.strip()
        if color_val == 'none':
            err_fmt = "{0}"
        elif color_val in TERM_COLORS:
            color_code = TERM_COLORS[color_val]
            err_fmt    = "\u001b[" + color_code + "m{0}\u001b[0m"
        elif COLOR_CODE_RE.match(color_val):
            err_fmt = "\u001b[" + color_val + "m{0}\u001b[0m"
        else:
            valid_codes = ", ".join(sorted(TERM_COLORS.keys()))
            err_msg     = (
                f"Invalid lp_err_color: {color_val}. "
                f"Must be 'none', {valid_codes} or a valid color code."
            )
            raise Exception(err_msg)

    out_prefix = get_directive(block, 'lp_out_prefix')
    err_prefix = get_directive(block, 'lp_err_prefix')

    info_directive = get_directive(block, 'lp_proc_info')
    if info_directive is None:
        info_fmt = "# exit: {exit}"
    else:
        info_fmt = info_directive.value

    expect               = get_directive(block, 'lp_expect')
    expected_exit_status = 0 if expect is None else int(expect.value)

    return SessionBlockOptions(
        command=command,
        directive=directive,
        is_stdin_writable=is_stdin_writable,
        is_debug=is_debug,
        keepends=keepends,
        timeout=timeout_val,
        input_delay=input_delay_val,
        debug_prefix=debug_prefix,
        expected_exit_status=expected_exit_status,
        out_fmt="{0}",
        err_fmt=err_fmt,
        info_fmt=info_fmt,
        out_prefix=_parse_prefix(out_prefix) if out_prefix else "",
        err_prefix=_parse_prefix(err_prefix) if err_prefix else "! ",
    )


def _parse_capture_output(capture: Capture, opts: SessionBlockOptions) -> str:
    # TODO: coloring
    # if "\u001b" in capture.stderr:
    #     stderr = capture.stderr
    # elif stderr.strip():
    #     stderr = opts.err_fmt.format(capture.stderr)

    output_lines = []
    for cl in capture.lines:
        if cl.is_err:
            if opts.err_prefix:
                line_val = opts.err_prefix + cl.line
            else:
                line_val = cl.line
        else:
            if opts.out_prefix:
                line_val = opts.out_prefix + cl.line
            else:
                line_val = cl.line
        output_lines.append(line_val.rstrip())

    output = "\n".join(output_lines)

    if not output.endswith("\n"):
        output += "\n"

    if opts.info_fmt != 'none':
        output += opts.info_fmt.format(
            **{
                'exit'   : capture.exit_status,
                'time'   : capture.runtime,
                'time_ms': capture.runtime * 1000,
            }
        )
        output = output.strip()

        # make sure the block closing backticks are
        # on their own line
        if not output.endswith("\n"):
            output += "\n"

    return output


def build(orig_ctx: Context, exitfirst: bool = False, in_place_update: bool = False) -> Context:
    # TODO: Immutable datastructures
    #   Context, MarkdownFile
    build_ctx = orig_ctx.copy()

    # TODO: mark build as running
    build_start = time.time()

    try:
        # NOTE (mb 2020-05-22): macros/constants are abandoned for now
        # phase 1: expand constants
        # build_ctx      = _expand_constants(build_ctx)

        # phase 2: expand lp_include directives
        expanded_files = list(_iter_expanded_files(build_ctx.files))
    except BlockError as err:
        # TODO (mb 2020-06-03): print context of block
        contents = err.include_contents or [err.block.content]
        for content in contents:
            for line in content.splitlines():
                if line.strip():
                    sys.stderr.write("E " + line.rstrip() + "\n")
        raise

    build_ctx = Context(expanded_files)

    # phase 3. validate blocks
    error_messages = list(_iter_block_errors(orig_ctx, build_ctx))
    for error_msg in error_messages:
        log.error(error_msg)

    if error_messages:
        sys.exit(1)

    # phase 4. write files with expanded blocks
    #   This has to happen before sub-processes, as those
    #   may use the newly created files.
    _dump_files(build_ctx)

    # TODO: Dependency graph of some kind so we can order
    #   process execution.
    doc_ctx = orig_ctx.copy()

    # phase 5. run sub-processes
    for file_idx, (orig_md_file, md_file) in enumerate(zip(orig_ctx.files, build_ctx.files)):
        captures_by_elem_index: typ.Dict[int, Capture] = {}
        updated_elements      : typ.List[MarkdownElement] = []

        old_capture_index = -1

        for block in md_file.blocks:
            opts = _parse_session_block_options(block)
            if opts is None:
                continue

            if opts.command:
                log.info(f"  {opts.directive} {opts.command}")

                isession = session.InteractiveSession(opts.command)

                if opts.is_stdin_writable:
                    stdin_lines = block.inner_content.splitlines(opts.keepends)
                else:
                    stdin_lines = []

                if opts.is_debug:
                    for i, line in enumerate(stdin_lines):
                        prefix = opts.debug_prefix.format(lineno=i + 1)
                        sys.stderr.write(prefix + line.rstrip() + "\n")

                try:
                    for i, line in enumerate(stdin_lines):
                        isession.send(line, delay=opts.input_delay)
                    exit_status = isession.wait(timeout=opts.timeout)
                except Exception as ex:
                    log.error(f"Error processing '{opts.command}': {ex}")
                    sys.stdout.write("".join(isession.iter_stdout()))
                    sys.stderr.write("".join(isession.iter_stderr()))
                    raise

                runtime_ms = isession.runtime * 1000

                if exit_status == opts.expected_exit_status:
                    exit_info = f"{exit_status:>3}       "
                else:
                    exit_info = f"{exit_status:>3} != {opts.expected_exit_status:<3}"

                lines   = list(isession.iter_lines())
                capture = Capture(opts.command, exit_status, isession.runtime, lines)

                log.info(f"  {opts.directive}  exit: {exit_info}  time: {runtime_ms:9.3f}ms")
                if exitfirst and exit_status != opts.expected_exit_status:
                    output = _parse_capture_output(capture, opts)
                    sys.stderr.write(output)
                    log.error(f"Line {block.first_line} of {block.md_path} - Error executing block")
                    sys.exit(1)

                # TODO: limit output using lp_max_bytes and lp_max_lines
                # TODO: output escaping/fence style change and errors

                old_capture_index = block.elem_index
                captures_by_elem_index[old_capture_index] = capture

            if opts.directive in ('lp_out', 'lp_run'):
                if opts.directive == 'lp_out':
                    capture_index = old_capture_index
                else:
                    capture_index = block.elem_index

                if capture_index < 0:
                    output = "<invalid no output captured>\n"
                else:
                    # NOTE: The capture may be the same as the elem_index
                    #   of the current block.
                    capture       = captures_by_elem_index[capture_index]
                    capture_index = -1
                    output        = _parse_capture_output(capture, opts)

                elem = md_file.elements[block.elem_index]
                assert elem.md_type == 'block'

                header_lines = [
                    line
                    for line in elem.content.splitlines(opts.keepends)
                    if line.startswith("```") or line.startswith("# lp_")
                ]

                last_line   = header_lines.pop()
                new_content = "".join(header_lines) + output + last_line

                if elem.content != new_content:
                    updated_elem = MarkdownElement(
                        elem.md_path,
                        elem.first_line,
                        elem.elem_index,
                        elem.md_type,
                        new_content,
                        None,
                    )
                    updated_elements.append(updated_elem)

        # phase 6. rewrite output blocks
        if not any(updated_elements):
            continue

        new_elements = list(orig_md_file.elements)
        for elem in updated_elements:
            orig_elem = orig_md_file.elements[elem.elem_index]
            assert 'lp_out' in orig_elem.content or 'lp_run' in orig_elem.content
            new_elements[elem.elem_index] = elem

        new_md_file = MarkdownFile(md_file.md_path, new_elements)
        if in_place_update:
            new_file_content = str(new_md_file)
            with new_md_file.md_path.open(mode="w", encoding="utf-8") as fh:
                fh.write(new_file_content)
        log.info(f"Updated {new_md_file.md_path}")
        doc_ctx.files[file_idx] = new_md_file

    duration = time.time() - build_start
    log.info(f"Build finished after {duration:9.3f}sec")

    return doc_ctx
