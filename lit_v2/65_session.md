## Interactive Command Session

A code block with `lptype: session` can be used to run arbitrary commands. This is useful for example to run tests which validate generated source code. A session can span multiple code blocks, each line of which is written to stdin of the spawned subprocess.

This module is based (very loosly) on code by ["Eli Bendersky"][eli_bendersky] and ["John Sharp"][john_sharp].

The current implementation was primarilly developed with interactive interpreters in mind such as `bash` and `python`. The input and output to these interpreters is line oriented and can in principle go on forever, but in practice a process will be terminated if a timeout is reached.


### Files for Code and Tests

Code file and imports/preamble.

```yaml
filepath: "src/litprog/session.py"
inputs  : ["boilerplate::*", "session::*"]
```

```python
# lpid = session::imports
import time
import shlex
import threading
import subprocess as sp

import litprog.lptyp as lptyp
```

Test file and imports/preamble.

```yaml
filepath: "test/test_session.py"
inputs  : ["boilerplate::preamble::*", "test_session::*"]
```

```python
# lpid = test_session::imports
import io
import litprog.session as sut

RAW_TEST_TEXT = b"""
Hello \xe4\xb8\x96\xe7\x95\x8c!
foo bar
"""
```

### Streamed Reading of STDOUT and STDERR

Since the subprocess runs concurrently to litprog and since stdout and stderr are written to independently, rough chronological ordering is only possible if we capture timestamps together with and as close as possible to when output was generated. 

We may have to revisit this and abstract it to `CapturedChunk` so that we don't have to rely on line-wise generation of output.

```python
# lpid = session::types
class SessionException(Exception):
    pass


Environ = typ.Mapping[str, str]
# make mypy fail if this is the wrong type
_: Environ = os.environ
```

The `_gen_captured_lines` is basically a constructor for `lptyp.CapturedLine`, but since the only use case is for streaming data it is written as a generator.

```python
# lpid = session::capture_util
def _gen_captured_lines(
    raw_lines: typ.Iterable[bytes],
    encoding : str = "utf-8",
) -> typ.Iterable[lptyp.CapturedLine]:
    for raw_line in raw_lines:
        # get timestamp as fast as possible after
        #   output was read
        ts = time.time()

        line_value = raw_line.decode(encoding)
        log.debug(f"read {len(raw_line)} bytes")
        yield lptyp.CapturedLine(ts, line_value)
```


```python
# lpid = test_session::testcase
def test_gen_captured_lines():
    raw_lines = RAW_TEST_TEXT.strip().splitlines()
    captured_lines = sut._gen_captured_lines(raw_lines)
    lines = [cl.line for cl in captured_lines]
    assert lines == ["Hello ??????!", "foo bar"]
```

The `_read_loop` function runs in a separate thread, consuming either a `STDOUT` or `STDERR` pipe of a subprocess and modifies `captured_lines`, which is an in/out parameter. In other words, it is not a mistake that this function returns `None`. This function does not terminate of itself, but instead it terminates when the pipe is closed, ie. when `readline` returns empty string. 

The term `output` may be a bit confusing here. It refers to the fact that the parameter relates to the output of a subprocess that is to be captured.

```python
# lpid = session::capture_util
def _read_loop(
    sp_output_pipe: typ.IO[bytes],
    captured_lines: typ.List[lptyp.CapturedLine],
    encoding      : str = "utf-8",
) -> None:
    raw_lines = iter(sp_output_pipe.readline, b'')
    cl_gen = _gen_captured_lines(raw_lines, encoding=encoding)
    for cl in cl_gen:
        captured_lines.append(cl)
```

`_start_reader` is a helper function to initialize and start a thread running `_read_loop`.

Note that `captured_lines` list is modified by the created thread and read from by the current thread. This should be fine, as reading only happens after the writer thread has been joined. If the list is accessed before writing is finished, an append might happen during iteration over the list. This convention is enforced by calling `InteractiveSession._assert_retcode()`. 

```python
# lpid = session::capture_util
class CapturingThread(typ.NamedTuple):
    thread: threading.Thread
    lines : typ.List[lptyp.CapturedLine]
```


```python
# lpid = session::capture_util
def _start_reader(
    sp_output_pipe: typ.IO[bytes], encoding: str = "utf-8"
) -> CapturingThread:
    captured_lines: typ.List[lptyp.CapturedLine] = []
    read_loop_thread = threading.Thread(
        target=_read_loop,
        args=(sp_output_pipe, captured_lines, encoding),
    )
    read_loop_thread.start()
    return CapturingThread(read_loop_thread, captured_lines)
```


```python
# lpid = test_session::testcase
def test_start_reader():
    expected = RAW_TEST_TEXT.decode("utf-8")

    raw_text_buf = io.BytesIO(RAW_TEST_TEXT)
    capture_thread = sut._start_reader(raw_text_buf)
    capture_thread.thread.join()

    content = "".join(
        cl.line for cl in capture_thread.lines
    )
    assert content == expected
```


```python
# lpid = session::util
AnyCommand = typ.Union[str, typ.List[str]]

def _normalize_command(command: AnyCommand) -> typ.List[str]:
    if isinstance(command, str):
        return shlex.split(command)
    elif isinstance(command, list):
        return command
    else:
        err_msg = f"Invalid command: {command}"
        raise Exception(err_msg)
```


`InteractiveSession` is the public API of the `session` module. It encapsulates running a process, capturing its output, waiting for it to finish and accesing, the captured output.

```python
# lpid = session::InteractiveSession
class InteractiveSession:

    encoding: str
    start   : float
    end     : float

    _retcode: typ.Optional[int]
    _proc   : sp.Popen

    _in_cl: typ.List[lptyp.CapturedLine]
    _out_ct: CapturingThread
    _err_ct: CapturingThread

    # lpinclude: def __init__
    # lpinclude: def send
    # lpinclude: def _assert_retcode
    # lpinclude: def wait
    # lpinclude: def iter_stdout
    # lpinclude: @property def retcode
    # lpinclude: @property def runtime
```


```python
def __init__(
    self,
    cmd: AnyCommand,
    *,
    env     : typ.Optional[Environ] = None,
    encoding: str = "utf-8",
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
    self._proc = sp.Popen(
        cmd_parts,
        stdin=sp.PIPE,
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        env=_env,
    )

    _enc = encoding

    self._in_cl = []
    self._out_ct = _start_reader(self._proc.stdout, _enc)
    self._err_ct = _start_reader(self._proc.stderr, _enc)
```

The `send` method simply encodes and writes a string to the stdin of the subprocess.

A delay is added at the end so the timing of inputs does not get ahead of the captured outputs. Put differently, it leaves enough time for the subprocess to generate its output and have it be captured before the next input is sent. This is not ideal as it limits execution to 100 lines per second. If it becomes a problem we could introduce `lpflags: nodelay` which would set the delay to 0, with the consequence being that all of the inputs happen at once before any output is captured.

Using the delay causes processing to be waaay slower that we would like it to be. A better approach would be to have markers inserted into the output which can then be parsed to determine the order which the subprocess wrote.


```python
def send(self, input_str: str, delay: float=0.01) -> None:
    self._in_cl.append(lptyp.CapturedLine(time.time(), input_str))
    input_data = input_str.encode(self.encoding)
    log.debug(f"sending {len(input_data)} bytes")
    self._proc.stdin.write(input_data)
    self._proc.stdin.flush()
    if delay:
        time.sleep(delay)
```

```python
def _assert_retcode(self) -> None:
    if self._retcode is None:
        raise AssertionError(
            "'InteractiveSession.wait()' must be called "
            + " before accessing captured output."
        )
```

```python
@property
def retcode(self) -> int:
    return self.wait()
```

TODO: What if the subprocess doesn't end,
    ie. doesn't cooperate after doing terminate?
    maybe retry with more brutal method.

```python
def wait(self, timeout=1) -> int:
    if self._retcode is not None:
        return self._retcode

    log.debug(f"wait with timeout={timeout}")
    returncode: typ.Optional[int] = None
    try:
        self._proc.stdin.close()
        max_time = self.start + timeout
        while (
            returncode is None
            and max_time > time.time()
        ):
            time_left = max_time - time.time()
            # print("poll", max_time - time.time())
            log.debug(f"poll {time_left}")
            time.sleep(
                min(0.01, max(0, time_left))
            )
            returncode = self._proc.poll()
    finally:
        if self._proc.returncode is None:
            log.debug("sending SIGTERM")
            self._proc.terminate()
            returncode = self._proc.wait()

    self._out_ct.thread.join()
    self._err_ct.thread.join()
    assert returncode is not None
    self._retcode = returncode
    self.end = time.time()
    return returncode
```

```python
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
    all_lines = (
        self._in_cl + self._out_ct.lines + self._err_ct.lines
    )
    for captured_line in sorted(all_lines):
        yield captured_line.line
```

Property accessors for convenience.

```python
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
```


```python
# lpid = test_session::testcase

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
    session = sut.InteractiveSession(cmd=["python"])
    for block in [BLOCK_0, BLOCK_1, BLOCK_2]:
        session.send(block)
    retcode = session.wait()
    assert session.stdout == "ok1\nok2ok3"
    assert session.stderr == "moep\n"
    assert retcode == 0
    assert session.runtime < 0.2
```

### Links

[eli_bendersky]: https://eli.thegreenplace.net/2017/interacting-with-a-long-running-child-process-in-python/
[john_sharp]: https://lyceum-allotments.github.io/2017/03/python-and-pipes-part-6-multiple-subprocesses-and-pipes/
