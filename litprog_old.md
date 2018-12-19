
#  `code.markdown` 

## In&shy;tro&shy;duc&shy;tion

 `code.markdown`  is a lit&shy;er&shy;ate pro&shy;gram&shy;ming tool. Source files are
writ&shy;ten in mark&shy;down, which con&shy;tain both doc&shy;u&shy;men&shy;ta&shy;tion and the
ex&shy;e&shy;cutable source code. The goal is to write high qual&shy;i&shy;ty
&shy;doc&shy;u&shy;men&shy;ti&shy;tion which al&shy;so hap&shy;pens to be the im&shy;ple&shy;men&shy;ta&shy;tion of what
is doc&shy;u&shy;ment&shy;ed.

Here is a min&shy;i&shy;mal ex&shy;am&shy;ple of what a file  `fib.py.lit`  might look
&shy;like:

    --------------------------------------------------

    ### Basic Fibonacci Example

    A function to compute the nth Fibonacci number might be
    defined as follows:

    $$ F_n = F_{n-1} + F_{n-2} $$
    $$ F_0 = 0 $$
    $$ F_1 = 1 $$

    A naive implementation in Python might look like this[^1]:

    [^1]:
        The infinite sequence can be produced with he following
        generator function:
        
        ```
        def fib():   
            a, b = 1, 1
            while True:
                yield a
                a, b = b, a + b
        ```

    ```
    def fib(n):
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)
    ```

    Now let's see it in action.

    {{capture: stdout}}
    ```
    for i in range(10):
        print("fib({}) == {}".format(i, fib(i)))
    ```

    --------------------------------------------------

Here is the html out&shy;put gen&shy;er&shy;at&shy;ed by the above code
(de&shy;lim&shy;it&shy;ed by the hor&shy;i&shy;zon&shy;tal rules):

--------------------------------------------------

### Ba&shy;sic Fi&shy;bonac&shy;ci Ex&shy;am&shy;ple

A func&shy;tion to com&shy;pute the nth Fi&shy;bonac&shy;ci num&shy;ber might be
de&shy;fined as fol&shy;lows:

$$ F_n = F_{n-1} + F_{n-2} $$
$$ F_0 = 0 $$
$$ F_1 = 1 $$

A naive im&shy;ple&shy;men&shy;ta&shy;tion in Python might look like this[^1]:

[^1]:
    The infinite sequence can be produced with he following
    generator function:
    
    ```
    def fib():   
        a, b = 1, 1
        while True:
            yield a
            a, b = b, a + b
    ```

```
:::python
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

Now let's see it in ac&shy;tion.

```
:::python
for i in range(10):
    print("fib({}) == {}".format(i, fib(i)))
```

--------------------------------------------------

## For&shy;mat

Meta&shy;da&shy;ta can be as&shy;so&shy;ci&shy;at&shy;ed with each sec&shy;tion of the mark&shy;dow file,
which gives you con&shy;trol over how the tar&shy;get for&shy;mats are gen&shy;er&shy;at&shy;ed.
&shy;Take a look at the gen&shy;er&shy;at&shy;ed [fib.py.htm&shy;l](&shy;fib.py.htm&shy;l). You can see,
that the out&shy;put of a fenced sec&shy;tion is be cap&shy;tured and a new sec&shy;tion
is gen&shy;er&shy;at&shy;ed.

We hope to make it as easy as pos&shy;si&shy;ble to write the high qual&shy;i&shy;ty
&shy;doc&shy;u&shy;men&shy;ta&shy;tion.


## Doc&shy;u&shy;men&shy;ta&shy;tion vs Code

&shy;Code de&shy;scribes what hap&shy;pens and doc&shy;u&shy;men&shy;ta&shy;tion should de&shy;scribe why
it hap&shy;pen&shy;s.

## Mo&shy;ti&shy;va&shy;tion - Lit&shy;er&shy;ate Pro&shy;gram&shy;ming

> [Let us change our at&shy;ti&shy;tude to pro&shy;gram&shy;ming: We should not fo&shy;cus
> on telling a com&shy;put&shy;er what to do, rather we should fo&shy;cus on
> ex&shy;plain&shy;ing to hu&shy;mans what we want a com&shy;put&shy;er to do.]
>
>  — Don&shy;ald Knuth para&shy;phrased from
> [
>   "Lit&shy;er&shy;ate Pro&shy;gram&shy;ming (1984)" CSLI, 1992, pg. 99
> ](http://www.lit&shy;er&shy;atepro&shy;gram&shy;ming.&shy;com/lpquotes.htm&shy;l).

&shy;Sounds good does&shy;n't it. It sounds even bet&shy;ter when you want to fix a
bug in an ex&shy;ist&shy;ing pro&shy;gram that some&shy;body else wrote. Or maybe you
wrote the code a while ago and now you have no idea why you wrote it
the way you did. So be&shy;sides curs&shy;ing de&shy;vel&shy;op&shy;ers that came be&shy;fore us,
what can we do to im&shy;prove this sit&shy;u&shy;a&shy;tion? One sug&shy;ges&shy;tion

&shy;So if lit&shy;er&shy;ate pro&shy;gram&shy;ming is such a great idea, why is&shy;n't it more
widespread in in&shy;dus&shy;try? It has had some suc&shy;cess in pro&shy;gram&shy;ming
lit&shy;er&shy;a&shy;ture and academi&shy;a, where ex&shy;po&shy;si&shy;tion to hu&shy;mans is more im&shy;por&shy;tan&shy;t,
&shy;so lets lis&shy;ten to what one prac&shy;ti&shy;tion&shy;er had to say about his
&shy;ex&shy;pe&shy;ri&shy;ence:


> It turned out to be much more dif&shy;fi&shy;cult to pro&shy;duce a lit&shy;er&shy;ate
> pro&shy;gram than pro&shy;duc&shy;ing ei&shy;ther a piece of lit&shy;er&shy;a&shy;ture or a pro&shy;gram
> alone. It is eas&shy;i&shy;er to write on&shy;ly a book, be&shy;cause the au&shy;thor can
> eas&shy;i&shy;ly de&shy;crease the lev&shy;el of de&shy;tail in the ex&shy;po&shy;si&shy;tion and re&shy;sort to
> a more su&shy;per&shy;fi&shy;cial de&shy;scrip&shy;tion when&shy;ev&shy;er de&shy;sired. It is eas&shy;i&shy;er to
> write on&shy;ly a pro&shy;gram, be&shy;cause the pro&shy;gram&shy;mer can set&shy;tle for cor&shy;rec&shy;t
> and ef&shy;fi&shy;cient code even if it is hard to un&shy;der&shy;stand. None of this is
> pos&shy;si&shy;ble in lit&shy;er&shy;ate pro&shy;gram&shy;ming. I found my&shy;self very of&shy;ten
> rewrit&shy;ing a cor&shy;rect and ef&shy;fi&shy;cient piece of code just be&shy;cause I did
> not man&shy;age to ex&shy;plain it very well. And I had to think hard about
> ex&shy;tract&shy;ing the in&shy;ter&shy;est&shy;ing ideas from repet&shy;i&shy;tive tasks, re&shy;sort&shy;ing to
> code and ta&shy;ble gen&shy;er&shy;a&shy;tion in&shy;stead of sim&shy;ple pro&shy;gram&shy;ming. On the
> pos&shy;i&shy;tive side, while both ac&shy;tiv&shy;i&shy;ties — writ&shy;ing and pro&shy;gram&shy;ming —
> be&shy;come hard&shy;er, the qual&shy;i&shy;ty in&shy;creas&shy;es too. Pro&shy;grams be&shy;come more
> ef&shy;fi&shy;cien&shy;t, more re&shy;li&shy;able, and more read&shy;able; the doc&shy;u&shy;men&shy;ta&shy;tion
> be&shy;comes com&shy;pre&shy;hen&shy;sive, de&shy;tailed, and may be even en&shy;joy&shy;able.
>
>  — Mar&shy;tin Ruck&shy;ert from "Un&shy;der&shy;stand&shy;ing MP3 (2005)", pg. v

In oth&shy;er word&shy;s, we should&shy;n't kid our&shy;selves. This is more work. What
we need to judge is, whether or not that work will pay of&shy;f.

I find, that I am much more thought&shy;ful about how I write code, if I
&shy;ex&shy;pect it to re&shy;ceive even the slight&shy;est bit of re&shy;view. An ex&shy;pe&shy;ri&shy;enced
&shy;col&shy;legue who does&shy;n't know the par&shy;tic&shy;u&shy;lar pro&shy;gram&shy;ming lan&shy;guage you are
us&shy;ing, may still be able to pro&shy;vide use&shy;ful feed&shy;back in a code re&shy;view
of a lit&shy;er&shy;ate pro&shy;gram.

&shy;Ex&shy;plo&shy;ration of ideas.

Well, lets look at one of the more pop&shy;u&shy;lar lit&shy;er&shy;ate pro&shy;gram&shy;ming tool&shy;s:

 doc&shy;u&shy;men&shy;ta&shy;tion be&shy;comes out&shy;dat&shy;ed
 yag&shy;ni

An&shy;ot&shy;er prob&shy;lem is that even in semi-pop&shy;u&shy;lar lit&shy;er&shy;ate pro&shy;gram&shy;ming
&shy;tool&shy;s, the doc&shy;u&shy;men&shy;ta&shy;tion is of&shy;ten still treat&shy;ed as a sec&shy;ond class
c&shy;i&shy;t&shy;i&shy;zen.

There are many bar&shy;ri&shy;ers to the adop&shy;tion of a pro&shy;gram&shy;ming tool.

 1. How hard is it to in&shy;stal&shy;l?
 2. If you get it set up, how hard is it to learn?
 3. If you have learned it, how much fric&shy;tion does it ad&shy;d
    to development?
 4. Is all that ef&shy;fort even worth it?

> [...a pro&shy;gram&shy;mer, who wants to pro&shy;vide the best pos&shy;si&shy;ble
> doc&shy;u&shy;men&shy;ta&shy;tion, needs two things: a lan&shy;guage for for&shy;mat&shy;ting, and a
> lan&shy;guage for pro&shy;gram&shy;ming. Nei&shy;ther by it&shy;self can pro&shy;vide the best
> doc&shy;u&shy;men&shy;ta&shy;tion; but when both lan&shy;guages are com&shy;bined, we ob&shy;tain a
> sys&shy;tem that is much more use&shy;ful than ei&shy;ther sep&shy;a&shy;rate&shy;ly.]
>
>  — Don&shy;ald Knuth para&shy;phrased from
> [
>   "Lit&shy;er&shy;ate Pro&shy;gram&shy;ming (1984)" CSLI, 1992, pg. 99
> ](http://www.lit&shy;er&shy;atepro&shy;gram&shy;ming.&shy;com/lpquotes.htm&shy;l).

> [Doc&shy;co is a quick&shy;-and-dirty doc&shy;u&shy;men&shy;ta&shy;tion gen&shy;er&shy;a&shy;tor... It pro&shy;duces
> an HTML doc&shy;u&shy;ment that dis&shy;plays your com&shy;ments in&shy;ter&shy;min&shy;gled with your
> code.]
>
> — Jere&shy;my Ashke&shy;nas para&shy;phrased from http&shy;s://&shy;jashke&shy;nas.github.io/&shy;doc&shy;co/

Dis&shy;ad&shy;van&shy;tages of doc&shy;u&shy;men&shy;ta&shy;tion in code

 - Out&shy;put of the code (doc&shy;u&shy;men&shy;ta&shy;tion is an&shy;cil&shy;lary)
 - Out&shy;put for the web (code is an&shy;cil&shy;lary)
 - Ty&shy;pog&shy;ra&shy;phy and Read&shy;abil&shy;i&shy;ty (a&shy;ka what doc&shy;co got right)
    - Max Width
    - Contrast, i.e. Black on White
    - Hyphenation and Justification
    - Font Size
    - Code Monospaced and max line length
    - Linking
    - use same link schema as standardlib where possible
      https://docs.python.org/3/library/collections.html#collections.namedtuple


## To&shy;ward a Cul&shy;ture of Qual&shy;i&shy;ty and Crafts&shy;man&shy;ship

The larg&shy;er a sys&shy;tem, the more com&shy;po&shy;nents it is com&shy;posed of, the high&shy;er
the like&shy;ly&shy;hood that any one of them will fail and bring the sys&shy;tem to
a halt. Af&shy;ter a long ses&shy;sion of de&shy;bug&shy;ging (e&shy;spe&shy;cial&shy;ly when deal&shy;ing
with a con&shy;cur&shy;ren&shy;cy is&shy;sue), I am of&shy;ten amazed that any of the&shy;se
&shy;com&shy;put&shy;er things ev&shy;er work at al&shy;l. I gain a new ap&shy;pre&shy;ci&shy;a&shy;tion for how
in&shy;cred&shy;i&shy;bly frag&shy;ile these sys&shy;tems can be and how much time we end up&shy;
wast&shy;ing by hot fix&shy;ing, re&shy;boot&shy;ing and re&shy;cov&shy;er&shy;ing, all in an ef&shy;fort to
&shy;keep&shy;

The more we have to ex&shy;plain our work to oth&shy;er&shy;s, the more like&shy;ly we
are be em&shy;bar&shy;resed at cut&shy;ting cor&shy;ner&shy;s. The more oth&shy;ers see and read&shy;
our work, the more like&shy;ly er&shy;rors and bad prac&shy;tices are to be
&shy;cor&shy;rect&shy;ed. Imag&shy;ine how com&shy;fort&shy;able pas&shy;sen&shy;gers would be, get&shy;ting on
a plane. Even for the best of us, code is of&shy;ten cryp&shy;tic and for the
av&shy;er&shy;age us&shy;er hid&shy;den from plain sight.

Let us take look at com&shy;mon per&shy;cep&shy;tions of cul&shy;tures. At least in my
&shy;mind,
These may be gen&shy;er&shy;al&shy;iza&shy;tion&shy;s, but they have a re&shy;al ef&shy;fec&shy;t. I think
&shy;by now, man&shy;agers will think twice about out&shy;sourc&shy;ing soft&shy;ware
de&shy;vel&shy;op&shy;ment to In&shy;di&shy;a. When high enough a price has been payed,
when enough projects have failed, the old truth re&shy;asserts it&shy;self:
Y&shy;ou get what you pay for.
&shy;Good work&shy;man&shy;ship can be rec&shy;og&shy;nized in dif&shy;fer&shy;ent cul&shy;tures. Ger&shy;man
engi&shy;neer&shy;ing vs
The re&shy;sults we have seen by out&shy;sourc&shy;ing to
The less we think of the next dead&shy;line and the more we think of
our&shy;selves a few years down the road, the


## Virtues for Pro&shy;gram&shy;ming

Own&shy;er&shy;ship
Dil&shy;li&shy;gence/Hu&shy;mil&shy;li&shy;ty
Fru&shy;gal&shy;i&shy;ty/&shy;Ef&shy;fi&shy;cien&shy;cy


## Meta&shy;data

The or&shy;der in which you would like to present code to a hu&shy;man may be
d&shy;if&shy;fer&shy;ent than the or&shy;der re&shy;quired by a com&shy;put&shy;er. For ex&shy;am&shy;ple, a hu&shy;man
might like to read a high lev&shy;el over&shy;view of an al&shy;go&shy;rithm and on&shy;ly
&shy;sub&shy;se&shy;quent&shy;ly go in&shy;to its de&shy;tail&shy;s. How&shy;ev&shy;er a pro&shy;gram&shy;ming lan&shy;guage may
re&shy;quire all the de&shy;pen&shy;den&shy;cies of an al&shy;go&shy;rithm to be de&shy;clared be&shy;fore
their us&shy;age.


## Boil&shy;er&shy;plate

```
:::python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
```

test is for from

```
:::python
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
```

## CLI --help Mes&shy;sage

```
:::python
"""

"""
```

## Stan&shy;dard Lib Im&shy;port&shy;s

```
:::python
import os
import io
import re
import sys
import ast
import subprocess as sp
from collections import namedtuple
```

## Ex&shy;ter&shy;nal Pack&shy;age Im&shy;port&shy;s
Pyphen is a ly&shy;brary to hy&shy;phen&shy;ate word&shy;s.

```
:::python
import docopt
import pyphen
import pygments
import markdown
```

## Con&shy;stants

```
:::python
# background                white
# keywords                  red         #905
# constants                 black
# braces                    black
# variables                 black
# strings                   blue        #029
# escape sequences          purple
# function declarations     green
# parameters                orange      #B40
# builtins                  blue        #08B
# operators                 red         #B00
# numbers/bools/None        purple
# comments                  gray


DEBUG = False

Section = namedtuple('Section', [
    'index', 'type', 'meta', 'lines'
])


def py_comment(lines):
    for line in lines:
        if line.strip():
            yield "# " + line
        else:
            yield line


def js_comment(lines):
    for line in lines:
        if line.strip():
            yield "// " + line
        else:
            yield line


def indent(content):
    # TODO (mbarkhau 2016-08-29): detect line endings
    # TODO (mbarkhau 2016-08-29): detect tab indent
    line_ending = "\n"
    indent = "    "
    return line_ending.join((
        indent + line
        for line in content.split(line_ending)
    ))


def py_capture_stdout(text, capture):
    text = (
        "import os\n"
        "import io\n"
        "import sys\n"
        "\n"
        "if os.getenv('CODE_DOT_MD_CAPURE'):\n"
        "    _orig_stdout = sys.stdout\n"
        "    _capture_out = io.StringIO()\n"
        "    sys.stdout = _capture_out\n"
        "\n"
    ) + indent(text) + (
        "\n"
        "    sys.stdout = _orig_stdout\n"
        "    _CAPTURED_OUT = _capture_out.getvalue()\n"
        "    fh = io.open('C:\\\\Users\\\\Manuel\\\\lit_test.txt', mode='w')\n"
        "    fh.write(_CAPTURED_OUT)\n"
    )
    return text


PLUGINS = {
    'py': {
        'comment' : py_comment,
        'capture': py_capture_stdout,
    },
    'js': {
        'comment' : js_comment,
        'capture': (lambda text, capture: text),
    }
}

# TODO (mbarkhau 2016-08-21): Warn about line length in
#       code blocks, because they cause horizontal
#       scrolling.
# TODO (mbarkhau 2016-08-21): Parse lang from file
#       level metadata

HYPHEN_DICT = pyphen.Pyphen(lang='en_US')


def open(filepath, mode='r', encoding='utf-8'):
    return io.open(filepath, mode=mode, encoding=encoding)


META_PARAM_RE = re.compile(r"""
    (?P<key>[\w\-\.]+)
    \:
    (?P<val>[^\}\,]+)
    (?:\}|\,)
""", re.VERBOSE | re.MULTILINE)


def parse_section_meta(raw_meta):
    meta = {}
    for match in META_PARAM_RE.finditer(raw_meta):
        key, val = match.groups()
        if key in meta:
            if not isinstance(meta[key], list):
                meta[key] = [meta[key]]
            meta[key].append(val)
        else:
            meta[key] = val

    # TODO (mbarkhau 2016-08-23): validate meta
    if raw_meta.strip():
        print(meta)
    return meta


# TODO (mbarkhau 2016-08-17): cleanup global
_section_index = 0


def parse_section(section_type, raw_section_meta, section_lines):
    has_meta = bool(raw_section_meta.strip())
    has_content = bool(section_lines)
    if not (has_content or has_meta):
        return

    global _section_index
    _section_index += 1

    section_meta = parse_section_meta(raw_section_meta)
    return Section(
        _section_index,
        section_type,
        section_meta,
        section_lines
    )


def iter_sections(fh, filepath="<filepath>"):
    # A very simple state machine that switches between
    # four states.
    stype = 'text'     # ('text'|'code'|'data'|'meta')
    smeta = ""
    slines = []
    prev_empty = False

    for i, line in enumerate(fh):
        line_no = i + 1
        illegal_state_err_msg = (
            "Illegal state {} reached on line {} of {}."
            .format(stype, line_no, filepath)
        )
        if DEBUG:
            print(
                "----",
                line_no,
                stype,
                len(smeta),
                len(slines),
                repr(line)
            )

        if line.strip() == "":
            slines.append(line)
            prev_empty = True
            continue

        if line.startswith("{{"):
            if stype not in ('text', 'data'):
                raise RuntimeError(illegal_state_err_msg)

            # Beginning of new metadata implies that the
            # previous section has ended.
            yield parse_section(stype, smeta, slines)

            smeta = line
            slines = []
            if line.rstrip().endswith("}}"):
                # single line metadata
                stype = 'text'
            else:
                # begin of a metadata block
                stype = 'meta'
            continue

        if line.rstrip() == "}}":
            # end of metadata
            smeta += line
            # The next section may or may not be
            # 'text' but that is the default.
            stype = 'text'
            continue

        if stype == 'meta':
            smeta += line
            continue

        if line.rstrip() == "```":
            if stype in ('text', 'data'):
                # begin of a new code block
                if slines:
                    yield parse_section(stype, smeta, slines)
                    smeta = ""
                    slines = []
                stype = 'code'
            elif stype == 'code':
                # end of current code block
                yield parse_section(stype, smeta, slines)

                stype = 'text'
                smeta = ""
                slines = []
            else:
                raise RuntimeError(illegal_state_err_msg)
            prev_empty = False
            continue

        is_indented = (
            line.startswith("    ") or
            line.startswith("\t")
        )

        if stype == 'text' and prev_empty and is_indented:
            # end of text section, begin of data
            if slines:
                yield parse_section(stype, smeta, slines)
            stype = 'data'
            smeta = ""
            slines = [line]
            prev_empty = False
            continue

        if stype == 'data' and line.strip() and not is_indented:
            # end of data block
            yield parse_section(stype, smeta, slines)
            stype = 'text'
            smeta = ""
            slines = [line]
            prev_empty = False
            continue

        # continue existing section
        slines.append(line)

    yield parse_section(stype, smeta, slines)


def iter_lit_paths(paths):
    if not isinstance(paths, list):
        paths = [paths]
    for path in paths:
        if os.path.isfile(path):
            yield path
        elif os.path.isdir(path):
            tree = os.walk(path)
            for dirname, dirnames, filenames in tree:
                for filename in filenames:
                    if filename.endswith('.lit'):
                        yield os.path.join(dirname, filename)
        else:
            print("Invalid path: ", path)


def parse_lit_sections(in_path):
    with open(in_path) as fh:
        return list(iter_sections(fh))


POSITION_TYPES = ['head', 'body', 'foot']


def section_key(section):
    pos = section.meta.get('pos', "body").strip()
    if "-" not in pos:
        pos += "-" + str(section.index)
    pos_type, pos_num = pos.split("-")
    return (POSITION_TYPES.index(pos_type), float(pos_num))


def write_src(sections, out_path):
    sections = sorted(sections, key=section_key)
    extension = out_path.rsplit(".", 1)[-1]
    # TODO (mbarkhau 2016-08-25): allow override via file metadata
    plugin = PLUGINS[extension]
    with open(out_path, mode='w') as fh:
        for section in sections:
            if section.type in ('text', 'data'):
                text = "".join(plugin['comment'](section.lines))
                fh.write(text)
            elif section.type == 'code':
                text = "".join(section.lines)
                capture = section.meta.get('capture')
                if capture:
                    text = plugin['capture'](text, capture)
                fh.write(text)


def hyphenate_words(content):
    parts = content.split("`")
    parts_iter = iter(parts)
    part = next(parts_iter, "")
    while part:
        for word in part.split(" "):
            yield HYPHEN_DICT.inserted(word, "&shy;")

        literal = next(parts_iter, "")
        if literal:
            yield "`" + literal + "`"

        part = next(parts_iter, "")


def write_md(sections, out_path):
    # TODO (mbarkhau 2016-08-15): cache hyphenation
    # TODO (mbarkhau 2016-08-14): parse and preserve
    #       line endings
    # TODO (mbarkhau 2016-08-21): set flavour based on metadata
    # TODO (mbarkhau 2016-08-14): syntax highlite for code
    with open(out_path, mode='w') as fh:
        for section in sections:
            if section.type == 'text':
                content = "".join(section.lines)
                fh.write(" ".join(hyphenate_words(content)))
            elif section.type == 'data':
                fh.write("".join(section.lines))
            elif section.type == 'code':
                fh.write(
                    "```\n:::python\n" +
                    "".join(section.lines) +
                    "```\n"
                )

def mtime(path):
    if not os.path.exists(path):
        return 0
    return os.stat(path).st_mtime
```


```
:::python
def main(args):
    # TODO (mbarkhau 2016-08-19): parse arguments
    paths = args or [
        "C:\\Users\\Manuel\\Dropbox\\software_projects\\umemo"
    ]
    verbose = True
    output_format = 'html'

    for lit_in_path in iter_lit_paths(paths):
        dir_path = os.path.dirname(lit_in_path)
        src_out_path = lit_in_path[:-4]
        md_out_path = lit_in_path[:-4] + ".md"
        html_out_path = lit_in_path[:-4] + "." + output_format
        tmpl_path = os.path.join(dir_path, "template.html")

        lit_mtime = mtime(lit_in_path)
        src_mtime = mtime(src_out_path)
        md_mtime = mtime(md_out_path)
        html_mtime = mtime(html_out_path)
        tmpl_mtime = mtime(tmpl_path)

        lit_changed = (
            lit_mtime > src_mtime or
            lit_mtime > md_mtime
        )
        tmpl_changed = tmpl_mtime > html_mtime

        if not (lit_changed or tmpl_changed):
            if verbose:
                print("unchanged ", lit_in_path)
            continue

        if verbose:
            print("updated   ", lit_in_path)

        sections = parse_lit_sections(lit_in_path)

        # To simplify things in the iterator we allow empty sections
        # to be emitted for now, which we filter out here.
        sections = [s for s in sections if s]

        if lit_changed:
            if verbose:
                print("refreshing", src_out_path)
            write_src(sections, src_out_path)

            env = os.environ.copy()
            env['CODE_DOT_MD_CAPURE'] = "1"
            sp.Popen(['python', '-c', 'import lit'], env=env)
        # TODO (mbarkhau 2016-08-14): run and capture output

        if lit_changed:
            if verbose:
                print("refreshing", md_out_path)
            write_md(sections, md_out_path)

        if lit_changed or tmpl_changed:
            if verbose:
                print("refreshing", html_out_path)

            md_data = open(md_out_path).read()
            html_data = markdown.markdown(md_data, extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.footnotes',
            ])

            with open(tmpl_path) as fh:
                tmpl_data = fh.read()
            # TODO (mbarkhau 2016-08-22): parse template
            #           as jinja2.
            # TODO (mbarkhau 2016-08-22): generate
            #           - authors
            #           - language
            #           - title
            #           - date
            with open(html_out_path, mode='w') as fh:
                fh.write(tmpl_data.replace("$body$", html_data))
            # args = [PANDOC_CMD]
            # sp.call([
            #     PANDOC_CMD,
            #     '--from', 'markdown',
            #     '--to', output_format,
            #     '--standalone',
            #     '--output', html_out_path,
            #     '--template', tmpl_path,
            #     md_out_path
            # ])
```

```
:::python
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
```
