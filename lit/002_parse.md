## Parsing

A `Context` object holds all results from the parsing phase. We'll get into the other datastructures used here in a moment, but first let's focus on what we're trying get as a result of parsing. The idea here is to find all the fenced blocks in the markdown files and build mappings/dict objects using the `lpid`/`LitprogID` as keys. Note that there can be multiple `FencedBlocks` with the same `lpid`, which are simply concatenated together. To know how these blocks are to be treated, we collect options for each lpid. In the most simple case such an option is for example the language.

```python
# lpid = context_class
class Context:

    blocks_by_id : typ.Dict[LitprogID, typ.List[FencedBlock]]
    options_by_id: typ.Dict[LitprogID, BlockOptions]

    def __init__(self) -> None:
        bbid = collections.defaultdict(list)

        self.blocks_by_id  = bbid
        self.options_by_id = {}
```

## Functional Core

Everything up to here has been the imperative shell of our command, now we will continue with the functional core that will be tested more thoroughly.

### File-System Utilities

```yaml
filepath: "src/litprog/parse.py"
inputs  : [
    "license_header_boilerplate",
    "common.imports",
    "module_logger",
    "parse.code",
]
```


As a first step, we want to simply scan for markdown files as if invoking `litprog build lit/` with a directory as an argument.

```python
# lpid = parse.code
InputPaths = typ.Sequence[str]
MarkdownPaths = typ.Iterable[pl.Path]

def iter_markdown_filepaths(
    input_paths: InputPaths
) -> MarkdownPaths:
    for in_path_str in input_paths:
        in_path = pl.Path(in_path_str)
        if in_path.is_dir():
            for in_filepath in in_path.glob("**/*.md"):
                yield in_filepath
        else:
            yield in_path
```

```yaml
lpid    : test_parse
lptype  : session
command : /usr/bin/env python3
requires: ['src/litprog/parse.py']
```

```python
# lpid = test_parse
import pathlib2 as pl
import litprog.parse

lit_paths = list(litprog.parse.iter_markdown_filepaths(["lit/"]))

assert len(lit_paths) > 0
assert all(isinstance(p, pl.Path) for p in lit_paths)
assert all(p.suffix == ".md" for p in lit_paths)
```

```python
# lpid = parse.code

class Line(typ.NamedTuple):

    line_no: int
    val    : str


Lines = typ.List[Line]


class RawFencedBlock(typ.NamedTuple):

    file_path  : pl.Path
    info_string: str
    lines      : Lines


LitprogID = str

Lang = str

MaybeLang = typ.Optional[Lang]

BlockOptions = typ.Dict[str, typ.Any]


class FencedBlock(typ.NamedTuple):

    file_path  : pl.Path
    info_string: str
    lines      : Lines
    lpid       : LitprogID
    language   : MaybeLang
    options    : BlockOptions
    content    : str


Block = typ.Union[RawFencedBlock, FencedBlock]
```

