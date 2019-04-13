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

InputPaths = typ.Sequence[str]
FilePaths  = typ.Iterable[pl.Path]

ExitCode = int
import signal
import fnmatch

import litprog.parse
import litprog.session
import litprog.types as lptyp


class GeneratorResult:
    output: typ.Optional[str]
    done  : bool
    error : bool

    def __init__(
        self,
        output: typ.Optional[str] = None,
        *,
        done : typ.Optional[bool] = None,
        error: bool = False,
    ) -> None:
        self.output = output
        if done is None:
            self.done = output is not None
        else:
            self.done = done
        self.error = error


GeneratorFunc = typ.Callable[[lptyp.BuildContext, lptyp.LitProgId], GeneratorResult]


def gen_meta_output(ctx: lptyp.BuildContext, lpid: lptyp.LitProgId) -> GeneratorResult:
    log.warning(f"lptype=meta not implemented")
    return GeneratorResult(done=True)


def gen_raw_block_output(ctx: lptyp.BuildContext, lpid: lptyp.LitProgId) -> GeneratorResult:
    output = "".join("".join(l.val for l in block.lines) for block in ctx.blocks[lpid])
    return GeneratorResult(output)


def gen_multi_block_output(ctx: lptyp.BuildContext, lpid: lptyp.LitProgId) -> GeneratorResult:
    log.warning(f"lptype=multi_block not implemented")
    return GeneratorResult(done=True)


def parse_all_ids(ctx: lptyp.BuildContext) -> typ.Sequence[lptyp.LitProgId]:
    assert isinstance(ctx.blocks, collections.OrderedDict)
    return list(ctx.blocks.keys())


def iter_expanded_lpids(
    ctx: lptyp.BuildContext, lpids: typ.Iterable[lptyp.LitProgId]
) -> typ.Iterable[lptyp.LitProgId]:
    all_ids = parse_all_ids(ctx)
    for glob_or_lpid in lpids:
        is_lp_id = not ("*" in glob_or_lpid or "?" in glob_or_lpid)
        if is_lp_id:
            yield glob_or_lpid
            continue

        lpid_pat = fnmatch.translate(glob_or_lpid)
        lpid_re  = re.compile(lpid_pat)
        for lpid in all_ids:
            if lpid_re.match(lpid):
                yield lpid


def parse_missing_ids(ctx: lptyp.BuildContext, lpid: lptyp.LitProgId) -> typ.Set[lptyp.LitProgId]:
    captured_ids = set(ctx.captured_outputs.keys())

    options      = ctx.options[lpid]
    required_ids = set(options.get('requires', []))
    if options['lptype'] == 'out_file':
        required_ids |= set(options['inputs'])

    required_ids = set(iter_expanded_lpids(ctx, required_ids))

    return required_ids - captured_ids


def parse_input_ids(options: lptyp.BlockOptions,) -> lptyp.LitProgIds:
    maybe_input_ids = options['inputs']
    # TODO: validate
    return typ.cast(lptyp.LitProgIds, maybe_input_ids)


def gen_out_file_output(ctx: lptyp.BuildContext, lpid: lptyp.LitProgId) -> GeneratorResult:
    options      = ctx.options[lpid]
    input_lpids  = parse_input_ids(options)
    input_lpids  = iter_expanded_lpids(ctx, input_lpids)
    output_parts = [ctx.captured_outputs[input_lpid] for input_lpid in input_lpids]

    # TODO: Add preulude/postscript for each block
    #   this may be needed to read content back in
    #   after running code formatting.
    # prelude_tmpl    = options.get('block_prelude')
    # postscript_tmpl = options.get('block_postscript')

    output = "".join(output_parts)
    return GeneratorResult(output)


TIMEOUT_RETCODE = -signal.SIGTERM.value


def gen_session_output(ctx: lptyp.BuildContext, lpid: lptyp.LitProgId) -> GeneratorResult:
    options = ctx.options[lpid]
    timeout = options.get('timeout', 2)

    command = options.get('command', "bash")
    log.info(f"starting session {lpid}. cmd: {command}")
    isession = litprog.session.InteractiveSession(command)

    for block in ctx.blocks[lpid]:
        for line in block.lines:
            isession.send(line.val)

    exit_code  = isession.wait(timeout=timeout)
    runtime_ms = isession.runtime * 1000
    log.info(f"  session block {lpid:<35} runtime: {runtime_ms:9.3f}ms")
    output = "".join(iter(isession))

    expected_exit_code = options.get('expected_exit_code', 0)
    if exit_code == expected_exit_code:
        log.info(f"  session block {lpid:<35} done ok. RETCODE: {exit_code}")
        return GeneratorResult(output)
    elif exit_code == TIMEOUT_RETCODE:
        log.error(f"  session block {lpid:<35} done fail. " + f"Timout of {timeout} exceeded.")
        sys.stderr.write(output)
        return GeneratorResult(output, error=True)
    else:
        log.error(f"  session block {lpid:<35} done fail. " + f"RETCODE: {exit_code} invalid!")
        sys.stderr.write(output)
        err_msg = f"Error processing session {lpid}"
        log.error(err_msg)
        # TODO: This is a bit harsh to do here. Probably
        #   we should raise an exception.
        return GeneratorResult(error=True)


OUTPUT_GENERATORS_BY_TYPE: typ.Mapping[str, GeneratorFunc] = {
    'meta'       : gen_meta_output,
    'raw_block'  : gen_raw_block_output,
    'multi_block': gen_multi_block_output,
    'out_file'   : gen_out_file_output,
    'session'    : gen_session_output,
}


def write_output(lpid: lptyp.LitProgId, ctx: lptyp.BuildContext) -> None:
    options        = ctx.options[lpid]
    maybe_filepath = options.get('filepath')
    if maybe_filepath is None:
        return

    filepath = pl.Path(maybe_filepath)
    encoding = options.get('encoding', "utf-8")
    with filepath.open(mode="w", encoding=encoding) as fh:
        fh.write(ctx.captured_outputs[lpid])

    if options.get('is_executable'):
        filepath.chmod(filepath.stat().st_mode | 0o100)

    log.info(f"wrote to '{filepath}'")


def build(parse_ctx: lptyp.ParseContext) -> ExitCode:
    ctx     = lptyp.BuildContext(parse_ctx)
    all_ids = parse_all_ids(ctx)

    while len(ctx.captured_outputs) < len(all_ids):

        assert len(ctx.options) == len(all_ids)

        prev_len_completed = len(ctx.captured_outputs)
        for lpid, options in sorted(ctx.options.items()):
            if lpid in ctx.captured_outputs:
                continue

            missing_ids = parse_missing_ids(ctx, lpid)
            if any(missing_ids):
                continue

            litprog_type: str = options['lptype']
            generator_func = OUTPUT_GENERATORS_BY_TYPE.get(litprog_type)
            if generator_func is None:
                log.error(f"lptype={litprog_type} not implemented")
                return 1

            res         : GeneratorResult = generator_func(ctx, lpid)
            if res.error:
                log.error(f"{litprog_type:>9} block {lpid:>25} had an error.")
                return 1
            elif res.done:
                if res.output is None:
                    ctx.captured_outputs[lpid] = ""
                    log.debug(f"{litprog_type:>9} block {lpid:>25} done (no output).")
                else:
                    ctx.captured_outputs[lpid] = res.output
                    log.debug(f"{litprog_type:>9} block {lpid:>25} done.")
                    write_output(lpid, ctx)
            else:
                continue

        if prev_len_completed < len(ctx.captured_outputs):
            continue

        log.error(f"Build failed: Unresolved requirements.")

        captured_block_ids  = set(ctx.captured_outputs.keys())
        remaining_block_ids = sorted(set(all_ids) - captured_block_ids)
        for block_id in remaining_block_ids:
            missing_ids = parse_missing_ids(ctx, lpid)
            log.error(f"Not Completed: '{block_id}'." + f" Missing requirements: {missing_ids}")
        return 1
    return 0
