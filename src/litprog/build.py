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
FilePaths  = typ.Iterable[pl.Path]

ExitCode = int
import logging

log = logging.getLogger(__name__)
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


GeneratorFunc = typ.Callable[[lptyp.LitprogID, lptyp.BuildContext], GeneratorResult]


def gen_meta_output(lpid: lptyp.LitprogID, ctx: lptyp.BuildContext) -> GeneratorResult:
    log.warning(f"lptype=meta not implemented")
    return GeneratorResult(done=True)


def gen_raw_block_output(lpid: lptyp.LitprogID, ctx: lptyp.BuildContext) -> GeneratorResult:
    output = "".join("".join(l.val for l in block.lines) for block in ctx.blocks[lpid])
    return GeneratorResult(output)


def gen_multi_block_output(lpid: lptyp.LitprogID, ctx: lptyp.BuildContext) -> GeneratorResult:
    log.warning(f"lptype=multi_block not implemented")
    return GeneratorResult(done=True)


def gen_out_file_output(lpid: lptyp.LitprogID, ctx: lptyp.BuildContext) -> GeneratorResult:
    options           = ctx.options[lpid]
    required_inputs   = set(options['inputs'])
    completed_outputs = set(ctx.captured_outputs.keys())
    missing_inputs    = required_inputs - completed_outputs

    if any(missing_inputs):
        return GeneratorResult(done=False)

    output_parts = [ctx.captured_outputs[input_lpid] for input_lpid in options['inputs']]

    # TODO: Add preulude/postscript for each block
    #   this may be needed to read content back in after formatting
    # prelude_tmpl    = options.get('block_prelude')
    # postscript_tmpl = options.get('block_postscript')

    output = "".join(output_parts)
    return GeneratorResult(output)


def gen_session_output(lpid: lptyp.LitprogID, ctx: lptyp.BuildContext) -> GeneratorResult:
    options         = ctx.options[lpid]
    required_blocks = set(options.get('requires', []))
    captured_blocks = set(ctx.captured_outputs.keys())
    missing_blocks  = required_blocks - captured_blocks
    if any(missing_blocks):
        log.debug(f"deferring {lpid} until {missing_blocks} are completed")
        return GeneratorResult(done=False)

    command = options.get('command', "bash")
    log.info(f"starting session {lpid}. cmd: {command}")
    isession = litprog.session.InteractiveSession(command)

    for block in ctx.blocks[lpid]:
        for line in block.lines:
            isession.send(line.val)

    exit_code = isession.wait(timeout=2)
    output    = "\n".join(iter(isession))

    expected_exit_code = options.get('expected_exit_code', 0)
    if exit_code == expected_exit_code:
        # TODO (mb): better output capture for sessions
        log.info(f"  session block {lpid:<15} done. RETCODE: {exit_code} ok.")
        return GeneratorResult(output)
    else:
        log.info(f"  session block {lpid:<15} fail. RETCODE: {exit_code} invalid!")
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


def write_output(lpid: lptyp.LitprogID, ctx: lptyp.BuildContext) -> None:
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
    ctx = lptyp.BuildContext(parse_ctx)

    option_ids = set(ctx.options.keys())
    block_ids  = set(ctx.blocks.keys())
    all_ids    = option_ids | block_ids

    while len(ctx.captured_outputs) < len(all_ids):

        assert len(ctx.options) == len(all_ids)

        prev_len_completed = len(ctx.captured_outputs)
        for lpid, options in ctx.options.items():
            if lpid in ctx.captured_outputs:
                continue

            litprog_type: str = options['lptype']
            generator_func = OUTPUT_GENERATORS_BY_TYPE.get(litprog_type)
            if generator_func is None:
                log.error(f"lptype={litprog_type} not implemented")
                return 1

            res         : GeneratorResult = generator_func(lpid, ctx)
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

        if prev_len_completed == len(ctx.captured_outputs):
            captured_blocks = list(ctx.captured_outputs.keys())
            log.error(f"Captured blocks: {captured_blocks}")
            log.error(f"Build failed: No progress/unresolved requirements.")
            return 1
    return 0
