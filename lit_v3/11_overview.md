## Introduction to LitProg

LitProg is a [Literate Programming (LP)][href_wiki_litprog] tool which 

 1. consumes [Markdown][href_wiki_markdown] files,
 2. produces code files from fenced blocks,
 3. produces HTML and PDF documentation.


```bob
      Markdown
 +-----------------+
++ lit/11_intro.md |\       .------------.
|| lit/12_test.md  +-+      |            |
|| lit/13_impl.md    o----->+   LitProg  |
|+------------------++      |            |
+-------------------+       '---+----+---'
                                |    |
         .----------------------'    |
         |                           |
         V                           V
 +------------------+    +-------------------+
++ src/app.py       |\  ++ doc/program.pdf   |\
|| src/ui.js        +-+ || doc/11_intro.html +-+
|| src/data.json      | || doc/12_test.html    |
|+-------------------++ |+--------------------++
+--------------------+  +---------------------+
        Code                   HTML/PDF
```

ABCD EFG HIJKL MNOPQ RSTUV WXYZ abcd efg hijkl mnopq rstuv wxyz ABCD EFG HIJKL MNOPQ RSTUV WXYZ abcd efg hijkl mnopq rstuv wxyz

LitProg aims to strike a great balance between
 
  - Ease of writing and editing
  - Greate layout even if little to no concern is given to it
  - Highly integrated generation of code, diagrams and charts

In short, LitProg aims to be your first choice for all technical writing, to let you focus on your ideas and not on document layout and to get beautiful documents fit for publication.

ABCD EFG HIJKL MNOPQ RSTUV WXYZ abcd efg hijkl mnopq rstuv wxyz ABCD EFG HIJKL MNOPQ RSTUV WXYZ abcd efg hijkl mnopq rstuv wxyz

I hope the day is not too far, where [each][] [and][] [literate][] [program][] must not either be itself or start with with an exposition on literate programming. I hope that this small program can serve that purpose for other programs, so that they can just get on with explaining themselves.

The lack of broad adoption casts some doubt on the [claims of the benefits of Literate Programming][href_knuthweb]. The closest thing to adoption of LP has been with some writers using [Jupyter][href_jupyter] style notebooks in the area of data science. Such notebooks can communicate to readers how data was processed and what calculations were used. The fact that these notebooks are executable is a form of automated review, which gives some credence to the correctness of the results. Literate Programming as a paradigm is somewhat different in that the communication between programmers is supposed. proported to result in higher quality software, at a higher initial pricehave a lower long term cost of development. Understanding such programs leads to greater trust in the results, but this is not the same as understanding the program The a to get a better idea of how a data analyst arrived at their results, but this is not the same as a programming are better suited to data analysis and reporting however, rather than creating libraries and applications. I believe lack of adoption of LP is partially the result of inadequate tooling and I hope LitProg will enable you to write good software in an LP style.

I've written more about the motivation for this project in the [next chapter][iref_touchy_feely], but in this chapter I will mostly focus on what LitProg is and how to use it.


### Getting Started

> Writing is nature's way of letting you know how sloppy your thinking is.
> 
> – Dick Guindon

*Literate Programming* is a programming paradigm. *LitProg* is a compiler/build tool. Even if you are not on board with LP, you may nonetheless find LitProg to be useful, for example if you want to write a technical article or tutorial. This book is a documentation artefact of the literate program for the `litprog` cli command, which has of course been compiled using itself. To get started you can download one of the software artifacts of LitProg and run `litprog build` with an example file.

```bash
$ pip install litprog
...
$ mkdir litprog_test;
$ cd litprog_test;
$ curl https://.../raw/.../example.md -O 11_intro.md
$ litprog build 11_intro.md
...
$ ls -R
examples/fib.py
examples/primes.py
```

The example file is written in Markdown, which is familiar to many programmers and widly supported by software related to programming. LitProg extends Markdown in a way that does not require special support by such software. In other words, your current editor should be fine.

When programming you will usually run `litprog build lit/` or `litprog watch lit/`. This will generate source code files and execute any subcommands that are part of your program. Such commands typically relate to testing and validating your program, or they might illustrate its behaviour.

Generating the full documentation can take some time, so it introduces a friction that you will want to avoid during regular programming. It can be a part of a build process or [CI][href_wiki_ci] pipeline and you will only occasionally you may want to generate documentation during development, but usually you shouldn't have to. You can pass the `--html <directory>` and `--pdf <directory>` parameters to generate the static HTML and PDF files.


```bash
$ litprog build 11_intro.md --html doc/ --pdf doc/
$ ls -R
examples/fib.py
doc/litprog.pdf
doc/index.html
doc/styles.css
doc/11_intro.html
```

### LitProg by Example

LitProg works by parsing your markdown for code blocks and parsing these code blocks for directives. These make it possible to compose programs in a flexible way, without being distracted by typesetting and page layout. LitProg allows programmers to focus on their code, their ideas and a coherent narrative to explain their programs.

I will use the familiar [Fibbonacci function][href_wiki_fib] and Python for this example. I hope you will learn nothing about the particular example and can instead focus on the mechanics of LitProg itself. I will later give a more extensive example, to give a better impression of Literate Programming, without being distracted by the mechanics of LitProg.

To produce an inline equation, write LaTeX as inline code, surrounded by $ characters: ``$`a^2+b^2=c^2`$`` -> $`a^2+b^2=c^2`$ (btw. there is a nice editor on [katex.org][href_katex] and [documentation][href_katex_docs] to help create such formulas). To produce a centered block, write LaTeX in a `math` block:

    ```math
    \begin{array}{l}
    F_0 = 0 \\
    F_1 = 1 \\
    F_n = F_{n-1} + F_{n-2}
    \end{array}    
    ```

Produces:

```math
\begin{array}{l}
F_0 = 0 \\
F_1 = 1 \\
F_n = F_{n-1} + F_{n-2}
\end{array}    
```

A Python implementation of the Fibbonacci function might look like this:

```python
def fib(n: int) -> int:
    if n < 2:
        return n 
    else:
        return fib(n - 1) + fib(n - 2)
```

In case you weren't aware, this naive recursive implementation is well known to have a complexity of $`O(2^n)`$ (in other words: it's pretty bad).


### The `lp_add` Directive

The previous[^fnote_avoid_above] code block is not treated specially by LitProg. It is not written to any file, not converted by any compiler, nor executed by any interpreter. It will end up in the documentation, just as you would expect from any Markdown renderer, but that's about it.

To actually use this code block, it must be referenced in a later code block by the use of an `lp_add` directive. LitProg directives are written using the comment syntax of the programming language declared for the block.

    ```python
    # lp_add: def fib
    assert fib(8) == 21
    ```

In this case, the syntax of the block is `python`, so all lines which start with a `#` character are parsed in search of litprog directives. In this case there is only one such line: `# lp_add: def fib`. The text after[^fnote_whitespace_in_directives] the `:` (`def fib`) is a query string that must be a substring of some other block in the literate program. The first block[^fnote_block_queries] which contains that substring is substituted in place of the directive. In other words, once the preceding block is expanded, it will be equivalent to the following:

    ```python
    def fib(n: int) -> int:
        if n < 2:
            return n 
        else:
            return fib(n - 1) + fib(n - 2)
    assert fib(8) == 21
    ```

!!! aside "On Parsing Comments"

    It is often seen critically, to embed programming constructs inside comments and rightfully so. Considering the context of LitProg however, where programmers have Markdown available to them for documentation and don't need to resort as much to comments, I think this repurposing of the comment syntax is a reasonable compromise: 

    1. It allows existing code/syntax highlight and formatting tools to work, without having to implement anything specific to LitProg.
    2. Only the distinctive `lp_<directive>` syntax is parsed and each directive can only span a single line. All other comments are ignored, so you can continue to use comments for other uses you see as appropriate.

!!! aside "Lanugage Support"

    LitProg supports the comment syntax of many programming languages and can be easilly extended to support more. For Python, Bash, PHP the comment syntax uses the `#` character, for Java, JavaScript, C, it uses the `//` string etc.

    Some blocks may not even have a meaningful language, in which case you can pick any language with a comment syntax you prefer. In this program I will use `shell` if there is not a more appropriate choice.

    Languages that are unknown to LitProg can nonetheless be used if it has the same comment syntax as another language. Since LitProg only parses the comments of a code block and doesn't do anything specific to a particular language, you can label the block with the other language (as a stop-gap measure until support is added). If you wanted to use the [Zig Language][href_ziglang] for example, you could label the block with `rust` instead, which also uses `//` for comments and for which the syntax highighting works tolerably well (at least in my editor).

        ```rust
        // This is actually zig code, but "```zig" doesn't
        // work yet, so we use "```rust" instead.
        const std = @import("std");

        pub fn main() void {
            std.debug.warn("Hello, world!\n");
        }
        ```


### Running Commands

While the `fib` function is quite simple to understand, you as a reader are either left to validate if it is correct for yourself, or to trust the claims of the author that the implementation is correct. The previous assertion `assert fib(8) == 21` is not actually executed anywhere, so who is to say if it is correct?

Instead of manual validation or trust, we can instead provide some code which will actually execute the `fib` function, and which would cause an error if any of our assertions were not to hold.

```python
fibs = [fib(n) for n in range(9)]
assert fibs == [0, 1, 1, 2, 3, 5, 8, 13, 21]
assert fib(12) == 144
assert fib(20) == fib(19) + fib(18)
```

I will use these assertions again later, so I've declared them in a separate block first, before now proceeding to run them.

```python
# lp_run: python3
# lp_add: def fib
# lp_add: assert fibs == [0, 1, 1, 2
```

The `lp_run` directive invokes a command (in this case `python3`), which receives the expanded block (after substitution of all `lp_add` directives) via its [stdin][href_wiki_std_streams].

If the [exit status][href_wiki_exit_status] of the `python3` process is anything other than the expected value of `0`, then the LitProg build will fail. This is an important point: The fact that you can read this literate program at all (assuming you have HTML or PDF form), is proof that the command exited successfully.

!!! aside "Options of `lp_run`"

    - `lp_expect`: The expected exit status of the process. The default value is `0`. 
    - `lp_timeout`: How many seconds a process may run before being terminated. The default value is `1.0`.
    - `lp_hide`: If the block should be hidden from generated documentation. Using this goes against the ethos of Literate Programming, but if your readers don't care about the assurance that they have access to the full program (for example if you're using LitProg to write a blog article) then this may be appropriate. The default value is `false`


### Capturing Output

While assertions and an exit status are nice, it will often be better to show some output generated by a program. The previous process didn't write anything to `stdout` or `stderr`, so let's run another which does.

```python
# lp_run: python3
# lp_add: def fib
for i in range(9):
    print(fib(i), end=" ")
```

The output of a process is always captured but that output is only made visible by using an `lp_out` directive.

```shell
# lp_out
0 1 1 2 3 5 8 13 21
# exit:   0
```

The `lp_out` directive marks its block as a container for the output of the process that was previously run. When the LitProg build is completed, the contents of the `lp_out` block is updated in-place with the captured output. If there is no `lp_out` block after an `lp_run` block, then the captured output is discarded.

!!! note "Options of `lp_out`"

     - `lp_proc_info`: A format string used to customize the process info that is appended to output blocks. It can be set to "none" to supress the process info. The available info is `exit`, `time` and `time_ms`. The default is "# exit: {exit:>3}".
     - `lp_max_lines`: The maximum number of lines to keep of the captured output. default `10`    
     - `lp_max_bytes`: The maximum number of bytes to keep of the captured output. default `1000`
     - `lp_out_prefix`: A string which is used to prefix every line of the stdout. default `""`
     - `lp_err_prefix`: A string which is used to prefix every line of the stderr. default `"! "`


The captured output gives the reader some assurance that the document they are reading is not just some manually composed fabrication which was written as an afterthought and is detatched from the actual program. Even with the best of intentions, humans often make mistakes, so program logic that has not been executed by a machine will inspire little confidence. Hence the famous quote by Knuth: "Beware of bugs in the above code; I have only proved it correct, not tried it".

The exit status and the captured output are demonstrations that at least on one machine and at some point in the past, the program was in some sense "correct", or at least that the generated documentation is consistent with the program that was used to generate it[^fnote_max_hedging]. This approach to including program output in generated documentation gives readers a chance to see if the author is trying to hide how the sausage is made. While it may be appropriate to relegate certain logic to an appendix, for example to avoid distraction from a desired narrative, the entire program can in principle be made accessible to inquisitive readers. They may still have to trust that the author was acting in good faith, but the issue of incompetence and outdated documentation is greatly mitigated.

By this point I hope you can see, that LitProg allows you to write 1. source code, 2. documentation and 3. automated testing, all combined in a way that makes the most sense to understand your program.


### In-Place Updates of Fenced Blocks

Validating that a program is correct, is not only important to communicate to readers, it is also part and parcel of the programming workflow. Most programmers are the first that want to know if their program is working. Generating HTML/PDF documentation takes a bit of time and switching back and forth between a browser window and a code editor would introduce a lot of friction into the programming workflow. To avoid this friction, LitProg instead does in-place updates to the original markdown files. The output that is captured during a build is inserted into the markdown text. This works well for editors that detect and automatically reload files that have changed. When using `litprog watch` programmers can simply hit save and see how the output of their program appears directly in their text editor.

This approach also has the advantage that output of the most recent execution and viewing the Markdown files on github/gitlab/bitbucket can give a good idea of what the generated documentation will look like. Reviewing the diff of a commit can also demonstrate the behavioural change that a change in the source code caused.

!!! note "The Pitfalls of Rewriting Input Files"

    Modifying the markdown files as they are being edited by a programmer can cause some issues. These issues are similar to those encountered when using code formatters that do in-place updates of source code files: What happens if the file is edited again before the in-place update is completed?

    LitProg will only update your markdown files if they have not been changed since the start of the build. This still leaves some scenarios where you may see surprising behaviour.

    1. If your editor does not automatically detect the file modification done by the build, you may continue editing and not see the updated output until you somehow manually cause your editor to reload the file.

    2. LitProg will only overwrite changes made *on the file system*; any changes you have made *in the buffer of your editor* which have not been saved yet, will overwrite the build output if you save them. If your editor detects modifications made by the build, it may prompt you with something like "File has changed on disk, do you want to reload the file? [Reload] [Cancel]". Usually you will want to hit "Cancel" in this case, unless you want to discard your recent changes.

!!! note "Deterministic Output"

    You can minimize spurrious updates of your Markdown files by making sure that the output of your program is deterministic. For example the captured output of a python code block that uses `time.time()` or `os.urandom(9)` will usually be different from one build to the next.

!!! note "The Dangers of Unbounded Output"

    When running a session, the default behaviour of LitProg is to only overwrite an output block using the last 1000 bytes or 10 lines of valid utf-8 output (whichever is less). This prevents your markdown files from being spammed with program output, for example if you introduce a bug that causes output to be much larger than expected.

!!! note "Escaping Output"

    A corner case of how LitProg processes captured output is when detects three &#96;&#96;&#96; (backtick) or &#126;&#126;&#126; (tilde) characters. These are treated specially if they would cause the code block to be closed prematurly. 

    1. If closing the block can be avoided by changing the style of the fence in the original file, LitProg will automatically do so.
    2. If both substrings appear in the output, LitProg will raise an error.

    This behaviour means that readers can be sure that the output they are reading is identical to what was originally captured.


## Creating Files

It might be enough for academics if LitProg were only to produce documentation, but most other people wnat to have artifacts that are actually useful. In the most simple case you can use the `lp_file: <filename>` directive to generate files. 

```python
# lp_file: examples/fib.py
# lp_add: def fib
for i in range(10):
    print(fib(i), end=" ")
```

!!! note "Cross Platform Filenames"
    
    Paths in LitProg always use the `/` (forward slash) character, even if you are running on a Windows machine. Avoid using absolute paths, so that your program can be built on machines with different directory layouts.


The `lp_out` directive can also have a command parameter: `lp_out: <command>`. Unlike `lp_run`, the process will not receive anything via stdin. This is not too limiting however, as all commands are only run after all `lp_file` directives have been completed. In other words, we can use `lp_out` to run the example script created by the previous block.

```bash
# lp_out: python3 examples/fib.py
0 1 1 2 3 5 8 13 21 34
# exit:   0
```


### Porcelain vs. Plumbing

```python
from typing import Sequence 

def pretty_print_fibs(ns: Sequence[int]) -> None:
    fibs = [fib(n) for n in ns]

    pad_n     = len(str(max(ns)))
    pad_fib_n = len(str(max(fibs)))

    for i, (n, fib_n) in enumerate(zip(ns, fibs)):
        in_str = f"fib({n:>{pad_n}})"
        res_str = f"{fib_n:>{pad_fib_n}}"
        print(f"{in_str} => {res_str}", end ="  ")
        if (i + 1) % 3 == 0: 
            print()

```

This function could be clearer, but sometimes it's ok for code to be a bit gnarly. Readers may not be interested in how every part of a program works, especially when the code is not part of the core logic of the program. A deep understanding of `pretty_print_fibs` will contribute little to the understanding of Fibonacci numbers or of LitProg. The very first line of the function is very straightforward and is also the most important line, everything else deals with padding, line breaks and writing output etc.

```python
# lp_run: python3
# lp_add: def fib
# lp_add: def pretty_print_fibs
pretty_print_fibs(range(18))
```

A review of the output will provide all the understanding we need for `pretty_print_fibs`.

```shell
# lp_out
fib( 0) =>    0  fib( 1) =>    1  fib( 2) =>    1
fib( 3) =>    2  fib( 4) =>    3  fib( 5) =>    5
fib( 6) =>    8  fib( 7) =>   13  fib( 8) =>   21
fib( 9) =>   34  fib(10) =>   55  fib(11) =>   89
fib(12) =>  144  fib(13) =>  233  fib(14) =>  377
fib(15) =>  610  fib(16) =>  987  fib(17) => 1597
# exit:   0
```


### Optimizing

Now that we have some code that is good, and which we can also see is correct, it's time we turned to optimization.

```python
from typing import Dict

_fib_cache: Dict[int, int] = {}

def fast_fib(n: int) -> int:
    if n <= 1:
        return n

    if n in _fib_cache:
        return _fib_cache[n]

    _fib_cache[n - 2] = fast_fib(n - 2)
    _fib_cache[n - 1] = fast_fib(n - 1)
    assert n - 1 in _fib_cache, n
    return _fib_cache[n - 1] + _fib_cache[n - 2]
```

We can run the same validation code as before, the only differenc being that we replace `fib` with `fast_fib`

```python
# lp_run: python3
# lp_add: def fast_fib
fib = fast_fib
# lp_add: assert fibs == 
```

```python
# lp_out
# exit:   0
```

This shows that that `fast_fib` is just as correct as the original `fib` function (the assertions ran through without any errors), but how do we know that it is faster?


### Macro Directives

This feature was dropped. If anything is needed it will have to be much better than textual replacements. The final nail in the coffin was trying to have namespaces that work across languages.

The simplest macro supported by LitProg is the `lp_const` directive. These can be defined inline or for example inside of a markdown listing.

 - The largest Fibonacci number to calculate: `lp_const: MAX_FIB=20` 
 - How many numbers to print per line `lp_const: FIBS_PER_LINE=5`

```python
# lp_run: python3
# lp_add: def fib
MAX_FIB = 20
FIBS_PER_LINE = 5

print(f"fib(2..{MAX_FIB}):", end="")
for n in range(MAX_FIB):
    if n % FIBS_PER_LINE == 0:
        print()
        print(f"  {n:>3}", end=": ")
    print(f"{fib(n):>5}", end=" ")
```

```shell
# lp_out
fib(2..20):
    0:     0     1     1     2     3
    5:     5     8    13    21    34
   10:    55    89   144   233   377
   15:   610   987  1597  2584  4181
# exit:   0
```

The choice of names for such a constant may be influenced by the language being used. If you want make it possible for code formatters to reformat a code block, then the code block must be syntactically valid even if it includes non-expanded macros. 

The preceding example prin
LitProg has support for macros using the `lp_def` directive. These are non-hygenic, can be parameterized and are recursively expanded.


!!! warning "Experimental"
    This is the feature is neither fully specified nor implemented and is subject to change.


```python
import time
import contextlib

@contextlib.contextmanager
def timeit(marker=""):
    t_before = time.time()
    yield
    t_after = time.time()
    duration_ms = 1000 * (t_after - t_before)
    print(f"{marker} {duration_ms:9.3f} ms")
```

```python
# lp_run: python3
# lp_add: def timeit
# lp_add: def fib
# lp_add: def fast_fib
with timeit("slow"): fib(13)
with timeit("slow"): fib(15)
with timeit("slow"): fib(17)
with timeit("fast"): fast_fib(13)
with timeit("fast"): fast_fib(15)
with timeit("fast"): fast_fib(17)
```

```shell
# lp_out
slow     0.128 ms
slow     0.329 ms
slow     0.472 ms
fast     0.007 ms
fast     0.002 ms
fast     0.002 ms
# exit:   0
```

!!! aside "`import timeit` is a thing"

    There is a perfectly good builtin module named `timeit`, indeed it is much better than this macro, especially for very fast expressions. The purpose here is to demonstrate the macro functionality of LitProg. 


### Writing Code to Disk

Up to here our code has been floating around in memory, but eventually we want to produce something that is useful. A program that our users might like to run. In other words, we want to write our code to disk so that it can either be used directly, or further processed by a compiler.

Next is some boring python scaffolding to wrap the functions written so far.

```python
ParamsAndFlags = Tuple[List[str], Set[str]]

def parse_args(args: List[str]) -> ParamsAndFlags:
    flags = {arg for arg in args if arg.startswith("-")}
    params = [arg for arg in args if arg not in flags]
    return params, flags
```

```python
#!/usr/bin/env python
__doc__ = f"""Usage: python {__file__} [--help] [--pretty] <n>..."""

import sys
from typing import List, Set, Tuple

# lp_add: def fast_fib
fib = fast_fib
# lp_add: def pretty_print_fibs
# lp_add: def parse_args

def main(args: List[str] = sys.argv[1:]) -> int:
    params, flags = parse_args(args)
    # lp_add: if not args or "--help"
    # lp_add: if any(invalid_params):

    ns = [int(n) for n in params]
    if "-p" in flags or "--pretty" in flags:
        pretty_print_fibs(ns)
    else:
        for n in ns:
            print(fib(n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

Don't worry if you're not familiar with python or top level scripts. The noteworthy thing about preceeding block are the two `lp_add` directives inside the `main` function. 

The first is to print a help message.

```python
if not args or "--help" in flags or "-h" in flags:
    print(__doc__)
    return 0
```

The second step in `main` is to validate the arguments to the script. They must all be numerical/decimal digits.

```python
invalid_params = [n for n in params if not n.isdigit()]
if any(invalid_params):
    print("Invalid parameters: ", invalid_params)
    return 1
```

Apart from their function it is important to see how the `lp_add` directive treats indentation. When a block is added, the indent level of the comment which holds the directive is prepended to every line of the added block. In other words the indent level of the added block is the same as the indent level of the directive that adds it.

Finally after we have prepared all our code, we can write it to disk...

```python
# lp_file: examples/fib_cli.py
# lp_add: def main
```

...and give it a spin.

```bash
# lp_out: python3 --version
Python 3.7.3
# exit:   0
```

```bash
# lp_out: python3 examples/fib_cli.py --help
Usage: python examples/fib_cli.py [--help] [--pretty] <n>...
# exit:   0
```

```bash
# lp_out: python3 examples/fib_cli.py 22
17711
# exit:   0
```

```bash
# lp_out: python3 examples/fib_cli.py --pretty 3 7 8 9 19 20
fib( 3) =>    2  fib( 7) =>   13  fib( 8) =>   21
fib( 9) =>   34  fib(19) => 4181  fib(20) => 6765
# exit:   0
```

```bash
# lp_out: python3 examples/fib_cli.py invalid argument
Invalid parameters:  ['invalid', 'argument']
# exit:   1
```


!!! aside

    Although the final invocation of `fib_example.py` has a non-zero exit status, the session nontheless has an exit status of `0`. This is because python3 is invoced by a bash process, which does not propagate the exit status of a command by default. If we wanted to propagate the exit status we could use [`set -e` / `set -o errexit`][href_explainsh_errexit].


### Make Directive

So far every process was independent of every other. In principle the process could have been executed in any order, or indeed concurrently to each other. Their dependencies on code blocks are explicitly declared by the `lp_add` directives inside of each `lp_run` block. 

    ```bash
    # lp_make: examples/fib_cli_compat.py
    # lp_deps: examples/fib_cli.py
    python -m lib3to6 examples/fib_cli.py \
        > examples/fib_cli_compat.py
    sjfmt examples/fib_cli_compat.py
    chmod +x examples/fib_cli_compat.py
    ```

I'm implementing this using lp_run for now.

```bash
# lp_file: examples/build_cli_compat.sh
python3 -m lib3to6 examples/fib_cli.py \
    > examples/fib_cli_compat.py
chmod +x examples/fib_cli_compat.py
```

```bash
# lp_run: bash examples/build_cli_compat.sh
```


!!! note "Why, oh why, does every tool need a new build system?!"

    In my defense, I don't feel that I'm reinventing the wheel, rather I'm reimplementing an existing and vernerable wheel called `make`. If you are familiar with make, you should have no problem using the build system of LitProg.

    Many large programs use a build system to produce the final artifacts, such as binaries or packages. Documenting how to produce these artifacts should at least be possible, otherwise there is a thick curtain behind which the reader can . 

!!! note "redo: mtime dependencies done right"
    
    @apenwarr has written enough about the [pitfalls of detecting changes using mtime comparison][href_apenwarr_mtime]. LitProg takes the reccomended apporoach of keeping a database/index of files and falling back on content hashing only as an optimization when file system metadata cannot be relied upon to determine if a dependency has changed.


```bash
# lp_out: python2 --version
! Python 2.7.17rc1
# exit:   0
```

```bash
# lp_out: python2 examples/fib_cli_compat.py 22
! Traceback (most recent call last):
!   File "examples/fib_cli_compat.py", line 16, in <module>
!     from typing import List, Set, Tuple
! ImportError: No module named typing
# exit:   1
```

```bash
# lp_out: python3 --version
Python 3.7.3
# exit:   0
```

```bash
# lp_out: python3 examples/fib_cli_compat.py 22
17711
# exit:   0
```

```bash
# lp_out: examples/fib_cli_compat.py --pretty 2 5 8 12 19 20
fib( 2) =>    1  fib( 5) =>    5  fib( 8) =>   21
fib(12) =>  144  fib(19) => 4181  fib(20) => 6765
# exit:   0
```

These examples are intended as a quick overview, but there is much more to be said about the how each of these primitives can be used and misused.

TODO: Further reading.


[^fnote_avoid_above]: When referencing parts of a document in your text, avoid phrases that are particular a specific format. Phrases like "the above image" or the below "code block" may be confusing if the reader is viewing a printed version of your program. Instead prefer wording which uses "previous"/"preceeding"/"earlier", "next"/"following"/"later".

[^fnote_avoid_numbers]: Chapter and section numbers can change when the structure of a project changes. Chapters can be reordered, new sections can be inserted, so any phrases such as "see chapter 3 section 2 for further details" will become invalid, or worse, point to something other than originally intended. TODO: stable links using names.

[^fnote_whitespace_in_directives]: Leading and trailing whitespace is stripped from directives. If you don't want this to happen, the value of a directive can be surrounded with `'` quotes or `"` double quotes.

[^fnote_block_queries]: For now, blocks can only reference other blocks in the same file and the first block to match is what will be used.

[^fnote_max_hedging]: Sorry about all the hedging. Any "proof" of correctness is only as good as the assertions made by the programmer. Hopefully the broader accessibility of LitProg programs means that programmers will feel the watchful eyes of readers and put some effort into making their programs demonstrably correct.


[href_jupyter]: https://jupyter.org/

[href_svgbob]: https://github.com/ivanceras/svgbob

[href_blockdiag]: http://blockdiag.com/en/blockdiag/index.html

[href_katex]: https://katex.org/

[href_wiki_ci]: https://en.wikipedia.org/wiki/Continuous_integration

[href_katex_docs]: https://katex.org/docs/supported.html

[href_wiki_fib]: https://en.wikipedia.org/wiki/Fibonacci_number

[href_knuthweb]: http://www.literateprogramming.com/knuthweb.pdf

[href_wiki_markdown]: https://en.wikipedia.org/wiki/Markdown

[href_wiki_std_streams]: https://en.wikipedia.org/wiki/Standard_streams

[href_wiki_exit_status]: https://en.wikipedia.org/wiki/Exit_status

[href_wiki_techdebt]: https://en.wikipedia.org/wiki/Technical_debt

[href_wiki_litprog]: https://en.wikipedia.org/wiki/Literate_programming

[href_explainsh_errexit]: https://explainshell.com/explain?cmd=set+-e

[href_apenwarr_mtime]: https://apenwarr.ca/log/20181113

[href_ziglang]: https://ziglang.org
