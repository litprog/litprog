## Build: Process Fenced Blocks

The purpose of the `build` module is to

    1. Generate the program files that can be executed
    2. Run any interactive sessions to illustrate or validate the program


```yaml
filepath     : "src/litprog/build.py"
inputs       : ["boilerplate::*", "build::*"]
```

```python
# lpid = build::code
import signal
import fnmatch

import litprog.parse
import litprog.session
import litprog.lptyp as lptyp
```


```python
class GeneratorResult:
    output: typ.Optional[str]
    done  : bool
    error : bool

    def __init__(self,
        output: typ.Optional[str] = None,
        *,
        done  : typ.Optional[bool] = None,
        error : bool = False,
    ) -> None:
        self.output = output
        if done is None:
            self.done = output is not None
        else:
            self.done = done
        self.error = error


GeneratorFunc = typ.Callable[
    [lptyp.BuildContext, lptyp.LitProgId],
    GeneratorResult,
]
```


```python
def gen_meta_output(
    ctx : lptyp.BuildContext,
    lpid: lptyp.LitProgId,
) -> GeneratorResult:
    log.warning(f"lptype=meta not implemented")
    return GeneratorResult(done=True)
```


```python
def _iter_lpid_blocks(
    ctx : lptyp.BuildContext,
    lpid: lptyp.LitProgId,
) -> typ.Iterable[lptyp.FencedBlock]:
    for elem in ctx.elements:
        if isinstance(elem, lptyp.FencedBlockData):
            if elem.lpid == lpid:
                yield elem


def gen_raw_block_output(
    ctx : lptyp.BuildContext,
    lpid: lptyp.LitProgId,
) -> GeneratorResult:
    output = "".join(
        block.content
        for block in _iter_lpid_blocks(ctx, lpid)
    )
    return GeneratorResult(output)
```

NOTE: Now that we have glob expansion on ids, this may be obsolete. A vast majority of use cases for this may be covered with a simple naming convention.

```python
def gen_multi_block_output(
    ctx : lptyp.BuildContext,
    lpid: lptyp.LitProgId,
) -> GeneratorResult:
    log.warning(f"lptype=multi_block not implemented")
    return GeneratorResult(done=True)
```

```python
def parse_all_ids(
    ctx: lptyp.BuildContext
) -> typ.Sequence[lptyp.LitProgId]:
    return list(ctx.options.keys())
```

```python
def iter_expanded_lpids(
    ctx  : lptyp.BuildContext,
    lpids: typ.Iterable[lptyp.LitProgId],
) -> typ.Iterable[lptyp.LitProgId]:
    all_ids = parse_all_ids(ctx)
    for glob_or_lpid in lpids:
        is_lp_id = not (
            "*" in glob_or_lpid or "?" in glob_or_lpid
        )
        if is_lp_id:
            yield glob_or_lpid
            continue

        lpid_pat = fnmatch.translate(glob_or_lpid)
        lpid_re = re.compile(lpid_pat)
        for lpid in all_ids:
            if lpid_re.match(lpid):
                yield lpid
```

```python
def parse_missing_ids(
    ctx : lptyp.BuildContext,
    lpid: lptyp.LitProgId,
) -> typ.Set[lptyp.LitProgId]:
    captured_ids   = set(ctx.captured_outputs.keys())

    options      = ctx.options[lpid]
    required_ids = set(options.get('requires', []))
    if options['lptype'] == 'out_file':
        required_ids |= set(options['inputs'])

    required_ids = set(iter_expanded_lpids(ctx, required_ids))

    return required_ids - captured_ids
```

NOTE: In some cases the order of lpids doesn't matter, but in the case of inputs it does. Unless explicitly wrapped with `set(lpids)`, the lpids are in the order they were declared.


```python
def parse_input_ids(
    options: lptyp.BlockOptions,
) -> lptyp.LitProgIds:
    maybe_input_ids = options['inputs']
    # TODO: validate
    return typ.cast(lptyp.LitProgIds, maybe_input_ids)
```

```python
def gen_out_file_output(
    ctx : lptyp.BuildContext,
    lpid: lptyp.LitProgId,
) -> GeneratorResult:
    options      = ctx.options[lpid]
    input_lpids  = parse_input_ids(options)
    input_lpids  = iter_expanded_lpids(ctx, input_lpids)
    output_parts = [
        ctx.captured_outputs[input_lpid]
        for input_lpid in input_lpids
    ]

    # TODO: Add preulude/postscript for each block
    #   this may be needed to read content back in
    #   after running code formatting.
    # prelude_tmpl    = options.get('block_prelude')
    # postscript_tmpl = options.get('block_postscript')

    output = "".join(output_parts)
    return GeneratorResult(output)
```

TODO (mb):
 - better output capture for sessions
   maybe the [`pty`](https://docs.python.org/3/library/pty.html)
   module will be helpful
 - expand wildcards, e.g. `'src/litprog/*.py'`
 - option to ignore exit codes

```python
TIMEOUT_RETCODE = -signal.SIGTERM.value


def gen_session_output(
    ctx : lptyp.BuildContext,
    lpid: lptyp.LitProgId,
) -> GeneratorResult:
    options      = ctx.options[lpid]
    timeout      = options.get('timeout', 2)

    command = options.get('command', "bash")
    log.info(f"starting session {lpid}. cmd: {command}")
    isession = litprog.session.InteractiveSession(command)

    keepends = True
    for block in _iter_lpid_blocks(ctx, lpid):
        for line in block.content.splitlines(keepends):
            isession.send(line)

    exit_code  = isession.wait(timeout=timeout)
    runtime_ms = isession.runtime * 1000
    log.info(f"  session block {lpid:<35} runtime: {runtime_ms:9.3f}ms")
    output     = "".join(iter(isession))

    expected_exit_code = options.get('expected_exit_code', 0)
    if exit_code == expected_exit_code:
        log.info(f"  session block {lpid:<35} done ok. RETCODE: {exit_code}")
        return GeneratorResult(output)
    elif exit_code == TIMEOUT_RETCODE:
        log.error(
            f"  session block {lpid:<35} done fail. " +
            f"Timout of {timeout} exceeded."
        )
        sys.stderr.write(output)
        return GeneratorResult(output, error=True)
    else:
        log.error(
            f"  session block {lpid:<35} done fail. " +
            f"RETCODE: {exit_code} invalid!"
        )
        sys.stderr.write(output)
        err_msg = f"Error processing session {lpid}"
        log.error(err_msg)
        # TODO: This is a bit harsh to do here. Probably
        #   we should raise an exception.
        return GeneratorResult(error=True)
```


```python
OUTPUT_GENERATORS_BY_TYPE: typ.Mapping[str, GeneratorFunc] = {
    'meta'       : gen_meta_output,
    'raw_block'  : gen_raw_block_output,
    'multi_block': gen_multi_block_output,
    'out_file'   : gen_out_file_output,
    'session'    : gen_session_output,
}
```


```python
def write_output(
    lpid: lptyp.LitProgId,
    ctx: lptyp.BuildContext,
) -> None:
    options = ctx.options[lpid]
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
```


```python
def build(parse_ctx: lptyp.ParseContext) -> ExitCode:
    ctx = lptyp.BuildContext(parse_ctx)
    all_ids = parse_all_ids(ctx)

    while len(ctx.captured_outputs) < len(all_ids):

        assert len(ctx.options) == len(all_ids)

        prev_len_completed = len(ctx.captured_outputs)
        for lpid, options in sorted(ctx.options.items()):
            if lpid in ctx.captured_outputs:
                continue

            missing_ids = parse_missing_ids(ctx, lpid)
            if any(missing_ids):
                continue

            litprog_type: str = options['lptype']
            generator_func = OUTPUT_GENERATORS_BY_TYPE.get(litprog_type)
            if generator_func is None:
                log.error(f"lptype={litprog_type} not implemented")
                return 1

            res: GeneratorResult = generator_func(ctx, lpid)
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

        if prev_len_completed < len(ctx.captured_outputs):
            continue

        log.error(f"Build failed: Unresolved requirements.")

        captured_block_ids = set(ctx.captured_outputs.keys())
        remaining_block_ids = sorted(set(all_ids) - captured_block_ids)
        for block_id in remaining_block_ids:
            missing_ids = parse_missing_ids(ctx, lpid)
            log.error(
                f"Not Completed: '{block_id}'."
                + f" Missing requirements: {missing_ids}"
            )
        return 1
    return 0
```


### Future Work

#### Temporary Directory

As of now, each output file is written to directly. It may be better (or at least give the option) to write output to a temporary directory first and only move the generated files to the working directory if the build succeeded.


### Metaprogramming

 - tagging infrastructure
 - block transformesr
 - build phases/stages



### Delete Old Files?

Should files that were previously generated be removed? If a file is renamed in the markdown source, then files by the old are not touched. To support this, we would have to implement some kind of manifest, to keep track of files from previous builds.


#### Parallel Build Steps

For now the build is completely linear, but eventually we may want to speed
things up. This is something to keep in mind when making design decisions

A very interesting approach to dealing with log output produced by parallel
build steps: [redo, buildroot, and serializing parallel logs](https://apenwarr.ca/log/20181106)

Long story short, the log output of a build step is persisted and only
written to stdout incrementally if it belongs the first and lowest level
step.

~~~
# lpid: redo_illustration
t01  A: redo J
t02  J:   ...stuff...
t03  J:   redo X
t04  X:     redo Q
t05  Q:       ...build Q...
t06  X:     ...X stuff...
t06  J:   redo Y
t06  Y:     redo Q
t07  Y:     ...Y stuff...
t08  J:   redo Z
t08  Z:     redo Q
t08  Z:     ...Z stuff...
t08  J:   ...stuff...
t08  A: exit 0
~~~

Notice that the output which belonged to the concurrently running steps was
buffered and written all at once only after steps which were started
earlier or as its own dependencies were completed.


#### Partial/Incremental Build

For slow builds it might be worth implementing something to build/run only subsets of the program.


#### Transparent Handling of stdin/stdout/stderr for Debugging

To enable terminal based debuggers and so that users can drop into a shell by creating a breakpoint, we should investigate if there is a mode where we don't capture the output of subprocesses, but instead pass everything through transparently. This would presumably imply a serial build.



