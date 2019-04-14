## Common Type Definitions and Datastructures

The `litprog` program has some types that are used across boundaries of submodules. They are declared in `types.py` and imported as `import litprog.types as lptyp`.

```yaml
filepath     : "src/litprog/lptyp.py"
inputs       : [
    "boilerplate::preamble::*",
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


class RawElement(typ.NamedTuple):

    file_path  : pl.Path
    lines      : Lines


class RawFencedBlock(typ.NamedTuple):

    file_path  : pl.Path
    lines      : Lines
    info_string: str


RawMarkdown = typ.Union[RawElement, RawFencedBlock]


class FencedBlockData(typ.NamedTuple):

    file_path  : pl.Path
    lines      : Lines
    info_string: str
    lpid       : LitProgId
    language   : MaybeLang
    options    : BlockOptions
    content    : str


class FencedBlockMeta(typ.NamedTuple):

    file_path  : pl.Path
    lines      : Lines
    info_string: str
    lpid       : LitProgId
    language   : MaybeLang
    options    : BlockOptions


FencedBlock = typ.Union[FencedBlockData, FencedBlockMeta]
Block = typ.Union[RawFencedBlock, FencedBlockData, FencedBlockMeta]


MardownElement = typ.Union[RawElement, RawFencedBlock]
```


```python
# lpid = types::code

OptionsById = typ.Dict[LitProgId, BlockOptions]


class ParseContext:

    md_paths  : FilePaths
    elements  : typ.List[MardownElement]
    options   : OptionsById
    prev_block: typ.Optional[FencedBlockData]

    def __init__(self) -> None:
        self.md_paths   = []
        self.elements   = []
        self.options    = {}
        self.prev_block = None


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
    elements        : typ.List[MardownElement]
    options         : OptionsById
    captured_outputs: OutputsById
    captured_procs  : ProgResultsById
    
    def __init__(self, pctx: ParseContext) -> None:
        self.md_paths         = pctx.md_paths
        self.elements         = pctx.elements
        self.options          = pctx.options
        self.captured_outputs = {}
        self.captured_procs   = {}
```
