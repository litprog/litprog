# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import os
import re
import sys
import time
import typing as typ
import logging
import pathlib as pl
import tempfile
import collections
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor

from . import cache
from . import parse
from . import common
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

DEFUALT_TIMEOUT = 9.0

MarkdownFiles = typ.Iterable[parse.MarkdownFile]

# The expanded files are structurally no different, it's just that
# their elements are expanded.
ExpandedMarkdownFile  = parse.MarkdownFile
ExpandedMarkdownFiles = typ.Iterable[ExpandedMarkdownFile]


class BlockError(Exception):

    block           : parse.Block
    include_contents: typ.List[str]

    def __init__(
        self, msg: str, block: parse.Block, include_contents: typ.Optional[typ.List[str]] = None
    ) -> None:
        self.block            = block
        self.include_contents = include_contents or []

        loc = parse.location(block).strip()
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
    elif len(found) > 1 and not many_ok:
        errmsg = f"Block with multiple '{name}'"
        raise BlockError(errmsg, block)
    else:
        return found[0]


def iter_directives(block: parse.Block, name: str) -> typ.Iterable[parse.Directive]:
    for directive in block.directives:
        if directive.name == name:
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


# TODO: this should be part of the parsing of all directives
def _parse_prefix(directive: parse.Directive) -> str:
    val = directive.value.strip()
    if val.startswith("'") and val.endswith("'"):
        val = val[1:-1]
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return val


BlockId       = str
ScopedBlockId = str

BlockIds       = typ.List[BlockId]
BlockListBySid = typ.Dict[ScopedBlockId, typ.List[parse.Block  ]]
DependencyMap  = typ.Dict[ScopedBlockId, typ.List[ScopedBlockId]]


def _namespaced_lp_id(block: parse.Block, lp_id: BlockId) -> ScopedBlockId:
    if "." in lp_id:
        return lp_id.strip()
    else:
        return block.namespace + "." + lp_id.strip()


def _iter_dep_sids(block: parse.Block) -> typ.Iterable[ScopedBlockId]:
    for lp_dep in iter_directives(block, 'dep'):
        for dep_id in lp_dep.value.split(","):
            yield _namespaced_lp_id(block, dep_id)


def _build_dep_map(blocks_by_sid: BlockListBySid) -> DependencyMap:
    """Build a mapping of block_ids to the Blocks they depend on.

    The mapped block_ids (keys) are only the direct (non-recursive) dependencies.
    """
    dep_map: DependencyMap = {}
    for lp_def_id, blocks in blocks_by_sid.items():
        for block in blocks:
            for dep_sid in _iter_dep_sids(block):
                if dep_sid in blocks_by_sid:
                    if lp_def_id in dep_map:
                        dep_map[lp_def_id].append(dep_sid)
                    else:
                        dep_map[lp_def_id] = [dep_sid]
                else:
                    raise BlockError(f"Unknown block id: {dep_sid}", block)

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
) -> typ.List[str]:
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
    block        : parse.Block,
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
    block        : parse.Block,
    added_deps   : typ.Set[str],
    dep_map      : DependencyMap,
    keep_fence   : bool,
    lvl          : int = 1,
) -> str:
    # NOTE (mb 2020-12-20): Depth first expansion of content.
    #   This ensures that the first occurance of an dep
    #   directive is expanded at the earliest possible point
    #   even if it is a recursive dep.
    lp_def = get_directive(block, 'def', missing_ok=True, many_ok=False)

    if keep_fence:
        new_content = block.content
    else:
        new_content = block.includable_content + "\n"

    for directive in block.directives:
        if directive.name not in ('dep', 'include'):
            continue

        is_dep = directive.name == 'dep'

        lp_dep_contents: typ.List[str] = []
        for lp_dep_id in directive.value.split(","):
            lp_dep_sid = _namespaced_lp_id(block, lp_dep_id)
            if lp_def:
                lp_def_id = _namespaced_lp_id(block, lp_def.value)
                _err_on_include_cycle(block, lp_dep_sid, blocks_by_sid, dep_map, root_id=lp_def_id)

            if is_dep:
                if lp_dep_sid in added_deps:
                    # skip already included dependencies
                    continue
                else:
                    added_deps.add(lp_dep_sid)

            for dep_block in blocks_by_sid[lp_dep_sid]:
                dep_content = _expand_block_content(
                    blocks_by_sid, dep_block, added_deps, dep_map, keep_fence=False, lvl=lvl + 1
                )
                dep_content = _match_indent(directive.raw_text, dep_content)
                lp_dep_contents.append(dep_content)

        include_content = "\n" + "\n".join(lp_dep_contents)
        dep_text        = directive.raw_text.lstrip("\n")
        new_content     = _indented_include(new_content, dep_text, include_content, is_dep=is_dep)

    return new_content


def _expand_directives(blocks_by_sid: BlockListBySid, md_file: parse.MarkdownFile) -> parse.MarkdownFile:
    new_md_file = md_file.copy()
    dep_map     = _build_dep_map(blocks_by_sid)

    for block in list(new_md_file.iter_blocks()):
        added_deps: typ.Set[str] = set()
        new_content = _expand_block_content(blocks_by_sid, block, added_deps, dep_map, keep_fence=True)
        if new_content != block.content:
            elem = new_md_file.elements[block.elem_index]
            new_md_file.elements[block.elem_index] = parse.MarkdownElement(
                elem.md_path, elem.first_line, elem.elem_index, elem.md_type, new_content, None
            )

    return new_md_file


def _get_blocks_by_id(md_files: MarkdownFiles) -> BlockListBySid:
    blocks_by_sid: BlockListBySid = {}

    for md_file in md_files:
        for block in md_file.iter_blocks():
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

            for lp_addto in iter_directives(block, 'addto'):
                lp_addto_id = _namespaced_lp_id(block, lp_addto.value)
                if lp_addto_id in blocks_by_sid:
                    blocks_by_sid[lp_addto_id].append(block)
                else:
                    errmsg = f"Unknown block id: {lp_addto_id}"
                    raise BlockError(errmsg, block)

    return blocks_by_sid


def _iter_expanded_files(md_files: MarkdownFiles) -> ExpandedMarkdownFiles:
    # NOTE (mb 2020-05-24): To do the expansion, we have to first
    #   build a graph so that we can resolve blocks for each dep/include.

    # pass 1. collect all blocks (globally) with def directives
    # NOTE (mb 2020-05-31): block ids are always absulute/fully qualified
    blocks_by_sid = _get_blocks_by_id(md_files)

    # pass 2. expand dep directives in markdown files
    for md_file in md_files:
        yield _expand_directives(blocks_by_sid, md_file)


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

        for block in md_file.iter_blocks():
            orig_elem = orig_md_file.elements[block.elem_index]
            for directive in block.directives:
                if directive.name not in ('dep', 'include'):
                    continue

                elem = md_file.elements[block.elem_index]

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
                    f"Error processing {md_file.md_path} on line {line_no}: "
                    + f"Could not expand {raw_text_repr}"
                )


def _dump_files(build_ctx: parse.Context) -> None:
    for md_file in build_ctx.files:
        for block in md_file.iter_blocks():
            file_directive = get_directive(block, 'file')
            if file_directive is None:
                continue

            path             = pl.Path(file_directive.value)
            new_content_data = block.includable_content.encode("utf-8")

            if path.exists():
                with path.open(mode="rb") as fobj:
                    old_content_data = fobj.read()

                if old_content_data == new_content_data:
                    # don't needlessly update mtimes
                    continue

            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open(mode="wb") as fobj:
                fobj.write(new_content_data)


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


def _get_default_command(block: parse.Block) -> typ.Optional[str]:
    # TODO (mb 2020-12-17): Allow override/configuration
    lang = block.info_string.strip()
    if lang == 'python':
        # TODO (mb 2020-12-18): sys.executable to work with pypy?
        return "python3"
    elif lang in ("bash", "shell"):
        return "bash"
    elif lang == 'sh':
        return "sh"
    else:
        return None


def _parse_format_options(block: parse.Block) -> common.FormatOptions:
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

    return common.FormatOptions(
        out=out_fmt,
        err=err_fmt,
        info=info_fmt,
        out_prefix=_parse_prefix(out_prefix) if out_prefix else "",
        err_prefix=_parse_prefix(err_prefix) if err_prefix else "! ",
    )


def _parse_session_block_options(block: parse.Block) -> typ.Optional[common.SessionBlockOptions]:
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

    _provides    = get_directive(block, 'def')
    _debug       = get_directive(block, 'debug')
    _requires    = get_directive(block, 'requires')
    _input_delay = get_directive(block, 'input_delay')
    _timeout     = get_directive(block, 'timeout')
    _expect      = get_directive(block, 'expect')

    provides_id : typ.Optional[str] = None
    if _provides:
        provides_id = _provides.value.strip()
        provides_id = _namespaced_lp_id(block, provides_id)

    if _requires:
        requires_ids = {_namespaced_lp_id(block, req_id) for req_id in _requires.value.split(",")}
    else:
        requires_ids = set()

    timeout_val          = float(_timeout.value    ) if _timeout else DEFUALT_TIMEOUT
    input_delay_val      = float(_input_delay.value) if _input_delay else 0.0
    expected_exit_status = int(_expect.value) if _expect else 0

    return common.SessionBlockOptions(
        command=command,
        directive=directive,
        provides_id=provides_id,
        requires_ids=requires_ids,
        timeout=timeout_val,
        input_delay=input_delay_val,
        expected_exit_status=expected_exit_status,
        is_stdin_writable=directive in ('exec', 'run'),
        is_debug=bool(_debug),
        keepends=True,
        fmt=_parse_format_options(block),
    )


def _parse_capture_output(capture: session.Capture, opts: common.SessionBlockOptions) -> str:
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
    block      : parse.Block,
    opts       : common.SessionBlockOptions,
    stdin_lines: typ.List[str],
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


def _init_isession(opts: common.SessionBlockOptions, command: Command) -> session.InteractiveSession:
    if opts.is_debug:
        return session.DebugInteractiveSession(command)
    else:
        return session.InteractiveSession(command)


def _init_command(opts: common.SessionBlockOptions) -> typ.Tuple[Tempfile, Command]:
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
    block      : parse.Block,
    opts       : common.SessionBlockOptions,
    command    : str,
    stdin_lines: typ.List[str],
) -> session.Capture:
    _cmd = command if len(command) < 40 else (command[:40] + "...")

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

    runtime_ms = round(isession.runtime * 1000)

    if exit_status == opts.expected_exit_status:
        exit_info = f"{exit_status}"
    else:
        exit_info = f"{exit_status} != {opts.expected_exit_status}"

    if runtime_ms < 500:
        logger.debug(f"{logmsg:<90} time: {runtime_ms:>6}ms  exit: {exit_info}")
    else:
        logger.info(f"{logmsg:<90} time: {runtime_ms:>6}ms  exit: {exit_info}")

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
    block: parse.Block,
    opts : common.SessionBlockOptions,
) -> session.Capture:
    tmp, command = _init_command(opts)

    if opts.is_stdin_writable:
        stdin_lines = block.inner_content.splitlines(opts.keepends)
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


def _iter_task_blocks(md_file: parse.MarkdownFile) -> typ.Iterable[common.TaskBlockOpts]:
    for block in md_file.iter_blocks():
        opts = _parse_session_block_options(block)
        if opts:
            yield common.TaskBlockOpts(block, opts)


def _iter_block_tasks(md_file: parse.MarkdownFile) -> typ.Iterable[common.BlockTask]:
    taskblockopt_items = list(_iter_task_blocks(md_file))
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

            yield common.BlockTask(md_file.md_path, command, block, opts, capture_index)


class MarkdownFileResult(typ.NamedTuple):

    orig_md_file    : parse.MarkdownFile
    updated_elements: typ.List[parse.MarkdownElement]


FilesItem = typ.Tuple[parse.MarkdownFile, parse.MarkdownFile]


class BuildOptions(typ.NamedTuple):

    exitfirst      : bool
    in_place_update: bool
    cache_enabled  : bool
    concurrency    : int


class Runner:

    orig_files : MarkdownFiles
    build_files: MarkdownFiles
    opts       : BuildOptions

    results: typ.List[MarkdownFileResult]

    _file_items_by_path: typ.Dict[pl.Path, FilesItem]
    _all_tasks         : typ.List[common.BlockTask]
    _task_results      : typ.List[typ.Tuple[common.BlockTask, session.Capture]]

    _cache: cache.ResultCache

    def __init__(
        self,
        orig_files : MarkdownFiles,
        build_files: MarkdownFiles,
        opts       : BuildOptions,
    ) -> None:
        self.orig_files  = orig_files
        self.build_files = build_files
        self.opts        = opts

        self.results             = []
        self._file_items_by_path = {}
        self._all_tasks          = []
        self._task_results       = []

        # TODO (mb 2021-03-04): _task_results and _cache are somewhat redundant.
        #   It might be possible/reasonable to always rely on the _cache to lookup
        #   the capture of a task, even one that was just executed.

        for orig_md_file, md_file in zip(self.orig_files, self.build_files):
            self._file_items_by_path[md_file.md_path] = (orig_md_file, md_file)
            self._all_tasks.extend(_iter_block_tasks(md_file))

        if self.opts.cache_enabled:
            self._cache = cache.LocalResultCache(self.orig_files)
        else:
            self._cache = cache.DummyCache()

    def _run_task(self, task: common.BlockTask) -> None:
        if self.opts.cache_enabled:
            cached_capture = self._cache.get_capture(task)
        else:
            cached_capture = None

        if cached_capture is None:
            capture = _process_command_block(task.block, task.opts)
            self._cache.update(task, capture)
        else:
            capture = cached_capture

        if task.capture_index >= 0:
            self._task_results.append((task, capture))

    def _postprocess_captures(self) -> None:
        updated_elements = collections.defaultdict(list)

        for task, capture in self._task_results:
            orig_md_file, md_file = self._file_items_by_path[task.md_path]
            output = _parse_capture_output(capture, task.opts)

            elem = md_file.elements[task.capture_index]
            assert elem.md_type == 'block'

            header_lines = [
                line
                for line in elem.content.splitlines(task.opts.keepends)
                if line.startswith("```") or parse.get_line_directive(line, language="shell", is_prelude=True)
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
                updated_elements[task.md_path].append(updated_elem)

        for orig_md_file, md_file in zip(self.orig_files, self.build_files):
            result = MarkdownFileResult(orig_md_file, updated_elements[md_file.md_path])
            self.results.append(result)

    def _start(self, submit_task: typ.Callable[[common.BlockTask], Future]) -> None:
        provided_ids        : typ.Set[str] = set()
        remaining_tasks     : typ.List[common.BlockTask] = list(self._all_tasks)
        prev_remaining_tasks: typ.List[common.BlockTask] = []
        num_completed = 0

        while remaining_tasks:
            if remaining_tasks == prev_remaining_tasks:
                for task in remaining_tasks:
                    logger.error(f"Task with unsatisfied requires: {task.opts.requires_ids}")
                raise RuntimeError("No progress made processing block tasks")
            else:
                prev_remaining_tasks = remaining_tasks

            defered_tasks: typ.List[common.BlockTask] = []
            futures      : typ.List[typ.Tuple[Future, common.BlockTask]] = []

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

        logger.info(f"Completed tasks: {num_completed} of {len(self._all_tasks)}")

    def start(self) -> None:
        if self.opts.concurrency == 1 or self.opts.exitfirst:

            def submit(task: common.BlockTask) -> Future:
                future: Future = Future()
                self._run_task(task)
                future.set_result(None)
                return future

            self._start(submit)
        else:
            with ThreadPoolExecutor(max_workers=self.opts.concurrency) as executor:

                def submit(task: common.BlockTask) -> Future:
                    return executor.submit(self._run_task, task)

                self._start(submit)

        self._postprocess_captures()
        self._cache.flush()

    def wait(self) -> None:
        pass


def _run_subprocs(orig_ctx: parse.Context, opts: BuildOptions, runner: Runner) -> parse.Context:
    runner.start()
    runner.wait()

    doc_ctx = orig_ctx.copy()

    for file_idx, md_file_result in enumerate(runner.results):
        if not any(md_file_result.updated_elements):
            continue

        md_path = md_file_result.orig_md_file.md_path

        # phase 6. rewrite output blocks
        orig_elements = list(md_file_result.orig_md_file.elements)
        new_elements  = list(orig_elements)  # copy
        for elem in md_file_result.updated_elements:
            orig_elem = orig_elements[elem.elem_index]
            assert 'out' in orig_elem.content or 'run' in orig_elem.content
            new_elements[elem.elem_index] = elem

        new_md_file = parse.MarkdownFile(md_path, new_elements)
        if opts.in_place_update:
            new_file_content = str(new_md_file)
            with new_md_file.md_path.open(mode="w", encoding="utf-8") as fobj:
                fobj.write(new_file_content)

            logger.info(f"Updated {new_md_file.md_path}")
        else:
            logger.info(f"Update skipped for {new_md_file.md_path} (use -i/--in-place-update)")

        doc_ctx.files[file_idx] = new_md_file

    return doc_ctx


def build(
    orig_ctx: parse.Context,
    opts    : BuildOptions,
) -> parse.Context:
    build_ctx   = orig_ctx.copy()
    build_start = time.time()

    try:
        # NOTE (mb 2020-05-22): macros/constants are abandoned for now
        # phase 1: expand constants
        # build_ctx      = _expand_constants(build_ctx)

        # phase 2: expand dep directives
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

    # TODO (mb 2021-01-02): Atomicity guarantees
    #   - Write new files to temp directory
    #   - Only update if original mtimes are still the same

    # phase 5. run sub-processes
    runner = Runner(orig_ctx.files, build_ctx.files, opts)
    try:
        return _run_subprocs(orig_ctx, opts, runner)
    finally:
        duration = time.time() - build_start
        logger.info(f"Build finished after {duration:9.3f}sec")
