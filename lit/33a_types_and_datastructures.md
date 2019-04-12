# Common Type Definitions

The `litprog` program has some types that are used across boundaries of submodules. They are declared in `types.py` and imported as `import litprog.types as lptyp`.

```yaml
filepath     : "src/litprog/types.py"
inputs       : [
    "license_header_boilerplate",
    "generated_preamble",
    "common.imports",
    "types.code",
]
```

## Parse -> Build

These types relate to the interaction between the `parse` and `build` modules. `parse` extracts all code blocks from the markdown files which `build` uses as inputs to generate code files and run the interactive sessions.

    
```python
# lpid = types.code

Lang = str

MaybeLang = typ.Optional[Lang]

LitprogID = str


class Line(typ.NamedTuple):

    line_no: int
    val    : str


Lines = typ.List[Line]

BlockOptions = typ.Dict[str, typ.Any]


class RawFencedBlock(typ.NamedTuple):

    file_path  : pl.Path
    info_string: str
    lines      : Lines


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


```python
# lpid = types.code

BlocksById  = typ.Dict[LitprogID, typ.List[FencedBlock]]
OptionsById = typ.Dict[LitprogID, BlockOptions]


class ParseContext:

    blocks : BlocksById
    options: OptionsById

    def __init__(self) -> None:
        self.blocks  = collections.defaultdict(list)
        self.options = {}


class CapturedLine(typ.NamedTuple):
    ts  : float
    line: str


class ProcResult(typ.NamedTuple):
    exit_code: int
    stdout   : typ.List[CapturedLine]
    stderr   : typ.List[CapturedLine]



OutputsById = typ.Dict[LitprogID, str       ]
ProgResultsById = typ.Dict[LitprogID, ProcResult]


class BuildContext:

    blocks          : BlocksById
    options         : OptionsById
    captured_outputs: OutputsById
    captured_procs  : ProgResultsById
    
    def __init__(self, pctx: ParseContext) -> None:
        self.blocks = pctx.blocks
        self.options = pctx.options
        self.captured_outputs = {}
        self.captured_procs = {}
```
