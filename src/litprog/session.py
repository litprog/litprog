# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import time
import shlex
import typing as typ
import logging
import os.path
import threading
import subprocess as sp

import pathlib as pl

log = logging.getLogger(__name__)

InputPaths = typ.Sequence[str]
FilePaths  = typ.Iterable[pl.Path]

ExitCode = int


class RawCapturedLine(typ.NamedTuple):
    ts  : float
    line: str


class CapturedLine(typ.NamedTuple):
    ts    : float
    line  : str
    is_err: bool


class SessionException(Exception):
    pass


Environ = typ.Mapping[str, str]
# make mypy fail if this is the wrong type
_: Environ = os.environ


def _gen_captured_lines(
    raw_lines: typ.Iterable[bytes], encoding: str = "utf-8"
) -> typ.Iterable[RawCapturedLine]:
    for raw_line in raw_lines:
        # get timestamp as fast as possible after
        #   output was read
        ts = time.time()

        line_value = raw_line.decode(encoding)
        log.debug(f"read {len(raw_line)} bytes")
        yield RawCapturedLine(ts, line_value)


def _read_loop(
    sp_output_pipe: typ.IO[bytes],
    captured_lines: typ.List[RawCapturedLine],
    encoding      : str = "utf-8",
) -> None:
    raw_lines = iter(sp_output_pipe.readline, b'')
    cl_gen    = _gen_captured_lines(raw_lines, encoding=encoding)
    for cl in cl_gen:
        captured_lines.append(cl)


class CapturingThread(typ.NamedTuple):
    thread: threading.Thread
    lines : typ.List[RawCapturedLine]


def _start_reader(sp_output_pipe: typ.IO[bytes], encoding: str = "utf-8") -> CapturingThread:
    captured_lines: typ.List[RawCapturedLine] = []
    read_loop_thread = threading.Thread(
        target=_read_loop, args=(sp_output_pipe, captured_lines, encoding)
    )
    read_loop_thread.start()
    return CapturingThread(read_loop_thread, captured_lines)


AnyCommand = typ.Union[str, typ.List[str]]


def _normalize_command(command: AnyCommand) -> typ.List[str]:
    if isinstance(command, str):
        return shlex.split(command)
    elif isinstance(command, list):
        return command
    else:
        err_msg = f"Invalid command: {command}"
        raise Exception(err_msg)


class InteractiveSession:

    encoding: str
    start   : float
    end     : float

    _retcode: typ.Optional[int]
    _proc   : sp.Popen

    _in_cl : typ.List[RawCapturedLine]
    _out_ct: CapturingThread
    _err_ct: CapturingThread

    def __init__(
        self, cmd: AnyCommand, *, env: typ.Optional[Environ] = None, encoding: str = "utf-8"
    ) -> None:
        _env: Environ
        if env is None:
            _env = os.environ.copy()
        else:
            _env = env

        self.encoding = encoding
        self.start    = time.time()
        self.end      = -1.0
        self._retcode = None

        cmd_parts = _normalize_command(cmd)
        log.debug(f"popen {cmd_parts}")
        self._proc = sp.Popen(cmd_parts, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, env=_env)

        _enc = encoding

        self._in_cl  = []
        self._out_ct = _start_reader(self._proc.stdout, _enc)
        self._err_ct = _start_reader(self._proc.stderr, _enc)

    def send(self, input_str: str, delay: float = 0) -> None:
        self._in_cl.append(RawCapturedLine(time.time(), input_str))
        input_data = input_str.encode(self.encoding)
        log.debug(f"sending {len(input_data)} bytes")
        self._proc.stdin.write(input_data)
        if delay:
            self._proc.stdin.flush()
            time.sleep(delay)

    @property
    def retcode(self) -> int:
        self._proc.stdin.flush()
        return self.wait()

    def _assert_retcode(self) -> None:
        if self._retcode is None:
            raise AssertionError(
                "'InteractiveSession.wait()' must be called " + " before accessing captured output."
            )

    def wait(self, timeout=1) -> int:
        if self._retcode is not None:
            return self._retcode

        log.debug(f"wait with timeout={timeout}")
        returncode: typ.Optional[int] = None
        try:
            self._proc.stdin.close()
        except BrokenPipeError:
            # NOTE (mb 2020-06-05): Some subprocesses exit so fast that the pipe
            #   may already be closed.
            log.debug("stdin already closed")

        try:
            max_time = self.start + timeout
            while True:
                time_left = max_time - time.time()
                log.debug(f"poll {time_left}")
                time.sleep(min(0.01, max(0, time_left)))
                returncode = self._proc.poll()
                if returncode is not None:
                    log.debug(f"poll() returned {returncode}")
                    break
                if time.time() > max_time:
                    log.debug("timeout")
                    break
        finally:
            if self._proc.returncode is None:
                log.debug("sending SIGTERM")
                self._proc.terminate()
                returncode = self._proc.wait()

        self._out_ct.thread.join()
        self._err_ct.thread.join()
        assert returncode is not None
        self._retcode = returncode
        self.end      = time.time()
        return returncode

    @property
    def out_lines(self) -> typ.List[RawCapturedLine]:
        return self._out_ct.lines

    @property
    def err_lines(self) -> typ.List[RawCapturedLine]:
        return self._err_ct.lines

    def iter_lines(self) -> typ.Iterable[CapturedLine]:
        out_lines = iter(self.out_lines)
        err_lines = iter(self.err_lines)
        ol        = next(out_lines, None)
        el        = next(err_lines, None)

        while True:
            if ol and el:
                if ol.ts <= el.ts:
                    yield CapturedLine(ol.ts, ol.line, False)
                    ol = next(out_lines, None)
                else:
                    yield CapturedLine(el.ts, el.line, True)
                    el = next(err_lines, None)
            elif el:
                yield CapturedLine(el.ts, el.line, True)
                el = next(err_lines, None)
            elif ol:
                yield CapturedLine(ol.ts, ol.line, False)
                ol = next(out_lines, None)
            else:
                break

    def iter_stdout(self) -> typ.Iterable[str]:
        for ts, line in self._out_ct.lines:
            yield line

    def iter_stderr(self) -> typ.Iterable[str]:
        for ts, line in self._err_ct.lines:
            yield line

    def __iter__(self) -> typ.Iterable[str]:
        all_lines = self._in_cl + self._out_ct.lines + self._err_ct.lines
        for captured_line in sorted(all_lines):
            yield captured_line.line

    @property
    def runtime(self) -> float:
        self._assert_retcode()
        return self.end - self.start

    @property
    def stdout(self) -> str:
        return "".join(self.iter_stdout())

    @property
    def stderr(self) -> str:
        return "".join(self.iter_stderr())
