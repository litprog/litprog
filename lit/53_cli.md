
## The LitProg Command

Here we generate the `src/litprog/cli.py` file, which has the main entry point for the `litprog` cli command, which is available after running `pip install litprog`.

The module declares/does:

 - `Backtrace` library initialization
 - Logging configuration/initialization
 - The `litprog` cli command using `click`
 - Configuration of the subcommands `build`
 - File system scanning


```yaml
filepath: "src/litprog/cli.py"
inputs  : ["boilerplate::*", "cli::*"]
```


### Entry points

In most cases (when installing with `pip install litprog`) this is strictly speaking not top level script. Instead there is a (platform dependent) file generated from the [`entry_points`][setup_py_entry_points] declared in `setup.py`.


### Backtrace for Nicer Stack Traces

The [`backtrace`](https://github.com/nir0s/backtrace) package produces human friendly tracebacks, but is not a requirement to use litprog. To enable it for just one invocation use `ENABLE_BACKTRACE=1 litprog --help`.

```python
# lpid = cli::code
# To enable pretty tracebacks:
#   echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc
if os.environ.get('ENABLE_BACKTRACE') == '1':
    import backtrace

    backtrace.hook(
        align=True,
        strip_path=True,
        enable_on_envvar_only=True,
    )
```

Note that the `backtrace` library messes with stdout and stderr, so it might not work together nicely with terminal based debuggers. If that's not an issue, you can enable it permanently using `echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc`.


### Logging Configuration

We use the standard python logging module throughout the codebase. Logging is
initialized using this helper function. The verbosity is set using the `--verbose` flag and controls the logging format and the level.

```python
# lpid = cli::code

class LogConfig(typ.NamedTuple):
    fmt: str
    lvl: int


def _parse_logging_config(verbosity: int) -> LogConfig:
    if verbosity == 0:
        return LogConfig(
            "%(levelname)-7s - %(message)s",
            logging.WARNING,
        )

    log_format = (
        "%(asctime)s.%(msecs)03d %(levelname)-7s "
        + "%(name)-15s - %(message)s"
    )
    if verbosity == 1:
        return LogConfig(log_format, logging.INFO)

    assert verbosity >= 2
    return LogConfig(log_format, logging.DEBUG)
```

Since the `--verbose` flag can be set both via the command group (the `cli` function) and via a sub-command, we need to deal with multiple invocations of `_configure_logging`. There are probably nicer ways of doing this if you want to get into the intricacies of the click library. The choice here is to override any previously configured logging only if the previous verbosity was lower.

```python
# lpid = cli::code

def _configure_logging(verbosity: int = 0) -> None:
    _prev_verbosity: int = getattr(_configure_logging, '_prev_verbosity', -1)

    if verbosity <= _prev_verbosity:
        return

    _configure_logging._prev_verbosity = verbosity

    # remove previous logging handlers
    for handler in list(logging.root.handlers):
        logging.root.removeHandler(handler)

    log_cfg = _parse_logging_config(verbosity)
    logging.basicConfig(
        level=log_cfg.lvl,
        format=log_cfg.fmt,
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
```


### CLI Command Group `litprog`

Since we're declaring the entry point here, we import most of the other modules directly (and all of them indirectly). While other modules are written in a functional style and have unit tests, this module represents the [imperative shell](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell) and thus only has a basic integration test. 

```python
# lpid = cli::code
import click

import litprog.parse
import litprog.build
import litprog.session
import litprog.types as lptyp
```

We'll be using the venerable [click][ref_click_lib] library to implement our CLI. `click` complains about use of `from __future__ import unicode_literals` [for some reason that I haven't dug into yet][ref_click_py3]. In the course of compiling LitProg to universal python using `lib3to6` the import is added. 

As far as I can tell, everything is behaving as expected, at least using ascii filenames, so the following is used to supress the warning.

```python
# lpid = cli::code
click.disable_unicode_literals_warning = True
```

We could implement `litprog` as one command atm. but in anticipation of future subcommands we'll use the `click.group` approach to implement git style cli with subcommands.

```python
# lpid = cli::code

verbosity_option = click.option(
    '-v',
    '--verbose',
    count=True,
    help="Control log level. -vv for debug level.",
)


@click.group()
@click.version_option(version="v201901.0001-alpha")
@verbosity_option
def cli(verbose: int = 0) -> None:
    """litprog cli."""
    _configure_logging(verbose)
```


### CLI sub-command `litprog build`

The `litprog build` is the main subcommand. It recursively scans the `input_paths` argument for markdown files, parses them (creating a context object) and then uses the context to build the various outputs (source files, html and pdf). 

```python
# lpid = cli::code
@cli.command()
@click.argument(
    'input_paths',
    nargs=-1,
    type=click.Path(exists=True),
)
@verbosity_option
def build(
    input_paths: InputPaths,
    verbose    : int = 0,
) -> None:
    _configure_logging(verbose)
    # TODO: figure out how to share this code between sub-commands
    md_paths = sorted(_iter_markdown_filepaths(input_paths))
    if len(md_paths) == 0:
        log.error("No markdown files found for {input_paths}.")
        click.secho("No markdown files found", fg='red')
        sys.exit(1)

    ctx = litprog.parse.parse_context(md_paths)
    try:
        sys.exit(litprog.build.build(ctx))
    except litprog.session.SessionException:
        sys.exit(1)
```


### CLI sub-command `litprog sync-manifest`

`litprog sync-manifest` may eventually be implemented as a plugin, but until the plugin system is ready (and to get an idea of how to implement the plugin system), it is implemented as a sub-command


```python
# lpid = cli::code
@cli.command()
@click.argument(
    'input_paths',
    nargs=-1,
    type=click.Path(exists=True),
)
@verbosity_option
def sync_manifest(
    input_paths: InputPaths,
    verbose    : int = 0,
) -> None:
    _configure_logging(verbose)
    # TODO: figure out how to share this code between sub-commands
    md_paths = sorted(_iter_markdown_filepaths(input_paths))
    if len(md_paths) == 0:
        log.error("No markdown files found for {input_paths}.")
        click.secho("No markdown files found", fg='red')
        sys.exit(1)

    ctx = litprog.parse.parse_context(md_paths)

    maybe_manifest = _parse_manifest(ctx)
    if maybe_manifest is None:
        return _init_manifest(ctx)
    else:
        return _sync_manifest(ctx, maybe_manifest)
```


#### Sync Manifest and File System


```python
# lpid = cli::code
FileId = str
PartId = str
ChapterId = str
ChapterNum = str    # eg. "00"
ChapterKey = typ.Tuple[PartId, ChapterId]


class ChapterItem(typ.NamedTuple):
    num       : ChapterNum
    part_id   : PartId
    chapter_id: ChapterId
    md_path   : pl.Path


ChaptersByKey = typ.Dict[ChapterKey, ChapterItem]

Manifest = typ.List[FileId]


def _sync_manifest(
    ctx: lptyp.ParseContext,
    manifest: Manifest,
) -> ExitCode:
    chapters: ChaptersByKey = _parse_chapters(ctx)

    # TODO: probably it's better to put the manifest in a config file
    #   and keep the markdown files a little bit cleaner. 
    chapters_by_file_id: typ.Dict[FileId, ChapterItem] = {}

    for file_id in manifest:
        if "::" not in file_id:
            errmsg = f"Invalid file id in manifest {file_id}"
            click.secho(errmsg, fg='red')
            return 1

        part_id, chapter_id = file_id.split("::", 1)
        chapter_key = (part_id, chapter_id)
        chapter_item = chapters.get(chapter_key)
        if chapter_item is None:
            # TODO: deal with renaming,
            #   maybe best guess based on ordering
            raise KeyError(chapter_key)
        else:
            chapters_by_file_id[file_id] = chapter_item

    renames: typ.List[typ.Tuple[pl.Path, pl.Path]] = []

    # TODO: padding when indexes are > 9

    part_index = 1
    chapter_index = 1
    prev_part_id = ""

    for file_id in manifest:
        part_id, chapter_id = file_id.split("::", 1)

        if prev_part_id and part_id != prev_part_id:
            part_index += 1
            chapter_index = 1

        chapter_item = chapters_by_file_id[file_id]

        path = chapter_item.md_path
        ext = path.name.split(".", 1)[-1]

        new_chapter_num = f"{part_index}{chapter_index}"
        new_filename = f"{new_chapter_num}_{chapter_id}.{ext}"
        new_filepath = path.parent / new_filename

        if new_filepath != path:
            renames.append((path, new_filepath))

        chapter_index += 1
        prev_part_id = part_id

    if not any(renames):
        return 0

    for src, tgt in renames:
        print(f"    {str(src):<35} -> {str(tgt):<35}")

    # TODO: perhaps rename should check for git and
    #   do git mv src tgt

    prompt = "Do you want to perform these renaming(s)?"
    if click.confirm(prompt):
        for src, tgt in renames:
            src.rename(tgt)

    return 0


CHAPTER_NUM_RE = re.compile(r"^[0-9A-Za-z]{2,3}_")


def _parse_chapters(ctx: lptyp.ParseContext) -> ChaptersByKey:
    chapters: ChaptersByKey = {}

    part_index = "1"
    chapter_index = "1"

    # first chapter_id is the first part_id
    part_id = ""

    for path in sorted(ctx.md_paths):
        basename = path.name.split(".", 1)[0]
        if "_" in basename and CHAPTER_NUM_RE.match(basename):
            chapter_num, chapter_id = basename.split("_", 1)
            this_part_index = chapter_num[0]
            if this_part_index != part_index:
                part_id = chapter_id
                part_index = this_part_index
            chapter_index = chapter_num[1]
        else:
            chapter_id = basename
            # auto generate chapter number
            chapter_num = part_index + chapter_index
            chapter_index = chr(ord(chapter_index) + 1)

        if part_id == "":
            part_id = chapter_id

        chapter_key = (part_id, chapter_id)
        chapter_item = ChapterItem(
            chapter_num,
            part_id,
            chapter_id,
            path,
        )
        chapters[chapter_key] = chapter_item 

    return chapters


def _parse_manifest(ctx: lptyp.ParseContext) -> typ.Optional[Manifest]:
    for blocks in ctx.blocks.values():
        for block in blocks:
            if block.options.get('lptype') != 'meta':
                continue
            manifest = block.options.get('manifest')
            if manifest is None:
                continue
            return manifest

    return None


def _init_manifest(ctx: lptyp.ParseContext) -> ExitCode:
    first_md_filepath = min(ctx.md_paths)
    print(
        f"Manifest not found. ", 
        f"Would you like to create one in",
        first_md_filepath
    )
    print("_init_manifest() not implemented")
    return 1

```


### Scanning for Markdown Files

These are the supported file extensions. It may may be worth revisiting this (for example by introducing a dedicated `.litmd` file extension), but for now I expect projects to have a dedicated directory with markdown files and this approach captures the broadest set of files.

```python
# lpid = cli::code

MARKDOWN_FILE_EXTENSIONS = {
    "markdown",
    "mdown",
    "mkdn",
    "md",
    "mkd",
    "mdwn",
    "mdtxt",
    "mdtext",
    "text",
    "Rmd",
}
```

This helper function scans the file system based on arguments to a subcommand. Note that paths that are passed directly as arguments are always selected, regardless of extension, but files that are in sub-directories are only selected if they have one of the [known extensions for markdown files][ref_md_file_extensons].


```python
# lpid = cli::code
def _iter_markdown_filepaths(
    input_paths: InputPaths
) -> FilePaths:
    for path_str in input_paths:
        path = pl.Path(path_str)
        if path.is_file():
            yield path
        else:
            for ext in MARKDOWN_FILE_EXTENSIONS:
                for fpath in path.glob(f"**/*.{ext}"):
                    yield fpath
```


### The `__main__` Module

In order to also be able to run when invoked with `python -m litprog`, we need to define a `__main__.py` file.

```yaml
filepath     : "src/litprog/__main__.py"
is_executable: true
inputs       : [
    "shebang_python",
    "boilerplate::preamble::*",
    "__main__::*",
]
```

The shebang line is mostly symbolic and indicates, (in case it wasn't obvious) that `src/litprog/__main__.py` is a top level script. 

```python
# lpid = shebang_python
#!/usr/bin/env python
```

```python
# lpid = __main__::code
import litprog.cli

if __name__ == '__main__':
    litprog.cli.cli()
```


### Basic Integration Test

This is a good starting point for tests. Just as a sanity check, let's see if we can import and access the `log` logger.

```yaml
filepath     : "test/test_cli.py"
inputs       : ["boilerplate::preamble::*", "test_cli"]
```

```python
# lpid = test_cli
import litprog.cli as sut

def test_sanity():
    assert sut.log.name == 'litprog.cli'
```


[ref_click_lib]: https://click.palletsprojects.com

[ref_click_py3]: https://click.palletsprojects.com/en/5.x/python3/

[ref_md_file_extensons]: https://superuser.com/questions/249436/file-extension-for-markdown-files
