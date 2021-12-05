# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import os
import re
import sys
import json
import time
import typing as typ
import fnmatch
import logging
import tempfile
import collections
from pathlib import Path
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor

from . import parse
from . import session
from . import common_types as ct
from . import capture_cache

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

DEFUALT_TIMEOUT = 9.0

Chapters = typ.Iterable[parse.Chapter]

# The expanded files are no different in structure/datatype, it's just
# that directives such as dep and include are expanded.
ExpandedChapter  = parse.Chapter
ExpandedChapters = typ.Iterator[ExpandedChapter]


class BlockError(Exception):

    block           : ct.Block
    include_contents: list[str]

    def __init__(self, msg: str, block: ct.Block, include_contents: typ.Optional[list[str]] = None) -> None:
        self.block            = block
        self.include_contents = include_contents or []

        loc = parse.location(block).strip()
        super().__init__(f"{loc} - " + msg)


def get_directive(
    block: ct.Block, name: str, missing_ok: bool = True, many_ok: bool = True
) -> typ.Optional[ct.Directive]:
    found: list[ct.Directive] = []
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
    elif len(found) > 1 and not many_ok:
        errmsg = f"Block with multiple '{name}'"
        raise BlockError(errmsg, block)
    else:
        return found[0]


def iter_directives(block: ct.Block, *directive_names) -> typ.Iterable[ct.Directive]:
    _names = set(directive_names)
    for directive in block.directives:
        if directive.name in _names:
            yield directive


def _match_indent(directive_text: str, include_val: str) -> str:
    unindented = directive_text.lstrip()
    indent     = directive_text[: -len(unindented)].strip("\n")
    if indent:
        return "\n".join(indent + line for line in include_val.splitlines())
    else:
        return include_val


def _indented_include(
    content       : str,
    directive_text: str,
    include_val   : str,
    is_dep        : bool = True,
) -> str:
    if is_dep:
        # dependencies are only included once (at the first occurance of a dep directive)
        return content.replace(directive_text, include_val, 1).replace(directive_text, "")
    else:
        return content.replace(directive_text, include_val)


# TODO: Maybe use this to parse all directive values, and thereby enable quoting.
def _parse_directive_val(directive: ct.Directive) -> str:
    val = directive.value.strip()
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    elif val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    else:
        return val


BlockId       = str
ScopedBlockId = str

BlockIds       = list[BlockId]
BlockListBySid = dict[ScopedBlockId, list[ct.Block     ]]
DependencyMap  = dict[ScopedBlockId, list[ScopedBlockId]]


def _namespaced_lp_id(block: ct.Block, lp_id: BlockId) -> ScopedBlockId:
    if "." in lp_id:
        return lp_id.strip()
    else:
        return block.namespace + "." + lp_id.strip()


def _iter_directive_sids(block: ct.Block, *directive_names) -> typ.Iterable[ScopedBlockId]:
    for directive in iter_directives(block, *directive_names):
        for dep_id in directive.value.split(","):
            yield _namespaced_lp_id(block, dep_id)


def _resolve_dep_sids(
    raw_dep_sid: ScopedBlockId, blocks_by_sid: BlockListBySid
) -> typ.Iterable[ScopedBlockId]:
    if raw_dep_sid in blocks_by_sid:
        yield raw_dep_sid
    elif "*" in raw_dep_sid:
        dep_sid_re = re.compile(fnmatch.translate(raw_dep_sid))
        for maybe_dep_sid in blocks_by_sid:
            if dep_sid_re.match(maybe_dep_sid):
                yield maybe_dep_sid


def _build_dep_map(blocks_by_sid: BlockListBySid) -> DependencyMap:
    """Build a mapping of block_ids to the Blocks they depend on.

    The mapped block_ids (keys) are only the direct (non-recursive) dependencies.
    """
    dep_map: DependencyMap = {}
    for def_id, blocks in blocks_by_sid.items():
        for block in blocks:
            for raw_dep_sid in _iter_directive_sids(block, 'dep'):
                dep_sids = list(_resolve_dep_sids(raw_dep_sid, blocks_by_sid))
                if not any(dep_sids):
                    # TODO (mb 2021-07-18): pylev for better message:
                    #   "Maybe you meant {closest_sids}"
                    raise BlockError(f"Invalid block id: {raw_dep_sid}", block)

                for dep_sid in dep_sids:
                    if def_id in dep_map:
                        dep_map[def_id].append(dep_sid)
                    else:
                        dep_map[def_id] = [dep_sid]

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("include map")
        for lp_id, dep_ids in sorted(dep_map.items()):
            dep_ids_str = ", ".join(sorted(dep_ids))
            logger.debug(f" deps  {lp_id:<20}: {dep_ids_str}")

    return dep_map


def _get_dep_cycle(
    lp_id  : BlockId,
    dep_map: DependencyMap,
    root_id: BlockId,
    depth  : int = 0,
) -> list[str]:
    if lp_id in dep_map:
        dep_sids = dep_map[lp_id]
        if root_id in dep_sids:
            return [lp_id]

        for _dep_sid in dep_sids:
            cycle_ids = _get_dep_cycle(_dep_sid, dep_map, root_id, depth + 1)
            if cycle_ids:
                return [lp_id] + cycle_ids

    return []


def _err_on_include_cycle(
    block        : ct.Block,
    lp_id        : BlockId,
    blocks_by_sid: BlockListBySid,
    dep_map      : DependencyMap,
    root_id      : BlockId,
) -> None:
    cycle_ids = _get_dep_cycle(lp_id, dep_map, root_id=root_id)
    if not cycle_ids:
        return

    cycle_ids = [root_id] + cycle_ids
    for cycle_id in cycle_ids:
        cycle_block = blocks_by_sid[cycle_id][0]
        loc         = parse.location(cycle_block).strip()
        logger.warning(f"{loc} - {cycle_id} (trace for include cycle)")

    path   = " -> ".join(f"'{cycle_id}'" for cycle_id in cycle_ids)
    errmsg = f"dep/include cycle {path}"
    raise BlockError(errmsg, block)


def _expand_block_content(
    blocks_by_sid: BlockListBySid,
    block        : ct.Block,
    added_deps   : set[str],
    dep_map      : DependencyMap,
    keep_fence   : bool,
    lvl          : int = 1,
) -> tuple[str, set[Path]]:
    # NOTE (mb 2020-12-20): Depth first expansion of content.
    #   This ensures that the first occurance of an dep
    #   directive is expanded at the earliest possible point
    #   even if it is a recursive dep.
    def_ = get_directive(block, 'def', missing_ok=True, many_ok=False)

    new_md_paths = {block.md_path}

    if keep_fence:
        new_content = block.content
    else:
        new_content = block.includable_content + "\n"

    for directive in iter_directives(block, 'dep', 'include'):
        is_dep = directive.name == 'dep'

        dep_contents: list[str] = []
        for raw_dep_sid in directive.value.split(","):
            raw_dep_sid = _namespaced_lp_id(block, raw_dep_sid)

            dep_sids = list(_resolve_dep_sids(raw_dep_sid, blocks_by_sid))
            if not dep_sids:
                # TODO (mb 2021-07-18): pylev for better message:
                #   "Maybe you meant {closest_sids}"
                raise BlockError(f"Invalid block id: {raw_dep_sid}", block)

            for dep_sid in dep_sids:
                if def_:
                    def_id = _namespaced_lp_id(block, def_.value)
                    _err_on_include_cycle(block, dep_sid, blocks_by_sid, dep_map, root_id=def_id)

                if is_dep:
                    if dep_sid in added_deps:
                        # skip already included dependencies
                        continue
                    else:
                        added_deps.add(dep_sid)

                for dep_block in blocks_by_sid[dep_sid]:
                    dep_content, dep_md_paths = _expand_block_content(
                        blocks_by_sid,
                        dep_block,
                        added_deps,
                        dep_map,
                        keep_fence=False,
                        lvl=lvl + 1,
                    )
                    dep_content = _match_indent(directive.raw_text, dep_content)
                    dep_contents.append(dep_content)
                    new_md_paths.update(dep_md_paths)

        include_content = "".join(dep_contents)
        dep_text        = directive.raw_text.lstrip("\n")
        new_content     = _indented_include(new_content, dep_text, include_content, is_dep=is_dep)

    return (new_content, new_md_paths)


def _expand_directives(blocks_by_sid: BlockListBySid, chapter: parse.Chapter) -> parse.Chapter:
    new_chapter = chapter.copy()
    dep_map     = _build_dep_map(blocks_by_sid)

    for block in list(new_chapter.iter_blocks()):
        added_deps: set[str] = set()
        new_content, new_md_paths = _expand_block_content(
            blocks_by_sid, block, added_deps, dep_map, keep_fence=True
        )
        if new_content != block.content:
            elements = new_chapter.elements[block.md_path]
            elem     = elements[block.elem_index]

            elements[block.elem_index] = parse.MarkdownElement(
                elem.md_path,
                elem.first_line,
                elem.elem_index,
                elem.md_type,
                new_content,
                None,
                new_md_paths | {elem.md_path},
            )

    return new_chapter


def _get_blocks_by_id(chapters: Chapters) -> BlockListBySid:
    blocks_by_sid: BlockListBySid = {}

    for chapter in chapters:
        for block in chapter.iter_blocks():
            lp_def = get_directive(block, 'def', missing_ok=True, many_ok=False)
            if lp_def:
                lp_def_id = lp_def.value
                if "." in lp_def_id and not lp_def_id.startswith(block.namespace + "."):
                    errmsg = f"Invalid block id: {lp_def_id} for namespace {block.namespace}"
                    raise BlockError(errmsg, block)

                block_sid = _namespaced_lp_id(block, lp_def_id)
                if block_sid in blocks_by_sid:
                    prev_block = blocks_by_sid[block_sid][0]
                    prev_loc   = parse.location(prev_block).strip()
                    errmsg     = f"Block already defined: {lp_def_id} at {prev_loc}"
                    raise BlockError(errmsg, block)

                blocks_by_sid[block_sid] = [block]

    # NOTE (mb 2021-08-19): The amend directive has been removed as it
    #   it would lead to confusion. When a reader wants to understand a block,
    #   it will be more easy for them if they need not worry about any other
    #   block in the project. They need only consider the block they
    #   see before them and they can see all contents either directly or
    #   as explicitly named expansions in the form of a dep/include
    #   directive.
    #
    # for chapter in chapters:
    #     for block in chapter.iter_blocks():
    #         for lp_amend in iter_directives(block, 'amend'):
    #             lp_amend_sid = _namespaced_lp_id(block, lp_amend.value)
    #             if lp_amend_sid in blocks_by_sid:
    #                 blocks_by_sid[lp_amend_sid].append(block)
    #             else:
    #                 errmsg = f"Unknown block id: {lp_amend_sid}"
    #                 raise BlockError(errmsg, block)

    return blocks_by_sid


def _iter_expanded_chapters(chapters: Chapters) -> ExpandedChapters:
    # NOTE (mb 2020-05-24): To do the expansion, we have to first
    #   build a graph so that we can resolve blocks for each dep/include.

    # pass 1. collect all blocks (globally) with def directives
    # NOTE (mb 2020-05-31): block ids are always absulute/fully qualified
    blocks_by_sid = _get_blocks_by_id(chapters)

    # pass 2. expand dep directives in markdown files
    for chapter in chapters:
        yield _expand_directives(blocks_by_sid, chapter)


def _iter_block_errors(parse_ctx: parse.Context, build_ctx: parse.Context) -> typ.Iterable[str]:
    """Validate that expansion worked correctly."""
    # NOTE: the main purpose of the parse_ctx is to produce
    #   better error messages. It allows us to point at the
    #   original block, whereas the build_ctx has been
    #   modified and line numbers no longer correspond to
    #   the original file.
    assert len(parse_ctx.chapters) == len(build_ctx.chapters)
    for orig_chapter, chapter in zip(parse_ctx.chapters, build_ctx.chapters):
        assert orig_chapter.md_paths == chapter.md_paths
        for md_path in orig_chapter.md_paths:
            assert len(orig_chapter.elements[md_path]) == len(chapter.elements[md_path])

        for block in chapter.iter_blocks():
            orig_elem = orig_chapter.elements[block.md_path][block.elem_index]
            for directive in block.directives:
                if directive.name in ('dep', 'include'):
                    elem = chapter.elements[block.md_path][block.elem_index]

                    rel_line_no = 0
                    for line in orig_elem.content.splitlines():
                        if directive.raw_text in line:
                            break

                        rel_line_no += 1

                    # TODO (mb 2020-12-30): These line numbers appear to be wrong,
                    #   I think for recursive dep directives in particular.
                    line_no       = elem.first_line + rel_line_no
                    raw_text_repr = repr(directive.raw_text.strip("\n"))
                    yield (
                        f"Error processing {block.md_path} on line {line_no}: "
                        + f"Could not expand {raw_text_repr}"
                    )


def _dump_files(build_ctx: parse.Context) -> None:
    # NOTE (mb 2021-08-27): We use the most recent md_mtime of all
    #   files, as they might contain a block that is
    #   dep(ed)/includ(ed) by a 'file' block. This is conservative and
    #   we could improve this if we would keep track of the input md
    #   files used to create an output file.
    md_mtimes = {
        md_path: md_path.stat().st_mtime for chapter in build_ctx.chapters for md_path in chapter.md_paths
    }
    md_mtime = max(md_mtimes.values())

    for chapter in build_ctx.chapters:
        for block in chapter.iter_blocks():
            file_directive = get_directive(block, 'file')
            if file_directive is None:
                continue

            md_elem  = chapter.elements[block.md_path][block.elem_index]
            md_mtime = max(md_mtimes[md_path] for md_path in md_elem.src_md_paths)

            file_path = Path(file_directive.value)

            # see if we can skip updating the output file
            if file_path.exists() and md_mtime <= file_path.stat().st_mtime:
                continue

            new_content_data = block.includable_content.encode("utf-8")
            if file_path.exists():
                with file_path.open(mode="rb") as fobj:
                    old_content_data = fobj.read()

                if old_content_data == new_content_data:
                    continue

            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open(mode="wb") as fobj:
                fobj.write(new_content_data)


def _parse_out_fmt(block: ct.Block, directive_name: str, default_fmt: str) -> str:
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


def _get_default_command(block: ct.Block) -> typ.Optional[str]:
    # TODO (mb 2020-12-17): Allow override/configuration
    lang = block.info_string.strip()
    if lang == 'python':
        return "python3"
    elif lang in ("bash", "shell"):
        return "bash"
    elif lang == 'sh':
        return "sh"
    else:
        return None


OptionValue = typ.Union[bool, str, int, float, None]


def _parse_option(
    block      : ct.Block,
    options    : dict[str, OptionValue],
    option_name: str,
    default_val: OptionValue,
) -> None:
    option_directive = get_directive(block, option_name)
    if option_directive:
        options[option_name] = json.loads(option_directive.value)
    elif option_name not in options:
        options[option_name] = default_val


def _parse_format_options(block: ct.Block) -> ct.FormatOptions:
    default_err_fmt = "\u001b[" + TERM_COLORS['red'] + "m{0}\u001b[0m"

    out_fmt = _parse_out_fmt(block, 'out_color', "{0}")
    err_fmt = _parse_out_fmt(block, 'err_color', default_err_fmt)

    out_prefix = get_directive(block, 'out_prefix')
    err_prefix = get_directive(block, 'err_prefix')

    info_directive = get_directive(block, 'proc_info')
    if info_directive is None:
        info_fmt = "# exit: {exit}"
    else:
        info_fmt = info_directive.value

    return ct.FormatOptions(
        out=out_fmt,
        err=err_fmt,
        info=info_fmt,
        out_prefix=_parse_directive_val(out_prefix) if out_prefix else "",
        err_prefix=_parse_directive_val(err_prefix) if err_prefix else "! ",
    )


def _parse_session_block_options(block: ct.Block) -> typ.Optional[ct.SessionBlockOptions]:
    exec_directive = get_directive(block, 'exec')
    run_directive  = get_directive(block, 'run')
    out_directive  = get_directive(block, 'out')

    command: typ.Optional[str]

    if exec_directive:
        directive = 'exec'
        command   = exec_directive.value or _get_default_command(block)
    elif run_directive:
        directive = 'run'
        command   = run_directive.value
    elif out_directive:
        directive = 'out'
        command   = None
    else:
        return None

    _provides = get_directive(block, 'def')
    _requires = get_directive(block, 'requires')

    provides_id : typ.Optional[str] = None
    if _provides:
        provides_id = _provides.value.strip()
        provides_id = _namespaced_lp_id(block, provides_id)

    if _requires:
        requires_ids = {_namespaced_lp_id(block, req_id) for req_id in _requires.value.split(",")}
    else:
        requires_ids = set()

    _options = get_directive(block, 'options')
    options  = json.loads(_options.value) if _options else {}

    _parse_option(block, options, 'timeout'      , DEFUALT_TIMEOUT)
    _parse_option(block, options, 'expect'       , 0)
    _parse_option(block, options, 'input_delay'  , 0.0)
    _parse_option(block, options, 'debug'        , False)
    _parse_option(block, options, 'deterministic', True)
    _parse_option(block, options, 'keepends'     , True)
    _parse_option(block, options, 'capture_file' , None)

    return ct.SessionBlockOptions(
        command=command,
        directive=directive,
        provides_id=provides_id,
        requires_ids=requires_ids,
        timeout=options['timeout'],
        input_delay=options['input_delay'],
        expected_exit_status=options['expect'],
        capture_file=None if options['capture_file'] is None else Path(options['capture_file']),
        is_stdin_writable=directive in ('exec', 'run'),
        is_debug=options['debug'],
        keepends=options['keepends'],
        fmt=_parse_format_options(block),
    )


def _parse_capture_output(capture: session.Capture, opts: ct.SessionBlockOptions) -> str:
    # TODO: coloring
    # if "\u001b" in capture.stderr:
    #     stderr = capture.stderr
    # elif stderr.strip():
    #     stderr = opts.fmt.err.format(capture.stderr)

    output_lines = []
    for captured_line in capture.lines:
        if captured_line.is_err:
            if opts.fmt.err_prefix:
                line_val = opts.fmt.err_prefix + captured_line.line
            else:
                line_val = captured_line.line
        else:
            if opts.fmt.out_prefix:
                line_val = opts.fmt.out_prefix + captured_line.line
            else:
                line_val = captured_line.line
        output_lines.append(line_val.rstrip())

    output = "\n".join(output_lines)

    if not output.endswith("\n"):
        output += "\n"

    if opts.fmt.info != 'none':
        output += opts.fmt.info.format(
            **{
                'exit'   : capture.exit_status,
                'time'   : capture.runtime,
                'time_ms': capture.runtime * 1000,
            }
        )
        output = output.strip("\r\n")

        # make sure the block closing backticks are
        # on their own line
        if not output.endswith("\n"):
            output += "\n"

    return output


class BlockExecutionError(Exception):
    pass


class BlockTimeoutError(BlockExecutionError):
    pass


TEMPFILE_PATTERN = r"<TEMPFILE([\.\w]+)>"

TEMPFILE_RE = re.compile(TEMPFILE_PATTERN)


def _postproc_failed_block(
    block      : ct.Block,
    opts       : ct.SessionBlockOptions,
    stdin_lines: list[str],
    capture    : session.Capture,
) -> None:
    rjust     = len(str(len(stdin_lines)))
    err_lines = []
    for i, line in enumerate(stdin_lines):
        prefix = f"In [{i+1:>{rjust}}]: "
        err_lines.append(prefix + line)
    sys.stderr.write("".join(err_lines) + "\n")
    sys.stderr.flush()

    output       = _parse_capture_output(capture, opts)
    output_lines = output.splitlines()
    rjust        = len(str(len(output_lines)))
    for i, line in enumerate(output_lines):
        prefix = f"Out [{i+1:>{rjust}}]: "
        sys.stderr.write(prefix + line + "\n")
    logger.error(f"Line {block.first_line} of {block.md_path} - Error executing block")


Tempfile = typ.Optional[typ.Any]
Command  = str


def _init_isession(opts: ct.SessionBlockOptions, command: Command) -> session.InteractiveSession:
    if opts.is_debug:
        return session.DebugInteractiveSession(command)
    else:
        return session.InteractiveSession(command)


def _init_command(opts: ct.SessionBlockOptions) -> tuple[Tempfile, Command]:
    # pylint: disable=consider-using-with; see later: os.unlink(tmp.name)
    command = opts.command
    if command is None:
        raise TypeError("Must be str but was None")

    tempfile_placeholder = TEMPFILE_RE.search(command)
    if tempfile_placeholder:
        placeholder = tempfile_placeholder.group(0)
        suffix      = tempfile_placeholder.group(1).split(".", 1)[-1]
        tmp         = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        command     = command.replace(placeholder, tmp.name)
        return (tmp, command)
    else:
        return (None, command)


def _process_isession(
    block      : ct.Block,
    opts       : ct.SessionBlockOptions,
    command    : str,
    stdin_lines: list[str],
) -> session.Capture:
    _cmd   = command if len(command) < 35 else (command[:35] + "...")
    logmsg = f"Line {block.first_line:>5} of {block.md_path} - {opts.directive} {_cmd}"
    logger.info(logmsg)

    isession = _init_isession(opts, command)

    for line in stdin_lines:
        isession.send(line, delay=opts.input_delay)

    try:
        exit_status = isession.wait(timeout=opts.timeout)
    except Exception as ex:
        logger.error(f"Error processing '{command}': {ex}")
        sys.stdout.write("".join(isession.iter_stdout()))
        sys.stderr.write("".join(isession.iter_stderr()))
        raise

    if exit_status == opts.expected_exit_status:
        exit_info = f"{exit_status}"
    else:
        exit_info = f"{exit_status} != {opts.expected_exit_status}"

    _cmd   = command if len(command) < 10 else (command[:10] + "...")
    logmsg = f"Line {block.first_line:>5} of {block.md_path} - {opts.directive} {_cmd}"

    runtime_ms = round(isession.runtime * 1000)
    if runtime_ms < 500:
        logger.debug(f"{logmsg:<55} time: {runtime_ms:>6}ms  exit: {exit_info}")
    else:
        logger.info(f"{logmsg:<55} time: {runtime_ms:>6}ms  exit: {exit_info}")

    lines   = isession.output_lines()
    capture = session.Capture(command, exit_status, isession.runtime, lines)

    if exit_status == opts.expected_exit_status:
        # TODO: limit output using max_bytes and max_lines
        # TODO: output escaping/fence style change and errors
        return capture
    else:
        _postproc_failed_block(block, opts, stdin_lines, capture)
        if exit_status == -15:
            raise BlockTimeoutError()
        else:
            raise BlockExecutionError()


def _process_command_block(
    block: ct.Block,
    opts : ct.SessionBlockOptions,
) -> session.Capture:
    tmp, command = _init_command(opts)

    if opts.is_stdin_writable:
        stdin_lines = block.includable_content.splitlines(opts.keepends)
    else:
        stdin_lines = []

    if tmp:
        tmp_text = "".join(stdin_lines)
        tmp_data = tmp_text.encode("utf-8")
        tmp.file.write(tmp_data)
        stdin_lines = []

    if opts.directive != 'exec':
        stdin_lines = []

    try:
        return _process_isession(block, opts, command, stdin_lines)
    finally:
        if tmp:
            os.unlink(tmp.name)


def _iter_task_blocks(chapter: parse.Chapter) -> typ.Iterable[ct.TaskBlockOpts]:
    for block in chapter.iter_blocks():
        opts = _parse_session_block_options(block)
        if opts:
            yield ct.TaskBlockOpts(block, opts)


def _iter_block_tasks(chapter: parse.Chapter) -> typ.Iterable[ct.BlockTask]:
    taskblockopt_items = list(_iter_task_blocks(chapter))
    for i, (block, opts) in enumerate(taskblockopt_items):
        capture_index = -1

        if i + 1 < len(taskblockopt_items):
            next_block, next_opts = taskblockopt_items[i + 1]
            if next_opts.directive == 'out':
                capture_index = next_block.elem_index

        command = opts.command
        if command:
            if opts.directive == 'run':
                capture_index = block.elem_index

            yield ct.BlockTask(block.md_path, command, block, opts, capture_index)


ChapNum = str


class BuildOptions(typ.NamedTuple):

    exitfirst      : bool
    in_place_update: bool
    cache_enabled  : bool
    concurrency    : int


class Runner:

    orig_chapters : Chapters
    build_chapters: Chapters
    opts          : BuildOptions

    elements_by_chapnum: dict[str, dict[Path, list[parse.MarkdownElement]]]

    _chapter_by_path: dict[Path, parse.Chapter]
    _all_tasks      : list[ct.BlockTask]
    _task_results   : list[tuple[ct.BlockTask, session.Capture]]
    _cached_tasks   : list[ct.BlockTask]

    _cache: capture_cache.ResultCache

    def __init__(
        self,
        orig_chapters : Chapters,
        build_chapters: Chapters,
        opts          : BuildOptions,
    ) -> None:
        self.orig_chapters  = orig_chapters
        self.build_chapters = build_chapters
        self.opts           = opts

        self.elements_by_chapnum = {}

        # TODO (mb 2021-03-04): _task_results and _cache are somewhat redundant.
        #   It might be possible/reasonable to always rely on the _cache to lookup
        #   the capture of a task, even one that was just executed.

        self._chapter_by_path = {}
        self._all_tasks       = []
        self._task_results    = []
        self._cached_tasks    = []

        if self.opts.cache_enabled:
            self._cache = capture_cache.LocalResultCache(self.orig_chapters)
        else:
            self._cache = capture_cache.DummyCache()

        for chapter in self.build_chapters:
            for md_path in chapter.md_paths:
                self._chapter_by_path[md_path] = chapter
            self._all_tasks.extend(_iter_block_tasks(chapter))

    def _run_task(self, task: ct.BlockTask) -> None:
        capture_file = task.opts.capture_file

        if not self.opts.cache_enabled:
            cached_capture = None
        elif capture_file and capture_file.exists():
            with capture_file.open(mode='rb') as fobj:
                cached_capture = session.loads_capture(fobj.read())
        else:
            cached_capture = self._cache.get_capture(task)

        if cached_capture:
            self._cached_tasks.append(task)
            capture = cached_capture
        else:
            capture = _process_command_block(task.block, task.opts)
            self._cache.update(task, capture)
            if capture_file:
                if not capture_file.parent.exists():
                    capture_file.parent.mkdir(parents=True, exist_ok=True)

                with capture_file.open(mode='wb') as fobj:
                    capture_data = session.dumps_capture(capture, pretty=True)
                    fobj.write(capture_data)

        if task.capture_index >= 0:
            self._task_results.append((task, capture))

    def _postprocess_captures(self) -> None:
        updated_elements = collections.defaultdict(list)

        for task, capture in self._task_results:
            chapter = self._chapter_by_path[task.md_path]
            output  = _parse_capture_output(capture, task.opts)

            elem = chapter.elements[task.md_path][task.capture_index]
            assert elem.md_type == 'block'

            header_lines = [
                line
                for line in elem.content.splitlines(task.opts.keepends)
                if line.startswith("```") or parse.has_directive(line, is_prelude=True, language="shell")
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
                    {elem.md_path},
                )
                key = (chapter.chapnum, task.md_path)
                updated_elements[key].append(updated_elem)

        for chapter in self.orig_chapters:
            self.elements_by_chapnum[chapter.chapnum] = {
                md_path: updated_elements.get((chapter.chapnum, md_path), []) for md_path in chapter.md_paths
            }

    def _start(self, submit_task: typ.Callable[[ct.BlockTask], Future]) -> None:
        provided_ids        : set[str] = set()
        remaining_tasks     : list[ct.BlockTask] = list(self._all_tasks)
        prev_remaining_tasks: list[ct.BlockTask] = []
        num_completed = 0

        while remaining_tasks:
            if remaining_tasks == prev_remaining_tasks:
                for task in remaining_tasks:
                    logger.error(f"Task with unsatisfied requires: {task.opts.requires_ids}")
                raise RuntimeError("No progress made processing block tasks")
            else:
                prev_remaining_tasks = remaining_tasks

            defered_tasks: list[ct.BlockTask] = []
            futures      : list[tuple[Future, ct.BlockTask]] = []

            for task in remaining_tasks:
                if task.opts.requires_ids <= provided_ids:
                    future = submit_task(task)
                    futures.append((future, task))
                else:
                    defered_tasks.append(task)

            for future, task in futures:
                future.result(timeout=task.opts.timeout)
                num_completed += 1
                if task.opts.provides_id:
                    provided_ids.add(task.opts.provides_id)

            remaining_tasks = defered_tasks

        total  = len(self._all_tasks)
        cached = len(self._cached_tasks)
        logger.info(f"Completed tasks: {num_completed} of {total} ({cached} cached)")

    def start(self) -> None:
        try:
            if self.opts.concurrency > 1 and self.opts.exitfirst:
                logger.warning("Incompatible --concurrency > 1 and --exit-first")
                logger.warning("    Fallback to --concurrency=1")

            if self.opts.concurrency == 1 or self.opts.exitfirst:

                def submit(task: ct.BlockTask) -> Future:
                    future: Future = Future()
                    self._run_task(task)
                    future.set_result(None)
                    return future

                self._start(submit)
            else:
                with ThreadPoolExecutor(max_workers=self.opts.concurrency) as executor:

                    def submit(task: ct.BlockTask) -> Future:
                        return executor.submit(self._run_task, task)

                    self._start(submit)
            self._postprocess_captures()
        finally:
            self._cache.flush()

    def wait(self) -> None:
        pass


def _run_subprocs(parse_ctx: parse.Context, opts: BuildOptions, runner: Runner) -> parse.Context:
    runner.start()
    runner.wait()

    doc_ctx = parse_ctx.copy()

    for chap_idx, orig_chapter in enumerate(parse_ctx.chapters):
        updated_elements = runner.elements_by_chapnum[orig_chapter.chapnum]

        # phase 6. rewrite output blocks
        new_elems_by_path = {}
        for md_path in orig_chapter.md_paths:
            orig_elems = orig_chapter.elements[md_path]
            if md_path in updated_elements:
                new_elems = list(orig_elems)  # copy
                for updated_elem in updated_elements[md_path]:
                    orig_elem = orig_elems[updated_elem.elem_index]
                    assert "out" in orig_elem.content or "run" in orig_elem.content
                    new_elems[updated_elem.elem_index] = updated_elem
                new_elems_by_path[md_path] = new_elems
            else:
                new_elems_by_path[md_path] = orig_elems

        new_chapter = parse.Chapter(
            orig_chapter.md_paths,
            orig_chapter.chapnum,
            orig_chapter.namespace,
            new_elems_by_path,
        )
        if opts.in_place_update:
            for md_path in new_chapter.md_paths:
                new_file_content = new_chapter.md_content(md_path)

                with md_path.open(mode="r", encoding="utf-8") as fobj:
                    old_file_content = fobj.read()

                if old_file_content != new_file_content:
                    with md_path.open(mode="w", encoding="utf-8") as fobj:
                        fobj.write(new_file_content)

                    logger.info(f"Updated {md_path}")

        doc_ctx.chapters[chap_idx] = new_chapter

    if not opts.in_place_update:
        logger.info("Update skipped. Use -i/--in-place-update to update 'out' blocks.")

    return doc_ctx


def build(parse_ctx: parse.Context, opts: BuildOptions) -> parse.Context:
    build_ctx   = parse_ctx.copy()
    build_start = time.time()

    try:
        # NOTE (mb 2020-05-22): macros/constants are abandoned for now
        # phase 1: expand constants
        # build_ctx      = _expand_constants(build_ctx)

        # phase 2: expand dep directives
        expanded_chapters = list(_iter_expanded_chapters(build_ctx.chapters))
    except BlockError as err:
        # TODO (mb 2020-06-03): print context of block
        contents = err.include_contents or [err.block.content]
        for content in contents:
            for line in content.splitlines():
                if line.strip():
                    sys.stderr.write("E " + line.rstrip() + "\n")
        raise

    build_ctx = parse.Context(chapters=expanded_chapters)

    # phase 3. validate blocks
    error_messages = list(_iter_block_errors(parse_ctx, build_ctx))
    for error_msg in error_messages:
        logger.error(error_msg)

    if error_messages:
        raise SystemExit(1)

    # phase 4. write files with expanded blocks
    #   This has to happen before sub-processes, as those
    #   may use the newly created files.
    _dump_files(build_ctx)

    # phase 5. run sub-processes and update output blocks
    runner = Runner(parse_ctx.chapters, build_ctx.chapters, opts)
    try:
        doc_ctx = _run_subprocs(parse_ctx, opts, runner)
        return doc_ctx
    finally:
        duration = time.time() - build_start
        logger.info(f"Build finished after {duration:9.3f}sec")
