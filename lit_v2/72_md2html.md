
```yaml
filepath: "src/litprog/md2html.py"
inputs  : ["boilerplate::*", "md2html::*"]
```

```python
# lpid=md2html::code
import io
import re
import sys

import typing as typ
import pathlib2 as pl

import pyphen


HTML_PART_PATTERN = re.compile(r"(&[#\w]+?;|<.*?>|\s+\w+)")


MarkdownText = str

HTMLText = str


def _is_entity(part: str) -> int:
    return part.startswith("&") and part.endswith(";")


def _is_tag(part: str) -> int:
    return part.startswith("<") and part.endswith(">")


def _part_len(part: str) -> int:
    if _is_entity(part):
        return 1
    elif _is_tag(part):
        return 0
    else:
        return len(part)


def _iter_wrapped_line_chunks(line: str, max_len: int) -> typ.Iterable[str]:
    if len(line) < max_len:
        yield line
        return

    # Step 1: Split apart whatever we can
    parts = []

    last_end_idx = 0

    for match in HTML_PART_PATTERN.finditer(line):
        begin_idx, end_idx = match.span()
        parts.append(line[last_end_idx:begin_idx])
        parts.append(line[begin_idx   :end_idx  ])
        last_end_idx = end_idx

    parts.append(line[last_end_idx:])

    # Step 2: Split apart whatever we have to
    #   - urls and paths on slash, ? and &
    #   - everything else simply by part[:max_len] part[max_len:]

    for i, part in enumerate(list(parts)):
        if _part_len(part) <= max_len:
            continue

        split_parts = []

        remaining_part = part
        while remaining_part:
            if "://" in remaining_part:
                new_part, remaining_part = remaining_part.split("://", 1)
                new_part += "://"
            elif "?" in remaining_part:
                new_part, remaining_part = remaining_part.split("?", 1)
                new_part += "?"
            elif "/" in remaining_part:
                new_part, remaining_part = remaining_part.split("/", 1)
                new_part += "/"
            elif "#" in remaining_part:
                new_part, remaining_part = remaining_part.split("#", 1)
                new_part += "#"
            elif "." in remaining_part:
                new_part, remaining_part = remaining_part.split(".", 1)
                new_part += "."
            else:
                new_part       = remaining_part[:max_len]
                remaining_part = remaining_part[max_len:]

            # If a line is wrapped, it should never have
            #   trailing whitespace. This gives readers the
            #   best chance of knowing that whitespace exists,
            #   namely by the fact that the wrapped portion of
            #   the line has some indentation
            new_part_rstrip    = new_part.rstrip()
            traling_whitespace = len(new_part) - len(new_part_rstrip)
            if new_part_rstrip and traling_whitespace:
                remaining_part = new_part[-traling_whitespace:] + remaining_part
                new_part       = new_part_rstrip

            split_parts.append(new_part)

        parts[i : i + 1] = split_parts

    if len(parts) == 1:
        yield parts[0]
        return

    chunk     = []
    chunk_len = 0
    for part in parts:
        if chunk and chunk_len + _part_len(part) >= max_len:
            yield "".join(chunk)
            chunk     = []
            chunk_len = 0

        chunk_len += _part_len(part)
        chunk.append(part)

    if chunk:
        yield "".join(chunk)


def iter_wrapped_lines(pre_content_text: str, add_line_numbers: bool = True) -> typ.Iterable[str]:
    pre_content_text  = pre_content_text.replace("<span></span>", "")
    pre_content_lines = pre_content_text.splitlines()
    num_lines         = len(pre_content_lines)
    for line_idx, line in enumerate(pre_content_lines):
        lineno = line_idx + 1

        for part_idx, line_part in enumerate(_iter_wrapped_line_chunks(line, max_len=51)):
            if add_line_numbers:
                if part_idx == 0:
                    yield f'<span class="lineno">{lineno}</span>'
                else:
                    yield f'<span class="lineno">&rarrhk;</span>'

            yield line_part + "\n"


PRE_CODE_BLOCK = """
PYCALVER_REGEX = re.compile(PYCALVER_PATTERN, flags=re.VERBOSE)
INFO    - git tag --annotate v201812.0006-beta --message v201812.0006-beta
INFO    - fetching tags from remote <span class="o">(</span>to turn off use: -n / --no-fetch<span class="o">)</span>
INFO    - git push origin v201812.0006-beta
mypkg  v201812.0665    # last stable release
mypkg  v201812.0666-rc # pre release for testers
mypkg  v201901.0667    # final release after testing period

# bug is discovered in v201812.0666-beta and v201901.0667

mypkg  v201901.0668    # identical code to v201812.0665

# new package is created with compatibility breaking code

mypkg2 v201901.0669    # identical code to v201901.0667
mypkg  v201901.0669    # updated readme, declaring support
                       # level for mypkg, pointing to mypgk2
                       # and documenting how to upgrade.
$ pycalver test 'v201811.0051-beta' '{pycalver}' --release final
"""


# for line_part in iter_wrapped_lines(PRE_CODE_BLOCK.strip(), add_line_numbers=False):
#     print(len(line_part), repr(line_part))
# sys.exit(1)


TAG_BEGIN_RE = re.compile(r"\<(\w+)[^\>]*\>")
TAG_END_RE   = re.compile(r"\</\w+>")
WORD_RE      = re.compile(r"\w+")
SOFT_HYPHEN  = "\u00AD"
SOFT_HYPHEN  = "&shy;"


def _shyphenate_text(dic: pyphen.Pyphen, text: str) -> str:
    if len(text) < 5:
        return text
    else:
        return " ".join(dic.inserted(word, hyphen=SOFT_HYPHEN) for word in text.split(" "))


def _iter_html_parts(
    html_text: HTMLText, begin_tag_re: typ.Pattern, end_tag_re: typ.Pattern
) -> typ.Iterable[typ.Tuple[HTMLText, HTMLText]]:
    remaining_html = html_text
    while remaining_html:
        begin_match = begin_tag_re.search(remaining_html)
        if begin_match is None:
            yield remaining_html, "", ""
            return

        begin_lidx, begin_ridx = begin_match.span()
        prelude = remaining_html[:begin_ridx]

        end_match = end_tag_re.search(remaining_html, begin_ridx)
        assert end_match is not None
        end_lidx, end_ridx = end_match.span()

        inner = remaining_html[begin_ridx:end_lidx]

        end_tag = remaining_html[end_lidx:end_ridx]

        print(prelude[-30:], "##", end_tag)
        yield (prelude, inner, end_tag)

        remaining_html = remaining_html[end_ridx:]


def _shyphenate_html(html_text: HTMLText) -> HTMLText:
    # TODO: parse language
    dic = pyphen.Pyphen(lang="en_US")

    def _iter_shyphenated(content_text: str) -> typ.Iterable[str]:
        html_parts = _iter_html_parts(content_text, TAG_BEGIN_RE, TAG_END_RE)
        for prelude, text, end_tag in html_parts:
            yield prelude
            yield _shyphenate_text(dic, text)
            yield end_tag

    text_tag_begin_re = re.compile(r"\<(p|li)( [^\>]*)?\>")
    text_tag_end_re   = re.compile(r"\</(p|li)\>")

    html_parts = _iter_html_parts(html_text, text_tag_begin_re, text_tag_end_re)
    for prelude, content, end_tag in html_parts:
        yield prelude
        yield "".join(_iter_shyphenated(content))
        yield end_tag


def _postprocess_html_v2(html_text: str) -> typ.Iterable[str]:
    headline_begin_re = re.compile(r"<h\d>")
    pre_begin_re      = re.compile(r'<div class="codehilite"><pre>')
    pre_end_re        = re.compile(r"</pre>")

    remaining_text = html_text
    while remaining_text:
        next_case = 'undefined'

        next_headline_match = headline_begin_re.search(remaining_text)
        next_pre_match      = pre_begin_re.search(remaining_text)

        if next_headline_match is None and next_pre_match is None:
            next_case = 'undefined'
        elif next_headline_match is None:
            next_case = 'pre'
        elif next_pre_match is None:
            next_case = 'headline'
        else:
            headline_begin_lidx, headline_begin_ridx = next_headline_match.span()
            pre_begin_lidx     , pre_begin_ridx      = next_pre_match.span()
            if headline_begin_lidx < pre_begin_lidx:
                next_case = 'headline'
            elif pre_begin_lidx < headline_begin_lidx:
                next_case = 'pre'
            else:
                assert False

        if next_case == 'pre':
            yield html_text[:pre_begin_ridx]

            end_match = pre_end_re.search(remaining_text, pre_begin_ridx + 1)
            assert end_match is not None
            pre_end_lidx, pre_end_ridx = end_match.span()
            pre_content_text = html_text[pre_begin_ridx:pre_end_lidx]
        elif next_case == 'headline':
            yield html_text[:pre_begin_ridx]
        else:
            assert next_case == 'undefined'
            yield remaining_text
            break

    last_end_idx = 0

    for match in pre_begin_re.finditer(html_text):
        yield "".join(iter_wrapped_lines(pre_content_text))

        yield html_text[pre_end_lidx : pre_end_ridx + 1]

        last_end_idx = pre_end_ridx + 1

    yield html_text[last_end_idx:]


def _postprocess_html(html_text: HTMLText) -> typ.Iterable[str]:
    html_text = html_text.replace("<table>" , """<div class="table-wrap"><table>""")
    html_text = html_text.replace("</table>", """</table></div>""")

    # - wrap headline and firstpara
    # - add below the fold
    # - add ids to headlines
    # - collect links and insert superscript (footnote links)

    pre_begin_re = re.compile(r'<div class="codehilite"><pre>')
    pre_end_re   = re.compile(r"</pre>")

    # TODO: firstpara

    last_end_idx = 0

    for match in pre_begin_re.finditer(html_text):
        begin_lidx, begin_ridx = match.span()
        yield html_text[last_end_idx:begin_ridx]

        end_match = pre_end_re.search(html_text, begin_ridx + 1)
        assert end_match is not None
        end_lidx, end_ridx = end_match.span()

        content_text = html_text[begin_ridx:end_lidx]
        yield "".join(iter_wrapped_lines(content_text))

        end_tag = html_text[end_lidx : end_ridx + 1]
        yield end_tag

        last_end_idx = end_ridx + 1

    yield html_text[last_end_idx:]


# If the user hit refresh, then hiding and then showing #below-the-fold
# just causes unnecessary flickering.

STATIC_DIR = pl.Path(".") / "static"

# TODO: Either we're ok with static files or we want a single self
#   contained file. Doing both is stupid.
BROWSER_STYLESHEETS_LINKS = """
<link rel="stylesheet" type="text/css" href="static/codehilite.css">
<link rel="stylesheet" type="text/css" href="static/print.css" media="print">
"""

GENERAL_STYLES_PATH    = STATIC_DIR / "general.css"
GENERAL_STYLES         = GENERAL_STYLES_PATH.open().read()
SCREEN_STYLES_PATH     = STATIC_DIR / "screen.css"
SCREEN_STYLES          = SCREEN_STYLES_PATH.open().read()
CODEHILITE_STYLES_PATH = STATIC_DIR / "codehilite.css"
CODEHILITE_STYLES      = CODEHILITE_STYLES_PATH.open().read()
PRINT_STYLES_PATH      = STATIC_DIR / "print.css"
PRINT_STYLES           = PRINT_STYLES_PATH.open().read()
NAVIGATION_STYLES_PATH = STATIC_DIR / "navigation.css"
NAVIGATION_STYLES      = NAVIGATION_STYLES_PATH.open().read()
PDF_MODAL_STYLES_PATH = STATIC_DIR / "pdf_modal.css"
PDF_MODAL_STYLES      = PDF_MODAL_STYLES_PATH.open().read()

CHECK_RELOADED_JS_PATH = STATIC_DIR / "check_reloaded.js"
CHECK_RELOADED_JS      = CHECK_RELOADED_JS_PATH.open().read()
NAVIGATION_JS_PATH     = STATIC_DIR / "navigation.js"
NAVIGATION_JS          = NAVIGATION_JS_PATH.open().read()


HEAD_HTML = f"""
<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style type="text/css">
{GENERAL_STYLES}
{SCREEN_STYLES}
</style>
</head>
<body class="font-slab">
<script>{CHECK_RELOADED_JS}</script>
<div class="wrapper">
<div class="content">
"""



FOOT_HTML = f"""
<div id="nav">
  <div id="toggle-theme"></div>
  <div id="toggle-font"></div>
  <div id="toggle-print"></div>
</div>
</div>
<div id="pdf">
  <div>normal text layout, more readable but uses more paper <-> dense text
  layout, less readable but fewer pages</div>
  <div>A6 - Portrait (good for Kindle)</div>
  <a href="a6.pdf"><div class="a6 onepage"></div></a>
  <a href="a6-dense.pdf"><div class="a6 onepage dense"></div></a>
  <div>A5 - Portrait</div>
  <a href="a5.pdf"><div class="a5 onepage"></div></a>
  <a href="a5-dense.pdf"><div class="a5 onepage dense"></div></a>
  <div>US Half-Letter - Portrait</div>
  <a href="half-letter.pdf"><div class="half-letter onepage"></div></a>
  <a href="half-letter-dense.pdf"><div class="half-letter onepage dense"></div></a>
  <div>For duplex print, configure your printer to flip on short edge.</div>
  <div>A4 - Booklet</div>
  <a href="a4-booklet.pdf"><div class="a4 twopage booklet"></div></a>
  <a href="a4-booklet-dense.pdf"><div class="a4 twopage booklet dense"></div></a>
  <div>US Letter - Booklet</div>
  <a href="letter-booklet.pdf"><div class="letter twopage booklet"></div></a>
  <a href="letter-booklet-dense.pdf"><div class="letter twopage booklet dense"></div></a>
  <div>If you don't have a duplex printer.</div>
  <div>A4 - Two Page</div>
  <a href="a4-twopage.pdf"><div class="a4 twopage"></div></a>
  <a href="a4-twopage-dense.pdf"><div class="a4 twopage dense"></div></a>
  <div>US Letter - Two Page</div>
  <a href="letter-twopage.pdf"><div class="letter twopage"></div></a>
  <a href="letter-twopage-dense.pdf"><div class="letter twopage dense"></div></a>
</div>
</div>
<style type="text/css">{PDF_MODAL_STYLES}</style>
<style type="text/css">{NAVIGATION_STYLES}</style>
<script type="text/javascript">{NAVIGATION_JS}</script>
{BROWSER_STYLESHEETS_LINKS}
<script src="instapage.js" async></script>
</body>
</html>
"""


def read_md_text(in_paths: typ.List[pl.Path]) -> MarkdownText:
    out_md_text_parts: typ.List[MarkdownText] = []

    for in_path in sorted(in_paths):
        with in_path.open(mode="r", encoding="utf-8") as fh:
            md_text_part: MarkdownText = fh.read()

        out_md_text_parts.append(md_text_part)

    return "\n\n".join(out_md_text_parts)


def _gen_raw_html(md_text: MarkdownText) -> HTMLText:
    import markdown as md

    # https://python-markdown.github.io/extensions/
    extensions = [
        "markdown.extensions.extra",
        "markdown.extensions.abbr",
        "markdown.extensions.attr_list",
        "markdown.extensions.def_list",
        "markdown.extensions.fenced_code",
        "markdown.extensions.footnotes",
        "markdown.extensions.tables",
        "markdown.extensions.admonition",
        "markdown.extensions.codehilite",
        "markdown.extensions.meta",
        "markdown.extensions.sane_lists",
        # # "markdown.extensions.toc",
        "markdown.extensions.wikilinks",
        "markdown_aafigure",
        "markdown_blockdiag",
        "markdown_svgbob",
        #####
        # "markdown.extensions.legacy_attr",
        # "markdown.extensions.legacy_em",
        # "markdown.extensions.nl2br",
        # "markdown.extensions.smarty",
    ]

    md_ctx        = md.Markdown(extensions=extensions)
    raw_html_text = md_ctx.convert(md_text)
    return raw_html_text


def main(args=sys.argv[1:]):
    in_paths: typ.List[pl.Path] = []
    for arg in args:
        in_path = pl.Path(arg)
        ext     = "".join(in_path.suffixes)

        if in_path.exists() and ext == ".md":
            in_paths.append(in_path)

    md_text = read_md_text(in_paths)

    out_dir = pl.Path("lit_out")
    out_dir.mkdir(exist_ok=True)
    out_path_html = out_dir / "out.html"
    out_path_pdf  = out_dir / "out.pdf"

    raw_html_text = _gen_raw_html(md_text)

    if "html" in args:
        browser_html_text = "".join(_postprocess_html(raw_html_text))
        browser_html_text = "".join(_shyphenate_html(browser_html_text))

        print("regenerating ", out_path_html)
        browser_html_string = HEAD_HTML + browser_html_text + FOOT_HTML
        with out_path_html.open(mode="w", encoding="utf-8") as fh:
            fh.write(browser_html_string)

        with (out_dir / "static/codehilite.css").open(mode="w") as fh:
            fh.write(CODEHILITE_STYLES)

        with (out_dir / "static/print.css").open(mode="w") as fh:
            fh.write(PRINT_STYLES)

    # import cmarkgfm
    # test_html_text = cmarkgfm.github_flavored_markdown_to_html(md_text)
    # test_html_text = cmarkgfm.markdown_to_html(md_text)

    if "pdf" in args:
        import weasyprint as wp

        print_html_text   = "".join(_postprocess_html(raw_html_text))
        print_html_string = HEAD_HTML + print_html_text + FOOT_HTML
        wp_ctx            = wp.HTML(string=print_html_string)

        stylesheets = [
            wp.CSS(string=GENERAL_STYLES),
            wp.CSS(string=CODEHILITE_STYLES),
            wp.CSS(string=PRINT_STYLES),
        ]

        print("regenerating ", out_path_pdf)
        with out_path_pdf.open(mode="wb") as fh:
            wp_ctx.write_pdf(fh, stylesheets=stylesheets)


if __name__ == '__main__':
    main()
```


### Future Work

 - Annotation for data sections. Probably only excerpts of these should be displayed/printed by default and on screens there may be styling to expand/collapse these large data blocks. Wasting screen real estate and paper for data is probably not desireable.
