# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import os
import io
import re
import sys
import math
import enum
import os.path
import typing as typ
import pathlib2 as pl
import operator as op
import itertools as it
import functools as ft

InputPaths = typ.Sequence[str]
FilePaths  = typ.Iterable[pl.Path]

ExitCode = int
import logging

log = logging.getLogger(__name__)
import shlex

import litprog.parse
import litprog.session


def build(context: litprog.parse.Context) -> ExitCode:
    captured_outputs: typ.Dict[litprog.parse.LitprogID, str                       ] = {}
    captured_procs  : typ.Dict[litprog.parse.LitprogID, litprog.session.ProcResult] = {}

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
                    "".join(l.val for l in block.lines) for block in context.blocks_by_id[lpid]
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
                isession = litprog.session.InteractiveSession(cmd_parts)

                for block in context.blocks_by_id[lpid]:
                    for line in block.lines:
                        isession.send(line.val)

                exit_code = isession.wait(timeout=2)
                output    = "\n".join(iter(isession))

                expected_exit_code = options.get('expected_exit_code', 0)
                if exit_code == expected_exit_code:
                    # TODO (mb): better output capture for sessions
                    captured_outputs[lpid] = output
                    log.info(f"{litprog_type:>9} block {lpid:<15} done. RETCODE: {exit_code} ok.")
                else:
                    log.info(
                        f"{litprog_type:>9} block {lpid:<15} fail. RETCODE: {exit_code} invalid!"
                    )
                    sys.stderr.write(output)
                    err_msg = f"Error processing session {lpid}"
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
