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

import time
import threading
import subprocess as sp


class SessionException(Exception):
    pass


class CapturedLine(typ.NamedTuple):
    ts  : float
    line: str


class CapturingThread(typ.NamedTuple):
    thread: threading.Thread
    lines : typ.List[CapturedLine]


class ProcResult(typ.NamedTuple):
    exit_code: int
    stdout   : typ.List[CapturedLine]
    stderr   : typ.List[CapturedLine]


Environ = typ.Mapping[str, str]
# make mypy fail if this is the wrong type
_: Environ = os.environ


def _gen_captured_lines(
    raw_lines: typ.Iterable[bytes], encoding: str = "utf-8"
) -> typ.Iterable[CapturedLine]:
    for raw_line in raw_lines:
        ts         = time.time()
        line_value = raw_line.decode(encoding)
        log.debug(f"read {len(raw_line)} bytes")
        yield CapturedLine(ts, line_value)


def _read_loop(
    sp_output_pipe: typ.IO[bytes], captured_lines: typ.List[CapturedLine], encoding: str = "utf-8"
) -> None:
    raw_lines = iter(sp_output_pipe.readline, b'')
    cl_gen    = _gen_captured_lines(raw_lines, encoding=encoding)
    for cl in cl_gen:
        captured_lines.append(cl)


def _start_reader(sp_output_pipe: typ.IO[bytes], encoding: str = "utf-8") -> CapturingThread:
    captured_lines: typ.List[CapturedLine] = []
    read_loop_thread = threading.Thread(
        target=_read_loop, args=(sp_output_pipe, captured_lines, encoding)
    )
    read_loop_thread.start()
    return CapturingThread(read_loop_thread, captured_lines)


class InteractiveSession:

    encoding: str
    start   : float

    _retcode: typ.Optional[int]
    _proc   : sp.Popen

    _in_cl : typ.List[CapturedLine]
    _out_ct: CapturingThread
    _err_ct: CapturingThread

    def __init__(
        self, cmd: typ.Sequence[str], *, env: typ.Optional[Environ] = None, encoding: str = "utf-8"
    ) -> None:
        _env: Environ
        if env is None:
            _env = os.environ.copy()
        else:
            _env = env

        self.encoding = encoding
        self.start    = time.time()
        self._retcode = None

        log.info(f"popen {cmd}")
        self._proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, env=_env)

        _enc = encoding

        self._in_cl  = []
        self._out_ct = _start_reader(self._proc.stdout, _enc)
        self._err_ct = _start_reader(self._proc.stderr, _enc)

    def send(self, input_str: str, delay: float = 0.01) -> None:
        self._in_cl.append(CapturedLine(time.time(), input_str))
        input_data = input_str.encode(self.encoding)
        log.debug(f"sending {len(input_data)} bytes")
        self._proc.stdin.write(input_data)
        self._proc.stdin.flush()
        if delay:
            time.sleep(delay)

    @property
    def retcode(self) -> int:
        return self.wait()

    def wait(self, timeout=1) -> int:
        if self._retcode is not None:
            return self._retcode

        log.info(f"wait with timeout={timeout}")
        returncode: typ.Optional[int] = None
        try:
            self._proc.stdin.close()
            max_time = self.start + timeout
            while returncode is None and max_time > time.time():
                time_left = max_time - time.time()
                # print("poll", max_time - time.time())
                log.debug(f"poll {time_left}")
                time.sleep(min(0.01, max(0, time_left)))
                returncode = self._proc.poll()
        finally:
            if self._proc.returncode is None:
                log.debug("sending SIGTERM")
                self._proc.terminate()
                # TODO: What if the subprocess doesn't end?
                returncode = self._proc.wait()

        self._out_ct.thread.join()
        self._err_ct.thread.join()
        assert returncode is not None
        self._retcode = returncode
        return returncode

    def _assert_retcode(self) -> None:
        if self._retcode is None:
            raise AssertionError(
                "'InteractiveSession.wait()' must be called " + " before accessing captured output."
            )

    def iter_stdout(self) -> typ.Iterable[str]:
        self._assert_retcode()
        for ts, line in self._out_ct.lines:
            yield line

    def iter_stderr(self) -> typ.Iterable[str]:
        self._assert_retcode()
        for ts, line in self._err_ct.lines:
            yield line

    def __iter__(self) -> typ.Iterable[str]:
        self._assert_retcode()
        all_lines = self._in_cl + self._out_ct.lines + self._err_ct.lines
        for captured_line in sorted(all_lines):
            yield captured_line.line
