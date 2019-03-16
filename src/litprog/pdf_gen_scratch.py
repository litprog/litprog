import io
import re
import sys

import typing as typ
import pathlib2 as pl

import html5lib


HTML_PART_PATTERN = re.compile(r"(&[#\w]+?;|<.*?>|\s+\w+)")


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


def _iter_line_chunks(line: str, max_len: int) -> typ.Iterable[str]:
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

            # If we break on whitespace, it shouldn't be trailing
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


def iter_lines(
    pre_content_text: str, add_line_numbers: bool = True
) -> typ.Iterable[str]:
    pre_content_text  = pre_content_text.replace("<span></span>", "")
    pre_content_lines = pre_content_text.splitlines()
    num_lines         = len(pre_content_lines)
    for line_idx, line in enumerate(pre_content_lines):
        lineno = line_idx + 1

        for part_idx, line_part in enumerate(_iter_line_chunks(line, max_len=51)):
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


# for line_part in iter_lines(PRE_CODE_BLOCK.strip(), add_line_numbers=False):
#     print(len(line_part), repr(line_part))
# sys.exit(1)


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
        yield "".join(iter_lines(pre_content_text))

        yield html_text[pre_end_lidx : pre_end_ridx + 1]

        last_end_idx = pre_end_ridx + 1

    yield html_text[last_end_idx:]


def _postprocess_html(html_text: str, shy=False) -> typ.Iterable[str]:
    # token_stream = html5lib.parse(html_text)
    html_text = html_text.replace("<table>" , """<div class="table-wrap"><table>""")
    html_text = html_text.replace("</table>", """</table></div>""")

    # - wrap headline and firstpara
    # - add below the fold
    # - add ids to headlines
    # - add shy to text
    # - collect links and insert superscript (footnote links)

    # html5lib.serialize(token_stream, omit_optional_tags=False)

    pre_begin_re = re.compile(r'<div class="codehilite"><pre>')
    pre_end_re   = re.compile(r"</pre>")

    para_begin_re = re.compile(r"<p>")
    para_end_re   = re.compile(r"</p>")

    # TODO: firstpara

    last_end_idx = 0

    for match in pre_begin_re.finditer(html_text):
        pre_begin_lidx, pre_begin_ridx = match.span()
        yield html_text[last_end_idx:pre_begin_ridx]

        end_match = pre_end_re.search(html_text, pre_begin_ridx + 1)
        assert end_match is not None
        pre_end_lidx, pre_end_ridx = end_match.span()

        pre_content_text = html_text[pre_begin_ridx:pre_end_lidx]
        yield "".join(iter_lines(pre_content_text))

        yield html_text[pre_end_lidx : pre_end_ridx + 1]

        last_end_idx = pre_end_ridx + 1

    yield html_text[last_end_idx:]


GENERAL_STYLES = r"""

html, body {
    padding: 0;
    margin: 0;

    text-align: justify;
    text-justify: inter-word;
    webkit-font-smoothing: antialiased;
}

body.font-slab {font-family: "Bitter", Gelasio, Georgia, serif;}
body.font-serif {font-family: Merriweather, Gelasio, Georgia, "Times New Roman", serif;}
body.font-sans {font-family: "PT Sans", Arial, Helvetica, sans-serif;}

body.font-serif code {font-size: 0.95em;}
body.font-serif code {font-size: 0.9em;}
body.font-sans code {font-size: 0.9em;}

table {
    border-collapse: collapse;
    text-align: left;
}
th, td {
    border: 1px solid #AAA;
    padding: 0.2em 0.4em;
    border-width: 0 1px;
}
tr td {
    border-bottom: 1px dashed #CCC;
}
th:last-child, td:last-child {
    border-right: none;
}
th:first-child, td:first-child {
    border-left: none;
}
th {
    border-bottom: 1px solid #AAA;
    padding-top: 0.5em;
    padding-bottom: 0.5em;
}
tr:first-child td {
    padding-top: 0.5em;
}
tr:last-child td {
    border-bottom: none;
}
p, ul, ol {hyphens: auto; hyphenate-limit-chars: 5 2 3; }
h1 {
    page-break-before: always;
    margin: 3em 0 2em 0;
}
h1, h2, h3, h4, h5 {
    margin-top: 2em;
    margin-bottom: 1em;
    letter-spacing: 0.1em;
    font-weight: bold;
    line-height: 1.3em;
    counter-reset: paragraph 1;
    counter-reset: section 1;
    font-variant: small-caps;
    text-align: left;
    transition: color 0ms linear 300ms;
}

h2:hover:before, h3:hover:before, h4:hover:before, h5:hover:before {
    content: "‣";
    display: inline-block;
    margin-left: -1em;
    width: 1em;
}

h1 {
    margin-bottom: 1em;
    text-align: center;
}

h1 > a, h2 > a, h3 > a, h4 > a, h5 > a {
    color: black;
    text-decoration: none;
    transition: color 0ms linear 300ms;
}
a, a:visited {
    color: black;
}

p, blockquote, div.codehilite, table {
    margin: 0 0 1em 0;
}

code {
    border: 1px dotted #AAA;
    font-size: 0.95em;
}

"""

# If the user hit refresh, then hiding and then showing #below-the-fold
# just causes unnecessary flickering.

CHECK_RELOADED_JS = """
(function () {
  var perf = window.performance;
  if (perf && perf.navigation.type == perf.navigation.TYPE_RELOAD) {
    var style = document.createElement("style");
    style.textContent = "#below-the-fold {display: block;}";
    document.head.appendChild(style);
  }

  var cl = document.body.classList;

  var stored_font = localStorage.getItem("litprog_font")
  if (stored_font != null) {
    cl.remove("font-serif");
    cl.remove("font-sans");
    cl.remove("font-slab");
    cl.add("font-" + stored_font);
  }

  var stored_theme = localStorage.getItem("litprog_theme")
  var use_dark_theme = (
    stored_theme !== null && stored_theme == "dark"
    || matchMedia('(light-level: dim)').matches
    || matchMedia('(prefers-color-scheme: dark)').matches
  );
  if (use_dark_theme) {
    cl.add("dark");
  } else {
    cl.add("light");
  }
})();
"""

SCREEN_STYLES = """

@keyframes fade-out-in-1 {
  0% {opacity: 1;}
  10% {opacity: 0;}
  90% {opacity: 0;}
  100% {opacity: 1;}
}

@keyframes fade-out-in-2 {
  0% {opacity: 1;}
  10% {opacity: 0;}
  90% {opacity: 0;}
  100% {opacity: 1;}
}

.animate.light .wrapper::after {
    animation: fade-out-in-1 1500ms;
    animation-fill-mode: forwards;
}
.animate.dark .wrapper::after {
    animation: fade-out-in-2 1500ms;
    animation-fill-mode: forwards;
}

.animate.light .content {
    animation: fade-out-in-1 1500ms;
    animation-fill-mode: forwards;
}
.animate.dark .content {
    animation: fade-out-in-2 1500ms;
    animation-fill-mode: forwards;
}

@media screen {
    body {
        color: #000;
        font-size: 20px;
        line-height: 1.5em;
        background: #F2F0F0;
        width: 100%;

        transition: background 1200ms linear 150ms, color 0ms linear 300ms;
        will-change: background;
    }
    .wrapper {
        position: relative;
        padding: 3em;
        margin: 6em auto 2em auto;
        line-height: 1.55em;
        min-width: 20em;
        min-height: 120em;
        max-width: 33em;
        box-shadow: #888 0 0 50px -5px;

        background: #F9F6F6;
        transition: background 1200ms linear 150ms;
        will-change: background;
    }
    /*
    .wrapper::after {
        content: "";
        background: #888;
        position: absolute;
        width: 100%;
        height: 100%;
        z-index: -1;
        top: 0;
        left: 0;
        filter: drop-shadow(0 0 10px #888);
        opacity: 0.5;
    }
    */

    code {
        margin: 0 0.2em;
        padding: 0.1em 0.2em 0.15em 0.2em;
    }

    .table-wrap, .codehilite {
        overflow-x: auto;
        padding-bottom: 0.3em;
    }
}

@media only screen and (max-width: 50em) {
    body {
        min-width: 23em;
        font-size: 20px;
        background: #F9F6F6;
    }
    body.dark { background: #000; }
    .wrapper, body.dark .wrapper {
        margin: 0 auto;
    }
    ul, ol {
        padding: 0 1.5em;
    }
}

@media only screen and (max-width: 50.0em) {.wrapper {padding: 3em 2em;}}

@media only screen and (max-width: 47.5em) {.wrapper {padding: 3em 1em;}}

@media only screen and (max-width: 45.0em) { body {font-size: 19px;} }
@media only screen and (max-width: 42.5em) { body {font-size: 18px;} }
@media only screen and (max-width: 40.0em) { body {font-size: 17px;} }
@media only screen and (max-width: 38.0em) { body {font-size: 16px;} }
@media only screen and (max-width: 35.5em) { body {font-size: 15px;} }
@media only screen and (max-width: 33.5em) { body {font-size: 16px;} }


@media screen {
    #below-the-fold {
        /*
        Depending on your device, this allows the
        first paint happen 50-300ms earlier.
        */
        display: none;
    }
}

.dark {
    background: #111;
    color: #FFF;
}
.dark h1 > a, .dark a, .dark a:visited {
    color: #FFF;
}
.dark .wrapper {
    background: #000;
}
"""


CODEHILITE_STYLES_PATH = pl.Path(".") / "litprog_codehilite.css"
CODEHILITE_STYLES      = CODEHILITE_STYLES_PATH.open().read()
PRINT_STYLES_PATH      = pl.Path(".") / "litprog_print.css"
PRINT_STYLES           = PRINT_STYLES_PATH.open().read()


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

NAVIGATION_JS = """
(function() {
  var cl = document.body.classList
  function toggle_color_theme(e) {
    if (cl.contains("dark")) {
      cl.remove("dark");
      cl.add("light");
    } else {
      cl.remove("light");
      cl.add("dark");
    }
    cl.add("animate");
    var prev_theme = localStorage.getItem("litprog_theme")
    if (prev_theme == "dark") {
        localStorage.setItem("litprog_theme", "light");
    } else {
        localStorage.setItem("litprog_theme", "dark");
    }
    e.stopPropagation();
  }

  function toggle_typeface(e) {
    if (cl.contains("font-slab")) {
      cl.remove("font-slab");
      cl.add("font-serif");
      localStorage.setItem("litprog_font", "serif");
    } else if (cl.contains("font-serif")) {
      cl.remove("font-serif");
      cl.add("font-sans");
      localStorage.setItem("litprog_font", "sans");
    } else {
      cl.remove("font-sans");
      cl.add("font-slab");
      localStorage.setItem("litprog_font", "slab");
    }
    e && e.stopPropagation();
  }

  document.getElementById("toggle-theme").addEventListener("click", toggle_color_theme);
  document.getElementById("toggle-font").addEventListener("click", toggle_typeface);
  document.getElementById("toggle-print").addEventListener("click", function(e) {
    document.getElementById("pdf").classList.toggle("active")
    e.stopPropagation();
  });
  document.getElementById("pdf").addEventListener("click", function(e) {
    e.stopPropagation();
  });
  document.addEventListener('click', function(e) {
    document.getElementById("pdf").classList.remove("active")
  });

  document.addEventListener('keydown', function(e) {
    if (e.key == "Alt") {return;}
    if (!e.altKey) {return;}

    // var styles = window.getComputedStyle(document.body, "p")
    // var line_height_str = styles.getPropertyValue("line-height");
    // var line_height_px = parseInt(line_height_str.slice(0, -2));
    //
    // var extra_scroll = 0;
    //
    // if (e.key == "j") {extra_scroll = line_height_px * 3;}
    // if (e.key == "J") {extra_scroll = line_height_px * 9;}
    // if (e.key == "k") {extra_scroll = line_height_px * -3;}
    // if (e.key == "K") {extra_scroll = line_height_px * -9;}
    //
    // if (extra_scroll !== 0) {
    //     window.scrollBy(0, extra_scroll);
    // }

    if (e.key == "n") {
        // Next Headline
    }
    if (e.key == "p") {
        // Previous Headline
    }
    if (e.key == "t") {
        toggle_typeface(e);
    }
    if (e.key == "c") {
        toggle_color_theme(e);
    }
  });
})();
"""

NAVIGATION_STYLES = """
  @media screen {
    #below-the-fold {
      display: block;
    }
    #nav {
      position: absolute;
      user-select: none;
      top: -4em;
      right: 2em;
    }
    #nav > div:before {
      display: block;
      font-weight: bold;
      text-align: center;
      vertical-align: middle;
      line-height: 1.1em;
    }
    #nav > div#toggle-theme:before {
      font-family: sans-serif;
      content: "☀";
    }
    .font-slab #nav > div#toggle-font:before {content: "F₁";}
    .font-serif #nav > div#toggle-font:before {content: "F₂";}
    .font-sans #nav > div#toggle-font:before {content: "F₃";}
    #nav > div#toggle-print:before {content: "P";}
    .dark #nav > div#toggle-theme:before {content: "☾";}
    #nav > div {
      display: inline-block;
      font-weight: bold;
      margin: 0 0.2em;
      cursor: pointer;
      background: #FFF;
      padding: 0.5em;
      width: 1em;
      height: 1em;
      border-radius: 1em;
      box-shadow: #888 0 0 20px -2px;
      transition: background 500ms, box-shadow 300ms;

      position: relative;
      overflow: hidden;
    }
    #nav > div:hover {
      box-shadow: #888 0px 1px 15px -2px;
    }
    .dark #nav > div {
      background: #000;
    }

    #nav div:after {
      content: "";
      background: #888;
      display: block;
      position: absolute;
      padding: 2em;
      border-radius: 4em;
      top: -1em;
      left: -1em;
      opacity: 0;
      transition: all 500ms;
    }

    #nav div:active:after {
      top: 1em;
      left: 1em;
      padding: 0;
      opacity: 1;
      transition: 0s
    }
  }
  @media only screen and (max-width: 50em) {
      #nav {
        position: absolute;
        user-select: none;
        top: 2em;
        right: 21
      }
  }
"""

PDF_MODAL_STYLES = """
  .dark #pdf {
    background: black;
  }
  #pdf {
    background: white;
    text-align: center;

    user-select: none;
    position: absolute;

    left: 50%;
    margin-left: -14em;
    width: 26em;

    padding: 1em;
    min-height: 15em;
    top: -150em;
    box-shadow: rgba(150, 150, 150, 0.3) 0px 2px 30px 5px;
    transition: top 300ms ease-in-out;
    will-change: top;
  }
  #pdf.active {
    top: 2em;
  }
  #pdf a div.onepage, #pdf a div.twopage {
    position: relative;
    color: black;
    background: #fff;
    border: 1px solid #888;
    margin: 1em;
    display: inline-block;
  }
  #pdf a div:before, #pdf a div.twopage:after {
    z-index: 1;
    top: 3%;
    position: absolute;
    font: 0.7em/0.4em black sans-serif;
    text-align: justify;
    content: "– — – — – – – — – — – – – — – — – – — –– — – –– – — – — – – – — – — – – — –– — – – — – – — – – — – — — – – — – — – — – — – — – — – — —– — – — – – — –– — – – — – – — – – — – — — – – — – — – — – — – — – — – — —– — – — – – — –– — – – — – – — – – — – — — – – — – — – — – — – — – — – — — – — – — – – – — – — – – – — – — – – — –– — – –– – — – — – – – — – — – – — –– — – – — – – — – – — – — — – – — – — – — – — – — – — – — —– — – — – – — –– — – – — – – — – – — – — — – – — – — – — – — – — – — – — —– — – — – – — –– — – – — – – — – – — – — — – – — – — – — – — – — – — – — —";
    color: #888;
    overflow: hidden;
    display: block;
    padding: 0 3%;
    height: 92%
  }
  #pdf a div.dense:before, #pdf a div.dense:after {
    line-height: 0.35;
    font-size: 0.6em;
  }
  #pdf a div.onepage:before {
    max-width: 90%;
    padding: 0 6%;
    left: 0;
  }
  #pdf a div.twopage:before {
    left: 0;
  }
  #pdf a div.twopage:before, #pdf a div.twopage:after {
    max-width: 44%;
  }
  #pdf a div.twopage:after {
    right: 0;
  }
  #pdf .a6 {
    width: calc(1.05 * 3em);
    height: calc(1.48 * 3em);
  }
  #pdf .a5 {
    width: calc(1.48 * 3em);
    height: calc(2.10 * 3em);
  }
  #pdf .half-letter {
    width: calc(1.40 * 3em);
    height: calc(2.16 * 3em);
  }
  #pdf .a4 {
    width: calc(2.96 * 3em);
    height: calc(2.10 * 3em);
  }
  #pdf .letter {
    width: calc(2.80 * 3em);
    height: calc(2.16 * 3em);
  }
"""

BROWSER_STYLESHEETS_LINKS = """
<link rel="stylesheet" type="text/css" href="litprog_codehilite.css">
<link rel="stylesheet" type="text/css" href="litprog_print.css" media="print">
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


def main(args=sys.argv[1:]):
    for arg in args:
        in_path = pl.Path(arg)
        ext     = "".join(in_path.suffixes)

        if not (in_path.exists() and ext == ".md"):
            continue

        in_name = in_path.name[: -len(ext)]

        in_path_md    = in_path.parent / (in_name + ".md")
        out_path_html = in_path.parent / (in_name + ".html")
        out_path_pdf  = in_path.parent / (in_name + ".pdf")

        with in_path_md.open(mode="r", encoding="utf-8") as fh:
            test_md_text = fh.read()

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
            # "markdown_aafigure",
            #####
            # "markdown.extensions.legacy_attr",
            # "markdown.extensions.legacy_em",
            # "markdown.extensions.nl2br",
            # "markdown.extensions.smarty",
        ]

        md_ctx        = md.Markdown(extensions=extensions)
        raw_html_text = md_ctx.convert(test_md_text)

        if "html" in args:
            browser_html_text = "".join(_postprocess_html(raw_html_text, shy=True))

            with (in_path.parent / "litprog_codehilite.css").open(mode="w") as fh:
                fh.write(CODEHILITE_STYLES)

            with (in_path.parent / "litprog_print.css").open(mode="w") as fh:
                fh.write(PRINT_STYLES)

            print("regenerating ", in_path, "->", out_path_html)
            browser_html_string = HEAD_HTML + browser_html_text + FOOT_HTML
            with out_path_html.open(mode="w", encoding="utf-8") as fh:
                fh.write(browser_html_string)

        # import cmarkgfm
        # test_html_text = cmarkgfm.github_flavored_markdown_to_html(test_md_text)
        # test_html_text = cmarkgfm.markdown_to_html(test_md_text)

        if "pdf" in args:
            import weasyprint as wp

            print_html_text   = "".join(_postprocess_html(raw_html_text, shy=False))
            print_html_string = HEAD_HTML + print_html_text + FOOT_HTML
            wp_ctx            = wp.HTML(string=print_html_string)

            stylesheets = [
                wp.CSS(string=GENERAL_STYLES),
                wp.CSS(string=CODEHILITE_STYLES),
                wp.CSS(string=PRINT_STYLES),
            ]

            print("regenerating ", in_path, "->", out_path_pdf)
            with out_path_pdf.open(mode="wb") as fh:
                wp_ctx.write_pdf(fh, stylesheets=stylesheets)


if __name__ == '__main__':
    main()
