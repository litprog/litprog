## Test Setup

### Testing Performance

For devs to not get frustrated with testing, and for them to not resent the practice of testing, it is important for tests to be as fast as possible. Creating an interactive session is pretty fast, but even just importing the `litprog.cli` cli module can take 300-400ms, so testing using interactive sessions would slow things down quite a bit. Unfortunately this messes with the capturing of output, which technically is generated all in one subprocess which invokes the `pytest` command.

The workaround is to have the output capture be a second pass over the output of the test run. This way the generated documents still accuratly refelct the correctness based on executed tests.

We want to run using [`py.test`][ref_pytest], which allows us to import the (stateless) `litprog` library only once and thus ammortize the cost of the imports.

### Test Execution


Some care must be taken to not reuse output from a previous test run. We'll be writing to `/tmp/litprog_test.log`, so we start off by overwriting any previous execution.

```yaml
lpid   : test_start_marker
lptype : session
command: python3
```

Using `mode="w"` to overwrite any previously captured output.

```python
# lpid = test_start_marker
import datetime as dt

ts = dt.datetime.utcnow().isoformat()
with open("/tmp/litprog_test.log", mode="w") as fh:
    fh.write(f"Starting Test Session {ts}\n")
```


```yaml
lpid   : run_pytest
lptype : session
command: bash
timeout: 5
requires: ["src/litprog/*.py", "test/*.py"]
```

TODO:

 - Optional Test Filtering using `-k <filter>`
 - How to run in debug mode ie. make `--capture=no` work
 - code coverage
 - --disable-warnings

```python
# lpid = run_pytest
set -o errexit;
export ENABLE_BACKTRACE=0;
export PYTHONPATH=src/:vendor/:$$PYTHONPATH;

/usr/bin/env pytest \
    --verbose \
    --color=yes \
    --disable-warnings \
    --cov-report term \
    test/ \
    >> /tmp/litprog_test.log 2>&1;
```


### Test Output Parsing

TODO: capture output of coverage for individual tests


### Test Coverage Parsing

TODO: capture output of coverage for individual functions


[ref_pytest]: https://pytest.org
