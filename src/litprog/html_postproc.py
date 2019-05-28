import re
import typing as typ


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


def iter_wrapped_lines(pre_content_text: str, add_line_numbers: bool = True) -> typ.Iterable[str]:
    pre_content_text  = pre_content_text.replace("<span></span>", "")
    pre_content_lines = pre_content_text.splitlines()
    num_lines         = len(pre_content_lines)
    for line_idx, line in enumerate(pre_content_lines):
        lineno = line_idx + 1

        for part_idx, line_part in enumerate(_iter_wrapped_line_chunks(line, max_len=60)):
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


def _iter_postproc_html(html_text: HTMLText) -> typ.Iterable[str]:
    html_text = html_text.replace("<table>" , """<div class="table-wrap"><table>""")
    html_text = html_text.replace("</table>", """</table></div>""")

    # TODO: firstpara
    # - wrap headline and firstpara
    # TODO: hyphens
    # TODO: split code blocks
    # - add ids to headlines
    # - collect links and insert superscript (footnote links)

    pre_begin_re = re.compile(r'<div class="codehilite"><pre>')
    pre_end_re   = re.compile(r"</pre>")

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


def postproc4all(html_text: HTMLText) -> HTMLText:
    return "".join(_iter_postproc_html(html_text))


def postproc4print(html_text: HTMLText) -> HTMLText:
    return html_text
