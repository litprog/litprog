# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import re
import typing as typ
import logging
import collections
from pathlib import Path

from . import common_types as ct

logger = logging.getLogger(__name__)


FilePaths = typ.Iterable[Path]

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

RENDERED_CODE_BLOCKS = ('bob', 'math')

MarkdownElementType = str

FrontMatterMetadata = typ.Dict[str, typ.Any]

DEFAULT_FRONT_MATTER_META = {'lang': "en-US", 'title': "-"}

VALID_METADATA_KEYS = {
    'author',
    'copyright',
    'copyright_url',
    'description',
    'favicon_url',
    'keywords',
    'lang',
    'logo_url',
    'project_name',
    'repo_url',
    'title',
}


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
    (\r\n|\r|\n)
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


LANGUAGE_COMMENT_PATTERNS = {
    "c++"          : (r"^[ \t]*//"  , r"$"),
    'actionscript' : (r"^[ \t]*//"  , r"$"),
    'actionscript3': (r"^[ \t]*//"  , r"$"),
    'bash'         : (r"^[ \t]*[#]" , r"$"),
    'c'            : (r"^[ \t]*//"  , r"$"),
    'd'            : (r"^[ \t]*//"  , r"$"),
    'elixir'       : (r"^[ \t]*[#]" , r"$"),
    'erlang'       : (r"^[ \t]*%"   , r"$"),
    'go'           : (r"^[ \t]*//"  , r"$"),
    'zig'          : (r"^[ \t]*//"  , r"$"),
    'java'         : (r"^[ \t]*//"  , r"$"),
    'javascript'   : (r"^[ \t]*//"  , r"$"),
    'json'         : (r"^[ \t]*//"  , r"$"),
    'swift'        : (r"^[ \t]*//"  , r"$"),
    'r'            : (r"^[ \t]*//"  , r"$"),
    'php'          : (r"^[ \t]*//"  , r"$"),
    'svg'          : (r"^[ \t]*<!--", r"-->$"),
    'html'         : (r"^[ \t]*<!--", r"-->$"),
    'css'          : (r"^[ \t]*/\*" , r"\*/$"),
    'csharp'       : (r"^[ \t]*//"  , r"$"),
    'fsharp'       : (r"^[ \t]*//"  , r"$"),
    'kotlin'       : (r"^[ \t]*//"  , r"$"),
    'make'         : (r"^[ \t]*[#]" , r"$"),
    'nim'          : (r"^[ \t]*[#]" , r"$"),
    'perl'         : (r"^[ \t]*[#]" , r"$"),
    'yaml'         : (r"^[ \t]*[#]" , r"$"),
    'prolog'       : (r"^[ \t]*%"   , r"$"),
    'scheme'       : (r"^[ \t]*;"   , r"$"),
    'clojure'      : (r"^[ \t]*;"   , r"$"),
    'lisp'         : (r"^[ \t]*;"   , r"$"),
    'coffee-script': (r"^[ \t]*[#]" , r"$"),
    'python'       : (r"^[ \t]*[#]" , r"$"),
    'ruby'         : (r"^[ \t]*[#]" , r"$"),
    'rust'         : (r"^[ \t]*//"  , r"$"),
    'scala'        : (r"^[ \t]*//"  , r"$"),
    'sh'           : (r"^[ \t]*[#]" , r"$"),
    'shell'        : (r"^[ \t]*[#]" , r"$"),
    'sql'          : (r"^[ \t]*--"  , r"$"),
    'typescript'   : (r"^[ \t]*//"  , r"$"),
}


def _re(pattern: str, flags: int = re.MULTILINE) -> typ.Pattern:
    return re.compile(pattern, flags=flags)


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


ELEMENT_RE = _re(ELEMENT_PATTERN, flags=re.VERBOSE | re.MULTILINE)

HEADLINE_RE_A = _re(HEADLINE_PATTERN_A, flags=re.VERBOSE | re.MULTILINE)
HEADLINE_RE_B = _re(HEADLINE_PATTERN_B, flags=re.VERBOSE | re.MULTILINE)

BLOCK_START_RE = _re(BLOCK_START_PATTERN, flags=re.VERBOSE | re.MULTILINE)

BLOCK_END_RE = {
    "```": _re(r"(\r\n|\r|\n)```", flags=re.VERBOSE | re.MULTILINE),
    "~~~": _re(r"(\r\n|\r|\n)~~~", flags=re.VERBOSE | re.MULTILINE),
}

IMAGE_URL_RE = _re(IMAGE_URL_PATTERN, flags=re.VERBOSE | re.MULTILINE)


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

    md_path     : Path
    first_line  : int
    elem_index  : int
    md_type     : MarkdownElementType
    content     : str
    _successor  : typ.Optional[typ.Any]
    src_md_paths: set[Path]

    # Recursive types not fully supported yet;
    # this class can be changed to a NamedTuple once they are.
    # Successor  : typ.Optional['MarkdownElement']
    @property
    def successor(self) -> Successor:
        return typ.cast(Successor, self._successor)

    def __init__(
        self,
        md_path     : Path,
        first_line  : int,
        elem_index  : int,
        md_type     : MarkdownElementType,
        content     : str,
        successor   : Successor,
        src_md_paths: set[Path],
    ) -> None:
        assert md_type in VALID_ELEMENT_TYPES
        self.md_path      = md_path
        self.first_line   = first_line
        self.elem_index   = elem_index
        self.md_type      = md_type
        self.content      = content
        self._successor   = successor
        self.src_md_paths = src_md_paths

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
            src_md_paths=self.src_md_paths,
        )


ElementsByPath = dict[Path, list[MarkdownElement]]


# NOTE (mb 2021-03-04): Right now the 'out' directive references the
#   preceeding block. We could also make it more general by allowing
#   explicit references to the def of an exec block. This would
#   be similar to requires.

VALID_DIRECTIVES = {
    'language',
    # block composition
    'def',
    # 'amend',  # depricated
    'dep',
    'include',
    # session/subprocess
    'exec',
    'out',
    'run',
    # parameters for out and run
    'debug',
    'expect',
    'options',
    'timeout',
    # NOTE: input_delay might allow the accurate
    #   association of input/output as long as output
    #   is always captured by the time the delay passes.
    'capture_file',
    'input_delay',
    'proc_info',
    'out_prefix',
    'err_prefix',
    'out_color',
    'err_color',
    # file generation
    'file',
    # build system
    'requires',  # comma separated globs for ids to invalidate block
    # 'cache'   # yes|once|never
    # 'stateful',
    # 'pure',
    # 'make',
    # 'const'
    # 'use_macro',
    # 'def_macro',
}


VALID_NOARG_DIRECTIVES  = {'exec', 'out', 'debug'}
VALID_ARG_DIRECTIVES    = VALID_DIRECTIVES - {'out', 'debug'}
VALID_INLINE_DIRECTIVES = {'dep', 'include'}


assert VALID_INLINE_DIRECTIVES < VALID_ARG_DIRECTIVES
assert VALID_NOARG_DIRECTIVES  < VALID_DIRECTIVES


def has_directive(comment_text: str, is_prelude: bool, language: typ.Optional[str] = None) -> bool:
    if language is not None:
        comment_start_re, comment_end_re = LANGUAGE_COMMENT_REGEXES[language]
        start_match = comment_start_re.search(comment_text)
        if start_match is None:
            return False

        comment_text = comment_text[start_match.end() :]
        end_match    = comment_end_re.search(comment_text)
        if end_match is None:
            return False

    comment_text = comment_text.strip()
    if is_prelude:
        if comment_text in VALID_NOARG_DIRECTIVES:
            return True

        for name in VALID_ARG_DIRECTIVES:
            if re.match(r"^" + name + r"\s*:", comment_text):
                return True
    else:
        for name in VALID_INLINE_DIRECTIVES:
            if re.match(r"^" + name + r"\s*:", comment_text):
                return True

    return False


def _parse_directives(comment_text: str, raw_text: str) -> typ.Iterable[ct.Directive]:
    # TODO (mb 2021-08-19): Is there a way we can support
    #   multiple directives on the same line?
    rest = comment_text
    while rest:
        # match = re.match(r"^" + name + r"\s*:", rest)
        if ":" in rest:
            name, value = rest.split(":", 1)
            name  = name.strip()
            value = value.strip()
        else:
            name  = rest.strip()
            value = ""

        if name in VALID_DIRECTIVES:
            yield ct.Directive(name, value, raw_text)
            return
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


AnyElem = typ.Union[MarkdownElement, ct.Block]


def location(elem: AnyElem) -> FileLocation:
    return f"Line {elem.first_line:<4} of {elem.md_path}"


def make_parse_error(message: str, elem: AnyElem, level: int = logging.ERROR) -> ParseError:
    return ParseError(location(elem), level, message)


class Chapter:

    md_paths : list[Path]
    chapnum  : str
    namespace: str
    elements : ElementsByPath
    errors   : set[ParseError]

    def __init__(
        self,
        md_paths : list[Path],
        chapnum  : str,
        namespace: str,
        elements : typ.Optional[ElementsByPath] = None,
    ) -> None:
        self.md_paths  = sorted(md_paths)
        self.chapnum   = chapnum
        self.namespace = namespace
        self.errors    = set()
        if elements is None:
            self.elements = {md_path: _parse_md_elements(md_path) for md_path in md_paths}
        else:
            self.elements = elements

    def copy(self) -> 'Chapter':
        new_elements = {path: list(elems) for path, elems in self.elements.items()}
        return Chapter(self.md_paths, self.chapnum, self.namespace, new_elements)

    def headlines(self) -> typ.Iterable[ct.Headline]:
        elem_index = 0
        for md_path in self.md_paths:
            for elem in self.elements[md_path]:
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

                yield ct.Headline(md_path, elem_index, text.strip(), level)
                elem_index += 1

    def image_tags(self) -> typ.Iterable[ImageTag]:
        for md_path in self.md_paths:
            for elem in self.elements[md_path]:
                if elem.md_type in (MD_HEADLINE, MD_BLOCK):
                    continue
                for image_match in IMAGE_URL_RE.finditer(elem.content):
                    yield ImageTag(*image_match.groups())

    def _init_plain_block(self, elem: MarkdownElement, info_string: str) -> ct.Block:
        inner_content = elem.content
        inner_content = inner_content.split("\n", 1)[-1]
        # trim off final fence
        inner_content = inner_content.rsplit("\n", 1)[0]

        return ct.Block(
            elem.md_path,
            self.namespace,
            elem.first_line,
            elem.elem_index,
            info_string,
            [],
            elem.content,
            # TODO (mb 2020-06-02): Why do we .strip() here ?
            inner_content.strip(),
            inner_content.strip(),
        )

    def _init_code_block(self, elem: MarkdownElement, info_string: str, rest_content: str) -> ct.Block:
        language = info_string
        comment_start_re, comment_end_re = LANGUAGE_COMMENT_REGEXES[language]

        directives = [ct.Directive('language', language, language)]

        inner_chunks      = []
        includable_chunks = []

        is_prelude = True
        rest       = rest_content

        while rest:
            start_match = comment_start_re.search(rest)

            if start_match is None:
                inner_chunks.append(rest)
                includable_chunks.append(rest)
                break

            prefix_chunk = rest[: start_match.start()]
            if prefix_chunk:
                inner_chunks.append(prefix_chunk)
                includable_chunks.append(prefix_chunk)

            rest = rest[start_match.end() :]

            if prefix_chunk.strip() and is_prelude:
                # prelude ends if there is non-whitespace before a comment
                is_prelude = False

            end_match = comment_end_re.search(rest)

            if end_match is None:
                comment_text = rest
                rest         = ""
            else:
                comment_text = rest[: end_match.start()]
                rest         = rest[end_match.end() :]

            if is_prelude:
                # TODO (mb 2021-08-27): hacky, isn't there a better
                #   way to capture the newlines earlier?
                if rest.startswith("\n") or rest.startswith("\r"):
                    comment_text = comment_text + rest[:1]
                    rest         = rest[1:]
                elif rest.startswith("\r\n"):
                    comment_text = comment_text + rest[:2]
                    rest         = rest[2:]

            raw_text = start_match.group(0) + comment_text

            assert raw_text in elem.content
            inner_chunks.append(raw_text)

            if has_directive(comment_text, is_prelude=is_prelude):
                for directive in _parse_directives(comment_text, raw_text):
                    directives.append(directive)
                    if directive.name in ('dep', 'include'):
                        # prelude ends with any include/dep directives
                        is_prelude = False
                        # NOTE (mb 2020-06-03): needed for recursive include
                        includable_chunks.append(raw_text)
            else:
                includable_chunks.append(raw_text)

        inner_content      = "".join(inner_chunks)
        includable_content = "".join(includable_chunks)

        # trim off final fence
        inner_content      = inner_content.rsplit("\n", 1)[0]
        includable_content = includable_content.rsplit("\n", 1)[0]

        return ct.Block(
            elem.md_path,
            self.namespace,
            elem.first_line,
            elem.elem_index,
            info_string,
            directives,
            elem.content,
            inner_content,
            includable_content,
        )

    def _iter_block_elements(self) -> typ.Iterable[tuple[MarkdownElement, str, str]]:
        for md_path in self.md_paths:
            for elem in self.elements[md_path]:
                if elem.md_type == 'block':
                    start_match = BLOCK_START_RE.match(elem.content)
                    assert start_match is not None
                    maybe_info_string = start_match.group('info_string')
                    info_string       = typ.cast(str, maybe_info_string or "")
                    info_string       = info_string.strip()
                    content_start     = start_match.end()
                    content           = elem.content[content_start:]
                    yield (elem, info_string, content)

    def iter_blocks(self) -> typ.Iterable[ct.Block]:
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

    def iter_block_linenos(self) -> typ.Iterable[ct.BlockLineInfo]:
        for elem, info_string, content in self._iter_block_elements():
            if info_string not in RENDERED_CODE_BLOCKS:
                num_lines = content.lstrip().count("\n")
                yield ct.BlockLineInfo(elem.md_path, elem.first_line, num_lines)

    def parse_front_matter_meta(self) -> FrontMatterMetadata:
        # pylint: disable=import-outside-toplevel;
        #   to speed up cli, lazy load modules: yaml and toml

        elements = self.elements[self.md_paths[0]]
        metadata = DEFAULT_FRONT_MATTER_META.copy()
        if len(elements) > 0 and elements[0].md_type == MD_FRONT_MATTER:
            content = elements[0].content
            if content.startswith("+++"):
                import toml

                meta = toml.loads(content.strip("+ \n\r"))
            elif content.startswith("---"):
                import yaml

                meta = yaml.safe_load(content.strip("- \n\r"))
            else:
                raise RuntimeError("Invalid front matter")

            for key, val in metadata.items():
                if key not in VALID_METADATA_KEYS:
                    errmsg = f"Invalid key Markdown front matter: {key}={val}"
                    raise KeyError(errmsg)

            metadata.update(meta)
        return metadata

    def __lt__(self, other: 'Chapter') -> bool:
        return self.chapnum < other.chapnum

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Chapter)
            and self.chapnum   == other.chapnum
            and self.namespace == other.namespace
            and self.md_paths  == other.md_paths
            and self.elements  == other.elements
        )

    def md_content(self, md_path: Path, front_matter: bool = True) -> str:
        return "".join(
            [
                elem.content
                for elem in self.elements[md_path]
                if front_matter or elem.md_type != MD_FRONT_MATTER
            ]
        )

    def __str__(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"litprog.parse.Chapter(\"{self.chapnum}\", {self.namespace})"

    def __hash__(self) -> int:
        return hash(self.chapnum) ^ hash(self.namespace)


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


def _parse_md_elements(md_path: Path) -> list[MarkdownElement]:
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
            {md_path},
        )
        elements.append(elem)

    # An important criteria for the context is that it has the
    # complete text of the original literate program and is able to
    # reproduce it byte for byte. This must be possible, because we
    # want to be able to update elements of the literate program and
    # write it back to disk.

    assert content == "".join(elem.content for elem in elements)
    return elements


# Input files for LitProg must match this pattern.
# The 'namespace' group is used to reference blocks
# in different files in a way that doesn't break if
# files are reordered.

FILENAME_PATTERN_URL = "https://regex101.com/r/sSc610/1"
FILENAME_PATTERN = r"""
^
(?:
  (?P<chapter>[0-9]{2})
  (?P<section>[0-9][a-z]?)?
  [_\-\s]
)?
(?P<namespace>[\w ]+)
(?:\.\w*)?
$
"""

FILENAME_RE = re.compile(FILENAME_PATTERN, flags=re.VERBOSE)


def parse_namespace(filename: str) -> tuple[str, str]:
    filename_match = FILENAME_RE.match(filename)
    if filename_match is None:
        errmsg = f"Invalid filename {filename}, must match {FILENAME_PATTERN_URL}"
        raise Exception(errmsg)
    else:
        chapter              = filename_match.group('chapter')
        raw_namespace        = filename_match.group('namespace')
        normalized_namespace = raw_namespace.replace("-", "_").replace(" ", "_")
        return (chapter or normalized_namespace, normalized_namespace)


class Context:

    chapters: list[Chapter]

    def __init__(self, *, md_paths: FilePaths = None, chapters: list[Chapter] = None) -> None:
        if chapters:
            assert md_paths is None
            self.chapters = chapters
        elif md_paths:
            assert chapters is None
            namespaces: dict[str, str] = {}
            paths_by_chapnum = collections.defaultdict(list)

            for md_path in md_paths:
                chapnum, namespace = parse_namespace(md_path.name)
                if chapnum in namespaces:
                    namespace = namespaces[chapnum]
                else:
                    namespaces[chapnum] = namespace

                paths_by_chapnum[chapnum, namespace].append(md_path)

            self.chapters = [
                Chapter(chapter_md_paths, chapnum, namespace)
                for (chapnum, namespace), chapter_md_paths in sorted(paths_by_chapnum.items())
            ]
            self.chapters.sort()
        else:
            raise ValueError("Missing argument 'md_paths' for Context.")

    def headlines(self) -> typ.Iterable[ct.Headline]:
        for chapter in self.chapters:
            for headline in chapter.headlines():
                yield headline

    def iter_blocks(self) -> typ.Iterable[ct.Block]:
        for chapter in self.chapters:
            for block in chapter.iter_blocks():
                yield block

    def copy(self) -> 'Context':
        return Context(chapters=[f.copy() for f in self.chapters])

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Context) and self.chapters == other.chapters


def parse_context(md_paths: FilePaths) -> Context:
    parse_ctx = Context(md_paths=md_paths)

    # provoke parse errors early on
    assert parse_ctx.copy() == parse_ctx
    list(parse_ctx.headlines())
    list(parse_ctx.iter_blocks())

    for chapter in parse_ctx.chapters:
        for err in chapter.errors:
            logger.log(err.level, f"{err.location:<3} : " + err.message)

    return parse_ctx
