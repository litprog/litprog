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


class OutputLine(typ.NamedTuple):

    us_ts: float
    line : str


class InteractiveSession:
    def __init__(self, cmd, *, env=None, encoding="utf-8") -> None:
        if env is None:
            env = os.environ.copy()

        self.encoding = encoding
        self.start    = time.time()
        self.proc     = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, env=env)

        self.stdout_lines: typ.List[OutputLine] = []
        self.stderr_lines: typ.List[OutputLine] = []
        stdout_args      = (self.proc.stdout, self.stdout_lines)
        stderr_args      = (self.proc.stderr, self.stderr_lines)
        self.stdout_loop = threading.Thread(target=self.read_loop, args=stdout_args)
        self.stderr_loop = threading.Thread(target=self.read_loop, args=stderr_args)
        self.stdout_loop.start()
        self.stderr_loop.start()

    def read_loop(self, out_buffer: typ.IO[bytes], output_lines: typ.List[OutputLine]) -> None:
        for line_data in iter(out_buffer.readline, b''):
            log.debug(f"read {len(line_data)} bytes")
            us_ts       = round(time.time() * 1_000_000)
            line        = line_data.decode(self.encoding)
            output_line = OutputLine(us_ts, line)
            output_lines.append(output_line)

    def send(self, input_str: str) -> None:
        input_data = input_str.encode(self.encoding)
        log.debug(f"sending {len(input_data)} bytes")
        self.proc.stdin.write(input_data)
        self.proc.stdin.flush()
        # The delay is added so the timing of inputs does not
        # get ahead of the captured outputs. This is a stop
        # gap measure.
        time.sleep(0.01)

    def wait(self, timeout=1) -> typ.Optional[int]:
        log.debug(f"exiting timeout={timeout}")
        returncode = None
        try:
            self.proc.stdin.close()
            max_time = self.start + timeout
            while returncode is None and max_time > time.time():
                # print("poll", max_time - time.time())
                time.sleep(min(0.1, max(0, max_time - time.time())))
                returncode = self.proc.poll()
        finally:
            if self.proc.returncode is None:
                # print("term")
                self.proc.terminate()
                returncode = self.proc.wait()

        self.stdout_loop.join()
        self.stderr_loop.join()
        return returncode


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
    print("<<<", returncode, session.proc.returncode)

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
