## Introduction to LitProg

LitProg is a [Markdown][href_wiki_markdown] processor for development of [Literate Programs (LP)][href_wiki_litprog].


```bob
      Markdown
 +-----------------+
++ lit/11_intro.md |\       .------------.
|| lit/12_test.md  +-+  1   |            |
|| lit/13_impl.md    |----->+   LitProg  |
|+------------------++      |            |
+-------------------+       '---+----+---'
                        3       |    |2
         .----------------------'    |
         V                           V
 +-------------------+    +------------------+
++ doc/program.pdf   |\  ++ src/app.py       |\
|| doc/11_intro.html +-+ || src/ui.js        +-+
|| doc/12_test.html    | || src/data.json      |
|+--------------------++ |+-------------------++
+---------------------+  +--------------------+
       HTML/PDF                  Code
```

You can use LitProg with practically any programming language, such as Python, JavaScript, Java, Ruby, Rust etc. LitProg will:

 1. read markdown files as input,
 2. write source code files as output,
 3. write HTML and PDF files as documentation.

While this *is* in essence what LitProg does, it doesn't show the key reason to use LitProg rather than other literate programming tools. LitProg is inspired by the interactive nature of Jupyter notebooks: You can mix documentation, code and critically also *execution*. This makes it possible to *demonstrate* to your readers, that your literate program works as advertised, by executing subprocesses and capturing their output. So a more complete picture of how LitProg is this:

```bob
 +----------+                        +----------+
++          |\     .-----------.    ++          |\
|| Markdown +-+ 1  |           | 2  ||   Code   +-+
||            |--->|  LitProg  +--->||            |
|+-----------++    |           |    |+-----------++
+------------+     '-+---+---+-'    +------------+
         ^           !   |  ^!             !
         !     4     !   |  !!             !
         '~~~~~~~~~~~'   |  !!             V
 +----------+            |  !!  3   .------------.
++          |\           |  !'~~~~~>|            +.
|| HTML/PDF +-+     5    |  '~~~~~~~+ Subprocs   ||
||            |<---------'          |            ||
|+-----------++                     '+-----------'|
+------------+                       '------------'
```

 1. read markdown files as input,
 2. write source code files as output,
 3. exectue code blocks and capture their output
    (code files from step 2 to are accessible).
 4. (optionally) rewrite input files with captured output from step 3
 5. write HTML and PDF artifacts as documentation.


### Programmer Flow

A critical goal of LitProg is to maintain programmer flow. You should be able to stay in your code editor most of the time. You should be able to focus on your ideas, your code and your writing, rather than on document layout and typesetting.

With LitProg, you can spend most of your time on a narrative and structure that will help your readers understand your program, and less time on formatting and styling of documentation. The goal is that you can treat the documentation artifacts as an afterthought, but since the correspondance between the markdown you write and the generated documentation is so close, you will never feel the desire to look at it.


### Pragmatism vs Dogmatism

Now I know what you're thinking: "I *already* don't spend any time on document layout, formatting, styling and whatever else kinda useless garbage nobody is going to read anyway. I just don't write any documentation, agile freedom baby whooooh 🤘". Fair enough, and let me also say, if you don't write your program as a Literate Program, that doesn't make you a bad person. If your program is a one-off script, almost certainly LitProg isn't the right choice. If your program is trivial and nobody other than you will ever work on it, then any effort you make to document its structure will be wasted. Not all software needs to satisfy lofty goals of being understandable and correct.

> Writing is nature's way of letting you know how sloppy your thinking is.
>
> – Dick Guindon

If on the other hand, the lifetime of the software you're writing is measured in years, if you don't even know all the people who may carry forward the torch you are lighting, if you can't get away with code that is so obtuse that others might get the idea that it's primary function is to provide job security, then LitProg is perhaps worth your consideration.

> Linus's Law: Given enough eyeballs, all bugs are shallow.
>
> – Linus Torvalds

Linus's law is true as far as it goes, but who is to say that you will ever get those eyeballs? Linux may be Free and Open Source and clones of the repository may exist on tens of thousands of computers, but how many people even make an attempt to understand any given part of its code? Getting eyeballs is not just a matter of making code available, it is also a matter of making it accessible.

Incidentally, Linus recently also said the following:

> what I hope people are doing is trying to make, not just good code, but
> these days we've been very good about having explanations for the code.
> So commit messages to me are almost as important as the code change
> itself.

This obviously depends on your workflow, but I basically don't read commit
messages and consider any time spent on them wasted. If they are read at
all, it is once as part of a review process and never again. If these
messages truely are valuable, then I would argue that it is better to keep
this kind of explanatory prose together with the code itself, rather than
hidden away in a database that can only be found by browsing the commit
history.

Arguably, your program might be better, more correct etc. if you write it
in an LP style, but  With LitProg you can take a gradual approach, when and if you
can see that it makes sense to improve the quality of some of your
software.


but if you feel like there are people
who may come after you that need to understand what you have written, then
maybe you should consider how easy it will be for them to figure out how
it works and what your original intent was.

Let me also say, if you've only ever hacked away on some software,

The main innovation of Literate Programming to change your focus as a
programmer toward the narrative that your readers will need to understand
your program, rather than writing code that is first and foremost read by
a compiler or interprerter. With LitProg, your program isn't a loose
collection of source files with a structure that is either implicit or
only apparent after understanding a build system and following dozens of
imports. Instead you can structure your program in a way that makes most
sense for your readers to understand it. You can write documentation,
diagrams, code and tests in whatever order makes most sense for people who
want to understand your program rather than in a structure that is
dictated by your build tools.

In practical terms, LitProg makes this possible by allowing you to compose
your program from fenced code blocks. You can give each block an id/name,
include them in others, write them to files and even run subprocesses that
execute a code block. A typical use case for such executable code blocks
is to validate (and demonstrate to your readers) that your program is
correct.

LitProg is simple and flexible. You can use it with any language, on any
platform, with any build system. With Markdown, the barrier to entry is
very low and you won't have to constantly check if the generated
documentation looks right. You can instead stay focused and productive in
your text editor and work with your existing tools. Granted, code
completion, jump to definition and other IDE features may not work as well
in code blocks of a markdown file as they do in plain source code files,
but since LitProg generates such source files, you can switch to them if
there is something more tricky you need to debug.



### Getting Started

*Literate Programming* is a programming paradigm. *LitProg* is a compiler/build tool. Even if you are not on board with LP, you may nonetheless find LitProg to be useful, for example if you want to write a technical article or tutorial. This book is a documentation artifact of the literate program for the `litprog` cli command, which has of course been compiled using itself. To get started you can download one of the software artifacts of LitProg and run `litprog build` with an example file.

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

The example file is written in Markdown, which is familiar to many programmers and widely supported by software related to programming. LitProg extends Markdown in a way that does not require special support by such software. In other words, it should work fine with your current text editor.

When programming you will usually run `litprog build lit/` or `litprog watch lit/`. This will generate source code files and execute any sub-commands that are part of your program. Such commands typically relate to testing and validating your program, or they might illustrate its behaviour.

You can pass the `--html <directory>` and `--pdf <directory>` parameters to generate the static HTML and PDF files. Generating these documentation artifacts (as opposed to just executing the code blocks) can take some time, so it introduces a friction that you will want to avoid during regular programming. It can be a part of a build process or [CI][href_wiki_ci] pipeline and you will only occasionally you may want to generate documentation during development, but usually you shouldn't have to.

```bash
$ litprog build --verbose 11_intro.md --html doc/ --pdf doc/
$ ls -R
examples/fib.py
doc/litprog.pdf
doc/index.html
doc/styles.css
doc/11_intro.html
```


### LitProg by Example

I will use the familiar [Fibonacci function][href_wiki_fib] and Python for this example. I hope you will learn nothing about the particular example and can instead focus on the mechanics of LitProg itself. I will later give a more extensive example, to give a better impression of Literate Programming, without being distracted by the mechanics of LitProg.

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

A Python implementation of the Fibonacci function might look like this:

```python
def fib(n: int) -> int:
    if n < 2:
        return n
    else:
        return fib(n - 1) + fib(n - 2)
```

In case you weren't aware, this naive recursive implementation is
well known to have a complexity of $`O(2^n)`$ (in other words: it's
pretty bad).


### The `lp_def` Directive

LitProg works by parsing your markdown for fenced code blocks and parsing these code blocks for directives. The previous[^fnote_avoid_relative] code block has no directive, so it is not treated specially by LitProg in any way. It is not written to any file and neither compiled or executed. It will end up in the documentation, just as you would expect from any Markdown renderer, but that's about it.

To make a code block usable, it must be assigned to a namespace using
the `lp_def` directive. The block can then be referenced in a later code block using other directives.

```python
# lp_def: slow_fib
def fib(n: int) -> int:
    if n < 2:
        return n
    else:
        return fib(n - 1) + fib(n - 2)
```

LitProg directives are written using the comment syntax of the programming language declared for the block. In this case, the syntax of the block is `python`, so all lines which start with a `#` character are parsed in search of LitProg directives. In this case there is only one such line: `# lp_def: slow_fib`. The text after[^fnote_whitespace_in_directives] the `:` (`slow_fib`) is an identifier, which places the block in the namespace of this file.

The previous block can be referenced either as `slow_fib` or `overview.slow_fib`. The namespace `overview` is derived from the filename `11_overview.md`, from which the file extension and any leading digits are stripped. Outside of the file, only the fully qualified name `overview.slow_fib` can be used.

The most simple way to refrence a code block is with the `lp_include` directive. We can use this for example, to add an assertion in a new block.

~~~
```python
# lp_include: slow_fib
assert fib(8) == 21
```
~~~

Once the preceding block is expanded, it is equivalent to the following literal markdown:

~~~
```python
def fib(n: int) -> int:
    if n < 2:
        return n
    else:
        return fib(n - 1) + fib(n - 2)
assert fib(8) == 21
```
~~~


!!! aside "Invalid Identifiers"

    LitProg is conservative when it comes to your identifiers. Each identifier must be unique to its block. If another block in this file contains `lp_def: slow_fib`, then LitProg will raise an error. Likewise if no `lp_def` for an `lp_include` can be found, then an error will be raised.


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

> Beware of bugs in the above code;
> I have only proved it correct, not tried it.
>
> – Donald E. Knuth

While the `fib` function is quite simple to understand, you as a
reader are either left to validate if it is correct for yourself, or
to trust the claims of the author that the implementation is correct.

Instead of manual validation or trust, we can instead provide some
code which will actually execute the `fib` function, and which would
cause an error if any of our assertions were false.

```python
# lp_def: test_fib
fibs = [fib(n) for n in range(9)]
assert fibs == [0, 1, 1, 2, 3, 5, 8, 13, 21]
assert fib(12) == 144
assert fib(20) == fib(19) + fib(18)
```

I will use these assertions again later, so I've declared them in a separate block first, before now proceeding to execute them.

```python
# lp_exec: python3
# lp_include: slow_fib
# lp_include: test_fib
```

The `lp_exec` directive invokes a command (in this case `python3`), which receives the expanded block (after substitution of all `lp_include` directives) via its [stdin][href_wiki_std_streams].

If the [exit status][href_wiki_exit_status] of the `python3` process is anything other than the expected value of `0`, then the LitProg build will fail. This is an important point: The fact that the HTML or PDF artifact that you are reading even exists, is proof[^fnote_proof_hedge] that the command exited successfully.

!!! aside "Options of `lp_exec`"

    - `lp_expect`: The expected exit status of the process. The default value is `0`.
    - `lp_timeout`: How many seconds a process may run before being terminated. The default value is `1.0`.
    - `lp_hide`: If the block should be hidden from generated documentation. Using this goes against the ethos of Literate Programming, but if your readers don't care about the assurance that they have access to the full program (for example if you're using LitProg to write a blog article) then this may be appropriate. The default value is `false`


### Capturing Output

While assertions and an exit status are nice, it will often be better to show some output generated by a program. The previous process didn't write anything to `stdout` or `stderr`, so let's run another which does.

```python
# lp_exec: python3
# lp_include: slow_fib
for i in range(9):
    print(fib(i), end=" ")
```

The output of a process is always captured but that output is only made visible by using an `lp_out` directive.

```shell
# lp_out
0 1 1 2 3 5 8 13 21
# exit: 0
```

The `lp_out` directive marks its block as a container for the output of the process that was previously run. When the LitProg build is completed, the contents of the `lp_out` block is updated in-place with the captured output when the `-i/--in-place-update` option is used. If there is no `lp_out` block after an `lp_exec` block, then the captured output is discarded.

!!! note "Options of `lp_out`"

     - `lp_proc_info`: A format string used to customize the process info that is appended to output blocks. It can be set to "none" to supress the process info. The available info is `exit`, `time` and `time_ms`. The default is `exit: {exit:>3}`.
     - `lp_max_lines`: The maximum number of lines to keep of the captured output. default `10`
     - `lp_max_bytes`: The maximum number of bytes to keep of the captured output. default `1000`
     - `lp_out_prefix`: A string which is used to prefix every line of the stdout. default `""`
     - `lp_err_prefix`: A string which is used to prefix every line of the stderr. default `"! "`


The captured output gives the reader some assurance that the document they are reading is not just some manually composed fabrication which was written as an afterthought and is detached from the actual program. Even with the best of intentions, humans often make mistakes, so program logic that has not been executed by a machine will inspire little confidence.

The exit status and the captured output are demonstrations that at least on one machine and at some point in the past, the program was in some sense "correct", or at least that the generated documentation is consistent with the program that was used to generate it[^fnote_max_hedging]. This approach to including program output in generated documentation gives readers a chance to see if the author is trying to hide how the sausage is made. While it may be appropriate to relegate certain logic to an appendix, for example to avoid distraction from a desired narrative, the entire program can in principle be made accessible to inquisitive readers. They may still have to trust that the author is acting in good faith, but at least the issues of outdated documentation and casual errors due to forgetfulness of the author is greatly mitigated.

By this point I hope you can see, that LitProg allows you to write:

1. documentation,
2. source code
3. automated tests

These can all be combined in a way that allows you to create a narrative that makes the most sense to understand your program.


### In-Place Updates of Fenced Blocks

Validating that a program is correct, is not only important to communicate to readers, it is also part and parcel of the programming workflow. Most programmers are the first that want to know if their program is working or broken. Generating HTML/PDF documentation takes a bit of time and switching back and forth between a browser window and a code editor would introduce a lot of friction into the programming workflow. To avoid this friction, LitProg can instead do in-place updates to the original markdown files. The output that is captured during a build is inserted into the markdown text. This works well for editors that detect and automatically reload files that have changed. When using `'litprog watch'` programmers can simply hit save and see the updated output of their program appear directly in their text editor.

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

It might be enough for academics if LitProg were only to produce documentation, but most other people want to have artifacts that are actually useful, such as an actual program. In the most simple case you can use the `lp_file: <filename>` directive to generate files.

```python
# lp_file: examples/fib.py
# lp_include: slow_fib
for i in range(10):
    print(fib(i), end=" ")
```

!!! note "Cross Platform Filenames"

    Paths in LitProg always use the `/` (forward slash) character, even if you are running on a Windows machine. Avoid using absolute paths, so that your program can be built on machines with different directory layouts.


The `lp_run: <command>` directive  combines `lp_exec` and `lp_out`, except that unlike `lp_exec`, the process will not receive anything via stdin. This is not too limiting however, as commands are only run after all `lp_file` directives have been written, so you can execute your program via a previously written file (instead of feeding in the program via stdin, as is the case for `lp_exec`). Let's try this for the `examples/fib.py` created by the previous block.

```bash
# lp_run: python3 examples/fib.py
0 1 1 2 3 5 8 13 21 34
# exit: 0
```

### The `lp_addto` Directive

If you're writing a full program or module, it will often make sense to
gradually build up certain parts of it. A typical example of this are
imports at the top of a module. For some imports that are used broadly
across your program, it may make sense to define them early or in some
appendix with boilerplate code.

```python
# lp_def: imports
from typing import Tuple, List, Dict, Set, Sequence
```

For other imports, it may make more sense to introduce them closer to
their usage site. Here we setup a block `imports` which can be updated
from other sections and finally included at the top of the module we're
creating. Usage examples of `lp_addto: imports` follow shortly.

!!! note "Order when using `lp_addto`"

    The order of blocks with `lp_addto` directives is the same as they appear in the markdown file.

    - You cannot use `lp_addto` with blocks that are defined in another file.
    - You cannot use `lp_addto` before the block with the corresponding `lp_def` directive.


### Porcelain vs. Plumbing

The `pretty_print_fibs` function prints a formatted string of the Fibonacci numbers in the given range given by the parameter `ns: Sequence[int]`.

```python
# lp_def: pretty_print_fibs
def pretty_print_fibs(ns: Sequence[int]) -> None:
    """Calculate Fibbonacci numbers and print them to stdout."""
    # lp_include: pretty_print_fibs_impl
```

This is a typical example of code that is not considered part of the
core/plumbing of a program, but rather porcelain. As such it's OK for code
to not be documented so well. A deep understanding of such porcelain code
will contribute little to the understanding of a program. Oftentimes it is
better to start with some example code that demonstrates its behaviour,
rather than with the full implementation.

```python
# lp_exec: python3
# lp_include: imports, slow_fib, pretty_print_fibs
pretty_print_fibs(range(15))
```

```shell
# lp_out
fib( 0) =>   0  fib( 1) =>   1  fib( 2) =>   1
fib( 3) =>   2  fib( 4) =>   3  fib( 5) =>   5
fib( 6) =>   8  fib( 7) =>  13  fib( 8) =>  21
fib( 9) =>  34  fib(10) =>  55  fib(11) =>  89
fib(12) => 144  fib(13) => 233  fib(14) => 377
# exit: 0
```

This also illustrates the use of forward references in LitProg. LitProg does multiple passes over the blocks of your program. It first collects all `lp_def` directives and then recursively resolves all `lp_include` directives and finally it evaluates any `lp_exec` or `lp_run` directives. In other words, it is fine to define parts of your program in an order that suits your narrative rather than linearly the way your compiler/interpreter requires them to be defined.

Finally the actual implementation (which most people will and should just skip).

```python
# lp_def: pretty_print_fibs_impl
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


### Optimizing

Now that we have some code that is good, and which we can also see is correct, it's time we turned to optimization.

```python
# lp_def: fast_fib
_cache: Dict[int, int] = {}

def fast_fib(n: int) -> int:
    if n < 2:
        return n
    if n not in _cache:
        _cache[n] = fast_fib(n - 1) + fast_fib(n - 2)
    return _cache[n]
```

Note that there is no dependency mechanism for blocks, so every time we `lp_include: fast_fib`, the block in which it is included will also have to `lp_include: imports` so that `Dict` is imported.

We can run the same validation code as before, the only difference being that we replace `fib` with `fast_fib`

```python
# lp_exec: python3
# lp_include: imports, slow_fib, fast_fib
fib = fast_fib
# lp_include: test_fib
```

```python
# lp_out
# exit: 0
```

So far so good, the `exit: 0` shows that that `fast_fib` is just as correct as the original `fib` function (the assertions ran through without any errors), but how do we know that it's any faster? Let's write something to time an arbitrary block of code.

```python
# lp_def: timeit
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

!!! aside "One time imports"

    Since we're only using this timeit code once, we don't add the imports to the `imports` block, which we'll be using later in a module where we don't want to have superflous imports.


```python
# lp_exec: python3
# lp_include: imports, timeit, slow_fib, fast_fib
with timeit("slow"): fib(12)
with timeit("slow"): fib(16)
with timeit("slow"): fib(20)
with timeit("fast"): fast_fib(12)
with timeit("fast"): fast_fib(16)
with timeit("fast"): fast_fib(20)
```

```shell
# lp_out
slow     0.201 ms
slow     1.067 ms
slow     7.132 ms
fast     0.025 ms
fast     0.009 ms
fast     0.008 ms
# exit: 0
```


### Macro Directives

This feature was dropped. If anything is needed it will have to be much better than textual replacements. The final nail in the coffin was trying to have namespaces that work across languages.

The simplest macro supported by LitProg is the `lp_const` directive. These can be defined inline or for example inside of a markdown listing.

 - The largest Fibonacci number to calculate: `lp_const: MAX_FIB=20`
 - How many numbers to print per line `lp_const: FIBS_PER_LINE=5`

```python
# lp_exec: python3
# lp_include: imports, slow_fib, fast_fib
MAX_FIB = 20
FIBS_PER_LINE = 5

print(f"fib(2..{MAX_FIB}):", end="")
for n in range(MAX_FIB):
    if n % FIBS_PER_LINE == 0:
        print()
        print(f"  {n:>3}", end=": ")
    print(f"{fast_fib(n):>5}", end=" ")
```

```shell
# lp_out
fib(2..20):
    0:     0     1     1     2     3
    5:     5     8    13    21    34
   10:    55    89   144   233   377
   15:   610   987  1597  2584  4181
# exit: 0
```

The choice of names for such a constant may be influenced by the language being used. If you want make it possible for code formatters to reformat a code block, then the code block must be syntactically valid even if it includes non-expanded macros.

The preceding example prin
LitProg has support for macros using the `lp_def` directive. These are non-hygenic, can be parameterized and are recursively expanded.


### Writing Code to Disk

Up to here our code has been floating around in memory, but eventually we want to produce something that is useful. A program that our users might like to run. In other words, we want to write our code to disk so that it can either be used directly, or further processed by a compiler.

Next is some boring python scaffolding to wrap the functions written so far.

```python
# lp_addto: imports
import sys
```

```python
# lp_def: parse_args
ParamsAndFlags = Tuple[List[str], Set[str]]

def parse_args(args: List[str]) -> ParamsAndFlags:
    flags = {arg for arg in args if arg.startswith("-")}
    params = [arg for arg in args if arg not in flags]
    return params, flags
```

```python
#!/usr/bin/env python
# lp_def: fib_cli_impl
# lp_include: imports

__doc__ = f"""Usage: python {__file__} [--help] [--pretty] <n>..."""

# lp_include: slow_fib, fast_fib
# lp_include: pretty_print_fibs
# lp_include: parse_args
# lp_include: main
```

```python
# lp_def: main
def main(args: List[str] = sys.argv[1:]) -> int:
    params, flags = parse_args(args)
    # lp_include: args_check

    ns = [int(n) for n in params]
    if "-p" in flags or "--pretty" in flags:
        pretty_print_fibs(ns)
    else:
        for n in ns:
            print(fast_fib(n))
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

Don't worry if you're not familiar with python or top level scripts. The noteworthy thing about preceding block is the `lp_include` directive inside the `main` function.

The first thing in `main` is to validate the arguments to the script and either print a help message or an error message.

```python
# lp_def: args_check
if not args or "--help" in flags or "-h" in flags:
    print(__doc__)
    return 0

invalid_params = [n for n in params if not n.isdigit()]
if any(invalid_params):
    print("Invalid parameters: ", invalid_params)
    return 1
```

Note that `lp_include` expands indentation to the level of the comment which holds the directive. In other words, every line of the block that is included is prepended with indentation according to where it is included and the block where it is defined does not have to anticipate the indentation level where it will be included. Note also that the `lp_include: args_check` directive precedes the `lp: args_check` directive. When LitProg expands an `lp_include` directive, LitProg will recursively resolve

Finally after we have prepared all our code, we can write it to disk...

```python
# lp_file: examples/fib_cli.py
# lp_include: fib_cli_impl
```

...and give it a spin.

```bash
# lp_run: python3 examples/fib_cli.py --help
Usage: python examples/fib_cli.py [--help] [--pretty] <n>...
# exit: 0
```

```bash
# lp_run: python3 examples/fib_cli.py 22
17711
# exit: 0
```

```bash
# lp_run: python3 examples/fib_cli.py --pretty 3 7 8 9 19 20
fib( 3) =>    2  fib( 7) =>   13  fib( 8) =>   21
fib( 9) =>   34  fib(19) => 4181  fib(20) => 6765
# exit: 0
```

```bash
# lp_run: python3 examples/fib_cli.py invalid argument
# lp_expect: 1
Invalid parameters:  ['invalid', 'argument']
# exit: 1
```


!!! aside

    Although the final invocation of `fib_example.py` has a non-zero exit status, the session nontheless has an exit status of `0`. This is because python3 is invoced by a bash process, which does not propagate the exit status of a command by default. If we wanted to propagate the exit status we could use [`set -e` / `set -o errexit`][href_explainsh_errexit].


### The `lp_make` Directive

So far every process was independent of every other. In principle the process could have been executed in any order, or indeed concurrently to each other. Dependencies on code blocks are explicitly declared by the `lp_include` directives inside of each `lp_exec` block.

~~~
```bash
# lp_make: examples/fib_cli_compat.py
# lp_deps: examples/fib_cli.py
python -m lib3to6 examples/fib_cli.py \
    > examples/fib_cli_compat.py
sjfmt examples/fib_cli_compat.py
chmod +x examples/fib_cli_compat.py
```
~~~

I'm implementing this using `lp_exec` for now.

```bash
# lp_file: examples/build_cli_compat.sh
python3 -m lib3to6 examples/fib_cli.py \
    > examples/fib_cli_compat.py
chmod +x examples/fib_cli_compat.py
```

```bash
# lp_exec: bash examples/build_cli_compat.sh
```


!!! note "Why, oh why, does every tool need a new build system?!"

    In my defense, I don't feel that I'm reinventing the wheel, rather I'm reimplementing an existing and vernerable wheel called `make`. If you are familiar with make, you should have no problem using the build system of LitProg.

    Even if this were reinventing the wheel, since output generated earlier phases of a LitProg build can be used by later phases (for example test results can be shown in output documents), it makes sense to have the build system be integrated and not separate.

    Many large programs use a build system to produce the final artifacts, such as binaries or packages. Documenting how to produce these artifacts should at least be possible, otherwise there is a thick curtain behind which the reader can .

!!! note "redo: mtime dependencies done right"

    @apenwarr has written enough about the [pitfalls of detecting changes using mtime comparison][href_apenwarr_mtime]. LitProg takes the reccomended apporoach of keeping a database/index of files and falling back on content hashing only as an optimization when file system metadata cannot be relied upon to determine if a dependency has changed.


```bash
# lp_run: python2 --version
! Python 2.7.18
# exit: 0
```

```bash
# lp_run: python2 examples/fib_cli_compat.py 22
# lp_expect: 1
! Traceback (most recent call last):
!   File "examples/fib_cli_compat.py", line 7, in <module>
!     from typing import Tuple, List, Dict, Set, Sequence
! ImportError: No module named typing
# exit: 1
```

```bash
# lp_run: python3 --version
Python 3.8.6
# exit: 0
```

```bash
# lp_run: python3 examples/fib_cli_compat.py 22
17711
# exit: 0
```

```bash
# lp_run: python3 examples/fib_cli_compat.py --pretty 2 5 8 12 19 20
fib( 2) =>    1  fib( 5) =>    5  fib( 8) =>   21
fib(12) =>  144  fib(19) => 4181  fib(20) => 6765
# exit: 0
```

These examples are intended as a quick overview, but there is much more to be said about the how each of these primitives can be used and misused.

TODO: Further reading.


[^fnote_good_enough_docs]: The documentation should be good enough for practical use. The effort devoted to the quality of the various artifacts corresponds to the use cases I anticipate. The PDF/print output is presumed to be used primarily as linearly read reference material. This means, it is draft quality rather than print quality as the files are intended for a few people to review, rather than for widespread publication. A feature of such output might be to annotate each definition with page numbers where it is used and vis-versa to annotate each usage with a page number for its definition. I've not put in the effort to do that, if you're diving that deep into the material, you should use the HTML, the markdown source or the generated code, where you have proper jump to definition and search.

[^fnote_avoid_relative]: When referencing parts of a document in your text, avoid phrases that are particular to a specific format. Phrases like "the above image" or the below "code block" may be confusing if the reader is viewing a printed version of your program and the image or code block is on a different page. Such relative references are also error prone paragraphs or images are reordered. Instead, prefer to use named references which are less error prone and confusing, regardless of output format.

[^fnote_avoid_numbers]: Chapter and section numbers can change when the structure of a project changes. Chapters can be reordered, new sections can be inserted, so any phrases such as "see chapter 3 section 2 for further details" will become invalid, or worse, point to something other than originally intended. TODO: stable links using names.

[^fnote_whitespace_in_directives]: Leading and trailing whitespace is stripped from directives. If you don't want this to happen, the value of a directive can be surrounded with `'` quotes or `"` double quotes.

[^fnote_max_hedging]: Any "proof" of correctness is only as good as the assertions made by the programmer. Hopefully the broader accessibility of LitProg programs means that programmers will feel the watchful eyes of readers and put some effort into making their programs demonstrably correct. Sorry about all the hedging.


[iref_touchy_feely]: 13_touchy_feely_pitch.html

[href_wiki_markdown]: https://en.wikipedia.org/wiki/Markdown

[href_wiki_litprog]: https://en.wikipedia.org/wiki/Literate_programming

[href_pbr_preface]: http://www.pbr-book.org/3ed-2018/Preface.html

[href_johndcook_blog1]: https://www.johndcook.com/blog/2016/07/06/literate-programming-presenting-code-in-human-order/

[href_ctan_web2w]: https://ctan.net/web/web2w/web2w.pdf#page=13

[href_amazon_understanding_mp3]: https://www.amazon.com/Understanding-MP3-Semantics-Mathematics-Algorithms/dp/1541259335/

[href_jupyter]: https://jupyter.org/

[href_svgbob]: https://github.com/ivanceras/svgbob

[href_blockdiag]: http://blockdiag.com/en/blockdiag/index.html

[href_katex]: https://katex.org/

[href_wiki_ci]: https://en.wikipedia.org/wiki/Continuous_integration

[href_katex_docs]: https://katex.org/docs/supported.html

[href_wiki_fib]: https://en.wikipedia.org/wiki/Fibonacci_number

[href_knuthweb]: http://www.literateprogramming.com/knuthweb.pdf

[href_wiki_std_streams]: https://en.wikipedia.org/wiki/Standard_streams

[href_wiki_exit_status]: https://en.wikipedia.org/wiki/Exit_status

[href_wiki_techdebt]: https://en.wikipedia.org/wiki/Technical_debt

[href_explainsh_errexit]: https://explainshell.com/explain?cmd=set+-e

[href_apenwarr_mtime]: https://apenwarr.ca/log/20181113

[href_ziglang]: https://ziglang.org
