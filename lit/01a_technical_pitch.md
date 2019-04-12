## Why use LitProg?

You probably shouldn't, there are good reasons it has not found wide adoption in industry or Open Source and we will go into those in this chapter.

## MVP

The initial implementation of LitProg is the bare bones minimum needed to start dogfooding the program itself. The initial goal is to

 1. Have an existing `litprog` command that accepts markdown files as inputs.
 2. Compiles python files in a temporary directory.
 3. Executes tests againts the compiled files and aborts if tests fail.
 4. Installs the new version of the command if the tests pass.

For now we will completely ignore the output as pdf/html tables, footnotes,
images or anything else.

Of course we have a chicken and egg problem here, so to bootstrap the program the python files will have to be implemented in a non LitProg form. For development the easiest python files to work are the ones in the `src/` directory. Using `source activate` and running `pip install .` will install the `litprog` command, which will use code from the `src/` directory. As soon as possible the program should be self hosted.

### Costs and Benefits

[Literate programming][ref_wiki_litprog] is not a silver bullet. Rather it offers a tradeoff that is quite similar to the common industry practice of automated testing: An initial investment/upfront cost which hopefully produces a long term payoff. Creating automated tests often takes more time than doing ad-hoc manual tests, but in the long run they reduce the chance that changes to a program will break existing functionality. They are a safety net that can limit the damage a programmer causes when they don't understand every implication of a change that they want to make.

Writing a literate program is quite similar, in that it is a greater effort to write documentation in addition to just the program code that is required to solve a problem/implement a solution. 

Just as slow and brittle tests can be a burdon for developers, bad documentation can not only be , then the time spend may not be just wasted, 

For short lived projects by a single author, with no human audience, writing in a literate programming style may not make much sense. The more people th


## The Mind of the Reader

There are various levels at which the reader of a literate program will want to understand it, but each of them should trust that the fact that they are viewing a document meands that it conceptually coherent. This is to say, that if the document contains assertions about how it works, then the existence of the document is a testament to the fact that these assertions are true.


### Proof of Correctness

The purpose of the narrative is not only to document for the reader how a program works, but to demonstrate to them by the mere fact of the existence of the document they are reading, that program is correct.

To this end, the `litprog build` command will generate program code, will also execute code in `session` blocks, which can contain code to demonstrate usage, test correctness and to generate images. The output of these `sessions` is caputred and rendered in html/pdf files.