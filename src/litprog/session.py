#!/usr/bin/env python
# https://eli.thegreenplace.net/2017/interacting-with-a-long-running-child-process-in-python/
# https://lyceum-allotments.github.io/2017/03/python-and-pipes-part-6-multiple-subprocesses-and-pipes/

import os
import io
import time
import threading
import typing as typ
import subprocess as sp

# TODO: if term, run and capture every line separately
import logging

log = logging.getLogger("litprog.session")


class CapturedLine(typ.NamedTuple):
    us_ts: float
    line : str


class CapturingThread(typ.NamedTuple):
    thread: threading.Thread
    lines : typ.List[CapturedLine]


def _gen_captured_lines(
    raw_lines: typ.Iterable[bytes], encoding: str = "utf-8"
) -> typ.Iterable[CapturedLine]:
    for raw_line in raw_lines:
        us_ts      = round(time.time() * 1_000_000)
        line_value = raw_line.decode(encoding)
        log.debug(f"read {len(raw_line)} bytes")
        yield CapturedLine(us_ts, line_value)


def _read_loop(
    sp_output_pipe: typ.IO[bytes],
    captured_lines: typ.List[CapturedLine],
    encoding      : str = "utf-8",
) -> None:
    raw_lines = iter(sp_output_pipe.readline, b'')
    for raw_line in _gen_captured_lines(raw_lines, encoding=encoding):
        captured_lines.append(raw_line)


import threading


def _start_reader(
    sp_output_pipe: typ.IO[bytes], encoding: str = "utf-8"
) -> CapturingThread:
    captured_lines: typ.List[CapturedLine] = []
    read_loop_thread = threading.Thread(
        target=_read_loop, args=(sp_output_pipe, captured_lines, encoding)
    )
    read_loop_thread.start()
    return CapturingThread(read_loop_thread, captured_lines)


class InteractiveSession:
    def __init__(self, cmd, *, env=None, encoding="utf-8") -> None:
        if env is None:
            env = os.environ.copy()

        log.debug(f"popen {cmd}")
        self.encoding = encoding
        self.start    = time.time()
        self._proc    = sp.Popen(
            cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, env=env
        )
        self._retcode: typ.Optional[int] = None

        self._stdout_ct = _start_reader(self._proc.stdout, encoding)
        self._stderr_ct = _start_reader(self._proc.stderr, encoding)

    def send(self, input_str: str) -> None:
        input_data = input_str.encode(self.encoding)
        log.debug(f"sending {len(input_data)} bytes")
        self._proc.stdin.write(input_data)
        self._proc.stdin.flush()
        # The delay is added so the timing of inputs does not
        # get ahead of the captured outputs. This is a stop
        # gap measure.
        time.sleep(0.01)

    @property
    def retcode(self) -> int:
        if self._retcode is None:
            return self.wait()
        else:
            return self._retcode

    def wait(self, timeout=1) -> int:
        if self._retcode is not None:
            return self._retcode

        log.debug(f"wait with timeout={timeout}")
        returncode: typ.Optional[int] = None
        try:
            self._proc.stdin.close()
            max_time = self.start + timeout
            while returncode is None and max_time > time.time():
                # print("poll", max_time - time.time())
                time.sleep(min(0.1, max(0, max_time - time.time())))
                returncode = self._proc.poll()
        finally:
            if self._proc.returncode is None:
                # print("term")
                self._proc.terminate()
                returncode = self._proc.wait()

        self._stdout_ct.thread.join()
        self._stderr_ct.thread.join()
        assert returncode is not None
        self._retcode = returncode
        return returncode

    def _assert_retcode(self) -> None:
        if self._retcode is None:
            raise AssertionError(
                "'InteractiveSession.wait()' must be called "
                + " before accessing captured output."
            )

    def iter_stdout(self) -> typ.Iterable[str]:
        self._assert_retcode()
        for ts, line in self._stdout_ct.lines:
            yield line

    def iter_stderr(self) -> typ.Iterable[str]:
        self._assert_retcode()
        for ts, line in self._stderr_ct.lines:
            yield line

    def __iter__(self) -> typ.Iterable[str]:
        self._assert_retcode()
        all_lines = self._stdout_ct.lines + self._stderr_ct.lines
        for output_line in sorted(all_lines):
            yield output_line.line


block_1 = r"""
import sys
sys.stdout.write("aok1\n")
sys.stdout.flush()
sys.stderr.write("moep\n")
sys.stderr.flush()
assert True
print("aok2")
sys.stdout.flush()
"""

block_2 = r"""
print("aok3")
sys.stdout.flush()
sys.exit()
import time
time.sleep(2)
assert False
print("aok4")
sys.stdout.flush()
"""


def demo():
    cmd = ['python']

    blocks = [block_1, block_2]

    session = InteractiveSession(cmd)

    for content in blocks:
        for line in content.splitlines():
            if line.strip():
                session.send(line + "\n")

    returncode = session.wait()

    all_lines = sorted(
        [(ts, "out", line) for ts, line in session.stdout_lines]
        + [(ts, "err", line) for ts, line in session.stderr_lines]
    )

    for ts, tgt, line in all_lines:
        print(tgt, ts, repr(line))

    # A negative value -N indicates that the child was terminated by signal N (Unix only).
    print("<<<", returncode, session._proc.returncode)

    # wait_ms      = float(block.get('wait_ms', "100"))
    # wait         = wait_ms / 1000
    # content_data = content.encode('utf-8')

    # if block['exit']:
    #     try:
    #         outs, errs = proc.communicate(input=content_data, timeout=wait)
    #     except sp.TimeoutExpired:
    #         print("...", timeout)
    #         proc.kill()
    #         outs, errs = proc.communicate()
    # else:
    #     proc.stdin.write(content_data)
    #     proc.stdin.flush()
    #     time.sleep(wait)
    #     out_lines = []
    #     while True:
    #         out_line = proc.stdout.readline()
    #         print(".,,,,", repr(out_line))
    #         if out_line:
    #             out_lines.append(out_line)
    #         else:
    #             break
    #     outs = b"".join(out_lines)
    #     # errs = proc.stderr.readline()
    #     errs = b"todo"

    # print("##>##" * 20)
    # print(repr(outs.decode('utf-8')))
    # print("?????" * 20)
    # print(repr(errs.decode('utf-8')))
    # print("##<##" * 20)


if __name__ == '__main__':
    demo()
