# How to Write LitProg

Best practices for structuring a LitProg project.

TODO: Look into best practices for writing RFC documents
which might make sense.

The Craft of Writing Effectively - Larry McEnerney
https://www.youtube.com/watch?v=aFwVf5a3pZM

Linguistics, Style and Writing in the 21st Century - Steven Pinker
https://www.youtube.com/watch?v=OV5J6BfToSw


## Disclaimer/Caveat Emptor

As of now, these "best practices" are in flux as I figure out and gather feedback on how best to approach this style of programming. It will be updated as I write more and larger literate programs, but for now this chapter represents my best guess at what can work, as well as 

duplication:
This chapter was written without extensive experience writing
a literate programs. The thoughts here are premonitions at
this point and are written to guide the development of litprog
itself.


### Audiences: Purpose Driven Narritive

#### Users

Users are the most common kind of programmer and so they should be
catered to first. The initial chapters of a literate program should
illustrate usage of a program, expressed for example in the form of
test code that invokes the core API of a program. It should be
possible to read this documentation like an essay from beginning

#### Newbies

#### Contributors

#### Reader Expectations/Prerequisites

 - Knowledge level for programming language/tools
 - Project setup
 - Background Knowledge
 

### Types of Documentation

In the case of literate programming, technical documentation is written to explain the intent and high level abstractions. This allows other programmers to rebuild the mental model that is required to verify the correctness of a program and to effectively make changes. Some of these can be expressed in program structure and with good naming, but code has to be valid which limits how expressive . Programmers who are introduced long after the initial authoring of the program will have an easier time building a mental model of the program and thus will more readilly be able to recognize flaws and make changes. , which cannot be easilly read just from reading the code. This makes it easier for programmers who are unfamiliar with the code to find their way around the codebase and more confidently make changes.


### Narrative Order vs Program Order

In terms of code, a definition usually has to preceed its usage. For narrative purposes it may be more appropriate to start with foundational datastructures and high level logic, assuming some prior knowledge about programming convetions, before proceeding to how everything fits together. Often it may be more appropriate to start by looking at code that uses an api and then go on to show how the api is implemented.

When a reader is reading your text, they are building up a context in their mind. If a new concept is introduced to them, it should be understandable to them either based example code which demonstrates how to use it and/or based on definitions and concepts that closely preceeded the introduction of the new concept or are known because they well established. Taken to the extreem, defintions would always preceed their usage and the topics of actual interest to a reader would only be introduced after pages and pages of boilerplate.



### Write Drunk, Edit Sober

#### Phases

- Prototype
    + Abstract
    + Hack
- Dev Loop
    + Test
    + Hack/Refactor
- Automated Review Loop
    + Stats (Coverage/Typecheck/Spellcheck/Readability)
    + Fix/Refactor/Edit
- Collaborative Review Loop
    + Feedback
    + Fix/Refactor/Edit



### Writing Workflow

When writing, don't interrupt your flow, just write. Edit on a
second pass, when you feel you've expressed your ideas well.
Similarly, write code using your unittests, in a flow of red,
refactor, green. On a second pass run the formatter linter
and type checker to make sure you have dotted every "I" and
crossed every "t".

There is a recommended practice that says "PEP8 only unto
thyself", which is an admonishment to not correct other peoples
mistakes, but to allow them to correct them themselves. Well,
there are mistakes and then there are mistakes. Fixing other
peoples typos and linter errors has the risk of building
resentment. Either the person doing the fix resents that the
original author is lazy and sloppy to not have their tools set up
correctly, or the author resents being nitpicked at by a
coleague. The communication overhead involved in the back and
forth to report these minute issues, to communicate why something
is an issue, and to verify that the issue was fixed correctly,
can be much higher than simply fixing the issue in place. As an
editor, just fix the issue, point to the rule or just reproduce
the complaint of the linter.

To bot curb lazyness and sloppyness, and encourage a culture of
code review, I suggest a light hearted approach. Since developers
should have their tooling set up correctly correctly and
established muscle memory actually use that tooling, it is fair
to play the following game: Any build which fails because of a
trivial error which could have been caught by a linter,
introduces a debt


### Cowboy Programming

Inevitably you may want to bypass all of the best practices
because you are short on time and know what you're doing. Since
LitProg only compiles to code which then is run separately, it is
easy for a cowboy to directly write code outside of litprog and
bypass all the linters and checkers it runs. In order to reduce
the temptation to do this, you can mark a file or peace of code
with a quality assurance level to control the build process of litprog:

 - `qa-disabled`
 - `qa-minimal`
 - `qa-full` (default)

Only under extrodenary circumstances should you have to mark code
with qa-disabled, very rarely and only for short periods (until
you have the time to refactor) should code be marked with
`qa-minimal`. `qa-full` reenables full checking for portions of
a file which has a lower qa level set at the file level.




#### Flow and Productivity

## Philosphy

### Write as if Your Code Will be Maintained by Your Child

This project is born out of disapointment in the quality of the
software we produce and consume. Everything is not bad and one
should always take the constraints of developers and markets into
consideration. Programmers are not always lazy and managers are
not always short sighted, at the end of the day features must be
shipped and payroll must be met. LitProg is an attempt to raise
the bar of software quality by

 1. Providing tooling that can be used in any project
 2. Leading by example.

LitProg will succeed or fail based on how well it can show to
programmers that it is easier for them to understand a program
written with LitProg and to organizations that this implies lower
long term costs and greater ability to adapt software to new
needs as they arise. LitProg produces html and pdf artifacts, so
that programs written with LitProg become more accessible to
people with little experience in version control or programming.
This increased visibility may help to expose poorly documented
and highly convoluted code, helping to justify the time needed
to improve its quality.



## Who is your reader?

There are three roles a reader may occupy that a literate program
needs to cater to.

 1. Users: Programmers who want to import and use the program and
    who are primarilly interested in using the public API of the
    program but otherwise want to treat it as a black box.
 2. Newbie: Programmer trying to (re)gain understanding of a
    program.
 3. Contributor: Programmers and editors familiar with the source
    text and structure, trying to extend or fix a part of it.

These are not fixed categories, rather they are roles and the same
person may have multiple roles at different times. A developer
may be a contributor in one part of a program, a newbie of another
part and a user of yet another, all at the same time. The purpose
of these roles is to scope what part of a text is relevant for
each role, so a developer can focus their attention.
