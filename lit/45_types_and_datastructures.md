## Common Type Definitions and Datastructures

The `litprog` program has some types that are used across boundaries of submodules. They are declared in `types.py` and imported as `import litprog.types as lptyp`.

```yaml
filepath     : "src/litprog/types.py"
inputs       : [
    "boilerplate::basic::*",
    "boilerplate::module::imports",
    "types::*",
]
```

### Parse -> Build

These types relate to the interaction between the `parse` and `build` modules. `parse` extracts all code blocks from the markdown files which `build` uses as inputs to generate code files and run the interactive sessions.

    
```python
# lpid = types::code

Lang = str

MaybeLang = typ.Optional[Lang]

LitProgId = str
LitProgIds = typ.List[LitProgId]


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
    lpid       : LitProgId
    language   : MaybeLang
    options    : BlockOptions
    content    : str

Block = typ.Union[RawFencedBlock, FencedBlock]
```


```python
# lpid = types::code

BlocksById  = typ.Dict[LitProgId, typ.List[FencedBlock]]
OptionsById = typ.Dict[LitProgId, BlockOptions]


class ParseContext:

    md_paths: FilePaths
    blocks  : BlocksById
    options : OptionsById

    def __init__(self) -> None:
        self.md_paths = []
        self.blocks   = collections.OrderedDict()
        self.options  = {}


class CapturedLine(typ.NamedTuple):
    ts  : float
    line: str


class ProcResult(typ.NamedTuple):
    exit_code: int
    stdout   : typ.List[CapturedLine]
    stderr   : typ.List[CapturedLine]



OutputsById = typ.Dict[LitProgId, str       ]
ProgResultsById = typ.Dict[LitProgId, ProcResult]


class BuildContext:

    md_paths        : FilePaths
    blocks          : BlocksById
    options         : OptionsById
    captured_outputs: OutputsById
    captured_procs  : ProgResultsById
    
    def __init__(self, pctx: ParseContext) -> None:
        self.md_paths         = pctx.md_paths
        self.blocks           = pctx.blocks
        self.options          = pctx.options
        self.captured_outputs = {}
        self.captured_procs   = {}
```
