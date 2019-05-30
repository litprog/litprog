# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import logging

log = logging.getLogger(__name__)

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

from litprog.parse import MarkdownElement, Headline, Block, Directive, MarkdownFile, Context

import litprog.session


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


CapturedLine = litprog.session.CapturedLine


class Capture(typ.NamedTuple):
    command    : str
    exit_status: int
    runtime    : float
    lines      : typ.List[CapturedLine]


def get_directive(block: Block, name: str) -> typ.Optional[Directive]:
    for directive in block.directives:
        if directive.name == name:
            return directive
    return None


def iter_directives(block: Block, name: str) -> typ.Iterable[Directive]:
    for directive in block.directives:
        if directive.name == name:
            yield directive


def has_directive(block: Block, name: str) -> bool:
    return get_directive(block, name) is not None


CONSTANT_RE = re.compile(r"`lp_const:\s*(?P<name>\w+)\s*=(?P<value>.*)`")


class ConstItem(typ.NamedTuple):
    decl_path: pl.Path
    name     : str
    value    : str


def _parse_constants(build_ctx: Context) -> typ.List[ConstItem]:
    constants: typ.List[ConstItem] = []
    for md_file in build_ctx.files:
        decl_path = md_file.md_path
        for elem in md_file.elements:
            for match in CONSTANT_RE.finditer(elem.content):
                name  = match.group('name')
                value = match.group('value')
                constants.append(ConstItem(decl_path, name, value))

    # Expand longer constants first, so constants that
    # are substrings of others don't clobber the longer
    # constant. This is not an ideal solution, but since
    # we are restricted to textual replacement with any
    # conceivable language this may be adequate.
    constants.sort(key=lambda item: len(item.name))

    return constants


def find_include(block_contents: typ.List[str], include_directive: Directive) -> typ.Optional[str]:
    query = include_directive.value.strip()
    for content in block_contents:
        if query in content:
            return content
    return None


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


def _expand_constants(build_ctx: Context) -> Context:
    constants = _parse_constants(build_ctx)
    # macros have been abandoned for now
    return build_ctx

    done = False
    while not done:
        done         = True
        new_md_files = []
        for md_file in build_ctx.files:
            cur_path = md_file.md_path

            new_elements = list(md_file.elements)

            for block in md_file.blocks:
                new_content = block.content
                for decl_path, name, const_val in constants:
                    namespace   = decl_path.name[: -len(decl_path.suffix)]
                    new_content = new_content.replace(name, const_val)
                    if decl_path == cur_path:
                        new_content = new_content.replace(name, const_val)

                # TODO: There may a bug here that relates to the order
                #   of expanding blocks. Since the addable_val is based
                #   on block.inner_content, there may be issues with
                #   recursive includes

                if new_content == block.content:
                    continue

                done = False

                elem = md_file.elements[block.elem_index]
                new_elements[block.elem_index] = MarkdownElement(
                    elem.md_path, elem.elem_index, elem.md_type, new_content, elem.first_line, None
                )

            new_md_file = MarkdownFile(md_file.md_path, new_elements)
            new_md_files.append(new_md_file)

        build_ctx = Context(new_md_files)

    return build_ctx


def _iter_addable_blocks(md_file: MarkdownFile) -> typ.Iterable[Block]:
    for block in md_file.blocks:
        is_simple_block = not any(
            (
                has_directive(block, 'lp_out'),
                has_directive(block, 'lp_run'),
                has_directive(block, 'lp_make'),
                has_directive(block, 'lp_add'),
                has_directive(block, 'lp_file'),
            )
        )
        if is_simple_block:
            yield block


def _expand_file_add_directives(md_file: MarkdownFile) -> MarkdownFile:
    addable_contents = [b.inner_content for b in _iter_addable_blocks(md_file)]

    new_elements = list(md_file.elements)
    for block in md_file.blocks:
        new_content = block.content
        for lp_add in iter_directives(block, 'lp_add'):
            addable_val = find_include(addable_contents, lp_add)
            if not addable_val:
                continue

            new_content = _indented_include(new_content, lp_add.raw_text, addable_val)

        if new_content == block.content:
            continue

        elem = md_file.elements[block.elem_index]
        new_elements[block.elem_index] = MarkdownElement(
            elem.md_path, elem.elem_index, elem.md_type, new_content, elem.first_line, None
        )

    return MarkdownFile(md_file.md_path, new_elements)


def _iter_expanded_files(md_files: typ.Iterable[MarkdownFile]) -> typ.Iterable[MarkdownFile]:
    # NOTE: To minimize complexity, we don't expand beyond the current
    #   file.
    #
    # This means, if you're looking for what an lp_add
    # directive will expand to, you only have to look for
    # the first occurrence of it's search string in the
    # same file.
    for md_file in md_files:
        prev_md_file = md_file
        while True:
            new_md_file = _expand_file_add_directives(prev_md_file)
            if new_md_file == prev_md_file:
                yield new_md_file
                break
            else:
                prev_md_file = new_md_file


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
            for directive in block.directives:
                if directive.name != 'lp_add':
                    continue

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
                fh.write(block.inner_content)


class SessionBlockOptions(typ.NamedTuple):
    """A Session Block uses either a 'lp_run' or 'lp_out' directive.

    If it is an lp_run directive a session is run and the output
    is captured for later use.
    If it is an lp_out directive, output is either used from
    a previous capture, or if a command is included, then the
    output of the command is captured and immediately used.
    """

    run    : typ.Optional[Directive]
    out    : typ.Optional[Directive]
    command: typ.Optional[str]

    is_stdin_writable: bool
    is_debug         : bool
    keepends         : bool
    timeout          : float
    input_delay      : float
    debug_prefix     : str

    out_fmt : str
    err_fmt : str
    info_fmt: str

    out_prefix: str
    err_prefix: str


def _parse_session_block_options(block: Block) -> typ.Optional[SessionBlockOptions]:
    run_directive = get_directive(block, 'lp_run')
    out_directive = get_directive(block, 'lp_out')
    if run_directive is None and out_directive is None:
        return None

    debug_directive = get_directive(block, 'lp_debug')
    if debug_directive:
        is_debug     = True
        debug_prefix = _parse_prefix(debug_directive) or "> "
    else:
        is_debug     = False
        debug_prefix = "> "

    command: typ.Optional[str]

    is_stdin_writable: bool

    if run_directive:
        command           = run_directive.value
        is_stdin_writable = True
    elif out_directive:
        command           = out_directive.value
        is_stdin_writable = False
    else:
        is_stdin_writable = False
        command           = None

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

    out_color = get_directive(block, 'lp_out_color')
    err_color = get_directive(block, 'lp_err_color')

    # TODO: parse out_color
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
        info_fmt = "# exit: {exit:>3}"
    else:
        info_fmt = info_directive.value

    return SessionBlockOptions(
        run=run_directive,
        out=out_directive,
        command=command,
        is_stdin_writable=is_stdin_writable,
        is_debug=is_debug,
        keepends=keepends,
        timeout=timeout_val,
        input_delay=input_delay_val,
        debug_prefix=debug_prefix,
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


def build(orig_ctx: Context) -> Context:
    # TODO: Immutable datastructures
    #   Context, MarkdownFile
    build_ctx = orig_ctx.copy()

    # TODO: mark build as running
    build_start = time.time()
    # pass 1: expand constants

    build_ctx      = _expand_constants(build_ctx)
    expanded_files = list(_iter_expanded_files(build_ctx.files))
    build_ctx      = Context(expanded_files)

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

        prev_capture_index = -1

        for block in md_file.blocks:
            opts = _parse_session_block_options(block)
            if opts is None:
                continue

            if opts.command:
                log.info(f"  lp_run {opts.command}")

                isession = litprog.session.InteractiveSession(opts.command)

                if opts.is_stdin_writable:
                    stdin_lines = block.inner_content.splitlines(opts.keepends)
                else:
                    stdin_lines = []

                try:
                    for line in stdin_lines:
                        if opts.is_debug:
                            sys.stderr.write(opts.debug_prefix + line.rstrip() + "\n")
                        isession.send(line, delay=opts.input_delay)
                    exit_status = isession.wait(timeout=opts.timeout)
                except Exception:
                    log.error(f"Error processing '{opts.command}'")
                    sys.stdout.write("".join(isession.iter_stdout()))
                    sys.stderr.write("".join(isession.iter_stderr()))
                    raise

                runtime_ms = isession.runtime * 1000
                log.info(f"  lp_run  exit: {exit_status}  time: {runtime_ms:9.3f}ms")

                lines = list(isession.iter_lines())

                # TODO: limit output using lp_max_bytes and lp_max_lines
                # TODO: output escaping/fence style change and errors

                prev_capture_index = block.elem_index
                captures_by_elem_index[prev_capture_index] = Capture(
                    opts.command, exit_status, isession.runtime, lines
                )

            if opts.out:
                if prev_capture_index < 0:
                    output = "<invalid no output captured>\n"
                else:
                    # NOTE: The capture may be the same as the elem_index
                    #   of the current block.
                    capture            = captures_by_elem_index[prev_capture_index]
                    prev_capture_index = -1
                    output             = _parse_capture_output(capture, opts)

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
                        elem.elem_index,
                        elem.md_type,
                        new_content,
                        elem.first_line,
                        None,
                    )
                    updated_elements.append(updated_elem)

        # phase 6. rewrite output blocks
        if not any(updated_elements):
            continue

        new_elements = list(orig_md_file.elements)
        for elem in updated_elements:
            orig_elem = orig_md_file.elements[elem.elem_index]
            assert "lp_out" in orig_elem.content
            new_elements[elem.elem_index] = elem

        new_md_file      = MarkdownFile(md_file.md_path, new_elements)
        new_file_content = str(new_md_file)
        with new_md_file.md_path.open(mode="w", encoding="utf-8") as fh:
            fh.write(new_file_content)
        log.info(f"Updated {new_md_file.md_path}")
        doc_ctx.files[file_idx] = new_md_file

    return doc_ctx
