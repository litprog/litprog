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

from litprog.parse import (
    MarkdownElement,
    Headline,
    Block,
    Directive,
    MarkdownFile,
    Context,
)

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


class CapturedLine(typ.NamedTuple):
    ts    : float
    line  : str
    is_err: bool


class CapturedSession(typ.NamedTuple):
    command    : str
    exit_status: int
    runtime_ms : float
    lines      : typ.List[CapturedLine]


# TODO: directive for session commands configuration
COMMANDS_BY_LANG = {
    "python": "python",
    "bash"  : "bash",
}


def get_directive(
    block: Block, name: str
) -> typ.Optional[Directive]:
    for directive in block.directives:
        if directive.name == name:
            return directive


def iter_directives(
    block: Block, name: str
) -> typ.Iterable[Directive]:
    for directive in block.directives:
        if directive.name == name:
            yield directive


def has_directive(block: Block, name: str) -> bool:
    return get_directive(block, name) is not None


CONSTANT_RE = re.compile(
    r"`lp_const:\s*(?P<name>\w+)\s*=(?P<value>.*)`"
)


def find_include(
    block_contents: typ.List[str],
    include_directive: Directive,
) -> typ.Optional[str]:
    query = include_directive.value.strip()
    for content in block_contents:
        if query in content:
            return content


def indented_include(content, raw_text, include_val) -> str:
    unindented = raw_text.lstrip()
    indent = raw_text[:-len(unindented)]
    if indent:
        include_val = "\n".join(
            indent + line
            for line in include_val.splitlines()
        )
    return content.replace(raw_text, include_val)


def _parse_prefix(directive: Directive) -> str:
    val = directive.value.strip()
    if val.startswith("'") and val.endswith("'"):
        val = val[1:-1]
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return val


def build(ctx: Context) -> None:
    files_by_md_path: typ.Dict[pl.Path, MarkdownFile] = {
        md_file.md_path: md_file
        for md_file in ctx.files
    }

    # TODO: mark build as running
    build_start = time.time()
    # pass 1: expand constants and includes

    constants_by_name = {}
    done = False

    orig_md_files: typ.Dict[pl.Path, MarkdownFile] = {
        md_file.md_path: md_file.copy()
        for md_file in ctx.files
    }

    while not done:
        done = True
        for md_file in ctx.files:
            for elem in md_file.elements:
                for match in CONSTANT_RE.finditer(elem.content):
                    name = match.group('name')
                    value = match.group('value')
                    constants_by_name[name] = value

            for block in md_file.blocks:
                content = block.content
                for const_dir in iter_directives(block, 'lp_const'):
                    name, value = const_dir.value.split("=", 1)
                    constants_by_name[name] = value
                    content = content.replace(const_dir.raw_text, "")

                if content == block.content:
                    continue

                done = False

                elem = md_file.elements[block.elem_index]
                md_file.elements[block.elem_index] = MarkdownElement(
                    elem.md_path,
                    elem.elem_index,
                    elem.md_type,
                    content,
                    elem.first_line,
                )

            constants = [
                (name, value)
                for name, value in constants_by_name.items()
            ]

            # We want to expand from longest to shortest,
            # in case the name of a constant is a substring
            # of another.
            constant_names = sorted(
                constants_by_name.keys(),
                key=len,
                reverse=True
            )

            includable_contents = [
                block.inner_content
                for block in md_file.blocks
                if not (
                    has_directive(block, 'lp_session')
                    or has_directive(block, 'lp_make')
                    or has_directive(block, 'lp_include')
                    or has_directive(block, 'lp_const')
                )
            ]

            new_elements = list(md_file.elements)

            for block in md_file.blocks:
                new_content = block.content
                for name in constant_names:
                    const_val = constants_by_name[name]
                    new_content = new_content.replace(name, const_val)

                for d in iter_directives(block, 'lp_include'):
                    include_val = find_include(includable_contents, d)
                    if include_val:
                        new_content = indented_include(
                            new_content, d.raw_text, include_val
                        )

                if new_content == block.content:
                    continue

                done = False

                elem = md_file.elements[block.elem_index]
                new_elements[block.elem_index] = MarkdownElement(
                    elem.md_path,
                    elem.elem_index,
                    elem.md_type,
                    new_content,
                    elem.first_line,
                )

            md_file.elements = new_elements

    # phase 3. validate blocks
    errors = 0
    for md_file in ctx.files:
        for block in md_file.blocks:
            for directive in block.directives:
                if directive.name != 'lp_include':
                    continue

                elem = md_file.elements[block.elem_index]

                rel_line_no = 0
                for line in elem.content.splitlines():
                    if directive.raw_text in line:
                        break
                    rel_line_no += 1

                line_no = elem.first_line + rel_line_no
                log.error(f"Error processing {md_file.md_path}")
                log.error(f"Could not expend '{directive.raw_text}' on line {line_no}")
                errors += 1

    if errors:
        sys.exit(1)

    # phase 4. write back files
    for md_file in ctx.files:
        for block in md_file.blocks:
            file_directive = get_directive(block, 'lp_file')
            if file_directive is None:
                continue

            path = pl.Path(file_directive.value)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open(mode="w", encoding="utf-8") as fh:
                fh.write(block.inner_content)

    # phase 5. run sessions
    captures_by_elem_index: typ.Dict[int, CapturedSession] = {}

    for md_file in ctx.files:
        updated_elements: typ.List[MarkdownElement] = []

        prev_capture_index = -1

        for block in md_file.blocks:
            is_debug = has_directive(block, 'lp_debug')
            if is_debug:
                debug_prefix = _parse_prefix(get_directive(block, 'lp_debug')) or "> "
            else:
                debug_prefix = "> "

            if has_directive(block, 'lp_session'):
                prev_capture_index = -1
                command_directive = get_directive(block, 'lp_command')
                if command_directive is None:
                    lang_directive = get_directive(block, 'lp_language')
                    command = COMMANDS_BY_LANG[lang_directive.value]
                else:
                    command = command_directive.value

                timeout = get_directive(block, 'lp_timeout')
                if timeout is None:
                    timeout_val = 1000.0
                else:
                    timeout_val = float(timeout.value) / 1000.0

                input_delay = get_directive(block, 'lp_input_delay')
                if input_delay is None:
                    input_delay_val = 0
                else:
                    input_delay_val = float(input_delay)

                isession = litprog.session.InteractiveSession(command)
                keepends = True
                try:
                    for line in block.inner_content.splitlines(keepends):
                        if is_debug:
                            sys.stderr.write(debug_prefix + line.rstrip() + "\n")
                        isession.send(line, delay=input_delay_val)
                    exit_status = isession.wait(timeout=timeout_val)
                except Exception:
                    log.error(f"Error processing session for {command}")
                    sys.stdout.write("".join(isession.iter_stdout()))
                    sys.stderr.write("".join(isession.iter_stderr()))
                    raise

                runtime_ms = isession.runtime * 1000
                log.info(f"  session block runtime: {runtime_ms:9.3f}ms")

                lines = list(isession.iter_lines())

                prev_capture_index = block.elem_index
                captures_by_elem_index[prev_capture_index] = CapturedSession(
                    command, exit_status, runtime_ms, lines
                )

            if has_directive(block, 'lp_output'):
                # TODO: parse out_color
                out_color = get_directive(block, 'lp_out_color')
                err_color = get_directive(block, 'lp_err_color')
                if err_color is None:
                    color_code = TERM_COLORS['red']
                    err_fmt = "\u001b[" + color_code + "m{0}\u001b[0m"
                else:
                    color_val = err_color.value.strip()
                    if color_val == "none":
                        err_fmt = "{0}"
                    elif color_val in TERM_COLORS:
                        color_code = TERM_COLORS[color_val]
                        err_fmt = "\u001b[" + color_code + "m{0}\u001b[0m"
                    elif COLOR_CODE_RE.match(color_val):
                        err_fmt = "\u001b[" + color_val + "m{0}\u001b[0m"
                    else:
                        valid_codes = ", ".join(sorted(TERM_COLORS.keys()))
                        err_msg = (
                            f"Invalid lp_err_color: {color_val}. "
                            f"Must be 'none', {valid_codes} or a valid color code."
                        )
                        raise Exception(err_msg)

                out_prefix = get_directive(block, 'lp_out_prefix')
                err_prefix = get_directive(block, 'lp_err_prefix')
                out_prefix_str = _parse_prefix(out_prefix) if out_prefix else ""
                err_prefix_str = _parse_prefix(err_prefix) if err_prefix else "! "

                if prev_capture_index < 0:
                    output = "<invalid no output captured>"
                else:
                    capture = captures_by_elem_index[prev_capture_index]
                    # TODO: coloring
                    # if "\u001b" in capture.stderr:
                    #     stderr = capture.stderr
                    # elif stderr.strip():
                    #     stderr = err_fmt.format(capture.stderr)

                    output_lines = []
                    for cl in capture.lines:
                        if cl.is_err:
                            if err_prefix_str:
                                line_val = err_prefix_str + cl.line
                            else:
                                line_val = cl.line
                        else:
                            if out_prefix_str:
                                line_val = out_prefix_str + cl.line
                            else:
                                line_val = cl.line
                        output_lines.append(line_val.rstrip())

                    output = "\n".join(output_lines)

                    if not output.endswith("\n"):
                        output += "\n"

                    if has_directive(block, 'lp_session_info'):
                        output += (
                            f"# exit_status: {capture.exit_status}; "
                            f"runtime: {capture.runtime_ms:.3f} ms\n"
                        )


                elem = md_file.elements[block.elem_index]
                assert elem.md_type == 'block'

                header_lines = []
                keepends = True
                for line in elem.content.splitlines(keepends):
                    if line.startswith("```") or line.startswith("# lp_"):
                        header_lines.append(line)

                last_line = header_lines.pop()
                new_content = "".join(header_lines) + output + last_line

                if elem.content != new_content:
                    updated_elem = MarkdownElement(
                        elem.md_path,
                        elem.elem_index,
                        elem.md_type,
                        new_content,
                        elem.first_line,
                    )
                    updated_elements.append(updated_elem)

        # phase 6. rewrite output blocks
        if updated_elements:
            orig_elements = list(orig_md_files[md_file.md_path].elements)
            for elem in updated_elements:
                # TODO: strip escape codes from output
                orig_elements[elem.elem_index] = elem

            file_content = "".join(elem.content for elem in orig_elements)
            with md_file.md_path.open(mode="w", encoding="utf-8") as fh:
                fh.write(file_content)
            log.info(f"Updated {md_file.md_path}")
