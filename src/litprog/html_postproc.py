# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import io
import re
import math
import string
import typing as typ
import logging
import itertools as it

import bs4
import pyphen

from . import md2html

logger = logging.getLogger(__name__)


MAX_CODE_BLOCK_LINE_LEN = 85

HTML_PART_PATTERN = re.compile(r"(&[#\w]+?;|<.*?>|\s+\w+)")


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


def _iter_new_parts(remaining_part: str, max_len: int) -> typ.Iterable[str]:
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

        yield new_part


def _iter_wrapped_line_parts(line: str, max_len: int) -> typ.Iterable[str]:
    if max_len == 0 or len(line) < max_len:
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
        if _part_len(part) > max_len:
            split_parts = list(_iter_new_parts(remaining_part=part, max_len=max_len))
            parts[i : i + 1] = split_parts

    if len(parts) == 1:
        yield parts[0]
        return

    chunk: typ.List[str] = []
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


BlockLinenos      = typ.List[typ.Tuple[int, int]]
MaybeBlockLinenos = typ.Optional[BlockLinenos]


def iter_wrapped_lines(
    pre_content_text     : str,
    max_line_len         : int  = 80,
    add_line_numbers     : bool = True,
    first_lineno         : int  = 0,
    add_initial_linebreak: bool = False,
) -> typ.Iterable[str]:
    pre_content_text  = pre_content_text.replace("<span></span>", "")
    pre_content_lines = pre_content_text.splitlines()

    # NOTE: code blocks are basically hardcoded to a width of two characters
    # line_number_width = len(str(len(pre_content_lines)))
    for line_idx, line in enumerate(pre_content_lines):
        lineno = first_lineno + line_idx + 1
        parts  = list(_iter_wrapped_line_parts(line, max_len=max_line_len))
        for part_idx, line_part in enumerate(parts):
            if add_line_numbers:
                if part_idx == 0:
                    lineno_span = f"<span class=\"lineno\">{lineno}</span>"
                else:
                    lineno_span = "<span class=\"lineno\">\u21AA</span>"

                if add_initial_linebreak and line_part.startswith("<code"):
                    tag_end_idx = line_part.index(">")
                    # TODO: Fix this cludge. For some reason, the
                    #   first line is indented by less than a full
                    #   space and I have no idea why.
                    _stupid_linebreak = "\n"
                    line_part         = (
                        line_part[: tag_end_idx + 1]
                        + _stupid_linebreak
                        + lineno_span
                        + line_part[tag_end_idx + 1 :]
                    )
                elif line_part != "</code>":
                    yield lineno_span

            if line_part == "</code>":
                # NOTE (mb 2020-06-04): since <code></code> is wrapped with <pre>
                #   we don't want to add extra whitespace at the end.
                yield line_part
            else:
                yield line_part + "\n"


PRE_CODE_BLOCK = """
PYCALVER_REGEX = re.compile(PYCALVER_PATTERN, flags=re.VERBOSE)
INFO    - git tag --annotate v201812.0006-beta --message v201812.0006-beta
INFO    - fetching tags from remote (to turn off use: -n / --no-fetch)
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


def _iter_postproc_content_html(
    html_res             : md2html.HTMLResult,
    max_line_len         : int,
    add_initial_linebreak: bool              = False,
    block_linenos        : MaybeBlockLinenos = None,
) -> typ.Iterable[str]:
    content_html: HTMLText = html_res.raw_html
    content_html = content_html.replace("<table>" , """<div class="table-wrap"><table>""")
    content_html = content_html.replace("</table>", """</table></div>""")

    pre_begin_re = re.compile(r'<div class="codehilite"><pre>')
    pre_end_re   = re.compile(r"</pre>")

    last_end_idx = 0
    block_index  = 0

    for match in pre_begin_re.finditer(content_html):
        _begin_lidx, begin_ridx = match.span()
        yield content_html[last_end_idx:begin_ridx]

        end_match = pre_end_re.search(content_html, begin_ridx + 1)
        assert end_match is not None
        end_lidx, end_ridx = end_match.span()
        content_text = content_html[begin_ridx:end_lidx]

        if block_linenos is None:
            first_lineno = 0
        elif block_index < len(block_linenos):
            first_lineno, num_lines = block_linenos[block_index]
            num_content_lines = content_text.strip("\n").count("\n")
            if num_lines == num_content_lines:
                block_index += 1
            else:
                loc = f"{html_res.filename}"
                logger.warning(f"could not match line numbers of block {loc} to html <code>")
                first_lineno = 0
        else:
            loc = f"{html_res.filename}"
            logger.warning(f"could not match line numbers in {loc} to html <code> block")

        wrapped_lines = iter_wrapped_lines(
            content_text,
            max_line_len=max_line_len,
            first_lineno=first_lineno,
            add_initial_linebreak=add_initial_linebreak,
        )
        yield "".join(wrapped_lines)

        end_tag = content_html[end_lidx : end_ridx + 1]
        yield end_tag

        last_end_idx = end_ridx + 1

    yield content_html[last_end_idx:]


SOFT_HYPHEN = "&shy;"


def _shyphenated(dic: pyphen.Pyphen, word: str) -> str:
    word = dic.inserted(word, hyphen=SOFT_HYPHEN)
    if word[2:7] == SOFT_HYPHEN:
        word = word[:2] + word[7:]
    if word[-7:-2] == SOFT_HYPHEN:
        word = word[:-7] + word[-2:]
    return word


WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


def _iter_shyphenated(dic: pyphen.Pyphen, text: str) -> typ.Iterable[str]:
    # NOTE (mb 2021-03-11): While all browsers now (2021 finally!)
    #   have support for "hyphens: auto;", I need to evaluate which
    #   performs better. Superficially the manuall hyphenation here
    #   seemed to work better.
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
            yield _shyphenated(dic, word)

        prev_end = end

    yield text[prev_end:]


PARSER_MODULE = "html.parser"

INLINE_TAG_NAMES = {"span", "b", "i", "a", "em", "small", "strong", "sub", "sup"}


def _shyphenate(dic: pyphen.Pyphen, text: str) -> str:
    if len(text) < 5:
        return text
    else:
        return "".join(_iter_shyphenated(dic, text))


def _shyphenate_html(soup: bs4.BeautifulSoup) -> None:
    dic = pyphen.Pyphen(lang="en_US")

    elements = it.chain(soup.find_all("p"), soup.find_all("li"))
    for elem in elements:
        for part in elem.contents:
            is_nav_string = isinstance(part, bs4.element.NavigableString)
            is_text_elem  = not is_nav_string and part.name in INLINE_TAG_NAMES and part.string
            if is_nav_string or is_text_elem:
                if is_text_elem:
                    classes  = part.attrs.get('class', ())
                    is_katex = "katex" in classes or "katex-display" in classes
                    if part.name == 'span' and is_katex:
                        continue

                shyphenated = _shyphenate(dic, str(part.string))
                # NOTE: Ugh! So much wrapping just to avoid escaping.
                #   If we don't do this though, we'll get "&shy;" -> "&amp;shy;"
                shy_text = bs4.BeautifulSoup(io.StringIO(shyphenated), PARSER_MODULE)
                part.string.replace_with(shy_text)


def _add_code_scrollers(soup: bs4.BeautifulSoup) -> None:
    for elem in soup.find_all('div', {'class': 'codehilite'}):
        scroller = soup.new_tag('div')
        scroller.attrs['class'] = ['code-scroller']
        list(elem.children)[0].wrap(scroller)


def _update_footnote_refs(soup: bs4.BeautifulSoup) -> None:
    for elem in soup.find_all('a', {'class': 'footnote-ref'}):
        elem.string = "[" + elem.string + "]"


FNOTES_TEXT = "Footnotes and Links"


def _add_footnotes_header(soup: bs4.BeautifulSoup) -> None:
    refs_h        = soup.new_tag('h1')
    refs_h.string = FNOTES_TEXT
    refs_h['id'] = ['references']

    footnotes = soup.find('div', {'class': 'footnote'})
    if footnotes:
        footnotes.insert(2, refs_h)


def _add_footer_links(soup: bs4.BeautifulSoup, fmt: str) -> None:
    hrefs = []
    for a_tag in soup.select('a'):
        href = a_tag.attrs['href']
        if href.startswith("http"):
            hrefs.append(href)

    linklist = soup.new_tag('ol')
    linklist.attrs['class'] = ['linklist']
    footnotes = soup.find('div', {'class': 'footnote'})
    if footnotes:
        footnotes.append(linklist)

    if 'tallcol' in fmt:
        stride = 70
    elif 'letter' in fmt:
        stride = 40
    else:
        stride = 42

    for i, href in enumerate(hrefs):
        linktext        = soup.new_tag('code')
        href_lines      = [href[i : i + stride] for i in range(0, len(href), stride)]
        linktext.string = "\n".join(href_lines)

        link = soup.new_tag('a')
        link['href'] = href
        link.append(linktext)

        li_tag = soup.new_tag('li')
        li_tag.append(link)
        linklist.append(li_tag)


def _add_heading_links(soup: bs4.BeautifulSoup) -> None:
    for heading in soup.select("h1, h2, h3, h4, h5"):
        a_tag = soup.new_tag("a", href="#" + heading['id'])
        if heading.string is None:
            a_tag.extend(list(heading.children))
            heading.clear()
            heading.append(a_tag)
        else:
            heading.string.wrap(a_tag)


def _add_heading_numbers_screen(content_soup: bs4.BeautifulSoup, sections_soup: bs4.BeautifulSoup) -> None:
    numbers_by_hashlink: typ.Dict[str, str] = {
        node['href'].split("#", 1)[-1]: node.text.split(" ", 1)[0] for node in sections_soup.select("a")
    }

    for heading in content_soup.select("h1, h2, h3, h4, h5"):
        number            = numbers_by_hashlink.get(heading['id'], "")
        is_section_number = number and "." in number
        if is_section_number:
            heading.insert(0, number + " ")


def _add_heading_numbers_print(
    soup: bs4.BeautifulSoup, toc_tokens: md2html.TocTokens, heading_prefix: str = ""
) -> None:
    for i, entry in enumerate(toc_tokens):
        heading_number = heading_prefix + str(i + 1)

        tag     = "h" + str(entry['level'])
        heading = soup.find(tag, {'id': entry['id']})
        heading['heading-num'] = heading_number
        if heading_prefix:
            heading.insert(0, heading_number + " ")
        _add_heading_numbers_print(soup, entry['children'], heading_number + ".")


def _add_figure_numbers(soup: bs4.BeautifulSoup) -> None:
    selectors = [
        "h1",
        "p > img",
        ".codehilite",
        ".katex-display",
        "table",
        ".admonition.caption",
    ]
    chapter = 0
    fig_num = -1
    for elem in soup.select(", ".join(selectors)):
        if elem.name == 'h1':
            chapter += 1
            fig_num = -1
        elif 'caption' in elem.get('class', []):
            fig_id      = ""
            cur_fig_num = fig_num
            while cur_fig_num > 0:
                cur_fig_num, rem = divmod(cur_fig_num, 26)
                fig_id = string.ascii_lowercase[rem - 1 if fig_id else rem] + fig_id

            if not fig_id:
                fig_id = "a"

            fig_prefix = "Figure " + str(chapter) + fig_id
            title_elem = elem.find('p', {'class': 'admonition-title'})
            if title_elem:
                title_elem.string = fig_prefix + ": " + (title_elem.string or "")
            else:
                title_elem = soup.new_tag('p')
                title_elem.attrs['class'] = ['admonition-title']
                title_elem.string = fig_prefix
                elem.insert(0, title_elem)
        else:
            fig_num += 1


def _add_nav_numbers(ul_tag: bs4.BeautifulSoup, heading_prefix: str = "", heading: str = "") -> None:
    li_children = [child for child in ul_tag.children if child.name == "li"]

    i = 1
    for li_tag in li_children:
        if heading == li_tag.a.string:
            sub_heading    = heading
            heading_number = sub_heading.split(" ", 1)[0]
        else:
            heading_number  = heading_prefix + str(i)
            sub_heading     = heading_number + " " + li_tag.a.string
            li_tag.a.string = sub_heading
            i += 1

        sub_uls = [child for child in li_tag.children if child.name == "ul"]
        for sub_ul in sub_uls:
            _add_nav_numbers(sub_ul, heading_number + ".", sub_heading)


CODE_CHUNK_SIZE = 5


def _split_code_blocks(soup: bs4.BeautifulSoup) -> None:
    """Split large code blocks so they can span multiple pdf pages."""
    for codehilite in soup.select(".codehilite"):
        code_blocks = codehilite.select("pre > code")
        assert len(code_blocks) == 1
        code_block = code_blocks[0]
        num_lines  = len(code_block.select(".lineno"))
        num_chunks = num_lines / CODE_CHUNK_SIZE
        if num_chunks <= 1:
            continue

        max_chunk_lines = num_lines // math.ceil(num_chunks) + 1
        chunks          = []

        code_nodes = iter(list(code_block.contents))

        try:
            chunk_lines = 0
            chunk       = []
            while True:
                code_node = next(code_nodes)
                is_tag    = isinstance(code_node, bs4.element.Tag)
                if is_tag and 'lineno' in code_node.attrs.get('class'):
                    chunk_lines += 1

                if chunk_lines < max_chunk_lines:
                    chunk.append(code_node)
                else:
                    chunks.append(chunk)

                    chunk_lines = 1
                    chunk       = [code_node]
        except StopIteration:
            if chunk:
                chunks.append(chunk)

        new_pre_nodes = []
        for chunk in chunks:
            new_block          = soup.new_tag('code')
            new_block.contents = chunk
            code_pre           = soup.new_tag('pre')
            code_pre.contents  = [new_block]
            new_pre_nodes.append(code_pre)

        codehilite.contents = new_pre_nodes


def postproc_nav_html(nav_html: HTMLText, has_footnotes: bool = False) -> HTMLText:
    nav_soup = bs4.BeautifulSoup(nav_html, PARSER_MODULE)
    toc_ul   = nav_soup.select(".toc > ul")[0]
    _add_nav_numbers(toc_ul)

    if has_footnotes:
        refs_a        = nav_soup.new_tag('a')
        refs_a.string = FNOTES_TEXT
        refs_a['href'] = "#references"
        refs_li = nav_soup.new_tag('li')
        refs_li.append(refs_a)

        toc_ul.append(refs_li)

    return str(nav_soup)


class HTMLTexts(typ.NamedTuple):
    content : HTMLText
    chapters: HTMLText
    sections: HTMLText

    chapter_prev_href: str
    chapter_next_href: str
    chapter_prev_text: str
    chapter_next_text: str


def postproc4screen(
    html_res     : md2html.HTMLResult,
    block_linenos: BlockLinenos,
    nav_html     : HTMLText,
) -> HTMLTexts:
    # content_html = "".join(_wrap_firstpara(content_html))
    html_chunks = _iter_postproc_content_html(
        html_res,
        max_line_len=MAX_CODE_BLOCK_LINE_LEN,
        add_initial_linebreak=False,
        block_linenos=block_linenos,
    )
    content_html = "".join(html_chunks)

    content_soup = bs4.BeautifulSoup(content_html, PARSER_MODULE)
    nav_soup     = bs4.BeautifulSoup(nav_html    , PARSER_MODULE)

    _add_heading_numbers_screen(content_soup, nav_soup)
    _add_figure_numbers(content_soup)
    _add_heading_links(content_soup)

    # NOTE (mb 2021-04-18): Since chrome finally supports hyphens: auto
    #   on balance is better to disable this. The main reason is that copy
    #   and paste from the html output will include invisible hyphens.
    # _shyphenate_html(content_soup)

    _add_code_scrollers(content_soup)
    _update_footnote_refs(content_soup)
    _add_footnotes_header(content_soup)
    content_html = str(content_soup)

    # content_html = content_html.replace("\u00AD", "&shy;")

    chapters_soup = bs4.BeautifulSoup(str(nav_soup), PARSER_MODULE)
    for elem in chapters_soup.select(".toc a"):
        elem.attrs['href'] = elem.attrs['href'].split("#")[0]

    for elem in chapters_soup.select(".toc > ul > li > ul > li > ul"):
        elem.decompose()

    current_elem = chapters_soup.select(".toc > ul > li > ul > li > a")[0]

    parent       = current_elem.parent.parent.parent
    prev_sibling = parent.previous_sibling
    next_sibling = parent.next_sibling

    while prev_sibling and isinstance(prev_sibling, bs4.element.NavigableString):
        prev_sibling = prev_sibling.previous_sibling
    while next_sibling and isinstance(next_sibling, bs4.element.NavigableString):
        next_sibling = next_sibling.next_sibling

    chapter_prev_href = ""
    chapter_next_href = ""
    chapter_prev_text = ""
    chapter_next_text = ""

    if prev_sibling:
        prev_elem         = prev_sibling.select("a")[0]
        chapter_prev_href = prev_elem.attrs['href'].split("#")[0]
        chapter_prev_text = prev_elem.text
    if next_sibling:
        next_elem         = next_sibling.select("a")[0]
        chapter_next_href = next_elem.attrs['href'].split("#")[0]
        chapter_next_text = next_elem.text

    current_elem.attrs['class'] = "active"
    parent.insert(0, current_elem)

    sections_soup = nav_soup.select(".toc > ul > li > ul")
    if sections_soup:
        sections_html = '<div class="toc">' + str(sections_soup[0]) + "</div>"
    else:
        sections_html = ""

    chapters_html = str(chapters_soup)
    return HTMLTexts(
        content_html,
        chapters_html,
        sections_html,
        chapter_prev_href,
        chapter_next_href,
        chapter_prev_text,
        chapter_next_text,
    )


def postproc4print(html_res: md2html.HTMLResult, fmt: str, block_linenos: BlockLinenos) -> HTMLText:
    # TODO: split code blocks
    # - add ids to headlines
    # - collect links and insert superscript (footnote links)
    if fmt in ("print_a4", "print_letter"):
        max_line_len = MAX_CODE_BLOCK_LINE_LEN
    elif "tallcol" in fmt:
        max_line_len = 72
    elif "ereader" in fmt:
        max_line_len = 72
    else:
        max_line_len = MAX_CODE_BLOCK_LINE_LEN

    html_chunks = _iter_postproc_content_html(
        html_res,
        max_line_len=max_line_len,
        add_initial_linebreak=True,
        block_linenos=block_linenos,
    )
    html_text = "".join(html_chunks)

    content_soup = bs4.BeautifulSoup(html_text, PARSER_MODULE)
    _add_heading_numbers_print(content_soup, html_res.toc_tokens)
    _add_figure_numbers(content_soup)
    _update_footnote_refs(content_soup)
    _add_footnotes_header(content_soup)
    _add_footer_links(content_soup, fmt)
    _split_code_blocks(content_soup)
    html_text = str(content_soup)

    return html_text
