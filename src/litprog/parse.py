# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import re
import typing as typ
import logging
import pathlib as pl

import toml
import yaml

logger = logging.getLogger(__name__)


FilePaths = typ.Iterable[pl.Path]

MD_FRONT_MATTER = 'front_matter'

MD_HEADLINE   = 'headline'
MD_PARAGRAPH  = 'paragraph'
MD_LIST       = 'list'
MD_BLOCKQUOTE = 'blockquote'

# https://python-markdown.github.io/extensions/definition_lists/
MD_DEF_LIST = 'def_list'

# https://python-markdown.github.io/extensions/footnotes/
MD_FOOTNOTE_DEF = 'footnote_def'

MD_BLOCK = 'block'

VALID_ELEMENT_TYPES = {
    MD_FRONT_MATTER,
    MD_HEADLINE,
    MD_PARAGRAPH,
    MD_LIST,
    MD_BLOCKQUOTE,
    MD_DEF_LIST,
    MD_FOOTNOTE_DEF,
    MD_BLOCK,
}

NON_CODE_BLOCKS = ('bob', 'math')

MarkdownElementType = str

FrontMatterMetadata = typ.Dict[str, typ.Any]

DEFAULT_FRONT_MATTER_META = {'lang': "en-US", 'title': "-"}


FRONT_MATTER_PATTERN = r"^(\+\+\+|\-\-\-)$"

FRONT_MATTER_RE = re.compile(FRONT_MATTER_PATTERN, flags=re.MULTILINE)


HEADLINE_PATTERN_A = r"""
    ^
    (?P<headline_marker_a>[#]+)
    (?P<headline_text_a>[^#\n]+)
    ([#]*)?
"""


HEADLINE_PATTERN_B = r"""
    ^
    (?P<headline_text_b>.*)\n
    (?P<headline_marker_b>=+|-+)
"""


BLOCK_START_PATTERN = r"""
    ^
    (?P<block_fence>```|~~~)
    (?P<info_string>[^\n]*)?
"""

ELEMENT_PATTERN = f"""
    (?:{HEADLINE_PATTERN_A})
    | (?:{HEADLINE_PATTERN_B})
    | (?:{BLOCK_START_PATTERN})
"""

# https://regex101.com/r/cSbfvF/35
IMAGE_URL_PATTERN = r"""
!\[
  (?P<alt>[^\]]*)
\]
\(
  (?P<url>.*?)(?=\"|\))
  (?P<title>\".*\")?
\)
"""

LANGUAGE_COMMENT_PATTERNS = {
    "c++"          : (r"^\s*//"  , r"$"),
    'actionscript' : (r"^\s*//"  , r"$"),
    'actionscript3': (r"^\s*//"  , r"$"),
    'bash'         : (r"^\s*[#]" , r"$"),
    'c'            : (r"^\s*//"  , r"$"),
    'd'            : (r"^\s*//"  , r"$"),
    'elixir'       : (r"^\s*[#]" , r"$"),
    'erlang'       : (r"^\s*%"   , r"$"),
    'go'           : (r"^\s*//"  , r"$"),
    'zig'          : (r"^\s*//"  , r"$"),
    'java'         : (r"^\s*//"  , r"$"),
    'javascript'   : (r"^\s*//"  , r"$"),
    'json'         : (r"^\s*//"  , r"$"),
    'swift'        : (r"^\s*//"  , r"$"),
    'r'            : (r"^\s*//"  , r"$"),
    'php'          : (r"^\s*//"  , r"$"),
    'svg'          : (r"^\s*<!--", r"-->"),
    'html'         : (r"^\s*<!--", r"-->"),
    'css'          : (r"^\s*/\*" , r"\*/"),
    'csharp'       : (r"^\s*//"  , r"$"),
    'fsharp'       : (r"^\s*//"  , r"$"),
    'kotlin'       : (r"^\s*//"  , r"$"),
    'make'         : (r"^\s*[#]" , r"$"),
    'nim'          : (r"^\s*[#]" , r"$"),
    'perl'         : (r"^\s*[#]" , r"$"),
    'yaml'         : (r"^\s*[#]" , r"$"),
    'prolog'       : (r"^\s*%"   , r"$"),
    'scheme'       : (r"^\s*;"   , r"$"),
    'clojure'      : (r"^\s*;"   , r"$"),
    'lisp'         : (r"^\s*;"   , r"$"),
    'coffee-script': (r"^\s*[#]" , r"$"),
    'python'       : (r"^\s*[#]" , r"$"),
    'ruby'         : (r"^\s*[#]" , r"$"),
    'rust'         : (r"^\s*//"  , r"$"),
    'scala'        : (r"^\s*//"  , r"$"),
    'sh'           : (r"^\s*[#]" , r"$"),
    'shell'        : (r"^\s*[#]" , r"$"),
    'sql'          : (r"^\s*--"  , r"$"),
    'typescript'   : (r"^\s*//"  , r"$"),
}


LANGUAGE_COMMENT_TEMPLATES = {
    "c++"          : "// {}",
    'actionscript' : "// {}",
    'actionscript3': "// {}",
    'bash'         : "# {}",
    'c'            : "// {}",
    'd'            : "// {}",
    'elixir'       : "# {}",
    'erlang'       : "% {}",
    'go'           : "// {}",
    'zig'          : "// {}",
    'java'         : "// {}",
    'javascript'   : "// {}",
    'json'         : "// {}",
    'swift'        : "// {}",
    'r'            : "// {}",
    'php'          : "// {}",
    'svg'          : "<!-- {} -->",
    'html'         : "<!-- {} -->",
    'css'          : "/* {} */",
    'csharp'       : "// {}",
    'fsharp'       : "// {}",
    'kotlin'       : "// {}",
    'make'         : "# {}",
    'nim'          : "# {}",
    'perl'         : "# {}",
    'yaml'         : "# {}",
    'prolog'       : "% {}",
    'scheme'       : "; {}",
    'clojure'      : "; {}",
    'lisp'         : "; {}",
    'coffee-script': "# {}",
    'python'       : "# {}",
    'ruby'         : "# {}",
    'rust'         : "// {}",
    'scala'        : "// {}",
    'sh'           : "# {}",
    'shell'        : "# {}",
    'sql'          : "-- {}",
    'typescript'   : "// {}",
}


def _re(pattern: str) -> typ.Pattern:
    return re.compile(pattern, flags=re.VERBOSE | re.MULTILINE)


LANGUAGE_COMMENT_REGEXES = {
    lang: (_re(start_pattern), _re(end_pattern))
    for lang, (start_pattern, end_pattern) in LANGUAGE_COMMENT_PATTERNS.items()
}

KNOWN_INFO_STRINGS = {
    'math',
    'bob',
    'aafigure',
}

KNOWN_INFO_STRINGS.update(LANGUAGE_COMMENT_REGEXES.keys())


ELEMENT_RE = _re(ELEMENT_PATTERN)

HEADLINE_RE_A = _re(HEADLINE_PATTERN_A)
HEADLINE_RE_B = _re(HEADLINE_PATTERN_B)

BLOCK_START_RE = _re(BLOCK_START_PATTERN)

BLOCK_END_RE = {"```": _re(r"^```"), "~~~": _re(r"^~~~")}

IMAGE_URL_RE = _re(IMAGE_URL_PATTERN)


class ImageTag(typ.NamedTuple):
    alt  : str
    url  : str
    title: str


class _RawMarkdownElement(typ.NamedTuple):

    md_type   : MarkdownElementType
    first_line: int
    content   : str


# NOTE (mb 2019-05-30): The word "Successor" refers
#   to the relationship of a MarkdownElement to a
#   modified version of itself. It does _not_ refer to
#   it's document position relative to another.
Successor = typ.Optional['MarkdownElement']


class MarkdownElement:

    md_path   : pl.Path
    first_line: int
    elem_index: int
    md_type   : MarkdownElementType
    content   : str
    _successor: typ.Optional[typ.Any]

    # Recursive types not fully supported yet;
    # this class can be changed to a NamedTuple once they are.
    # Successor  : typ.Optional['MarkdownElement']
    @property
    def successor(self) -> Successor:
        return typ.cast(Successor, self._successor)

    def __init__(
        self,
        md_path   : pl.Path,
        first_line: int,
        elem_index: int,
        md_type   : MarkdownElementType,
        content   : str,
        successor : Successor,
    ) -> None:
        assert md_type in VALID_ELEMENT_TYPES
        self.md_path    = md_path
        self.first_line = first_line
        self.elem_index = elem_index
        self.md_type    = md_type
        self.content    = content
        self._successor = successor

    def __repr__(self) -> str:
        addr = hex(id(self))
        return (
            "MarkdownElement("
            + f"'{self.md_path}', "
            + f"{self.first_line}, "
            + f"{self.elem_index}, "
            + f"'{self.md_type}', "
            + f"...) at {addr}"
        )

    def clone(self) -> 'MarkdownElement':
        return MarkdownElement(
            md_path=self.md_path,
            first_line=self.first_line,
            elem_index=self.elem_index,
            md_type=self.md_type,
            content=self.content,
            successor=self._successor or self,
        )


MarkdownElements      = typ.List[MarkdownElement]
MaybeMarkdownElements = typ.Optional[MarkdownElements]


class Headline(typ.NamedTuple):

    md_path   : pl.Path
    elem_index: int
    text      : str
    level     : int


InfoString = str


class Directive(typ.NamedTuple):

    name : str
    value: str

    raw_text: str


class Block(typ.NamedTuple):

    md_path           : pl.Path
    namespace         : str
    first_line        : int
    elem_index        : int
    info_string       : InfoString
    directives        : typ.List[Directive]
    content           : str
    inner_content     : str
    includable_content: str


VALID_DIRECTIVE_NAMES = {
    'language',
    # block composition
    'def',
    'addto',
    'dep',
    'include',
    # session/subprocess
    'exec',
    'out',
    'run',
    # parameters for out and run
    'debug',
    'expect',
    'timeout',
    # NOTE: input_delay might allow the accurate
    #   association of input/output as long as output
    #   is always captured by the time the delay passes.
    'input_delay',
    'hide',
    'proc_info',
    'out_prefix',
    'err_prefix',
    'out_color',
    'err_color',
    # file generation
    'file',
    # TODO (mb 2021-01-30): build system
    'requires',
    'provides',
    'idempotent',
    # 'make',
    # 'const'
    # 'use_macro',
    # 'def_macro',
}


def has_directive(line: str, language: typ.Optional[str]) -> bool:
    if language is None:
        comment_text = line
    else:
        comment_start_re, comment_end_re = LANGUAGE_COMMENT_REGEXES[language]
        start_match = comment_start_re.search(line)
        if start_match is None:
            return False

        comment_text = line[start_match.end() :]
        end_match    = comment_end_re.search(comment_text)
        if end_match is None:
            return False

    comment_text = comment_text.strip()

    for name in VALID_DIRECTIVE_NAMES:
        if comment_text.startswith(name):
            return True

    return False


def _parse_directive(directive_text: str, raw_text: str) -> Directive:
    if ":" in directive_text:
        name, value = directive_text.split(":", 1)
        name  = name.strip()
        value = value.strip()
    else:
        name  = directive_text.strip()
        value = ""

    if name in VALID_DIRECTIVE_NAMES:
        return Directive(name, value, raw_text)
    else:
        errmsg = f"Invalid directive '{name}'"
        raise Exception(errmsg)


# NOTE (mb 2020-05-22): Since we do multiple passes over the file, we
#   avoid reporting

FileLocation = str


class ParseError(typ.NamedTuple):

    location: FileLocation
    level   : int
    message : str


AnyElem = typ.Union[MarkdownElement, Block]


def location(elem: AnyElem) -> FileLocation:
    return f"Line {elem.first_line:<4} of {elem.md_path}"


def make_parse_error(message: str, elem: AnyElem, level: int = logging.ERROR) -> ParseError:
    return ParseError(location(elem), level, message)


FILENAME_PATTERN_URL = "https://regex101.com/r/sLzB5p/4"

# Input files for LitProg must match this pattern.
# The 'namespace' group is used to reference blocks
# in different files in a way that doesn't break if
# files are reordered.

FILENAME_PATTERN = r"""
^
(?:[0-9_\-\s]+)?
(?P<namespace>[\w ]+)
(?:\.\w*)?
$
"""

FILENAME_RE = re.compile(FILENAME_PATTERN, flags=re.VERBOSE)


class MarkdownFile:

    md_path : pl.Path
    errors  : typ.Set[ParseError]
    elements: MarkdownElements

    def __init__(self, md_path: pl.Path, elements: MaybeMarkdownElements = None) -> None:
        self.md_path = md_path
        self.errors  = set()
        if elements is None:
            self.elements = _parse_md_elements(md_path)
        else:
            self.elements = elements

    def copy(self) -> 'MarkdownFile':
        return MarkdownFile(self.md_path, list(self.elements))

    @property
    def block_namespace(self) -> str:
        # The namespace is based only on the filename, directories are
        # only for organization, otherwise they are ignored.
        filename       = self.md_path.name
        filename_match = FILENAME_RE.match(filename)
        if filename_match is None:
            errmsg = f"Invalid filename {filename}, must match {FILENAME_PATTERN_URL}"
            raise Exception(errmsg)
        else:
            raw_namespace        = filename_match.group('namespace')
            normalized_namespace = raw_namespace.replace("-", "_").replace(" ", "_")
            return normalized_namespace

    @property
    def headlines(self) -> typ.Iterable[Headline]:
        for elem_index, elem in enumerate(self.elements):
            if elem.md_type != MD_HEADLINE:
                continue

            a_match = HEADLINE_RE_A.match(elem.content)
            b_match = HEADLINE_RE_B.match(elem.content)
            if a_match:
                text   = a_match.group('headline_text_a')
                marker = a_match.group('headline_marker_a')
                level  = marker.count("#")
            elif b_match:
                text   = b_match.group('headline_text_b')
                marker = b_match.group('headline_marker_b')
                level  = 1 if "-" in marker else 2
            else:
                err_msg = "Invalid headline: {elem.content}"
                raise ValueError(err_msg)

            yield Headline(self.md_path, elem_index, text.strip(), level)

    @property
    def image_tags(self) -> typ.Iterable[ImageTag]:
        for elem in self.elements:
            if elem.md_type in (MD_HEADLINE, MD_BLOCK):
                continue
            for image_match in IMAGE_URL_RE.finditer(elem.content):
                yield ImageTag(*image_match.groups())

    def _init_plain_block(self, elem: MarkdownElement, info_string: str) -> Block:
        inner_content = elem.content
        inner_content = inner_content.split("\n", 1)[-1]
        # trim off final fence
        inner_content = inner_content.rsplit("\n", 1)[0]

        return Block(
            self.md_path,
            self.block_namespace,
            elem.first_line,
            elem.elem_index,
            info_string,
            [],
            elem.content,
            # TODO (mb 2020-06-02): Why do we .strip() here ?
            inner_content.strip(),
            inner_content.strip(),
        )

    def _init_code_block(self, elem: MarkdownElement, info_string: str, rest_content: str) -> Block:
        language = info_string
        comment_start_re, comment_end_re = LANGUAGE_COMMENT_REGEXES[language]

        directives = [Directive('language', language, language)]

        inner_chunks      = []
        includable_chunks = []

        rest = rest_content
        while rest:
            start_match = comment_start_re.search(rest)
            if start_match is None:
                inner_chunks.append(rest)
                includable_chunks.append(rest)
                break

            chunk = rest[: start_match.start()]
            if chunk:
                inner_chunks.append(chunk)
                includable_chunks.append(chunk)

            rest      = rest[start_match.end() :]
            end_match = comment_end_re.search(rest)
            if end_match is None:
                comment_text = rest
                rest         = ""
            else:
                comment_text = rest[: end_match.start()]
                rest         = rest[end_match.end() :]

            raw_text = start_match.group(0) + comment_text
            assert raw_text in elem.content

            comment_text = comment_text.strip()
            if has_directive(comment_text, language=None):
                directive = _parse_directive(comment_text, raw_text)
                directives.append(directive)
                inner_chunks.append(raw_text)
                if directive.name in ('dep', 'include'):
                    # NOTE (mb 2020-06-03): needed for recursive include
                    includable_chunks.append(raw_text)
            else:
                inner_chunks.append(raw_text)
                includable_chunks.append(raw_text)

        inner_content = "".join(inner_chunks)
        # trim off final fence
        inner_content = inner_content.rsplit("\n", 1)[0]
        inner_content = "\n".join(line for line in inner_content.splitlines() if line.strip())

        includable_content = "".join(includable_chunks)
        # trim off final fence
        includable_content = includable_content.rsplit("\n", 1)[0]
        includable_content = "\n".join(line for line in includable_content.splitlines() if line.strip())

        return Block(
            self.md_path,
            self.block_namespace,
            elem.first_line,
            elem.elem_index,
            info_string,
            directives,
            elem.content,
            inner_content,
            includable_content,
        )

    def _iter_block_elements(self) -> typ.Iterable[typ.Tuple[MarkdownElement, str, str]]:
        for elem in self.elements:
            if elem.md_type == 'block':
                start_match = BLOCK_START_RE.match(elem.content)
                assert start_match is not None
                maybe_info_string = start_match.group('info_string')
                info_string       = typ.cast(str, maybe_info_string or "")
                info_string       = info_string.strip()
                content_start     = start_match.end()
                content           = elem.content[content_start:]
                yield (elem, info_string, content)

    def iter_blocks(self) -> typ.Iterable[Block]:
        for elem, info_string, content in self._iter_block_elements():
            is_known_info_string = info_string in KNOWN_INFO_STRINGS
            if info_string.strip() and not is_known_info_string:
                err = make_parse_error(f"Unknown language '{info_string}'", elem, logging.WARNING)
                self.errors.add(err)

            is_valid_language = info_string in LANGUAGE_COMMENT_REGEXES
            if is_valid_language:
                yield self._init_code_block(elem, info_string, rest_content=content)
            else:
                yield self._init_plain_block(elem, info_string)

    def iter_block_linenos(self) -> typ.Iterable[typ.Tuple[int, int]]:
        for elem, info_string, content in self._iter_block_elements():
            if info_string not in NON_CODE_BLOCKS:
                num_lines = content.strip().count("\n")
                yield elem.first_line, num_lines

    def parse_front_matter_meta(self) -> FrontMatterMetadata:
        metadata = DEFAULT_FRONT_MATTER_META.copy()
        if len(self.elements) > 0 and self.elements[0].md_type == MD_FRONT_MATTER:
            content = self.elements[0].content
            if content.startswith("+++"):
                meta = toml.loads(content.strip("+ \n\r"))
            elif content.startswith("---"):
                meta = yaml.safe_load(content.strip("- \n\r"))
            else:
                raise RuntimeError("Invalid front matter")

            # TODO (mb 2021-01-31): Better validation
            #   - Check that only known keys and corresponding values are used
            metadata.update(meta)
        return metadata

    def __lt__(self, other: 'MarkdownFile') -> bool:
        return self.md_path < other.md_path

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MarkdownFile):
            return False
        elif not self.md_path == other.md_path:
            return False
        elif not self.elements == other.elements:
            return False
        else:
            return True

    def __str__(self) -> str:
        return "".join(elem.content for elem in self.elements if elem.md_type != MD_FRONT_MATTER)

    def __repr__(self) -> str:
        return f"litprog.parse.MarkdownFile(\"{self.md_path}\")"


def _iter_raw_md_elements(content: str) -> typ.Iterable[_RawMarkdownElement]:
    line_no = 1
    while content:
        if line_no == 1:
            start_match = FRONT_MATTER_RE.match(content)
            if start_match and start_match.start() == 0:
                end_match = FRONT_MATTER_RE.search(content, pos=start_match.end())
                if end_match:
                    front_matter_end     = end_match.end()
                    front_matter_content = content[:front_matter_end]
                    yield _RawMarkdownElement(MD_FRONT_MATTER, line_no, front_matter_content)
                    line_no += front_matter_content.count("\n")
                    content = content[front_matter_end:]

        match = ELEMENT_RE.search(content)
        if match is None:
            break

        # yield preceding paragraph
        para_content = content[: match.start()]
        if para_content:
            yield _RawMarkdownElement(MD_PARAGRAPH, line_no, para_content)

        line_no += para_content.count("\n")

        # parse match as special element
        groups         = match.groupdict()
        is_headline    = bool(groups['headline_marker_a'] or groups['headline_marker_b'])
        is_block_fence = groups['block_fence']
        match_content  = content[match.start() : match.end()]
        rest_content   = content[match.end() :]

        if is_headline:
            md_type = MD_HEADLINE
        elif is_block_fence:
            md_type      = MD_BLOCK
            block_fence  = groups['block_fence']
            block_end_re = BLOCK_END_RE[block_fence]
            end_match    = block_end_re.search(rest_content)
            if end_match is None:
                match_content += rest_content
                rest_content = ""
            else:
                end_pos = end_match.end()
                match_content += rest_content[:end_pos]
                rest_content = rest_content[end_pos:]

        yield _RawMarkdownElement(md_type, line_no, match_content)

        line_no += match_content.count("\n")
        content = rest_content

    if content:
        yield _RawMarkdownElement(MD_PARAGRAPH, line_no, content)


def _parse_md_elements(md_path: pl.Path) -> MarkdownElements:
    # TODO: encoding from config
    with md_path.open(mode='r', encoding="utf-8") as fobj:
        content = fobj.read()

    elements = []
    for elem_index, raw_elem in enumerate(_iter_raw_md_elements(content)):
        elem = MarkdownElement(
            md_path,
            raw_elem.first_line,
            elem_index,
            raw_elem.md_type,
            raw_elem.content,
            None,
        )
        elements.append(elem)

    # An important criteria for the context is that it has the
    # complete text of the original literate program and is able to
    # reproduce it byte for byte. This must be possible, because we
    # want to be able to update elements of the literate program and
    # write it back to disk.

    assert content == "".join(elem.content for elem in elements)
    return elements


MarkdownFiles = typ.List[MarkdownFile]


class Context:

    files: MarkdownFiles

    def __init__(self, md_path_or_files: typ.Union[FilePaths, MarkdownFiles]) -> None:
        self.files = []
        for path_or_file in md_path_or_files:
            if isinstance(path_or_file, MarkdownFile):
                self.files.append(path_or_file)
            else:
                self.files.append(MarkdownFile(path_or_file))
        self.files.sort()

    @property
    def headlines(self) -> typ.Iterable[Headline]:
        for md_file in self.files:
            for headline in md_file.headlines:
                yield headline

    def iter_blocks(self) -> typ.Iterable[Block]:
        for md_file in self.files:
            for block in md_file.iter_blocks():
                yield block

    def copy(self) -> 'Context':
        return Context([f.copy() for f in self.files])

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Context) and self.files == other.files


def parse_context(md_paths: FilePaths) -> Context:
    parse_ctx = Context(md_paths)

    # provoke parse errors early on
    assert parse_ctx.copy() == parse_ctx
    list(parse_ctx.headlines)
    list(parse_ctx.iter_blocks())

    for md_file in parse_ctx.files:
        for err in md_file.errors:
            logger.log(err.level, f"{err.location:<3} : " + err.message)

    return parse_ctx
