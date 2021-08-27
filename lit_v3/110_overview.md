# Introduction to LitProg

LitProg is a [Markdown][href_wiki_markdown] processor for [Literate Programming (LP)][href_wiki_litprog].

[href_wiki_markdown]: https://en.wikipedia.org/wiki/Markdown

[href_wiki_litprog]: https://en.wikipedia.org/wiki/Literate_programming


```bob
               +------------+
              ++            |\
              ||  Markdown  +-+
              ||              |
              |+-------------++
              +-------+------+
 +--------+           V           +------------+
++        |\    .------------.   ++            |\
||  Code  +-+   |            |   || "HTML/PDF" +-+
||          |<--+   LitProg  +-->||              |
|+---------++   |            |   |+-------------++
+----------+    '------------'   +--------------+
```

LitProg does the following steps:

 1. read Markdown files as input,
 2. write source code files as output,
 3. write HTML and PDF files as documentation.

While this *is* in essence what LitProg does, it doesn't explain why to use LitProg rather than a static site generator, other literate programming tools or to just continue directly writing source code files, without any extra ceremony.

LitProg is inspired by the interactive nature of [Jupyter notebooks][href_jupyter]: You can mix documentation, code and critically also *execution*. This makes it possible to *demonstrate* to your readers, that your literate program actually works as advertised, by executing sub-processes and capturing their output. So a more complete picture of how LitProg works is this:

[href_jupyter]: https://jupyter.org/


```bob
               +------------+
              ++            |\
              ||  Markdown  +-+
              ||              |
              |+-------------++
              +------+-------+
                    1|  ^
 +--------+          V  !4        +------------+
++        |\    .-------+----.   ++            |\
||  Code  +-+ 2 |            | 5 || "HTML/PDF" +-+
||          |<--+   LitProg  +-->||              |
|+---------++   |            |   |+-------------++
+-----o----+    '----+-------'   +--------------+
      !            3 !  ^
      !              v  !
      !         .-------+----.
      !         |            +.
      '~~~~~~~~~+  Subprocs  ||
                |            ||
                '+-----------'|
                 '------------'
```

 1. read Markdown files as input,
 2. write source code files as output,
 3. execute code blocks and capture their output
    (optionally using code files generated in step 2).
 4. use captured output from step 3 for in-place
    updates of the markdown from step 1.
 5. write HTML and PDF artifacts as documentation.


## Theories of Programs

!!! warning "WIP: Work in Progress"

    This is very much incomplete. Probably half of it needs to either
    be cut, or at least moved to another chapter.

    I am currently dogfooding LitProg on a separate project before attempting a self-hosted implementation.


[Peter Naur][href_wiki_naur] (the N in BNF) wrote a wonderful essay [Programming as Theory Building][href_naur_patb] in 1985 that I think still holds up to this day.  What resonates strongly with many experienced programmers is the idea, that code by itself is almost worthless, because it does not capture the theories upon which it is based.  The code by itself, may for a while continue to serve a use-case, but any attempt to modify or build upon code, without access to the theories used to create it, is ultimately doomed to fail or to be so expensive, that reimplementation from scratch should be considered.

Naur is not optimistic that such theories can be captured in artifacts at all, as they are a form of tacit knowledge, difficult to express in code, in diagrams or documentation.  If these theories can at all be transmitted from one person to another, then only through ongoing interactions between a programmer who knows the theories and another who has to rebuild the theories from scratch in their own mind.

[href_wiki_naur]: https://en.wikipedia.org/wiki/Peter_Naur

[href_naur_patb]: https://pages.cs.wisc.edu/~remzi/Naur.pdf

I don't know if Naur is correct in his pessimism about documentation.  He may well be.  To the extent that such artifacts *can* be created however, to the extent that theories *can* be captured effectively, the Literate Programming paradigm is worth a shot.  The goal of LitProg is to reduce, as much as possible, the friction to create artifacts that represent the full program, including its theories, not just its code.  The goal is to help new programmers to gain full ownership of the programs they inherit, be it as users or as maintainers.  The goal is to reduce the effort to communicate the essence of a program, so that later programmers can understand it just as well as the original authors[^fnote_green_vs_brown].

[^fnote_green_vs_brown]:
    Incidentally, a [recent blog article][href_green_vs_brown] made the distinction between programming languages that are "green" vs "brown". This may have less to do with the languages themselves as much as the fact that a new programming language also implies green field development, whereas an old language may imply an existing codebase.

    To write new code is more easy than to modify unfamiliar existing code. This leads to a positive association with the new "green" programming language compared to the old "brown" programming language, even though this may have nothing to do with the merrits of the languages themselves.

    It will be interesting to see programmers have the same dread of working with a project that uses LitProg, or if such projects will have a more enduring perception as "green".

[href_green_vs_brown]: https://earthly.dev/blog/brown-green-language/


## Narratives of Programs

The idea of Literate Programming is to direct your focus as a programmer more toward your human readers and less to the compiler or interpreter.  Change the main focus from the code and how it is parsed by a machine, toward your human readers, who will want to understand *why* you wrote the code the way you did.  If you cannot or will not justify the existence of your program, then your unfortunate readers will be like Sherlock Holmes, trying to piece together from morsels of evidence, how anything fits together.  If they cannot find such a justification, they may well resort to adding kludge after kludge, hacking together a cancerous growth, that is incoherent with the original theories upon which the program was based.

With LitProg, your program doesn't have to be loose collection of source files with a structure that is either implicit or only apparent after understanding a build system, and only after chasing down recursive levels of imports.  Instead you can structure your program in a way that makes most sense for your readers.  You can write documentation, diagrams, code and tests in whatever order makes the most sense for people who want to understand the "why" of your program.

TANSTAFL

## Building, Block by Block

In practical terms, LitProg makes it possible to construct a narrative for your program by composing it with fenced code blocks.  You can define an id/name for each block, include them in others, write them to files and run them in sub-processes.  A typical use case for such executable code blocks is to validate (and demonstrate to your readers) that your program is correct.

LitProg is simple and flexible.  You can use it with practically any programming language and use your existing tools.  With Markdown, the barrier to entry is very low and the generated documentation is very close to the original Markdown, so you won't have to constantly check if the generated documentation looks OK.  Instead, you can stay focused and productive in your text editor and continue to work with your existing tools.

!!! aside "Caveat on "existing tools""

    Granted, code completion, jump to definition and other IDE features may not work as well in code blocks of a Markdown file as they do in plain source code files.  Since LitProg generates such source files however, you can at least fall back on them for debugging.


## Minimal Example

With LitProg, code blocks can be referenced by others and used to compose a program.

```python
# def: prime_sieve
def prime_sieve(n):
    is_prime = [True for i in range(n)]

    p = 2
    while p * p < n:
        if is_prime[p]:
            for i in range(p * p, n, p):
                is_prime[i] = False
        p += 1
    return is_prime
```

Such code blocks can be written to files or executed directly via the `stdin` to another process (as is commonly supported by interpreted languages).

```python
# exec: python3
# dep: prime_sieve
for number, is_prime in enumerate(prime_sieve(n=50)):
    if is_prime:
        print(number, end=" ")
```

During `litprog build`, the output of each sub-process is captured/buffered and can be displayed in a separate code block using the `out` directive.

```shell
# out
0 1 2 3 5 7 11 13 17 19 23 29 31 37 41 43 47
# exit: 0
```

!!! note "Line Numbers"

    In the HTML and PDF output generated by LitProg, the line numbers of a code block match the line numbers in the original Markdown file.


## Getting Started

*Literate Programming* is a programming paradigm.  *LitProg* is a build tool.  Even if you are not on board with the LP paradigm, you may nonetheless find LitProg to be useful, for example if you want to write a technical article or tutorial.  This book is a documentation artifact of the literate program for the `litprog` cli command, which has been compiled (how else of course could it be) using itself.  To get started you can download one of the software artifacts of LitProg and run `litprog build` with an example file.

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

When programming, you will usually run `litprog build lit/`. This will generate source code files and execute any sub-commands that are part of your program. A typical use-case for such commands is to test and validate your program and illustrate its behavior to the reader.

You can pass the `--html <directory>` and `--pdf <directory>` parameters to generate the static HTML and PDF output. Generating these documentation artifacts (as opposed to just executing the code blocks) can take some time, so it introduces a friction that you will want to avoid during regular programming. It can be a part of a build process or [CI][href_wiki_ci] pipeline and you can usually skip generating the documentation during development.

```bash
$ litprog build --verbose 11_intro.md --html doc/
$ ls -R .
11_intro.md

.doc/:
litprog.pdf
index.html
11_intro.html
styles.css
...

.examples/:
fib.py
```

[href_wiki_ci]: https://en.wikipedia.org/wiki/Continuous_integration


## LitProg by Example

I will use the familiar [Fibonacci function][href_wiki_fib] and Python for this example. I hope you will learn nothing about the particular example and can instead focus on the mechanics of LitProg itself. I will later give a more extensive example, to give a better impression of Literate Programming, without being distracted by the mechanics of LitProg.

To produce an inline equation, write LaTeX as inline code, surrounded by $ characters: ``$`a^2+b^2=c^2`$`` -> $`a^2+b^2=c^2`$ (btw. there is a nice editor on [katex.org][href_katex] and [documentation][href_katex_docs] to help create such formulas). To produce a centered block, write LaTeX in a `math` block:

[href_wiki_fib]: https://en.wikipedia.org/wiki/Fibonacci_number

[href_katex]: https://katex.org/

[href_katex_docs]: https://katex.org/docs/supported.html


~~~
```math
\begin{array}{l}
F_0 = 0 \\
F_1 = 1 \\
F_n = F_{n-1} + F_{n-2}
\end{array}
```
~~~

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


### The `def` Directive

LitProg works by parsing your Markdown for fenced code blocks and then parsing these code blocks for directives such as `def: <identifier>`. The previous [^fnote_avoid_positional_refs] [^fnote_avoid_numbers] code block has no directive, so it is not treated specially by LitProg in any way. It is not written to any file and neither compiled or executed. It will end up in the documentation, just as you would expect from any Markdown processor, but that's about it.

[^fnote_avoid_positional_refs]: When referencing code blocks or images in your prose, avoid phrases that only work for a particular document layout. Phrases like "the above image" or "the code block below" may be confusing if the reader is viewing a printed version of your program and the image or code block is on a different page, causing "the image below" to in fact be on the next page, positionally above the paragraph with a reference to it as "below". Instead, prefer to use words such as "following" or "previous" that work regardless of document layout. Even better are named references, which will continue to be correct, even if a paragraph or image is later reordered.

[^fnote_avoid_numbers]: Chapter and section numbers can change when the structure of a project changes. Chapters can be reordered, new sections can be inserted, so any phrases such as "see chapter 3 section 2 for further details" will become invalid, or worse, point to something other than originally intended. TODO: stable links using names.


To make a code block usable, it must be assigned to a namespace using
the `def` directive. The block can then be referenced in a later code block using other directives.

```python
# def: slow_fib
def fib(n: int) -> int:
    if n < 2:
        return n
    else:
        return fib(n - 1) + fib(n - 2)
```

LitProg directives are written using the comment syntax of the programming language declared for the block. In this case, the syntax of the block is `python`, so all lines which start with a `#` character are parsed in search of LitProg directives. In this case there is only one such line: `# def: slow_fib`. The text after the colon (`slow_fib`) is an identifier[^fnote_whitespace_in_directives], which places the block in the namespace of the current file.

[^fnote_whitespace_in_directives]: Leading and trailing whitespace is stripped from directives. If you don't want this to happen, the value of a directive can be surrounded with `'` quotes or `"` double quotes.


!!! aside "On Parsing Comments"

    It is often seen critically, to embed programming constructs inside comments and rightfully so. Considering the context of LitProg however, where programmers have Markdown available to them for documentation and don't need to resort as much to comments, I think this repurposing of the comment syntax is a reasonable compromise:

    1. It allows existing code/syntax highlight and formatting tools to work, without having to implement anything specific to LitProg.
    2. Only comments with LitProg specific directives are parsed. All other comments are ignored, so you can continue to use comments for other uses, as you deem appropriate.


The previous block can be referenced either as `slow_fib` or `overview.slow_fib`. The namespace `overview` is derived from the filename `11_overview.md`. The normalization of the filename removes the file extension as well as any leading digits and underscores. Within the `11_overview.md` file, the shorter reference `slow_fib` is valid, but from other Markdown files, you must use the fully qualified name `overview.slow_fib`.

!!! aside "Invalid Identifiers"

    LitProg is conservative when it comes to your identifiers. Each identifier must be unique to a file. If another block in the current file contains `def: slow_fib`, then LitProg would raise an error. Likewise if no `def` for an `dep` can be found, then an error would be raised.

The most common way to reference a code block is with the `dep` directive. We can use this for example, to add an assertion in a new block.

~~~
```python
# dep: slow_fib
assert fib(8) == 21
```
~~~

Once the preceding block is expanded, it is equivalent to the following literal Markdown:

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

!!! aside "Lanugage Support"

    LitProg supports the comment syntax of many programming languages and can be easilly extended to support more. For Python, Bash, PHP the comment syntax uses the `#` character, for Java, JavaScript, C, it uses the `//` string etc.

    Some blocks may not even have a meaningful language (such as output blocks), in which case you can pick any language with a comment syntax you prefer. In this program I will use `shell` if there is not a more appropriate choice.

    Languages that are unknown to LitProg can nonetheless be used if it has the same comment syntax as another language. Since LitProg only parses the comments of a code block and doesn't do anything specific to a particular language, you can label the block with the other language (as a stop-gap measure until support is added). If you wanted to use the [Zig Language][href_ziglang] for example, you could label the block with `rust` instead, which also uses `//` for comments and for which the syntax highighting works tolerably well (at least in my editor).


[href_ziglang]: https://ziglang.org


### Running Commands

> Beware of bugs in the above code;
> I have only proved it correct, not tried it.
>
> – Donald E. Knuth

While the `fib` function is quite simple to understand, you as a
reader are either left to validate for yourself if it is correct, or
to trust the claims of the author that the implementation is correct.

Instead of manual validation or trust, we can instead provide some
code which will actually execute the `fib` function, and which would
cause an error if any of our assertions were false.

```python
# def: test_fib
fibs = [fib(n) for n in range(9)]
assert fibs == [0, 1, 1, 2, 3, 5, 8, 13, 21]
assert fib(12) == 144
assert fib(20) == fib(19) + fib(18)
```

The `test_fib` block is not executed just yet. I have declared a separate block first, as I plan to use these tests multiple times later. Note that this block does not directly depend on any other block that would contain a `fib` function, instead it will use whatever `fib` function is defined inside the block which has a `# dep: test_fib` directive.

To illustrate execution, we will write the code to a file
`examples/fib_slow.py` ...

```python
# file: examples/fib_slow.py
print("starting")
# dep: slow_fib
# dep: test_fib
print("fibs:", fibs)
print("complete")
```

... and then run a command that uses that file.

```python
# run: python3 examples/fib_slow.py
starting
fibs: [0, 1, 1, 2, 3, 5, 8, 13, 21]
complete
# exit: 0
```

The `run` directive invokes a command (in this case `python3 examples/fib_slow.py`), captures its output and writes the captured output back into the block, directly after the `# run: python...` directive.

We needn't have written to a temporary file first. Many interpreters support execution of code that is given via [`stdin`][href_wiki_std_streams], as is the case with python. The `exec` directive makes it possible to skip the temporary file.

[href_wiki_std_streams]: https://en.wikipedia.org/wiki/Standard_streams

```python
# exec: python3
# dep: slow_fib
# dep: test_fib
print("ok")
```

The `exec` directive invokes a command (in this case `python3`), which receives the expanded block (after substitution of all `dep` directives) via its stdin.
If the [exit status][href_wiki_exit_status] of the `python3` process were anything other than the expected value of `0`, then the LitProg build will fail. This is an important point:

[href_wiki_exit_status]: https://en.wikipedia.org/wiki/Exit_status

<center>
The mere existence of the HTML or PDF that you are reading,
is a kind of "proof"[^fnote_max_hedging].<br/>The documentation artifacts would not exist,<br/>if any command exited with an unexpected exit status.
</center>

To accept as proof, something that is not visible may not be satisfying. As with the `run` directive, the output is captured for the `exec` directive, however it is only written back to the markdown file, if there is a block with an `out` directive directly afterward.

```python
# out
ok
# exit: 0
```

[^fnote_max_hedging]: Any "proof" of correctness is only as good as the assertions made by the programmer. Hopefully the accessibility of LitProg programs to more readers, means that programmers will feel it more worthwhile make the effort to demonstrate the correctness of their programs.

!!! aside "Options of `run` and `exec`"

    - `expect`: The expected exit status of the process. The default value is `0`.
    - `timeout`: How many seconds a process may run before being terminated. The default value is `1.0`.
    - `hide`: If the block should be hidden from generated documentation. Using this goes against the ethos of Literate Programming, but if your readers don't care about the assurance that they have access to the full program (for example if you're using LitProg to write a blog article) then this may be appropriate. The default value is `false`


### Capturing Output

While assertions and an exit status are nice, it will often be better to show some output generated by a program. The previous process didn't write anything to `stdout` or `stderr`, so let's run another which does.

```python
# exec: python3
# dep: slow_fib
for i in range(9):
    print(fib(i), end=" ")
```

The output of a process is always captured but is only made visible in a subsequent block with an `out` directive.

```shell
# out
0 1 1 2 3 5 8 13 21
# exit: 0
```

The `out` directive marks its block as a container for the output of the process that was previously run. When the LitProg build is completed, the contents of the `out` block is updated in-place with the captured output when the `-i/--in-place-update` option is used. If there is no `out` block after an `exec` block, then the captured output is discarded.

!!! aside "Options of `out`"

     - `proc_info`: A format string used to customize the process info that is appended to output blocks. It can be set to "none" to supress the process info. The available info is `exit`, `time` and `time_ms`. The default is `exit: {exit:>3}`.
     - `max_lines`: The maximum number of lines to keep of the captured output. default `10`
     - `max_bytes`: The maximum number of bytes to keep of the captured output. default `1000`
     - `out_prefix`: A string which is used to prefix every line of the stdout. default `""`
     - `err_prefix`: A string which is used to prefix every line of the stderr. default `"! "`


The captured output gives the reader some assurance that the document they are reading is not just some manually composed fabrication which was written as an afterthought and is detached from the actual program. Even with the best of intentions, humans often make mistakes, so program logic that has not been executed by a machine will inspire little confidence.

The exit status and the captured output are demonstrations that at least on one machine and at some point in the past, the program was in some sense "correct", or at least that the generated documentation is consistent with the program that was used to generate it[^fnote_max_hedging]. This approach to including program output in generated documentation gives readers a chance to see if the author is trying to hide how the sausage is made. While it may be appropriate to relegate certain logic to an appendix, for example to avoid distraction from a desired narrative, the entire program can in principle be made accessible to inquisitive readers. They may still have to trust that the author is acting in good faith, but at least the issues of outdated documentation and casual errors due to forgetfulness of the author is greatly mitigated.

By this point I hope you can see, that LitProg allows you to write:

1. documentation,
2. source code
3. automated tests

These can all be combined in a way that allows you to create a narrative that makes the most sense to understand your program.


## Interlude on Motivation

By now you have had a taste of how LitProg works, so I'd like to interject some comments on why you might want to use LitProg.


### In-Place Updates of Fenced Blocks

Validating that a program is correct, is not only important to communicate to readers, it is also part and parcel of the programming workflow. Most programmers are the first that want to know if their program is working or broken. Generating HTML/PDF documentation takes a bit of time and switching back and forth between a browser/pdf viewer and a code editor would introduce some friction into the programming workflow. To avoid this friction, LitProg can instead do in-place updates to the original Markdown files. The output that is captured during a build is inserted into the Markdown text. This works well for editors that detect and automatically reload files that have changed. When using `'litprog watch'` programmers can simply hit save and see the updated output of their program appear directly in their text editor.

This approach also has the advantage that output of the most recent execution and viewing the Markdown files on github/gitlab/bitbucket can give a good idea of what the generated documentation will look like. Reviewing the diff of a commit can also demonstrate the behavioral change caused by a change in the source code, rather than looking at the output of a separate log file.


!!! warning "The Pitfalls of Rewriting Input Files"

    Modifying the Markdown files as they are being edited by a programmer can cause some issues. These issues are similar to those encountered when using code formatters that do in-place updates of source code files: What happens if the file is edited again before the in-place update is completed?

    LitProg will only update your Markdown files if they have not been changed since the start of the build. This still leaves some scenarios where you may see surprising behaviour.

    1. If your editor does not automatically detect the file modification done by the build, you may continue editing and not see the updated output until you somehow manually cause your editor to reload the file.

    2. LitProg will only overwrite changes made *on the file system*; any changes you have made *in the buffer of your editor* which have not been saved yet, will overwrite the build output if you save them. If your editor detects modifications made by the build, it may prompt you with something like "File has changed on disk, do you want to reload the file? [Reload] [Cancel]". Usually you will want to hit "Cancel" in this case, unless you want to discard your recent changes.

!!! aside "Deterministic Output"

    You can minimize spurrious updates of your Markdown files by making sure that the output of your program is deterministic. For example the captured output of a python code block that uses `time.time()` or `os.urandom(9)` will usually be different from one build to the next.

!!! warning "The Dangers of Unbounded Output"

    When running a session, the default behaviour of LitProg is to only overwrite an output block using the last 1000 bytes or 10 lines of valid utf-8 output (whichever is less). This prevents your Markdown files from being spammed with program output, for example if you introduce a bug that causes output to be much larger than expected.

!!! info "Escaping Output"

    A corner case of how LitProg processes captured output is when detects three &#96;&#96;&#96; (backtick) or &#126;&#126;&#126; (tilde) characters. These are treated specially if they would cause the code block to be closed prematurly.

    1. If closing the block can be avoided by changing the style of the fence in the original file, LitProg will automatically do so.
    2. If both substrings appear in the output, LitProg will raise an error.

    This behaviour means that readers can be sure that the output they are reading is identical to what was originally captured.


### Programmer Workflow

A critical goal of LitProg is to integrate well with the existing workflows of programmers. You as a programmer should be able to stay in your code editor most of the time. You should be able to use git, github and any existing build systems or tooling. You should be able to focus on your ideas, your code, your narrative and your writing, rather than on document layout, typesetting or an unfamiliar and markup language.

The goal is that you can treat the documentation artifacts almost as an afterthought. Since the Markdown you write corresponds very closely to the generated documentation, there is practically no need to look at the html/pdf output and you can just stay in your editor/IDE (with the obvious exception of embedded content such as images and graphs).


### But Documentation Isn't Agile

Now I know what you're thinking: "I *already* don't spend any time on document layout, formatting, styling and whatever else kinda useless garbage that nobody ever reads anyway. I just don't write *any* documentation, agile freedom baby whooooh!!". Fair enough, and let me also say, if you don't write your program as a Literate Program, that doesn't make you a bad person.

- If your program is a one-off script, almost certainly LitProg isn't the right choice.
- If your program is trivial and nobody other than you will ever work on it, then any effort to create a narrative will be wasted.
- If you are still exploring your problem domain and can't even begin to explain your program, then it may well be fine to put off the LP approach, until you better understand it.

Not all software needs to satisfy lofty goals of being understandable and demonstrably correct.


### Writing Improves Quality

> Writing is nature's way of letting you know how sloppy your thinking is.
>
> – Dick Guindon

The more important the quality of your program is, the more LitProg is worth your consideration.

- If the lifetime of the software you're writing is measured in years.
- If you don't even know all the people who may carry forward the torch you are lighting.
- If you can't get away with code that is so obtuse that others might think it's primary function is job security for the original author.

> Linus's Law: Given enough eyeballs, all bugs are shallow.
>
> – Linus Torvalds

Linus's law is true as far as it goes, but who is to say that you will ever get those eyeballs? Linux may be Free and Open Source and clones of the repository may exist on tens of thousands of computers, but how many people even make an attempt to understand any given part of its code? Getting eyeballs is not just a matter of making code available, it is also a matter of making it accessible.

Incidentally, Linus also said the following:

> what I hope people are doing is trying to make, not just good code, but
> these days we've been very good about having explanations for the code.
> So commit messages to me are almost as important as the code change
> itself.

This obviously depends on your workflow, but personally I almost never read commit messages. If they are read at all, it is once as part of a review process and never again. If these messages truly are valuable, then I think it would be better to keep explanatory prose together with the code itself, rather than hidden away in the commit history.


## Example Continued

### Creating Files

It might be enough for academics if LitProg were only to produce documentation, but most other people want to have artifacts that are more useful, such as an actual program. In the most simple case you can use the `file: <filename>` directive to generate files.

```python
# file: examples/fib.py
# dep: slow_fib
for i in range(12):
    print(f"fib({i:>2}) -> {fib(i):>3}  ", end=" ")
    if (i + 1) % 3 == 0:
        print()
```

!!! aside "Cross Platform Filenames"

    Paths in LitProg always use the `/` (forward slash) character, even if you are running on a Windows machine. Avoid using absolute paths, so that your program can be built on machines with different directory layouts.


The `run: <command>` directive  combines `exec` and `out`, except that unlike `exec`, the process will not receive anything via stdin. This is not too limiting however, as commands are only run after all `file` directives have been written, so you can execute your program via a previously written file (instead of feeding in the program via stdin, as is the case for `exec`). Let's try this for the `examples/fib.py` created by the previous block.

```bash
# run: python3 examples/fib.py
fib( 0) ->   0   fib( 1) ->   1   fib( 2) ->   1
fib( 3) ->   2   fib( 4) ->   3   fib( 5) ->   5
fib( 6) ->   8   fib( 7) ->  13   fib( 8) ->  21
fib( 9) ->  34   fib(10) ->  55   fib(11) ->  89
# exit: 0
```

<!--

### The `amend` Directive

!!! aside "This directive is pending further evaluation"

    Since you can always just edit the original block, the usefulness of
    this directive is questionable. This will be revisited after some
    more example programs have been written.

If you're writing a full program or module, it will often make sense to
gradually build up certain parts of it. A typical example of this are
imports at the top of a module. For some imports that are used broadly
across your program, it may make sense to define them early or in some
appendix with boilerplate code.

For other imports, it may make more sense to introduce them closer to
their usage site. Here we setup a block `imports` which can be updated
from other sections and finally included at the top of the module we're
creating. Usage examples of `amend: imports` follow shortly.

!!! aside "Order when using `amend`"

    The order of blocks with `amend` directives is the same as they appear in the Markdown file.

    - You cannot use `amend` with blocks that are defined in another file.
    - You cannot use `amend` before the block with the corresponding `def` directive.

-->

### Porcelain vs. Plumbing

The `pretty_print_fibs` function prints a formatted string of the Fibonacci numbers in the given range given by the parameter `ns: Sequence[int]`.

```python
# def: pretty_print_fibs
def pretty_print_fibs(ns: Sequence[int]) -> None:
    """Calculate Fibbonacci numbers and print them to stdout."""
    # dep: pretty_print_fibs_impl
```

This is a typical example of code that is not considered part of the
core/plumbing of a program, but rather porcelain. As such it's OK for code
to not be documented so well. A deep understanding of such porcelain code
will contribute little to the understanding of a program. Oftentimes it is
better to start with some example code that demonstrates its behaviour,
rather than with the full implementation.

```python
# exec: python3
# dep: imports, slow_fib, pretty_print_fibs
pretty_print_fibs(range(15))
```

```shell
# out
fib( 0) =>   0  fib( 1) =>   1  fib( 2) =>   1
fib( 3) =>   2  fib( 4) =>   3  fib( 5) =>   5
fib( 6) =>   8  fib( 7) =>  13  fib( 8) =>  21
fib( 9) =>  34  fib(10) =>  55  fib(11) =>  89
fib(12) => 144  fib(13) => 233  fib(14) => 377
# exit: 0
```

This also illustrates the use of forward references in LitProg. LitProg does multiple passes over the blocks of your program. It first collects all `def` directives and then recursively resolves all `dep` directives and finally it evaluates any `exec` or `run` directives. In other words, it is fine to define parts of your program in an order that suits your narrative rather than linearly the way your compiler/interpreter requires them to be defined.

Finally the actual implementation (which most people will and should just skip).

```python
# def: pretty_print_fibs_impl
fibs = [fib(n) for n in ns]

pad_n     = len(str(max(ns)))
pad_fib_n = len(str(max(fibs)))

for i, (n, fib_n) in enumerate(zip(ns, fibs)):
    in_str = f"fib({n:>{pad_n}})"
    res_str = f"{fib_n:>{pad_fib_n}}"
    print(f"{in_str} => {res_str}", end="  ")
    if (i + 1) % 3 == 0:
        print()
```


### Optimizing

Now that we have some code that works, and which we can also see is correct, it's time we turned to optimization.

```python
# def: fast_fib
_cache: dict[int, int] = {}

def fast_fib(n: int) -> int:
    if n < 2:
        return n
    elif n in _cache:
        return _cache[n]
    else:
        _cache[n] = fast_fib(n - 1) + fast_fib(n - 2)
        return _cache[n]
```

We can run the same validation code as before, the only difference being that we replace `fib` with `fast_fib`

```python
# exec: python3
# dep: imports, slow_fib, fast_fib
fib = fast_fib
# dep: test_fib
```

```python
# out
# exit: 0
```

So far so good, the `exit: 0` shows that that `fast_fib` is just as correct as the original `fib` function (the assertions ran through without any errors), but how do we know that it's any faster? Let's write something to time an arbitrary block of code.

```python
# def: timeit
# dep: imports

@contextlib.contextmanager
def timeit(marker=""):
    t_before = time.time()
    yield
    t_after = time.time()
    duration_ms = 1000 * (t_after - t_before)
    print(f"{marker} {duration_ms:9.3f} ms")
```

!!! aside "One time imports"

    Since we're only using this `timeit` code once, we don't add the imports to the `imports` block, which we'll be using later in a module where we don't want to have superflous imports.


```python
# exec: python3
# dep: imports, timeit, slow_fib, fast_fib
with timeit("slow"): fib(12)
with timeit("slow"): fib(16)
with timeit("slow"): fib(20)
with timeit("fast"): fast_fib(12)
with timeit("fast"): fast_fib(16)
with timeit("fast"): fast_fib(20)
```

```shell
# out
slow     0.172 ms
slow     1.037 ms
slow     7.021 ms
fast     0.024 ms
fast     0.008 ms
fast     0.007 ms
# exit: 0
```


### Writing Code to Disk

Up to here our code has been floating around in memory, but eventually we want to produce something that is useful, such as a program that our users can run. In other words, we want to write our code to disk so that it can either be used directly, or further processed by a compiler.

Next is some boring python scaffolding to wrap the functions written so far.

```python
# def: parse_args
Flags = set[str]
Params = list[str]

def parse_args(args: list[str]) -> tuple[Flags, Params]:
    flags = {arg for arg in args if arg.startswith("-")}
    params = [arg for arg in args if arg not in flags]
    return (flags, params)
```

```python
#!/usr/bin/env python
# def: fib_cli_impl
# dep: imports

__doc__ = f"""Usage: python {__file__} [--help] [--pretty] <n>..."""

# dep: slow_fib, fast_fib
# dep: pretty_print_fibs
# dep: parse_args
# dep: main
```

```python
# def: main
def main(args: list[str] = sys.argv[1:]) -> int:
    flags, params = parse_args(args)
    # dep: args_check

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

Don't worry if you're not familiar with python or top level scripts. The noteworthy thing about preceding block is the `dep` directive inside the `main` function.

The first thing in `main` is to validate the arguments to the script and either print a help message or an error message.

```python
# def: args_check
if not args or "--help" in flags or "-h" in flags:
    print(__doc__)
    return 0

invalid_params = [n for n in params if not n.isdigit()]
if any(invalid_params):
    print("Invalid parameters: ", invalid_params)
    return 1
```

Note that `dep` expands indentation to the level of the comment which holds the directive. In other words, every line of the block that is included is prepended with indentation according to where it is included and the block where it is defined does not have to anticipate the indentation level where it will be included.

Finally after we have prepared all our code, we can write it to disk...

```python
# file: examples/fib_cli.py
# dep: fib_cli_impl
```

...and give it a spin.

```bash
# run: python3 examples/fib_cli.py --help
Usage: python /home/mbarkhau/foss/litprog/examples/fib_cli.py [--help] [--pretty] <n>...
# exit: 0
```

```bash
# run: python3 examples/fib_cli.py 22
17711
# exit: 0
```

```bash
# run: python3 examples/fib_cli.py --pretty 3 7 8 9 18 20
fib( 3) =>    2  fib( 7) =>   13  fib( 8) =>   21
fib( 9) =>   34  fib(18) => 2584  fib(20) => 6765
# exit: 0
```

```bash
# run: python examples/fib_cli.py invalid argument
# expect: 1
Invalid parameters:  ['invalid', 'argument']
# exit: 1
```

## Dependencies

So far, each process could run independently. Unless you declare dependencies explicitly, `litprog build` will execute processes concurrently and in any order. If a block with and `exec` or `run` directive has a dependency on another, then they must be declared with the `requires: <identifier>` directive. A block with such a directive will only execute after the specified block.

!!! aside "Why, oh why, does every tool need a new build system?!"

    In my defense, I don't feel that I'm reinventing the wheel, rather I'm reimplementing an existing and vernerable wheel called `make`. If you are familiar with make, it should be easy for you to learn the build system of LitProg.

    Even if LitProg were a reinvention of the wheel, since output generated by earlier phases of a LitProg build can be used by later phases (for example test results can be shown in output documents), it makes sense to have the build system be integrated, rather than using separate tool.

    Many large programs use a build system to produce their final artifacts, such as binaries or packages. Documenting how to produce these artifacts should at least be possible, otherwise there is a thick curtain behind which the author will be tempted to hide all manner of magical incantations.


### The `requires` Declaration

A `requires` declaration references blocks with an `exec` or `run` directive and a `def: <identifier>` directive. The block with the `requires` declaration will be executed only after all requirements have completed without errors. Blocks with `requires` directives can reference others and form recursive[^fnote_circular_deps] chains of dependencies.

[^fnote_circular_deps]: Circular dependencies are detected and `litprog build` will fail if any are found.

As an example use case, we will generate a dataset for timings of our function and then plot the dataset.

```python
# def: save_bar_plot
import pandas as pd

def save_bar_plot(series: pd.Series, path: str, **kwargs) -> None:
    # I am aware that this is manipulates global state
    # and I don't like it either. I can't be bothered
    # to deal with this anymore.
    plot = series.plot.bar(legend=None, colormap="gray", **kwargs)
    plot.axes.xaxis.set_visible(False)
    plot.figure.set_size_inches((3.5 * 1.78, 3.5))
    plot.figure.savefig(path, transparent=True)
```

We declare plotting code first, before the code that generates the file it depends upon. When running `litprog build` with `-e/--exitfirst` or `-n/--concurrency=1`, each block is usually executed in order of declaration, which would satisfy the requierment implicitly, rather than explicitly via the `requires: gen_fib_durations_csv` declaration.

```python
# exec: python3
# dep: imports, save_bar_plot
# requires: gen_fib_durations_csv
import pandas as pd

def mtime(path: str) -> float:
    return os.stat(path).st_mtime

csv_path = "examples/fib_durations.csv"
svg_path = "lit_v3/static/overview_fib_durations.svg"

df = pd.read_csv(csv_path, header=0, names=["n", "us"])
save_bar_plot(df['us'], svg_path, logy=True)

assert os.path.exists(svg_path) and mtime(svg_path) >= mtime(csv_path)
```

![](static/overview_fib_durations.svg)

```python
# exec: python3
# def: gen_fib_durations_csv
# dep: imports, slow_fib
# timeout: 60
def csv_lines() -> list[str]:
    for n in range(22):
        tzero = time.time()
        fib(n)
        duration_us = round((time.time() - tzero) * 1000_000)
        yield (n, duration_us)

rows = [",".join(map(str, row)) for row in sorted(csv_lines())]
csv_text = "\n".join(["n,us"] + rows)

with open("examples/fib_durations.csv", mode="w") as fobj:
    fobj.write(csv_text)
```

```bash
# run: bash -c "tail -n 5 examples/fib_durations.csv"
# requires: gen_fib_durations_csv
17,1653
18,2590
19,4215
20,6839
21,11042
# exit: 0
```


### Statefulness and Caching

For LitProg to be useful as an every-day development tool, it is essential that it introduce as little friction as possible into the developer workflow. Fast build times are essential to this goal and to that end, LitProg makes heavy use of caching.

By default, an executable block is assumed to be pure/stateless. This means that the output it generates is cached on disk. If the dependencies of a block have not changed, the cached results will be reused. A block that produces a side effect (such as writes to file on disk or a database update) does not satisfy this assumption (i.e. they are stateful). One way to deal with this, is to generate output based on the side effects. If a block causes writes to a file for example, you could also write a hash of these files to the `stdout` of the subprocess, thereby propagating the mutated state and causing the cache to be invalidated. The downside of this

then you should make sure that. can mark that block with the declaration `pure: no`. All direct dependencies of an "impure" block will be executed, even if the output to `stdout` and `stderr` do not change.


## Appendix

```python
# def: imports
import os, sys, math, time
import contextlib

from typing import Sequence
```
