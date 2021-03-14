# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

# pylint: disable=protected-access

import io

import litprog.session as sut

RAW_TEST_TEXT = b"""
Hello \xe4\xb8\x96\xe7\x95\x8c!
foo bar
"""


def test_gen_captured_lines():
    raw_lines      = RAW_TEST_TEXT.strip().splitlines()
    captured_lines = sut._gen_captured_lines(raw_lines)
    lines          = [cl.line for cl in captured_lines]
    assert lines == ["Hello 世界!", "foo bar"]


def test_start_reader():
    expected = RAW_TEST_TEXT.decode("utf-8")

    raw_text_buf   = io.BytesIO(RAW_TEST_TEXT)
    capture_thread = sut._start_reader(raw_text_buf)
    capture_thread.thread.join()

    content = "".join(cl.line for cl in capture_thread.lines)
    assert content == expected


BLOCK_0 = r"""
import sys

def out(s: str):
    sys.stdout.write(s)
    sys.stdout.flush()

def err(s: str):
    sys.stderr.write(s)
    sys.stderr.flush()
"""

BLOCK_1 = r"""
out("ok1\n")
err("moep\n")
assert True
out("ok2")
"""

BLOCK_2 = r"""
out("ok3")
sys.exit(0)
import time
time.sleep(2)
assert False
out("ok4")
"""


def test_integration():
    session = sut.InteractiveSession(cmd=['python3'])
    for block in [BLOCK_0, BLOCK_1, BLOCK_2]:
        session.send(block)
    retcode = session.wait()
    assert session.stdout == "ok1\nok2ok3"
    assert session.stderr == "moep\n"
    assert retcode        == 0
    assert session.runtime < 0.5
