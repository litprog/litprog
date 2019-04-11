# LitProg - Programs for Humans

```yaml
lptype: meta
title: LitProg
subtitle: Programs for Humans
language: en
authors: [
    "Manuel Barkhau",
]
```

[TOC]

    Der Mensch ist doch ein Augentier,
    nur schöne Dinge wünsch' ich mir.
    
        – Goethe


LitProg is a markdown based literate programming tool which can be used together with most[^languages_caveat] programming languages. A literate program is written, first and foremost, to be understood by other people and not merely to be valid input for a compiler or interpreter.


## Costs and Benefits

Literate programming is not a silver bullet. Rather it offers al tradeoff that is quite similar to the practice automated testing: An initial investment/upfront cost which hopefully produces a long term payoff. Creating automated tests is reduces the chance that changes to a program will break existing functionality. They are a safety net that limit the damage a programmers can cause when they don't understand all of the implications of a change that they want to make.

In the case of literate programming, technical documentation is written to explain the intent and high level abstractions. This allows other programmers to rebuild the mental model that is required to verify the correctness of a program and to effectively make changes. Some of these can be expressed in program structure and with good naming, but code has to be valid which limits how expressive . Programmers who are introduced long after the initial authoring of the program will have an easier time building a mental model of the program and thus will more readilly be able to recognize flaws and make changes. , which cannot be easilly read just from reading the code. This makes it easier for programmers who are unfamiliar with the code to find their way around the codebase and more confidently make changes.

For short lived projects by a single author, with no human audience, writing in a literate programming style may not make much sense. The more people th

### Visibility

With automated testing, when using a continuous integration environment, members of the project who are not intimately involved in the details of the code-base can gain some insight into the health of the codebase. Programmers who diligently write tests with high coverage can keep themselves honest and the temptation to cut corners is either kept in check or at the very least exposed. If coverage goes down, if builds are failing and if deployments are happening anyway, then all of this may be justified in the context of a project, but it is a sure sign of degeneration in the standards of the project and may reduce the long-run viability of the project.

Literate programming offers a similar kind of exposure. Programmers who express the intent, the abstractions, the work-arounds and the trade-offs in plain english, who express ideas that are not expressed in the code, will keep themselves more honest as they can assume that their peers will not simply gloss over an undocumented and cryptic part of the codebase. If they simply hack together some code and only half understand what it's actually doing, then the lack of or incoherence of documentation will more readilly expose the degraded health and long-run viability of the project.

### Narrative Order vs Program Order

In terms of code, a definition usually has to preceed its usage. For narrative purposes it may be more appropriate to start with foundational datastructures and high level logic, assuming some prior knowledge about programming convetions, before proceeding to how everything fits together. Often it may be more appropriate to start by looking at code that uses an api and then go on to show how the api is implemented.

When a reader is reading your text, they are building up a context in their mind. If a new concept is introduced to them, it should be understandable to them either based example code which demonstrates how to use it and/or based on definitions and concepts that closely preceeded the introduction of the new concept or are known because they well established. Taken to the extreem, defintions would always preceed their usage and the topics of actual interest to a reader would only be introduced after pages and pages of boilerplate.


## MVP

The initial implementation of LitProg is the bare bones minimum needed to start dogfooding the program itself. The initial goal is to

 1. Have an existing `litprog` command that accepts markdown files as inputs.
 2. Compiles python files in a temporary directory.
 3. Executes tests againts the compiled files and aborts if tests fail.
 4. Installs the new version of the command if the tests pass.

For now we will completely ignore the output as pdf/html tables, footnotes,
images or anything else.

Of course we have a chicken and egg problem here, so to bootstrap the program the python files will have to be implemented in a non LitProg form. For development the easiest python files to work are the ones in the `src/` directory. Using `source activate` and running `pip install .` will install the `litprog` command, which will use code from the `src/` directory. As soon as possible the program should be self hosted.
## Glossary

- [Input] Source Files: Markdown based inputs
- [Output] Code Files: An artifact generated from fenced code blocks
- [Output] Documents: HTML or PDF files

## The Goal

There are various levels at which the reader of a literate program will want to understand it, but each of them should trust that the fact that they are viewing a document meands that it conceptually coherent. This is to say, that if the document contains assertions about how it works, then the existence of the document is a testament to the fact that these assertions are true.

If the following code were to fail, the output document would have programatically generatiod visual indication that this was the case.

```yaml
lpid   : demo
lptype : session
command: python3
timeout: 1
echo   : False     # output
term   : True
expected_exit_code: 1
```

```python
# lpid = demo
assert True
```

```python
# lpid = demo
# This code block inherits the LitProg declarations of
# the previous block. In this case it is a continuation of the previous
# "validation" session.
print(1 + 1)
assert False          # The captured output should be an error
```

In order to make integration with existing tools easy and so that LitProg is language agnostic, the macro and plugin system works strictly with text, and does not do any ast/parsing of code blocks. The exception to this is LitProg metadata in the form of code block options.

- `litprog` declarations for code blocks use language specific comment syntax.
  In other words, a LitProg declaration in a python code block the first line
  would start with `# litprog` and in a c++ code block the code the first line
  would start with `// litprog`. This choice was made

## Compile/Build Phases

Some of the considerations that go into what the phases of the compiler do
are

- Plugins/Libraries that do pre- or post-processing and are only referenced.
  Some plugins might be, spell checker, readability score generator, and
  linters.
- We want to be able to integrate code formatters, in other words feed the
  output of a command which takes a fenced code block as input and feeds it
  back into the initial fenced code block.
- To reduce boilerplate, we want to have macros. But other than for
  demonstration of what the macro does, we don't want the code generated by
  them to be in the pdf files (maybe in the html files, but only if it is
  hidden by default).
- LitProg is a build system and the declaration of output files should allow
  for caching/reuse of build artifacts. TODO: investigate `redo` which is
  supposidly a nicer version of `make`.

To produce a program

 0. Run macro definition code blocks.
 1. Run macros to produce intermediate markdown.
 2. Compile code artifacts to tmp directory.
 3. Run interactive sessions and capture outputs.
 4. Produce code artifacts.
 5. Produce intermediate html artifacts from original markdown.
 6. Extend intermediate html artifacts with captured outputs.
 7. Extend intermediate html by running plugins, for example to add anchor tags that enable jump to definition.
 8. Produce pdf artifacts from html.


[^click_lib_ref]: https://click.palletsprojects.com

[^languages_caveat]: Any language as long as its code is stored in text based files. This is almost all languages, but LitProg won't work with something like scratch.
