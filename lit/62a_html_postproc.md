TODO: 
 - Side by side layout on wide screens
 - TOC and Navigation

### Generated Content

Some parts of a text are more important than others, so in
order to help users and newbies, there are three things
which `litprog` generates from the program text.

 - Table of Contents (from h1: part, h2: chapter headings)
 - Overview (from h1, h2, h3: section headings and summaries)
 - Glossary (from definitions)


```yaml
filepath     : "src/litprog/html_postproc_v2.py"
inputs       : [
    "license_header_boilerplate",
    "generated_preamble",
    "common.imports",
    "module_logger",
    "html_postproc_v2.imports",
    "html_postproc_v2.code",
]
```

```python
# lpid = html_postproc_v2.imports
import re
import bs4
import pyphen

PARSER_MODULE = 'html.parser'
PARSER_MODULE = 'lxml'
```

```python
# lpid = html_postproc_v2.code

def _iter_filepaths(params: typ.List[str]) -> FilePaths:
    for param in params:
        path = pl.Path(param)
        if path.is_file():
            yield path
        elif path.is_dir():
            dirs = [path]
            while dirs:
                for dirpath, dirnames, filenames in os.walk(dirs.pop()):
                    dirpaths = [
                        pl.Path(dirpath, dirname)
                        for dirname in dirnames
                    ]
                    dirs.extend(dirpaths)

                    filepaths = [
                        pl.Path(dirpath, filename)
                        for filename in filenames
                    ]
                    for filepath in filepaths:
                        if filepath.suffix == ".html":
                            yield filepath
        else:
            err_msg = f"Unknown file or directory {param}"
            log.warning(err_msg)


def _iter_headlines(soup: bs4.BeautifulSoup) -> typ.Iterable[bs4.element.Tag]:
    for n in range(1, 7):
        for h in soup.find_all(f"h{n}"):
            yield h


INLINE_TAG_NAMES = {
    "span",
    "b",
    "i",
    "a",
    "em",
    "small",
    "strong",
    "sub",
    "sup",
}


SOFT_HYPHEN  = "&shy;"
SOFT_HYPHEN  = "\u00AD"

WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


def _iter_shyphenated(dic: pyphen.Pyphen, text: str) -> typ.Iterable[str]:
    text = text.replace("\u00AD", "").replace("&shy;", "")
    prev_end = 0
    for match in WORD_RE.finditer(text):
        start, end = match.span()
        if prev_end < start:
            yield text[prev_end:start]

        word = text[start:end]
        if len(word) < 6:
            yield word
        else:
            yield dic.inserted(word, hyphen=SOFT_HYPHEN) 

        prev_end = end

    yield text[prev_end:]


def _shyphenate(dic: pyphen.Pyphen, text: str) -> str:
    return "".join(_iter_shyphenated(dic, text))


def _postprocess_soup(soup: bs4.BeautifulSoup) -> str:
    """Change html for better rendering in print and web.

    - Group headline and first paragraph to prevent orphaned headlines
    - Hyphenate body text for web output
    - Split off first few lines of code blocks to prevent orphans
    """

    for headline in _iter_headlines(soup):
        next_sibling = headline.next_sibling
        while isinstance(next_sibling, bs4.element.NavigableString):
            next_sibling = next_sibling.next_sibling
        assert isinstance(next_sibling, bs4.element.Tag)

        if next_sibling.name != "p":
            continue

        section_start = soup.new_tag("div")
        section_start['class'] = "firstpara"
        headline.wrap(section_start)
        first_para = next_sibling.extract()
        section_start.append(first_para)

    # TODO: parse language
    dic = pyphen.Pyphen(lang="en_US")

    elements = it.chain(soup.find_all(f"p"), soup.find_all(f"li"))
    for elem in elements:
        for part in elem.contents:
            is_text_elem = (
                isinstance(part, bs4.element.NavigableString)
                or (part.name in INLINE_TAG_NAMES and part.string)
            )
            if is_text_elem:
                shyphenated = _shyphenate(dic, part.string)
                part.string.replace_with(shyphenated)
            # print(type(part), len(part), str(part)[:10])

    return str(soup)
    

def _postproc_html(filepath: pl.Path) -> None:
    with filepath.open(mode="rb") as fh:
        soup = bs4.BeautifulSoup(fh, PARSER_MODULE)

    output = _postprocess_soup(soup)
    # output = s.serialize(stream)

    tmp_filepath = pl.Path(filepath.parent, filepath.name + ".tmp.html")
    with tmp_filepath.open(mode="wb") as fh:
        fh.write(output.encode("utf-8"))

    print("<<<", tmp_filepath)
    # tmp_filepath.rename(filepath)

    
def main(args: typ.List[str] = sys.argv[1:]) -> int:
    flags = set(arg for arg in args if arg.startswith("-"))
    params = [arg for arg in args if arg not in flags]

    for filepath in _iter_filepaths(params):
        _postproc_html(filepath)

    return 0


if __name__ == '__main__':
    sys.exit(main())
```

```yaml
lpid   : html_postproc_v2.test
lptype : session
command: /usr/bin/env python3
requires: [src/litprog/html_postproc_v2.py]
```

```python
# lpid = html_postproc_v2.test
import litprog.html_postproc_v2
# litprog.html_postproc_v2.main(["lit_out/out.html"])
```
