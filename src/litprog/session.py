# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import json
import time
import shlex
import typing as typ
import logging
import os.path
import pathlib as pl
import threading
import subprocess as sp

logger = logging.getLogger(__name__)

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


class Capture(typ.NamedTuple):
    command    : str
    exit_status: int
    runtime    : float
    lines      : typ.List[CapturedLine]


CaptureData = bytes


def loads_capture(capture_bytes: CaptureData) -> Capture:
    capture_json = capture_bytes.decode("utf-8")
    capture_obj  = json.loads(capture_json)
    command, exit_status, runtime, lines_args = capture_obj

    lines = [CapturedLine(*line_args) for line_args in lines_args]
    return Capture(
        command,
        exit_status,
        runtime,
        lines,
    )


def dumps_capture(capture: Capture) -> CaptureData:
    line_args   = [[line.ts, line.line, line.is_err] for line in capture.lines]
    capture_obj = [
        capture.command,
        capture.exit_status,
        capture.runtime,
        line_args,
    ]
    capture_json  = json.dumps(capture_obj)
    capture_bytes = capture_json.encode("utf-8")
    return capture_bytes


class SessionException(Exception):
    pass


Environ = typ.Mapping[str, str]
# make mypy fail if this is the wrong type
_: Environ = os.environ


def _gen_captured_lines(
    raw_lines: typ.Iterable[bytes], encoding: str = "utf-8", debug_log: bool = False
) -> typ.Iterable[RawCapturedLine]:
    for raw_line in raw_lines:
        # get timestamp as fast as possible after
        #   output was read
        ts = time.time()

        line_value = raw_line.decode(encoding)
        if debug_log:
            logger.debug(f"read {len(raw_line)} bytes")
        yield RawCapturedLine(ts, line_value)


def _read_loop(
    sp_output_pipe: typ.IO[bytes],
    captured_lines: typ.List[RawCapturedLine],
    encoding      : str = "utf-8",
) -> None:
    raw_lines = iter(sp_output_pipe.readline, b'')
    for captured_line in _gen_captured_lines(raw_lines, encoding=encoding):
        captured_lines.append(captured_line)


class CapturingThread(typ.NamedTuple):
    thread: threading.Thread
    lines : typ.List[RawCapturedLine]


def _start_reader(
    sp_output_pipe: typ.IO[bytes],
    encoding      : str = "utf-8",
) -> CapturingThread:
    captured_lines: typ.List[RawCapturedLine] = []
    read_loop_thread = threading.Thread(target=_read_loop, args=(sp_output_pipe, captured_lines, encoding))
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
    _stdin  : typ.Optional[typ.IO[bytes]]
    _stdout : typ.IO[bytes]
    _stderr : typ.IO[bytes]

    _in_cl : typ.List[RawCapturedLine]
    _out_ct: CapturingThread
    _err_ct: CapturingThread

    def __init__(
        self,
        cmd: AnyCommand,
        *,
        env      : typ.Optional[Environ] = None,
        encoding : str  = "utf-8",
        debug_log: bool = False,
    ) -> None:
        _env: Environ
        if env is None:
            _env = os.environ.copy()
        else:
            _env = env

        self.encoding  = encoding
        self.debug_log = debug_log
        self.start     = time.time()
        self.end       = -1.0
        self._retcode  = None

        cmd_parts = _normalize_command(cmd)
        if self.debug_log:
            logger.debug(f"popen {cmd_parts}")
        self._proc = sp.Popen(cmd_parts, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, env=_env)

        assert self._proc.stdin  is not None
        assert self._proc.stdout is not None
        assert self._proc.stderr is not None
        self._stdin  = self._proc.stdin
        self._stdout = self._proc.stdout
        self._stderr = self._proc.stderr

        _enc = encoding

        self._in_cl  = []
        self._out_ct = _start_reader(self._stdout, _enc)
        self._err_ct = _start_reader(self._stderr, _enc)

    def send(self, input_str: str, delay: float = 0) -> None:
        self._in_cl.append(RawCapturedLine(time.time(), input_str))
        input_data = input_str.encode(self.encoding)

        _stdin = self._stdin
        if _stdin:
            _stdin.write(input_data)

            if delay:
                _stdin.flush()
        if delay:
            time.sleep(delay)

    @property
    def retcode(self) -> int:
        _stdin = self._stdin
        if _stdin:
            _stdin.flush()
        return self.wait()

    def _assert_retcode(self) -> None:
        if self._retcode is None:
            cls = type(self)
            msg = f"'{cls}.wait()' must be called before accessing captured output."
            raise RuntimeError(msg)

    def _wait(self, timeout) -> int:
        try:
            max_time = self.start + timeout
            while True:
                time_left = max_time - time.time()
                if self.debug_log:
                    logger.debug(f"poll {time_left}")
                time.sleep(min(0.01, max(0, time_left)))
                returncode = self._proc.poll()
                if returncode is not None:
                    if self.debug_log:
                        logger.debug(f"poll() returned {returncode}")
                    break
                if time.time() > max_time:
                    if self.debug_log:
                        logger.debug("timeout")
                    break
        finally:
            if returncode is None:
                if self.debug_log:
                    logger.debug("sending SIGTERM")
                self._proc.terminate()
                returncode = self._proc.wait()

        assert returncode is not None
        self._retcode = returncode
        self.end      = time.time()
        return returncode

    def wait(self, timeout=1) -> int:
        if self._retcode is not None:
            return self._retcode

        if self.debug_log:
            logger.debug(f"wait with timeout={timeout}")
        returncode: typ.Optional[int] = None
        _stdin = self._stdin
        if _stdin:
            try:
                _stdin.close()
            except BrokenPipeError:
                # NOTE (mb 2020-06-05): Some subprocesses exit so fast that the pipe
                #   may already be closed.
                logger.debug("stdin already closed")

        returncode = self._wait(timeout)
        self._out_ct.thread.join()
        self._err_ct.thread.join()
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
        out_line  = next(out_lines, None)
        err_line  = next(err_lines, None)

        while True:
            if out_line and err_line:
                if out_line.ts <= err_line.ts:
                    yield CapturedLine(out_line.ts, out_line.line, False)
                    out_line = next(out_lines, None)
                else:
                    yield CapturedLine(err_line.ts, err_line.line, True)
                    err_line = next(err_lines, None)
            elif err_line:
                yield CapturedLine(err_line.ts, err_line.line, True)
                err_line = next(err_lines, None)
            elif out_line:
                yield CapturedLine(out_line.ts, out_line.line, False)
                out_line = next(out_lines, None)
            else:
                break

    def output_lines(self) -> typ.List[CapturedLine]:
        return list(self.iter_lines())

    def iter_stdout(self) -> typ.Iterable[str]:
        for _ts, line in self._out_ct.lines:
            yield line

    def iter_stderr(self) -> typ.Iterable[str]:
        for _ts, line in self._err_ct.lines:
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


class DebugInteractiveSession(InteractiveSession):

    start: float
    end  : float

    _retcode: typ.Optional[int]
    _proc   : sp.Popen
    _stdin  : typ.Optional[typ.IO[bytes]]

    _in_cl: typ.List[RawCapturedLine]

    def __init__(
        self,
        cmd: AnyCommand,
        *,
        env      : typ.Optional[Environ] = None,
        encoding : str  = "utf-8",
        debug_log: bool = False,
    ) -> None:
        # pylint: disable=super-init-not-called; initialization is substantially different
        _env: Environ
        if env is None:
            _env = os.environ.copy()
        else:
            _env = env

        self.encoding  = encoding
        self.debug_log = debug_log
        self.start     = time.time()
        self.end       = -1.0
        self._retcode  = None

        cmd_parts = _normalize_command(cmd)
        if self.debug_log:
            logger.debug(f"popen {cmd_parts}")
        self._proc = sp.Popen(cmd_parts, env=_env)

        self._stdin = self._proc.stdin
        self._in_cl = []

    def wait(self, timeout=1) -> int:
        if self._retcode is not None:
            return self._retcode

        return self._wait(timeout)

    def output_lines(self) -> typ.List[CapturedLine]:
        return []
