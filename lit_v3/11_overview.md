# Introduction to LitProg

LitProg is a [literate programming][ref_wiki_litprog] tool which 

 1. uses [markdown][ref_wiki_markdown] files as input,
 2. generates code files using fenced blocks,
 3. generates documentation in HTML and PDF formats.

```bob
                   +------------------+        
                  ++                  |\       
                  || lit/11_intro.md  +-+      
       .----------+* lit/12_test.md     |      
       |          || lit/13_impl.md     |      
       V          ||                    |      
 .-----------.    |+-------------------++      
 |           |    +--------------------+       
 |  LitProg  |                                 
 |           |     +---------------+           
 '---+---+---'    ++               |\          
     |   |        || src/code.py   +-+         
     |   '------->|| src/logic.js    |         
     |            || src/data.json   |         
     |            ||                 |         
     |            |+----------------++         
     |            +-----------------+          
     |                                         
     |             +-------------------+       
     |            ++                   |\      
     |            || doc/11_intro.pdf  +-+     
     '----------->|| doc/11_intro.html   |     
                  || doc/12_test.html    |     
                  ||                     |     
                  |+--------------------++     
                  +---------------------+      
```

## LitProg by Example

Much has been claimed about the benefits of [Literate Programming][ref_knuthweb]. Instead of repeating what has been said better elsewhere, I will focus here on demonstrating by example.

This example is primarilly about the features of LitProg and not the example itself, so I will use the trivial and familiar [Fibbonacci function][ref_wiki_fib] for illustration.

```python
def fib(n: int) -> int:
    if n < 2:
        return n 
    else:
        return fib(n - 1) + fib(n - 2)
```

In case you weren't aware, this function is well known to have an algorithmic complexity of O(₂ⁿ) aka. catastrophic performance. 


### The `lp_include` Directive

The preceding code block is just that, a block, with no further meaning so far. It is neither written to any file, fed through any compiler, nor executed by any interpreter, it just is.

The primary way these blocks are used is by referencing them in subsequent code blocks using the `lp_include` directive. LitProg directives are written using the comment syntax of the programming language declared for the block. 

```python
# lp_include: def fib
assert fib(8) == 21
```

The text after the `:` is a query string that must be a substring of some other block in the literate program. The [first][ref_block_order] block which contains that substring is used as a naive textual replacement for the directive. In other words, the preceding block when s equivalent to the following when fully expanded:

```python
def fib(n: int) -> int:
    if n < 2:
        return n 
    else:
        return fib(n - 1) + fib(n - 2)
assert fib(8) == 21
```

It is often seen critically, to embed program constructs inside of comments which are subsequently parsed, and rightfully so. Considering the context of LitProg, where programmers can use Markdown for documentation, I think this repurposing of the comment syntax is a reasonable compromise, since it 

 1. allows the generated output to preserve the directives that were used for program generation,
 2. allows existing code/syntax highlight and formatting tools to work, without having to implement anything dedicated to LitProg,
 3. always uses the distinctive `lp_<directive>:` syntax and ignores all other comments.

LitProg supports an extensive and easilly expandable list of programming languages.


### Sub-Command Sessions

While the preceding code block is quite simple to understand, the reader is either left to validate what it does for themselves, or to trust the claims of correctness made by the author.

Ideally we might want to execute some code that uses the function we care about abort if something is wrong.

```python
fibs = [fib(n) for n in range(9)]
assert fibs == [0, 1, 1, 2, 3, 5, 8, 13, 21]
```

This is where the perhaps most distinguishing feature of LitProg comes in. Using the `lp_session` directive, you can invoke sub-commands that receive the expanded text of the block as input and the captured output of the session is included in the generated documentation.

```python
# lp_session
# lp_command: python3
# lp_include: def fib
# lp_include: assert fibs == 
```

If the [exit status][ref_wiki_exit_status] of the `python` process were anything other than the expected value `0`, then the documentation would not even have been generated. Here we override the default for a case which we expect to fail.

```python
# lp_session
# lp_expect: 1
assert False
```

!!! note "Options of `lp_session`"

     - `lp_command`: Explicit command for the sub-process. The default is derived based on the language of the session block.
     - `lp_expect`: The expected exit status of the subprocess. The default value is `0`. 
     - `lp_timeout`: How many milliseconds a session may run before being terminated. The default value is `1000`.
     - `lp_capture_limit`: How many bytes from stdout and stderr to keep in a buffer for later use. The defauld value is `10000`.


An exit status is nice and all, but it often it's better to show the captured output. Before we can capture output though, we first have to generate it.

```python
from typing import Sequence 

def pretty_print_fibs(ns: Sequence[int]) -> None:
    fibs = [fib(n) for n in ns]

    pad_n     = len(str(max(ns)))
    pad_fib_n = len(str(max(fibs)))

    for n, fib_n in zip(ns, fibs):
        in_str = f"fib({n:>{pad_n}})"
        res_str = f"{fib_n:>{pad_fib_n}}"
        print(f"{in_str} => {res_str}", end ="  ")
        if (n + 1) % 3 == 0: 
            print()

    print()
```

This function could be clearer, but sometimes it's ok for code to be a bit gnarly. Readers may not be interested in how every part of a program works, especially when the code is not part of the core logic of the program. A deep understanding of `pretty_print_fibs` will contribute little to the understanding of Fibonacci numbers or of LitProg. The very first line of the function is very straightforward and is also the most important line, everything else deals with padding, line breaks and writing output etc.

```python
# lp_session
# lp_include: def fib
# lp_include: def pretty_print_fibs
pretty_print_fibs(range(21))
```

A review of the output will provide all the understanding we need for `pretty_print_fibs`.

```shell
# lp_ouptut
fib( 0) =>    0  fib( 1) =>    1  fib( 2) =>    1
fib( 3) =>    2  fib( 4) =>    3  fib( 5) =>    5
fib( 6) =>    8  fib( 7) =>   13  fib( 8) =>   21
fib( 9) =>   34  fib(10) =>   55  fib(11) =>   89
fib(12) =>  144  fib(13) =>  233  fib(14) =>  377
fib(15) =>  610  fib(16) =>  987  fib(17) => 1597
fib(18) => 2584  fib(19) => 4181  fib(20) => 6765
```

!!! note "Options of `lp_ouptut`"

     - `lp_max_lines`: default 10
     - `lp_max_bytes`: default 1000

!!! note "Language info string"
    
    Beyond determining which comment syntax to use, the language string at the beginning of any block is meaningless to LitProg. For an `lp_output` block this is perhaps more jarring than for other blocks. The contents of `lp_output` may be quite arbitrary and have little to no relation with the captured output, whereas the usual case is that label of the block should match its contents.

The `lp_ouptut` marks which portion of the Markdown file to overwrite. When the program is compiled, the contents of the block is replaced using the captured output from the session of the immediately preceeding block. The captured output of a session can be ignored simply by not including such a block in the markdown file.

!!! note "The Dangers of Rewriting Input Files"

    Modifying the files that are edited by a programmer is admittedly a dicy proposition. Code formatters do this to some extend already, but there is always a concern that the editor/IDE will not recognize the modification of the underlying file.

    I think the approach is justified, because it is not enough for the captured output to be part of the generated documentation. Validating the correctnes of a program is part and parcel of the workflow of developing a program, so the time spend waiting for the generated documentation and switch back and forth would introduce unnecessary friction to the developer workflow.

!!! note "The Dangers of Unbounded Output"

    When running a session, the default behaviour of LitProg is to only overwrite an output block using the last 1k or 10 lines of valid utf-8 output (whichever is less). This prevents your markdown files from being spammed with program output that is much larger than expected or some kind of binary data.

The captured output gives the reader some assurance, that the document they are reading is not just a manually composed fabrication of the author. Even with the best of intentions, humans are prone to make mistakes, so program logic that has not been executed by a machine will inspire little confidence. The exit status and the captured output are demonstrations that at least on one machine and at some point in time the program was in some sense "correct", or at least that the generated documentation is consistent with the program that was used to generate it.


### Optimizing

Now that we have some code that is good, and which we can also see is correct, it's time we turned to optimization.

```python
from typing import Dict

_fib_cache: Dict[int, int] = {}

def fast_fib(n: int) -> int:
    if n < 2:
        return n 

    if n in _fib_cache:
        return _fib_cache[n]

    _fib_cache[n - 1] = fast_fib(n - 1)
    assert n - 2 in _fib_cache
    return _fib_cache[n - 1] + _fib_cache[n - 2]
```

We can run the same validation code as before, the only differenc being that we swap the implementation of `fib` for our `fast_fib`

```python
# lp_session
# lp_command: python3
# lp_include: def fast_fib
fib = fast_fib
# lp_include: assert fibs == 
```

While this shows that that `fast_fib` is just as correct as the original `fib` function, but how do we know that it is faster?


### Macro Directives

!!! warning "Experimental"
    This is the feature is neither fully specified nor implemented and is subject to change.


```python
# fast_and_slow_fib

# lp_include: def fib
slow_fib = fib
# lp_include: def fast_fib
fib = fast_fib
```

```python
# lp_def_macro: timeit(_EXPR_)
import time
t_before = time.time()
_EXPR_
t_after = time.time()
duration_ms = 1000 * (t_after - t_before)
print(f"{duration_ms:9.3f} _EXPR_")
```

```python
# lp_session
# lp_use_macro: timeit
# lp_include: fast_and_slow_fib
timeit(slow_fib(20))
timeit(slow_fib(21))
timeit(slow_fib(22))
timeit(fast_fib(20))
timeit(fast_fib(21))
timeit(fast_fib(22))
```

```python
# lp_output
```

!!! asside: "`import timeit` is a thing"

    There is a perfectly good builtin module named `timeit`, indeed it is much better than this macro, especially for very fast expressions. The purpose here is to demonstrate the macro functionality of LitProg. 


The simplest macro supported by LitProg is the `lp_const` directive. These can be defined inline or for example inside of a markdown listing.

 - The largest Fibonacci number to calculate: `lp_const: MAX_FIB = 20` 
 - How many numbers to print per line `lp_const: FIBS_PER_LINE = 5`

```python
# lp_session
# lp_include: def fib
print("fib(2..MAX_FIB)")
for n in range(MAX_FIB):
    if n % FIBS_PER_LINE == 0:
        print()
        print(f"{n:>3}", end=": ")
    print(f"{fib(n):>9}", end=" ")
```

The choice of names for such a constant may be influenced by the language being used. If you want make it possible for code formatters to reformat a code block, then the code block must be syntactically valid even if it includes non-expanded macros. 

The preceding example prin
LitProg has support for macros using the `lp_def` directive. These are non-hygenic, can be parameterized and are recursively expanded.

### Writing Code to Disk

Up to here our code has been floating around in memory, but eventually we want to produce something that is useful. A program that our users might like to run. In other words, we want to write our code to disk so that it can either be used directly, or further processed by a compiler.

Next is some boring python scaffolding to wrap the functions written so far.

```python
#!/usr/bin/env python
__doc__ = f"""Usage: python {__file__} [--help] [--pretty] <n>..."""

import sys
from typing import List

# lp_include: def fast_fib
# lp_include: fib = lru_cache(fib)
# lp_include: def pretty_print_fibs
# lp_include: def parse_args

def main(args: List[str] = sys.argv[1:]) -> int:
    params, flags = parse_args()
    # lp_include: if not params or "--help" in flags
    # lp_include: if any(invalid_arguments):

    ns = [int(n) for n in params]
    if "-p" in flags or "--pretty" in flags:
        pretty_print_fibs(ns)
    else:
        for n in ns:
            print(n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

Don't worry if you're not familiar with python or top level scripts. The noteworthy thing about preceeding block are the two `lp_include` directives inside the `main` function. 

The first is to print a help message.

```python
if not args or "--help" in args or "-h" in args:
    print(__doc__)
    return 0
```

The second step in `main` is to validate the arguments to the script. They must all be numerical/decimal digits.

```python
invalid_arguments = [n for n in args if not n.isdigit()]
if any(invalid_arguments):
    print("Invalid arguments: ", invalid_arguments)
    return 1
```

Apart from their function it is important to see how the `lp_include` directive treats indentation. When a block is included, the indent level of the comment which holds the directive is prepended to every line of the included block. In other words the indent level of the included block is the same as the indent level of the directive that includes it.

Finally after we have prepared all our code, we can write it to disk...

```python
# lp_file: examples/fib.py
# lp_include: def main
```

...and give it a spin.

```bash
# lp_session
python3 --version
python3 fib_example.py --help
python3 fib_example.py 22
python3 fib_example.py --pretty 2 5 8 12 19 20
python3 fib_example.py invalid argument
```

```shell
# lp_ouptut 
Python 3.6.7

Usage: python fib_example.py <n>...
123456
fib( 9) =>   34  fib(10) =>   55  fib(11) =>   89
fib(12) =>  144  fib(13) =>  233  fib(14) =>  377

Invalid arguments: ['invalid', 'argument']
```

!!! asside

    Although the final invocation of `fib_example.py` has a non-zero exit status, the session nontheless has an exit status of `0`. This is because python3 is invoced by a bash sub-process, which does not propagate the exit status of a sub-command by default. If we wanted to propagate the exit status we could use [`set -e` / `set -o errexit`][ref_explainsh_errexit].


### Make Directive

So far every session has been independent of every other. In principle the sessions could have been executed in any order, or indeed concurrently to each other. Their dependencies on code blocks are explicitly declared by the `lp_include` directives inside of each session block. 

```
# lp_file: requirements/fib_example
```

```shell
# lp_make: examples/fib_py2py3.py
# lp_deps: examples/fib.py
python -m lib_3to6 examples/fib.py \
    > examples/fib_py2py3.py
chmod +x examples/fib_py2py3.py
```

!!! note "Why, oh why, does every tool need a new build system?!"

    In my defense, I don't feel that I'm reinventing the wheel, rather I'm reimplementing an existing and vernerable wheel called `make`. If you are familiar with make, you should have no problem using the build system of LitProg.

    Many large programs use a build system to produce the final artifacts, such as binaries or packages. Documenting how to produce these artifacts should at least be possible, otherwise there is a thick curtain behind which the reader can . 


```shell
# lp_session
# lp_hidden
set -o errexit
set -o xtrace
python2 --version
python2 examples/fib.py 22
python3 --version
python3 examples/fib.py 22
./examples/fib.py --pretty 2 5 8 12 19 20
```

```shell
# lp_ouptut 
+ python2 --version
Python 2.7.15+
+ python2 examples/fib.py 23
12345
+ python3 --version
Python 3.6.7
+ python3 examples/fib.py 23
12345
fib( 9) =>   34  fib(10) =>   55  fib(11) =>   89
fib( 9) =>   34  fib(10) =>   55  fib(11) =>   89
```



These examples are intended as a quick overview, but there is much more to be said about the how each of these primitive features can be used and misused.

[ref_block_order]: TODO: Link to documentation for definition of "first"

[ref_wiki_fib]: https://en.wikipedia.org/wiki/Fibonacci_number

[ref_wiki_exit_status]: https://en.wikipedia.org/wiki/Exit_status

[ref_explainsh_errexit]: https://explainshell.com/explain?cmd=set+-e