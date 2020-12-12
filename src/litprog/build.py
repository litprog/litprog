# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import re
import sys
import time
import typing as typ
import logging
import pathlib as pl

from . import parse
from . import session

logger = logging.getLogger(__name__)


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


MarkdownFiles = typ.Iterable[parse.MarkdownFile]

# The expanded files are structurally no different, it's just that
# their elements are expanded.
ExpandedMarkdownFile  = parse.MarkdownFile
ExpandedMarkdownFiles = typ.Iterable[ExpandedMarkdownFile]

CapturedLine = session.CapturedLine


class Capture(typ.NamedTuple):
    command    : str
    exit_status: int
    runtime    : float
    lines      : typ.List[CapturedLine]


class BlockError(Exception):

    block           : parse.Block
    include_contents: typ.List[str]

    def __init__(
        self, msg: str, block: parse.Block, include_contents: typ.Optional[typ.List[str]] = None
    ) -> None:
        self.block            = block
        self.include_contents = include_contents or []
        loc                   = parse.location(block).strip()
        super().__init__(f"{loc} - " + msg)


def get_directive(
    block: parse.Block, name: str, missing_ok: bool = True, many_ok: bool = True
) -> typ.Optional[parse.Directive]:
    found: typ.List[parse.Directive] = []
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


def has_directive(block: parse.Block, name: str) -> bool:
    return get_directive(block, name, missing_ok=True) is not None


def iter_directives(block: parse.Block, name: str) -> typ.Iterable[parse.Directive]:
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
# def _parse_constants(build_ctx: parse.Context) -> typ.List[ConstItem]:
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
# def _expand_constants(build_ctx: parse.Context) -> parse.Context:
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
#                 new_elements[block.elem_index] = parse.MarkdownElement(
#                     elem.md_path, elem.first_line, elem.elem_index, elem.md_type, new_content, None
#                 )
#
#             new_md_file = parse.MarkdownFile(md_file.md_path, new_elements)
#             new_md_files.append(new_md_file)
#
#         build_ctx = parse.Context(new_md_files)
#
#     return build_ctx


# # TODO (mb 2020-06-01): maybe use for lp_include_match
# def find_include(block_contents: typ.List[str], include_directive: parse.Directive) -> typ.Optional[str]:
#     query = include_directive.value.strip()
#     for content in block_contents:
#         if query in content:
#             return content
#     return None


def _indented_include(content: str, raw_text: str, include_val: str) -> str:
    unindented = raw_text.lstrip()
    indent     = raw_text[: -len(unindented)]
    if indent:
        include_val = "\n".join(indent + line for line in include_val.splitlines())
    return content.replace(raw_text, include_val)


# TODO: this should be part of the parsing of all directives
def _parse_prefix(directive: parse.Directive) -> str:
    val = directive.value.strip()
    if val.startswith("'") and val.endswith("'"):
        val = val[1:-1]
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return val


BlockId    = str
BlockIds   = typ.List[BlockId]
BlocksById = typ.Dict[BlockId, typ.List[parse.Block]]
IncludeMap = typ.Dict[BlockId, typ.Set[BlockId]]


def _namespaced_lp_id(block: parse.Block, lp_id: BlockId) -> BlockId:
    if "." in lp_id:
        return lp_id.strip()
    else:
        return block.namespace + "." + lp_id.strip()


def _build_include_map(blocks_by_id: BlocksById) -> IncludeMap:
    include_map: IncludeMap = {}
    for lp_def_id, blocks in blocks_by_id.items():
        for block in blocks:
            for lp_include in iter_directives(block, 'lp_include'):
                lp_included_ids = [
                    _namespaced_lp_id(block, _lp_id) for _lp_id in lp_include.value.split(",")
                ]
                for included_id in lp_included_ids:
                    if included_id not in blocks_by_id:
                        errmsg = f"Unknown block id: {included_id}"
                        raise BlockError(errmsg, block)
                    elif lp_def_id in include_map:
                        include_map[lp_def_id].add(included_id)
                    else:
                        include_map[lp_def_id] = {included_id}

    logger.debug("include map")
    for lp_id, including_ids in sorted(include_map.items()):
        logger.debug("   {lp_id} -> {including_ids}")

    return include_map


def _get_include_cycle(
    lp_id      : BlockId,
    include_map: IncludeMap,
    root_id    : BlockId,
    depth      : int = 0,
) -> typ.List[str]:
    if lp_id in include_map:
        include_ids = include_map[lp_id]
        if root_id in include_ids:
            return [lp_id]

        for _include_id in include_ids:
            cycle_ids = _get_include_cycle(_include_id, include_map, root_id, depth + 1)
            if cycle_ids:
                return [lp_id] + cycle_ids

    return []


def _err_on_include_cycle(
    block       : parse.Block,
    lp_id       : BlockId,
    blocks_by_id: BlocksById,
    include_map : IncludeMap,
    root_id     : BlockId,
) -> None:
    cycle_ids = _get_include_cycle(lp_id, include_map, root_id=root_id)
    if not cycle_ids:
        return

    cycle_ids = [root_id] + cycle_ids
    for cycle_id in cycle_ids:
        cycle_block = blocks_by_id[cycle_id][0]
        loc         = parse.location(cycle_block).strip()
        logger.warning(f"{loc} - {cycle_id} (trace for include cycle)")

    path   = " -> ".join(f"'{cycle_id}'" for cycle_id in cycle_ids)
    errmsg = f"Include cycle {path}"
    raise BlockError(errmsg, block)


def _expand_directives(blocks_by_id: BlocksById, md_file: parse.MarkdownFile) -> parse.MarkdownFile:
    new_md_file = md_file.copy()
    include_map = _build_include_map(blocks_by_id)

    is_done = False
    while not is_done:
        is_done = True
        blocks  = list(new_md_file.blocks)
        for block in blocks:
            lp_def = get_directive(block, 'lp_def', missing_ok=True, many_ok=False)
            if lp_def is None:
                lp_def_id = None
            else:
                lp_def_id = _namespaced_lp_id(block, lp_def.value)

            new_content = block.content
            for lp_include in iter_directives(block, 'lp_include'):
                content_chunks: typ.List[str] = []
                lp_include_ids = [
                    _namespaced_lp_id(block, lp_id) for lp_id in lp_include.value.split(",")
                ]

                for lp_id in lp_include_ids:
                    _err_on_include_cycle(
                        block, lp_id, blocks_by_id, include_map, root_id=lp_def_id
                    )

                    content_chunks.extend(
                        [b.includable_content + "\n" for b in blocks_by_id[lp_id]]
                    )

                include_content = "".join(content_chunks)
                new_content     = _indented_include(new_content, lp_include.raw_text, include_content)

            if new_content != block.content:
                is_done = False  # may need more recursive includes

                elem = new_md_file.elements[block.elem_index]
                new_md_file.elements[block.elem_index] = parse.MarkdownElement(
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
    # NOTE (mb 2020-05-31): block ids are always absulute/fully qualified
    blocks_by_id = _get_blocks_by_id(md_files)

    # pass 2. expand lp_include directives in file
    for md_file in md_files:
        yield _expand_directives(blocks_by_id, md_file)


def _iter_block_errors(orig_ctx: parse.Context, build_ctx: parse.Context) -> typ.Iterable[str]:
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

                    rel_line_no += 1

                line_no = elem.first_line + rel_line_no
                yield f"Error processing {md_file.md_path}"
                yield f"Could not expend '{directive.raw_text}' on line {line_no}"


def _dump_files(build_ctx: parse.Context) -> None:
    for md_file in build_ctx.files:
        for block in md_file.blocks:
            file_directive = get_directive(block, 'lp_file')
            if file_directive is None:
                continue

            path = pl.Path(file_directive.value)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open(mode="w", encoding="utf-8") as fobj:
                fobj.write(block.includable_content)


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


def _parse_out_fmt(block: parse.Block, directive_name: str, default_fmt: str) -> str:
    color_directive = get_directive(block, directive_name)
    if color_directive is None:
        return default_fmt

    color_val = color_directive.value.strip()
    if color_val == 'none':
        return default_fmt
    elif color_val in TERM_COLORS:
        color_code = TERM_COLORS[color_val]
        return "\u001b[" + color_code + "m{0}\u001b[0m"
    elif COLOR_CODE_RE.match(color_val):
        return "\u001b[" + color_val + "m{0}\u001b[0m"
    else:
        valid_codes = ", ".join(sorted(TERM_COLORS.keys()))
        err_msg     = (
            f"Invalid {color_directive.name}: {color_val}. "
            f"Must be 'none', {valid_codes} or a valid color code."
        )
        raise Exception(err_msg)


def _parse_session_block_options(block: parse.Block) -> typ.Optional[SessionBlockOptions]:
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

    default_err_fmt = "\u001b[" + TERM_COLORS['red'] + "m{0}\u001b[0m"

    out_fmt = _parse_out_fmt(block, 'lp_out_color', "{0}")
    err_fmt = _parse_out_fmt(block, 'lp_err_color', default_err_fmt)

    out_prefix = get_directive(block, 'lp_out_prefix')
    err_prefix = get_directive(block, 'lp_err_prefix')

    info_directive = get_directive(block, 'lp_proc_info')
    if info_directive is None:
        info_fmt = "# exit: {exit}"
    else:
        info_fmt = info_directive.value

    expect = get_directive(block, 'lp_expect')

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
        out_fmt=out_fmt,
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
    for captured_line in capture.lines:
        if captured_line.is_err:
            if opts.err_prefix:
                line_val = opts.err_prefix + captured_line.line
            else:
                line_val = captured_line.line
        else:
            if opts.out_prefix:
                line_val = opts.out_prefix + captured_line.line
            else:
                line_val = captured_line.line
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


def _process_command_block(
    block: parse.Block, opts: SessionBlockOptions, exitfirst: bool = False
) -> Capture:
    command = opts.command
    if command is None:
        raise TypeError(f"Must be str, not {type(command)}")

    logger.info(f"  {opts.directive} {command}")

    isession = session.InteractiveSession(command)

    if opts.is_stdin_writable:
        stdin_lines = block.inner_content.splitlines(opts.keepends)
    else:
        stdin_lines = []

    if opts.is_debug:
        for i, line in enumerate(stdin_lines):
            prefix = opts.debug_prefix.format(lineno=i + 1)
            sys.stderr.write(prefix + line.rstrip() + "\n")

    try:
        for line in stdin_lines:
            isession.send(line, delay=opts.input_delay)
        exit_status = isession.wait(timeout=opts.timeout)
    except Exception as ex:
        logger.error(f"Error processing '{command}': {ex}")
        sys.stdout.write("".join(isession.iter_stdout()))
        sys.stderr.write("".join(isession.iter_stderr()))
        raise

    runtime_ms = isession.runtime * 1000

    if exit_status == opts.expected_exit_status:
        exit_info = f"{exit_status:>3}       "
    else:
        exit_info = f"{exit_status:>3} != {opts.expected_exit_status:<3}"

    lines   = list(isession.iter_lines())
    capture = Capture(command, exit_status, isession.runtime, lines)

    logger.info(f"  {opts.directive}  exit: {exit_info}  time: {runtime_ms:9.3f}ms")
    if exitfirst and exit_status != opts.expected_exit_status:
        output = _parse_capture_output(capture, opts)
        sys.stderr.write(output)
        logger.error(f"Line {block.first_line} of {block.md_path} - Error executing block")
        raise SystemExit(1)
    else:
        # TODO: limit output using lp_max_bytes and lp_max_lines
        # TODO: output escaping/fence style change and errors
        return capture


def _process_blocks(
    md_file: parse.MarkdownFile, exitfirst: bool = False
) -> typ.Iterable[parse.MarkdownElement]:
    captures_by_elem_index: typ.Dict[int, Capture] = {}

    old_capture_index = -1

    for block in md_file.blocks:
        opts = _parse_session_block_options(block)
        if opts is None:
            continue

        if opts.command:
            capture           = _process_command_block(block, opts, exitfirst=exitfirst)
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
                updated_elem = parse.MarkdownElement(
                    elem.md_path,
                    elem.first_line,
                    elem.elem_index,
                    elem.md_type,
                    new_content,
                    None,
                )
                yield updated_elem


def build(
    orig_ctx: parse.Context, exitfirst: bool = False, in_place_update: bool = False
) -> parse.Context:
    # TODO: Immutable datastructures
    #   parse.Context, parse.MarkdownFile
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

    build_ctx = parse.Context(expanded_files)

    # phase 3. validate blocks
    error_messages = list(_iter_block_errors(orig_ctx, build_ctx))
    for error_msg in error_messages:
        logger.error(error_msg)

    if error_messages:
        raise SystemExit(1)

    # phase 4. write files with expanded blocks
    #   This has to happen before sub-processes, as those
    #   may use the newly created files.
    _dump_files(build_ctx)

    # TODO: Dependency graph of some kind so we can order
    #   process execution.
    doc_ctx = orig_ctx.copy()

    # phase 5. run sub-processes
    for file_idx, (orig_md_file, md_file) in enumerate(zip(orig_ctx.files, build_ctx.files)):
        updated_elements = list(_process_blocks(md_file, exitfirst=exitfirst))

        # phase 6. rewrite output blocks
        if any(updated_elements):
            new_elements = list(orig_md_file.elements)
            for elem in updated_elements:
                orig_elem = orig_md_file.elements[elem.elem_index]
                assert 'lp_out' in orig_elem.content or 'lp_run' in orig_elem.content
                new_elements[elem.elem_index] = elem

            new_md_file = parse.MarkdownFile(md_file.md_path, new_elements)
            if in_place_update:
                new_file_content = str(new_md_file)
                with new_md_file.md_path.open(mode="w", encoding="utf-8") as fobj:
                    fobj.write(new_file_content)

            logger.info(f"Updated {new_md_file.md_path}")
            doc_ctx.files[file_idx] = new_md_file

    duration = time.time() - build_start
    logger.info(f"Build finished after {duration:9.3f}sec")

    return doc_ctx
